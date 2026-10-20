"""Derive workflows/Changjutsu_V7_cloud.json from the sanitized V7.

Comfy Cloud cannot load third-party node packs, so the three comfyui_changjutsu
pipeline nodes are bypassed:
  - vocals: Mel-Band RoFormer -> (gain, pitch shift removed) -> AUDIO TO API switch
  - mode G: gray depth -> (masked normalise removed) -> composite; default mode set to B
The setup-check node and its group are dropped (no custom pack to check).
"""
import json, sys
from pathlib import Path
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "workflows/Changjutsu_V7.json")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "workflows/Changjutsu_V7_cloud.json")
wf = json.loads(SRC.read_text())
nodes = {n["id"]: n for n in wf["nodes"]}
links = {l[0]: l for l in wf["links"]}

def upstream(nid, input_name):
    inp = next(i for i in nodes[nid]["inputs"] if i["name"] == input_name)
    l = links[inp["link"]]; return l[1], l[2]

def rewire_through(remove_ids, in_node, in_name, out_node, out_slot_name):
    """Connect the source of `in_node.in_name` directly to every consumer of `out_node.out_slot_name`."""
    src, src_slot = upstream(in_node, in_name)
    out = next(o for o in nodes[out_node]["outputs"] if o["name"] == out_slot_name)
    consumers = list(out.get("links") or [])
    # drop every link feeding the removed nodes (including internal ones)
    for rid in remove_ids:
        for i in nodes[rid]["inputs"]:
            if i.get("link") is not None and i["link"] in links:
                l = links.pop(i["link"])
                if l[1] in nodes:
                    so = nodes[l[1]]["outputs"][l[2]]
                    if so.get("links"): so["links"] = [x for x in so["links"] if x != l[0]]
    # re-point the consumers at the original source
    for lid in consumers:
        l = links[lid]
        l[1], l[2] = src, src_slot
        so = nodes[src]["outputs"][src_slot]
        so.setdefault("links", []); so["links"].append(lid)
    for rid in remove_ids:
        del nodes[rid]

rewire_through([75, 76], 75, "audio", 76, "audio")       # vocals bypass
rewire_through([50], 50, "image", 50, "IMAGE")           # depth normalise bypass

# drop setup check + preview + group 0
for rid in (900, 901):
    for i in nodes[rid]["inputs"]:
        if i.get("link") is not None: links.pop(i["link"], None)
    del nodes[rid]
wf["groups"] = [g for g in wf["groups"] if g["id"] != 0]

# default disguise mode -> B
m = nodes[51]; m["widgets_values"][0] = "B: depth people + skeleton"
if "widgets_values_named" in m: m["widgets_values_named"]["value"] = m["widgets_values"][0]

# readme note
n1 = nodes[1]; txt = n1["widgets_values"][0]
txt = txt.replace("## Comfy-Changjutsu V7", "## Comfy-Changjutsu V7 — Comfy Cloud edition")
txt = txt.replace("**First run:** queue the `Changjutsu Setup Check` node (group 0) once. It lists any missing model, node pack, ffmpeg, or comfy.org login in plain text instead of a red-node error. Missing models can also be fetched from ComfyUI's model-download prompt when this workflow is opened.",
                  "**Cloud edition:** identical to the GitHub V7 except the three `comfyui_changjutsu` nodes are bypassed (Cloud can't load third-party packs): vocals are sent un-shifted, and mode G has no in-mask normalise, so the default mode is **B**. For the full pipeline run V7 locally: github.com/motioninspire/Comfy-Changjutsu")
txt = txt.replace("Audio: vocal isolation + pitch shift are not comfy-core; see the note in group 2.", "")
n1["widgets_values"][0] = txt.rstrip()
if "widgets_values_named" in n1: n1["widgets_values_named"]["text"] = n1["widgets_values"][0]
n12 = nodes[12]; t = n12["widgets_values"][0]
t = t.replace("they are normalised and pitch-shifted (+3 st default) and embedded", "they are embedded (un-shifted on Cloud; the local V7 pitch-shifts them +3 st)")
t = t.replace("- Needs the `comfyui_changjutsu` node pack (pitch shift / gain / masked depth normalise / setup check) in `custom_nodes` — restart Comfy after adding it.", "- Cloud edition: no custom node pack needed.")
n12["widgets_values"][0] = t.rstrip()
if "widgets_values_named" in n12: n12["widgets_values_named"]["text"] = n12["widgets_values"][0]

wf["nodes"] = list(nodes.values()); wf["links"] = list(links.values())
wf["id"] = "changjutsu-v7-cloud"; wf["last_node_id"] = max(nodes); wf["last_link_id"] = max(links)
wf["extra"]["ds"] = {"scale": 0.25, "offset": [300, 100]}
OUT.write_text(json.dumps(wf, ensure_ascii=False, indent=1))
print("wrote", OUT, len(nodes), "nodes", len(links), "links")
