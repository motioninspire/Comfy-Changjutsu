# Comfy-Changjutsu

A ComfyUI workflow for **video motion transfer onto reference characters** — the open rebuild of the "Genjutsu"-style tool. Feed it a source clip and a couple of reference stills; it strips identity from the clip (depth + skeleton "motion disguise"), builds the prompt, and sends the result to the backend you pick:

| Backend | Where it runs | Needs |
|---|---|---|
| Seedance 2.5 | comfy.org API | comfy.org account + credits |
| MiniMax H3 | comfy.org API | comfy.org account + credits |
| Bernini-R (Wan 2.2) | your GPU | ~40 GB of models, 24 GB+ VRAM recommended |

The disguise step exists because closed APIs reject recognisable faces and fingerprinted audio, but not motion. The workflow keeps the *how* (performance, timing, lip movement) and removes the *who*.

## Install

### Option A — ComfyUI-Manager (recommended)
1. Update ComfyUI to the current release (SAM3, Depth Anything 3 and Bernini-R are core nodes).
2. Manager → *Install via Git URL* → this repo's `custom_nodes/comfyui_changjutsu` (or install from the registry once published).
3. Open `Changjutsu_V7` from the template browser (*Workflow → Browse Templates → Changjutsu*) or drag `workflows/Changjutsu_V7.json` onto the canvas.
4. Manager → *Install Missing Custom Nodes* → restart.
5. Accept ComfyUI's model-download prompt, or download the files listed in `models.json` by hand.
6. Queue the **Setup Check** node (group 0). Fix anything it flags, then run for real.

### Option B — script
```bash
./install.sh /path/to/ComfyUI            # Linux / macOS
.\install.ps1 -Comfy C:\ComfyUI           # Windows (PowerShell)
```
Add `--with-bernini` / `-WithBernini` to also pull the local-backend models (~40 GB). The script clones the third-party packs from `node_deps.json`, installs their requirements, downloads `models.json`, and copies the workflow into your workflows folder.

### Requirements
- ComfyUI ≥ `REPLACE_ME` (version tested)
- Python 3.10+ with the ComfyUI venv
- `ffmpeg` on PATH
- For the API backends: log in to comfy.org inside ComfyUI (top-right menu) and have credits
- Third-party node packs (auto-installed by Manager or the script): `comfyui_controlnet_aux`, `ComfyUI-MelBandRoFormer`

## First run
1. Queue **Changjutsu Setup Check**. It reports missing models, node packs, ffmpeg and API login as text instead of a stack trace.
2. Load the bundled example clip and stills (copied to `ComfyUI/input/` by the installer).
3. Leave *Use motion disguise* on, queue, and open `output/video/Changjutsu_V7/01_disguised_*.mp4`. That file is what the API will see — review it before spending credits.
4. Switch backend, adjust the prompt, queue again. The final file is `02_result_*.mp4`, re-muxed with the original audio.

## Workflow map
```
0 · Setup check
1 · Source & references      LoadVideo → Video Slice → frames/audio/fps · @image1..N → fit 1024²
2 · Preprocess (disguise)    SAM3 per subject → union → DA3 depth over plate · DWPose skeleton · logo cover
                             Mel-Band RoFormer vocals → normalise → pitch shift · anti-fingerprint crop
3 · Prompt builder           Mode × Preset × your text → API wording / local wording · @imageN remap
4 · Seedance 2.5 (API)       edit (objects swap) | reference (motion transfer)
5 · MiniMax H3 (API)
6 · Bernini-R (local)        Wan 2.2 high/low noise, optional lightx2v turbo (6 steps, cfg 1)
7 · Backend select · audio · save
```

### Disguise modes
| Mode | Output sent to the model |
|---|---|
| A | coloured depth people over the real plate |
| B | A + DWPose skeleton lines |
| C | full-frame depth |
| D | skeleton on black |
| E | flat grey silhouettes + skeleton |
| F | real bodies, depth heads |
| G | grayscale depth people + skeleton (default, best results so far) |

### Prompt tags
`@image1…@imageN` = reference stills, `@video1` = the source clip. The builder rewrites them per backend (`Image N` / `Video N` for the APIs, `imageN` / "the source video" for Bernini).

## Tips learned the hard way
- **Fewer references.** Seedance weighs stills against the video. Face + wardrobe crops only; full-body standing poses pull the output toward a static frontal pose. Disconnect unused reference slots entirely.
- **Clothing-based SAM3 prompts** ("person in the striped shirt") segment better than names or positions.
- **Audio:** *disguised vocals* gives the model speech to lip-sync to without the original fingerprint; *none* makes it invent mouth shapes. The final result always gets the untouched original audio back.
- Duration limits: Seedance 4–30 s, MiniMax 4–15 s, Bernini-R = frame cap (4n+1 frames).

## Repo layout
```
workflows/Changjutsu_V7.json            sanitized workflow (also inside the node pack as a template)
custom_nodes/comfyui_changjutsu/        our node pack: audio gain, pitch shift, masked depth normalise, setup check
models.json                             model files + download URLs + target folders
node_deps.json                          third-party packs (pin commits before release)
install.py / install.sh / install.ps1   one-shot installer for non-Manager setups
example/                                demo clip + reference stills
CREDITS.md                              what was built on what
```

## Credits & licence
See [CREDITS.md](CREDITS.md) for the projects this builds on. The `comfyui_changjutsu` node pack is original code. Model weights are **not** redistributed here; each is downloaded from its publisher under that publisher's licence (SAM 3.1: Meta; Wan / Bernini-R: ByteDance & Alibaba terms; see `models.json`).

Workflow and node pack: MIT (see LICENSE).
