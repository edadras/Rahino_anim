#!/usr/bin/env python3
"""Full character pipeline: image -> 3D model -> rig -> animation set.

Runs the whole Tripo3D chain for one character image and downloads every
result into assets/, ready for the web viewer in viewer/.

    python pipeline.py assets/rahino.png
    python pipeline.py assets/rahino.png --animations preset:idle preset:walk preset:run

State is saved in assets/pipeline_state.json after every step, so a crashed
or interrupted run resumes instead of re-paying for finished tasks.
"""

import argparse
import json
from pathlib import Path

from tripo_client import TripoClient, TripoError

DEFAULT_ANIMATIONS = [
    "preset:idle",
    "preset:walk",
    "preset:run",
    "preset:jump",
]

ASSETS = Path("assets")
STATE_FILE = ASSETS / "pipeline_state.json"


def load_state() -> dict:
    if STATE_FILE.is_file():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict):
    ASSETS.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def step(client: TripoClient, state: dict, key: str, submit) -> dict:
    """Run one pipeline step once: submit if new, then wait and download."""
    if key not in state:
        state[key] = {"task_id": submit()}
        save_state(state)
        print(f"[{key}] submitted task {state[key]['task_id']}")
    entry = state[key]
    if not entry.get("done"):
        task = client.wait_for_task(entry["task_id"])
        files = client.download_outputs(task, str(ASSETS))
        entry["done"] = True
        entry["files"] = [str(f) for f in files]
        save_state(state)
    return entry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", help="character reference image (kept as-is)")
    parser.add_argument(
        "--animations",
        nargs="*",
        default=DEFAULT_ANIMATIONS,
        help=f"preset animations to retarget (default: {' '.join(DEFAULT_ANIMATIONS)})",
    )
    parser.add_argument(
        "--no-rig", action="store_true", help="stop after the static model"
    )
    args = parser.parse_args()

    client = TripoClient()
    state = load_state()

    print("== 1. image -> 3D model ==")
    model = step(
        client,
        state,
        "model",
        lambda: client.image_to_model(args.image, texture=True, pbr=True),
    )
    model_id = model["task_id"]

    if args.no_rig:
        print("Done (static model only).")
        return

    print("== 2. rig check ==")
    try:
        step(
            client,
            state,
            "prerigcheck",
            lambda: client.create_task(
                {"type": "animate_prerigcheck", "original_model_task_id": model_id}
            ),
        )
    except TripoError as err:
        print(f"  prerigcheck warning (continuing): {err}")

    print("== 3. rig ==")
    rig = step(client, state, "rig", lambda: client.rig(model_id))
    rig_id = rig["task_id"]

    print("== 4. animations ==")
    manifest = {"model": model_id, "rig": rig_id, "animations": {}}
    for anim in args.animations:
        key = f"anim:{anim}"
        entry = step(client, state, key, lambda a=anim: client.animate(rig_id, a))
        manifest["animations"][anim] = {
            "task_id": entry["task_id"],
            "files": entry.get("files", []),
        }

    manifest["rig_files"] = rig.get("files", [])
    (ASSETS / "character_manifest.json").write_text(json.dumps(manifest, indent=2))
    print("\nAll done. Manifest: assets/character_manifest.json")
    print("Copy the rigged/animated GLBs into viewer/models/ and open the viewer.")


if __name__ == "__main__":
    main()
