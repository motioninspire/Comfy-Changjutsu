#!/usr/bin/env python3
"""Comfy-Changjutsu installer — for people not using ComfyUI-Manager.

    python install.py --comfy /path/to/ComfyUI [--skip-models] [--with-bernini]

Steps:
  1. copies custom_nodes/comfyui_changjutsu into ComfyUI/custom_nodes
  2. clones the third-party packs from node_deps.json (pinned commit if set)
  3. pip-installs each pack's requirements.txt
  4. downloads models from models.json into ComfyUI/models/<directory>
     (optional Bernini-R files only with --with-bernini; ~40 GB)
  5. copies the workflow into ComfyUI/user/default/workflows
  6. checks that ffmpeg is on PATH

Nothing here is interactive; re-running is safe (existing files are kept).
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sh(*cmd, cwd=None):
    print("  $", " ".join(str(c) for c in cmd))
    subprocess.check_call([str(c) for c in cmd], cwd=cwd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comfy", required=True, help="path to the ComfyUI folder")
    ap.add_argument("--skip-models", action="store_true")
    ap.add_argument("--with-bernini", action="store_true", help="also download the optional Bernini-R local-backend models")
    args = ap.parse_args()

    comfy = Path(args.comfy).expanduser().resolve()
    if not (comfy / "main.py").exists():
        sys.exit(f"{comfy} does not look like a ComfyUI folder (no main.py)")
    custom = comfy / "custom_nodes"
    models_dir = comfy / "models"
    py = sys.executable

    # 1. our pack
    print("\n[1/6] comfyui_changjutsu")
    dst = custom / "comfyui_changjutsu"
    if dst.exists():
        print("  already present, leaving as is")
    else:
        shutil.copytree(ROOT / "custom_nodes" / "comfyui_changjutsu", dst)
    sh(py, "-m", "pip", "install", "-r", dst / "requirements.txt")

    # 2+3. third-party packs
    print("\n[2/6] third-party node packs")
    deps = json.loads((ROOT / "node_deps.json").read_text())
    for pack in deps["packs"]:
        target = custom / pack["name"]
        if target.exists():
            print(f"  {pack['name']}: already present")
        else:
            sh("git", "clone", pack["repo"], target)
            if pack.get("commit"):
                sh("git", "checkout", pack["commit"], cwd=target)
        req = target / "requirements.txt"
        if req.exists():
            print(f"[3/6] requirements for {pack['name']}")
            sh(py, "-m", "pip", "install", "-r", req)

    # 4. models
    print("\n[4/6] models")
    if args.skip_models:
        print("  skipped")
    else:
        try:
            from huggingface_hub import hf_hub_download  # noqa: F401
        except ImportError:
            sh(py, "-m", "pip", "install", "huggingface_hub")
        import urllib.request
        for m in json.loads((ROOT / "models.json").read_text())["models"]:
            if m.get("optional") and not args.with_bernini:
                print(f"  skip optional {m['name']} (use --with-bernini)")
                continue
            out = models_dir / m["directory"] / m["name"]
            if out.exists():
                print(f"  ok  {out.relative_to(comfy)}")
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            print(f"  get {m['name']} (~{m['size_gb']} GB)")
            tmp = out.with_suffix(out.suffix + ".part")
            urllib.request.urlretrieve(m["url"], tmp)
            tmp.rename(out)

    # 5. workflow
    print("\n[5/6] workflow")
    wf_dir = comfy / "user" / "default" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "workflows" / "Changjutsu_V7.json", wf_dir / "Changjutsu_V7.json")
    ex = ROOT / "example"
    if ex.exists():
        inp = comfy / "input"
        for f in ex.iterdir():
            if f.is_file() and not (inp / f.name).exists():
                shutil.copy2(f, inp / f.name)
    print(f"  copied to {wf_dir}")

    # 6. ffmpeg
    print("\n[6/6] ffmpeg:", shutil.which("ffmpeg") or "NOT FOUND — install ffmpeg and add it to PATH")

    print("\nDone. Start ComfyUI, open Changjutsu_V7 from the workflows sidebar, and queue the Setup Check node once.")


if __name__ == "__main__":
    main()
