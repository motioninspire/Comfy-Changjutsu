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
MODELS = json.loads((Path(__file__).resolve().parent / "models.json").read_text())["models"]

wf = json.loads(SRC.read_text())

README_NOTE = """## Comfy-Changjutsu V7.1

**Flow:** Source → Preprocess (motion disguise) → Prompt → Backend → Save. Works with any clip: resolution, fps and length are read from the source.

**First run:** queue the `Changjutsu Setup Check` node (group 0) once. It lists any missing model, node pack, ffmpeg or comfy.org login in plain text. Missing models can also be fetched from ComfyUI's download prompt when the workflow opens.

**Per clip:**
1. Pick the source video, start and duration. Limits: Seedance 4–30 s · MiniMax 4–15 s · Bernini-R = frame cap (4n+1).
2. `@image1` is the replacement identity. Turn **USE @image2** on only when you have a second character or a second view; off = slot 2 repeats image 1, so nothing dangles. Faces + wardrobe crops work best; avoid full-body standing poses — Seedance copies posture from stills. Seedance takes up to 30 references, MiniMax 6, Bernini 5.
3. **SUBJECT A** = `person` selects everyone in the shot; narrow it (clothing works best: `man in the red jacket`) when only one of several people should change. **SUBJECT B** is optional — leave empty to skip its SAM pass. Same for FACE A/B (mode F only).
4. PROMPT: say who changes and which @image is theirs. The default replaces the primary foreground person with @image1 and keeps everything else.
5. Logo patch and centre crop are off by default; enable per source if a burned-in logo or fingerprint rejection shows up.
6. Queue once with a cheap backend or review `01_disguised` in the output folder before a paid run."""

PREPROCESS_NOTE = """**Why:** closed APIs reject recognisable faces/music but not motion. Keep the *how*, remove the *who*.

- **Subjects:** SAM3 tracks one text-prompted instance per pass. `person` catches every person; describe clothing to isolate one. Subject B / Face B run only when their selector is non-empty. Masks are unioned, then padded.
- **Depth:** Depth Anything 3 pass, scaled to source size, composited inside the people mask — the real backdrop stays so the model stops tracing a silhouette.
- **Skeleton:** DWPose body + hand + face keypoints drawn on top (modes B, E, G). This is what carries lip and eye motion.
- **Logo cover:** opacity 0 = off. Set size/position per source when a burned-in logo needs covering.
- **Centre crop:** optional 8 % crop against fingerprint matching; off keeps the source framing.
- **Audio:** `AUDIO TO API` → *disguised vocals*: Mel-Band RoFormer isolates vocals, normalise + pitch shift (+3 st) so the model hears speech to lip-sync to without the fingerprint matching. The final `02_result` is always re-muxed with the untouched original audio.
- Needs the `comfyui_changjutsu` node pack (pitch shift / gain / masked depth normalise / setup check) in `custom_nodes`."""

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
    14: {0: 0.0, 1: 130, 2: 170},
    15: {0: 0, 1: 0},
    19: {0: "person"},
    39: {0: "face"},
    160: {1: 8.0},
}
# named-widget mirrors of the above (widgets_values_named) are regenerated below.

NAMED_KEYS = {
    1: ["text"], 12: ["text"], 2: ["file", "upload"], 3: ["value"], 4: ["value"],
    5: ["start_time", "duration", "strict_duration"], 8: ["image", "upload"],
    10: ["image", "upload"], 14: ["value", "width", "height"], 15: ["x", "y", "operation"],
    19: ["text"], 39: ["text"],
    160: ["start_index", "duration"],
}

SEED_NODES = {111: 10, 112: 10, 115: 5, 147: 1}  # node id -> seed widget index

DELETE_NODES = {164}
RETITLE = {165: "Source frames → Bernini", 8: "@image1 — replacement identity  [Seedance·MiniMax·Bernini]", 10: "@image2 — optional second character / view  [Seedance·MiniMax·Bernini]", 11: "@image2 → fit 1024² (aspect-safe)"}

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

# --- un-bypass everything (a bypassed LoadImage outputs None downstream) ---
for n in nodes:
    if n.get("mode") == 4:
        n["mode"] = 0

# --- USE @image2 toggle: off -> slot 2 repeats @image1 so no backend gets None
USE2_ID, USE2_SWITCH_ID = 902, 903
nodes_by_id = {n["id"]: n for n in nodes}
fit1, fit2 = nodes_by_id[9], nodes_by_id[11]
consumers = list(fit2["outputs"][0].get("links") or [])
next_link = max(l[0] for l in links) + 1
links_by_id = {l[0]: l for l in links}
# re-point every consumer of fit2 at the switch output
for lid in consumers:
    links_by_id[lid][1], links_by_id[lid][2] = USE2_SWITCH_ID, 0
fit2["outputs"][0]["links"] = [next_link]        # fit2 -> switch.on_true
fit1["outputs"][0].setdefault("links", []).append(next_link + 1)  # fit1 -> switch.on_false
links.append([next_link, 11, 0, USE2_SWITCH_ID, 1, "IMAGE"])
links.append([next_link + 1, 9, 0, USE2_SWITCH_ID, 2, "IMAGE"])
links.append([next_link + 2, USE2_ID, 0, USE2_SWITCH_ID, 0, "BOOLEAN"])
p10 = nodes_by_id[10]["pos"]
nodes.append({
    "id": USE2_ID, "type": "PrimitiveBoolean", "pos": [p10[0], p10[1] - 70], "size": [300, 58],
    "flags": {}, "order": 0, "mode": 0, "inputs": [],
    "outputs": [{"name": "BOOLEAN", "type": "BOOLEAN", "links": [next_link + 2]}],
    "title": "USE @image2?  off = slot 2 repeats @image1",
    "properties": {"Node name for S&R": "PrimitiveBoolean"}, "widgets_values": [False],
    "color": "#223", "bgcolor": "#335",
})
nodes.append({
    "id": USE2_SWITCH_ID, "type": "ComfySwitchNode", "pos": [p10[0] + 330, p10[1] + 160], "size": [240, 100],
    "flags": {}, "order": 0, "mode": 0,
    "inputs": [{"name": "switch", "type": "BOOLEAN", "link": next_link + 2},
               {"name": "on_true", "type": "IMAGE", "link": next_link},
               {"name": "on_false", "type": "IMAGE", "link": next_link + 1}],
    "outputs": [{"name": "output", "type": "IMAGE", "links": consumers}],
    "title": "@image2 slot → backends",
    "properties": {"Node name for S&R": "ComfySwitchNode"}, "widgets_values": [False],
    "color": "#223", "bgcolor": "#335",
})

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
wf["id"] = "changjutsu-v7.1-public"
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
