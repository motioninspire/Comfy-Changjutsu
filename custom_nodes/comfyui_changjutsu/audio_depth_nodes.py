"""Changjutsu audio + depth helpers — tiny nodes the motion-disguise pipeline needs.

AudioPitchShift: shift an AUDIO by N semitones (torchaudio phase vocoder).
Used to send isolated, pitch-shifted vocals to API backends so they lip-sync
without the audio fingerprint matching the original recording.
"""
import torch
import torchaudio.functional as TAF


class AudioPitchShift:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "semitones": ("FLOAT", {"default": 3.0, "min": -24.0, "max": 24.0, "step": 0.5,
                                         "tooltip": "Positive = higher. +3 is enough to defeat audio fingerprinting while staying intelligible."}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "shift"
    CATEGORY = "audio/changjutsu"

    def shift(self, audio, semitones):
        wav = audio["waveform"]          # [B, C, T]
        sr = int(audio["sample_rate"])
        if abs(semitones) < 1e-6:
            return (audio,)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        out = []
        for b in range(wav.shape[0]):
            x = wav[b].to(device=device, dtype=torch.float32)
            # torchaudio pitch_shift works on [..., time]; process per batch item
            y = TAF.pitch_shift(x, sr, n_steps=float(semitones), bins_per_octave=12,
                                n_fft=2048, win_length=2048, hop_length=512)
            out.append(y.cpu())
        y = torch.stack(out, 0)
        y = torch.clamp(y, -1.0, 1.0)
        return ({"waveform": y, "sample_rate": sr},)


class AudioGain:
    """Simple linear gain + optional peak normalise (keeps vocals audible after separation)."""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "gain": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.05}),
                "peak_normalize": ("BOOLEAN", {"default": True}),
                "peak": ("FLOAT", {"default": 0.9, "min": 0.1, "max": 1.0, "step": 0.05}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "apply"
    CATEGORY = "audio/changjutsu"

    def apply(self, audio, gain, peak_normalize, peak):
        wav = audio["waveform"].clone() * gain
        if peak_normalize:
            m = wav.abs().amax()
            if m > 1e-6:
                wav = wav * (peak / m)
        return ({"waveform": torch.clamp(wav, -1.0, 1.0), "sample_rate": audio["sample_rate"]},)


class MaskedDepthNormalize:
    """Per-frame contrast stretch of a grayscale image *inside a mask* to [low, high].

    Depth maps normalised over the whole frame put a person at one flat end of the
    range (person-to-backdrop distance dominates). Normalising only inside the people
    mask restores shading on arms/torso/head, and capping `high` below 1.0 keeps white
    pose/face dots visible on top.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "low": ("FLOAT", {"default": 0.08, "min": 0.0, "max": 1.0, "step": 0.01}),
                "high": ("FLOAT", {"default": 0.55, "min": 0.0, "max": 1.0, "step": 0.01}),
                "invert": ("BOOLEAN", {"default": False, "tooltip": "On = nearer is darker."}),
                "percentile": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.5,
                                          "tooltip": "Clip this % at both ends before stretching (robust to outliers)."}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "run"
    CATEGORY = "image/changjutsu"

    def run(self, image, mask, low, high, invert, percentile):
        img = image.clone()                       # [B,H,W,C]
        B, H, W, C = img.shape
        m = mask
        if m.dim() == 2:
            m = m.unsqueeze(0)
        if m.shape[0] == 1 and B > 1:
            m = m.expand(B, -1, -1)
        if m.shape[-2:] != (H, W):
            m = torch.nn.functional.interpolate(m.unsqueeze(1), size=(H, W), mode="bilinear", align_corners=False).squeeze(1)
        gray = img.mean(dim=-1)                   # [B,H,W]
        out = torch.zeros_like(gray)
        p = percentile / 100.0
        for b in range(B):
            sel = m[b] > 0.5
            if sel.sum() < 16:
                out[b] = gray[b]
                continue
            vals = gray[b][sel]
            lo = torch.quantile(vals, p) if p > 0 else vals.min()
            hi = torch.quantile(vals, 1 - p) if p > 0 else vals.max()
            if (hi - lo) < 1e-5:
                n = torch.full_like(gray[b], 0.5)
            else:
                n = ((gray[b] - lo) / (hi - lo)).clamp(0, 1)
            if invert:
                n = 1.0 - n
            out[b] = low + n * (high - low)
        return (out.unsqueeze(-1).expand(-1, -1, -1, C).contiguous(),)


NODE_CLASS_MAPPINGS = {
    "ChangjutsuAudioPitchShift": AudioPitchShift,
    "ChangjutsuAudioGain": AudioGain,
    "ChangjutsuMaskedDepthNormalize": MaskedDepthNormalize,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "ChangjutsuAudioPitchShift": "Audio Pitch Shift (semitones)",
    "ChangjutsuAudioGain": "Audio Gain / Normalize",
    "ChangjutsuMaskedDepthNormalize": "Masked Depth Normalize (per frame)",
}
