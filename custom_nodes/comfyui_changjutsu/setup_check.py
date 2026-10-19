"""Changjutsu Setup Check — first-run diagnostics as a node.

Queue it once. It reports, in plain text, everything the Changjutsu
workflow needs and whether it is present: model files, node classes,
ffmpeg, and the comfy.org login that the Seedance / MiniMax API nodes use.
It never downloads or installs anything.
"""
import json
import os
import shutil
from pathlib import Path

try:
    import folder_paths
except ImportError:  # running outside ComfyUI
    folder_paths = None

HERE = Path(__file__).resolve().parent
PACK_ROOT = HERE.parent.parent  # repo root when installed from the release layout


def _load_json(name):
    for candidate in (HERE / name, PACK_ROOT / name):
        if candidate.exists():
            with open(candidate) as f:
                return json.load(f)
    return None


REQUIRED_NODES = {
    # class name: where it comes from
    "SAM3_Detect": "comfy-core (update ComfyUI)",
    "LoadDA3Model": "comfy-core (update ComfyUI)",
    "DA3Inference": "comfy-core (update ComfyUI)",
    "DA3Render": "comfy-core (update ComfyUI)",
    "BerniniConditioning": "comfy-core (update ComfyUI) — Local backend only",
    "ByteDance2ReferenceNodeV2": "comfy-core API nodes — Seedance backend",
    "MinimaxHailuo03ReferenceNode": "comfy-core API nodes — MiniMax backend",
    "Video Slice": "comfy-core (update ComfyUI)",
    "GetVideoComponents": "comfy-core",
    "ComfySwitchNode": "comfy-core",
    "ComfyMathExpression": "comfy-core",
    "CustomCombo": "comfy-core",
    "JsonExtractString": "comfy-core",
    "DWPreprocessor": "comfyui_controlnet_aux",
    "MelBandRoFormerModelLoader": "ComfyUI-MelBandRoFormer",
    "MelBandRoFormerSampler": "ComfyUI-MelBandRoFormer",
    "ChangjutsuAudioGain": "comfyui_changjutsu (this pack)",
    "ChangjutsuAudioPitchShift": "comfyui_changjutsu (this pack)",
    "ChangjutsuMaskedDepthNormalize": "comfyui_changjutsu (this pack)",
}


def _model_present(name, directory):
    if folder_paths is None:
        return None
    try:
        paths = folder_paths.get_folder_paths(directory)
    except Exception:
        base = Path(folder_paths.models_dir)
        paths = [base / directory]
    for p in paths:
        if (Path(p) / name).exists():
            return True
    return False


def _comfy_api_login():
    """Best-effort: look for a stored comfy.org API key. Returns True/False/None."""
    if os.environ.get("COMFY_API_KEY"):
        return True
    if folder_paths is None:
        return None
    try:
        user_dir = Path(folder_paths.get_user_directory())
    except Exception:
        return None
    for f in user_dir.rglob("comfy.settings.json"):
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        if any("api" in k.lower() and "key" in k.lower() and v for k, v in data.items()):
            return True
    return False


class ChangjutsuSetupCheck:
    CATEGORY = "Changjutsu"
    FUNCTION = "run"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("report",)
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    @classmethod
    def IS_CHANGED(cls, **kw):
        return float("nan")  # always re-run

    def run(self):
        lines = ["CHANGJUTSU SETUP CHECK", ""]
        problems = 0

        # ffmpeg
        ff = shutil.which("ffmpeg")
        lines.append(f"[{'ok' if ff else 'MISSING'}] ffmpeg on PATH" + (f" ({ff})" if ff else " — install ffmpeg and restart ComfyUI"))
        problems += 0 if ff else 1

        # node classes
        try:
            import nodes as comfy_nodes
            registry = comfy_nodes.NODE_CLASS_MAPPINGS
        except Exception:
            registry = {}
        lines.append("")
        lines.append("Node packs:")
        for cls_name, source in REQUIRED_NODES.items():
            ok = cls_name in registry
            problems += 0 if ok else 1
            lines.append(f"  [{'ok' if ok else 'MISSING'}] {cls_name}  ← {source}")

        # models
        manifest = _load_json("models.json")
        lines.append("")
        lines.append("Models:")
        if not manifest:
            lines.append("  (models.json not found next to this pack — skipped)")
        else:
            for m in manifest["models"]:
                present = _model_present(m["name"], m["directory"])
                tag = "ok" if present else ("MISSING" if present is False else "?")
                opt = f"  (optional: {m['optional']})" if m.get("optional") else ""
                if present is False and not m.get("optional"):
                    problems += 1
                lines.append(f"  [{tag}] models/{m['directory']}/{m['name']}{opt}")
                if present is False:
                    lines.append(f"         ↳ {m['url']}")

        # API login
        lines.append("")
        login = _comfy_api_login()
        if login is True:
            lines.append("[ok] comfy.org API key found (needed for Seedance / MiniMax backends)")
        elif login is False:
            lines.append("[note] no comfy.org API key detected — log in via the ComfyUI menu before using the Seedance or MiniMax backends. Not needed for Local: Bernini-R.")
        else:
            lines.append("[?] could not determine comfy.org login state")

        lines.append("")
        lines.append("RESULT: " + ("ready to run" if problems == 0 else f"{problems} required item(s) missing — see above"))
        report = "\n".join(lines)
        print(report)
        return {"ui": {"text": [report]}, "result": (report,)}


NODE_CLASS_MAPPINGS = {"ChangjutsuSetupCheck": ChangjutsuSetupCheck}
NODE_DISPLAY_NAME_MAPPINGS = {"ChangjutsuSetupCheck": "Changjutsu Setup Check"}
