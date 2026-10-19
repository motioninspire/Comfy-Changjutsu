"""Produce the public release copy of Comfy-Changjutsu V7.

Reads the working workflow JSON, strips everything personal / scene-specific,
removes editor metadata that other installs don't need, and injects the
`extra.models` manifest so ComfyUI offers to download missing models on open.
"""
import json
import sys
from pathlib import Path

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "Comfy-Changjutsu_V7.json")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "release/workflows/Changjutsu_V7.json")
MODELS = json.loads(Path("release/models.json").read_text())["models"]

wf = json.loads(SRC.read_text())

README_NOTE = """## Comfy-Changjutsu V7

**Flow:** Source → Preprocess (motion disguise) → Prompt → Backend → Save.

**First run:** queue the `Changjutsu Setup Check` node (group 0) once. It lists any missing model, node pack, ffmpeg, or comfy.org login in plain text instead of a red-node error. Missing models can also be fetched from ComfyUI's model-download prompt when this workflow is opened.

1. Load the source clip and the reference stills. Seedance 2.5 takes all of them (API cap 30); MiniMax uses `@image1..6`, Bernini `@image1..5`. Each loader's title says which backends it reaches. **Fewer references = better motion fidelity.** Seedance weighs stills against the video; a run with a few face/wardrobe crops tracked the performance frame-for-frame, one with many full-body/product shots went frontal and static. Use faces + wardrobe crops only; no full-body standing poses. Point unused loaders at any image, then **disconnect** their `fit 1024²` → backend links (or delete the loader) so the slot is empty.
2. Set start/duration. Limits: Seedance 4–30 s · MiniMax 4–15 s · Bernini-R = frame cap (4n+1).
3. **Motion disguise** (group 2): one SAM3 detection per subject (describe each in words), union → depth render over the real plate, logo cover. Turn it off to send the raw clip.
4. Review `01_disguised` in the output folder before running a paid backend.
5. Pick Mode / Preset / Backend, write the prompt, queue.

Audio: vocal isolation + pitch shift are not comfy-core; see the note in group 2."""

PREPROCESS_NOTE = """**Why:** closed APIs reject recognisable faces/music but not motion. Keep the *how*, remove the *who*.

- **Subjects:** the SAM3 video model tracks ONE text-prompted instance, so each person gets its own detection. Describe them (clothing works best); the masks are unioned, then padded.
- **Depth:** Depth Anything 3 `depth_colored` pass, scaled to source size, composited only inside the people mask — the real backdrop stays so the model stops tracing a silhouette.
- **Skeleton:** DWPose body + hand + face keypoints, drawn over the depth people (modes B, E, G). This is what carries lip and eye motion.
- **Logo cover:** flat patch at a burned-in logo. Set x/y/size per source; set patch size to 1×1 if there is no logo.
- **Audio (lip-sync):** `AUDIO TO API` → *disguised vocals*: Mel-Band RoFormer isolates the vocals, they are normalised and pitch-shifted (+3 st default) and embedded in the disguised clip, so the model hears speech to lip-sync to without the audio fingerprint matching the record. *none* = silent (mouths will be invented). The final `02_result` is always re-muxed with the untouched original audio.
- Needs the `comfyui_changjutsu` node pack (pitch shift / gain / masked depth normalise / setup check) in `custom_nodes` — restart Comfy after adding it."""

# node id -> {widget index: new value}
WIDGET_OVERRIDES = {
    1:  {0: README_NOTE},
    12: {0: PREPROCESS_NOTE},
    2:  {0: "changjutsu_example.mp4"},
    3:  {0: 0.0},
    4:  {0: 8.0},
    5:  {0: 0.0, 1: 8.0},
    8:  {0: "changjutsu_ref_A.png"},
    10: {0: "changjutsu_ref_B.png"},
    14: {1: 1, 2: 1},            # logo patch 1x1 = effectively off
    15: {0: 0, 1: 0},
    19: {0: "person on the left"},
    21: {0: "person on the right"},
    39: {0: "face of the person on the left"},
    41: {0: "face of the person on the right"},
    89: {0: "Replace the person on the left with the person from @image1. Replace the person on the right with the person from @image2.\n\nKeep the exact performance, lip movement and hand gestures from @video1. Keep the camera the same as @video1. Keep the background and set dressing from @video1."},
    160: {1: 8.0},
}
# named-widget mirrors of the above (widgets_values_named) are regenerated below.

