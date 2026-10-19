# comfyui_changjutsu

Each `.py` here exposes `NODE_CLASS_MAPPINGS`; `__init__.py` collects them automatically.
`audio_depth_nodes.py` holds the three pipeline nodes, `setup_check.py` the diagnostics node.

Expected classes (the workflow references these names):

- `ChangjutsuAudioGain`            — gain / peak-normalise an AUDIO
- `ChangjutsuAudioPitchShift`      — pitch-shift an AUDIO by N semitones
- `ChangjutsuMaskedDepthNormalize` — re-range a depth image inside a mask
- `ChangjutsuSetupCheck`           — first-run diagnostics

`models.json` is a copy of the repo-root manifest so the setup check can find
it after a Manager install (where the repo root is not present).
