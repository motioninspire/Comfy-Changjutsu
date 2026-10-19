"""comfyui_changjutsu — helper nodes for the Comfy-Changjutsu workflow.

Node classes are collected from every sibling module that defines
NODE_CLASS_MAPPINGS, so the existing audio / depth nodes can be dropped in
as their own .py files without editing this file.
"""
import importlib
import pkgutil
import sys

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

_pkg = sys.modules[__name__]
for _mod in pkgutil.iter_modules(_pkg.__path__):
    if _mod.name.startswith("_") or _mod.name == "install":
        continue
    try:
        _m = importlib.import_module(f"{__name__}.{_mod.name}")
    except Exception as e:  # keep the pack loading even if one module breaks
        print(f"[comfyui_changjutsu] could not import {_mod.name}: {e}")
        continue
    NODE_CLASS_MAPPINGS.update(getattr(_m, "NODE_CLASS_MAPPINGS", {}))
    NODE_DISPLAY_NAME_MAPPINGS.update(getattr(_m, "NODE_DISPLAY_NAME_MAPPINGS", {}))

WEB_DIRECTORY = None
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
