# Credits

Comfy-Changjutsu is a workflow assembled from the projects below. Nothing here would work without them.

## Concept
- **Higgsfield Genjutsu** — the original closed tool this workflow re-creates the behaviour of. No code or assets from Higgsfield are used.

## ComfyUI core (no install needed, keep ComfyUI current)
- [ComfyUI](https://github.com/Comfy-Org/ComfyUI) — GPL-3.0
- SAM 3 / 3.1 native support — Comfy-Org PR #13408 (kijai)
- Depth Anything 3 native support — Comfy-Org PR #13853
- Bernini-R (Wan 2.2 video edit with reference) native support — Comfy-Org PR #14216
- Comfy API nodes for Seedance 2.5 (ByteDance) and MiniMax Hailuo 03

## Third-party node packs (installed as dependencies, not vendored)
- [comfyui_controlnet_aux](https://github.com/Fannovel16/comfyui_controlnet_aux) (Fannovel16) — DWPose preprocessor
- [ComfyUI-MelBandRoFormer](https://github.com/kijai/ComfyUI-MelBandRoFormer) (kijai) — vocal isolation

## Models (downloaded from their publishers, see `models.json`)
- SAM 3.1 — Meta; ComfyUI repack by Comfy-Org / kijai
- Depth Anything 3 — ByteDance Seed; ComfyUI repack by Comfy-Org
- Mel-Band RoFormer — ComfyUI repack by kijai
- Wan 2.2 Bernini-R — ByteDance; ComfyUI fp8 repack by Comfy-Org / kijai
- lightx2v step-distill LoRA — lightx2v; ComfyUI repack by kijai
- umT5-XXL text encoder, Wan 2.1 VAE — Alibaba Wan team; repacks by Comfy-Org / kijai
- DWPose / YOLOX weights — IDEA-Research / yzd-v, hr16

## `comfyui_changjutsu` node pack
All four nodes are original to this repo (pure torch / torchaudio, no forked code):

| Node | Purpose |
|---|---|
| `ChangjutsuAudioPitchShift` | semitone pitch shift (torchaudio phase vocoder) so vocals lip-sync without fingerprint-matching the record |
| `ChangjutsuAudioGain` | linear gain + peak normalise |
| `ChangjutsuMaskedDepthNormalize` | per-frame percentile contrast stretch of a depth image inside the people mask |
| `ChangjutsuSetupCheck` | first-run diagnostics |

Licensed with the rest of the repo (see LICENSE).