NAMED_KEYS = {
    1: ["text"], 12: ["text"], 2: ["file", "upload"], 3: ["value"], 4: ["value"],
    5: ["start_time", "duration", "strict_duration"], 8: ["image", "upload"],
    10: ["image", "upload"], 14: ["value", "width", "height"], 15: ["x", "y", "operation"],
    19: ["text"], 21: ["text"], 39: ["text"], 41: ["text"], 89: ["value"],
    160: ["start_index", "duration"],
}

SEED_NODES = {111: 10, 112: 10, 115: 5, 147: 1}  # node id -> seed widget index

DELETE_NODES = {164}
RETITLE = {165: "Source frames → Bernini"}

# Setup-check node, placed in a new group 0 at the far left.
SETUP_NODE_ID = 900
SETUP_PREVIEW_ID = 901
SETUP_LINK_ID = 9000

nodes = wf["nodes"]
links = wf["links"]

# --- delete stray nodes and their links -----------------------------------
dead_links = set()
for n in nodes:
    if n["id"] in DELETE_NODES:
        for inp in n.get("inputs", []):
            if inp.get("link") is not None:
                dead_links.add(inp["link"])
        for out in n.get("outputs", []):
            for l in out.get("links") or []:
                dead_links.add(l)
nodes = [n for n in nodes if n["id"] not in DELETE_NODES]
links = [l for l in links if l[0] not in dead_links]
for n in nodes:
    for out in n.get("outputs", []):
        if out.get("links"):
            out["links"] = [l for l in out["links"] if l not in dead_links]

# --- per-node edits --------------------------------------------------------
for n in nodes:
    nid = n["id"]
    n.get("properties", {}).pop("ue_properties", None)
    if nid in RETITLE:
        n["title"] = RETITLE[nid]
    if nid in WIDGET_OVERRIDES:
        for idx, val in WIDGET_OVERRIDES[nid].items():
            n["widgets_values"][idx] = val
        if "widgets_values_named" in n and nid in NAMED_KEYS:
            for idx, key in enumerate(NAMED_KEYS[nid]):
                if idx < len(n["widgets_values"]):
                    n["widgets_values_named"][key] = n["widgets_values"][idx]
    if nid in SEED_NODES:
        n["widgets_values"][SEED_NODES[nid]] = 0
        named = n.get("widgets_values_named", {})
        for k in ("seed", "noise_seed"):
            if k in named:
                named[k] = 0

# --- setup-check node ------------------------------------------------------
nodes.insert(0, {
    "id": SETUP_NODE_ID, "type": "ChangjutsuSetupCheck",
    "pos": [-1100, 0], "size": [420, 120], "flags": {}, "order": 0, "mode": 0,
    "inputs": [], "outputs": [{"name": "report", "type": "STRING", "links": [SETUP_LINK_ID]}],
    "title": "Changjutsu Setup Check — queue this once on first run",
    "properties": {"Node name for S&R": "ChangjutsuSetupCheck"},
    "widgets_values": [],
    "color": "#432", "bgcolor": "#653",
})
nodes.insert(1, {
    "id": SETUP_PREVIEW_ID, "type": "PreviewAny",
    "pos": [-1100, 170], "size": [420, 520], "flags": {}, "order": 1, "mode": 0,
    "inputs": [{"name": "source", "type": "*", "link": SETUP_LINK_ID}],
    "outputs": [{"name": "STRING", "type": "STRING", "links": []}],
    "title": "SETUP REPORT",
    "properties": {"Node name for S&R": "PreviewAny"},
    "widgets_values": [],
    "color": "#432", "bgcolor": "#653",
})
links.append([SETUP_LINK_ID, SETUP_NODE_ID, 0, SETUP_PREVIEW_ID, 0, "STRING"])
wf["groups"].insert(0, {
    "id": 0, "title": "0 · FIRST RUN — setup check",
    "bounding": [-1130, -90, 480, 810], "color": "#595040", "flags": {},
})

wf["nodes"] = nodes
wf["links"] = links
wf["id"] = "changjutsu-v7-public"
wf["revision"] = 0
wf["last_node_id"] = max(n["id"] for n in nodes)
wf["last_link_id"] = max(l[0] for l in links)
wf["extra"] = {
    "ds": {"scale": 0.25, "offset": [1200, 100]},
    "models": [{"name": m["name"], "url": m["url"], "directory": m["directory"]} for m in MODELS],
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(wf, ensure_ascii=False, indent=1))
print(f"wrote {OUT}: {len(nodes)} nodes, {len(links)} links")
