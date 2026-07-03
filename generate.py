#!/usr/bin/env python3
"""Command-line entry point for creating Tripo3D assets.

Examples:
    python generate.py balance
    python generate.py text "a cute cartoon rhino, pixar style"
    python generate.py image ./rhino.jpg
    python generate.py rig <model_task_id>
    python generate.py animate <rig_task_id> --animation preset:run
    python generate.py status <task_id>
    python generate.py download <task_id>
"""

import argparse
import json

from tripo_client import TripoClient


def _finish(client: TripoClient, task_id: str, wait: bool, out: str):
    print(f"task_id: {task_id}")
    if not wait:
        print("Submitted. Check later with: python generate.py status", task_id)
        return
    task = client.wait_for_task(task_id)
    client.download_outputs(task, out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("balance", help="show remaining API credits")

    p = sub.add_parser("text", help="text -> 3D model")
    p.add_argument("prompt")
    p.add_argument("--no-wait", action="store_true")
    p.add_argument("--out", default="outputs")

    p = sub.add_parser("image", help="image -> 3D model")
    p.add_argument("path")
    p.add_argument("--no-wait", action="store_true")
    p.add_argument("--out", default="outputs")

    p = sub.add_parser("rig", help="rig a generated model for animation")
    p.add_argument("model_task_id")
    p.add_argument("--no-wait", action="store_true")
    p.add_argument("--out", default="outputs")

    p = sub.add_parser("animate", help="apply a preset animation to a rigged model")
    p.add_argument("rig_task_id")
    p.add_argument("--animation", default="preset:walk", help="e.g. preset:walk, preset:run")
    p.add_argument("--no-wait", action="store_true")
    p.add_argument("--out", default="outputs")

    p = sub.add_parser("status", help="show raw task state")
    p.add_argument("task_id")

    p = sub.add_parser("download", help="download outputs of a finished task")
    p.add_argument("task_id")
    p.add_argument("--out", default="outputs")

    args = parser.parse_args()
    client = TripoClient()

    if args.cmd == "balance":
        print(json.dumps(client.balance(), indent=2))
    elif args.cmd == "text":
        _finish(client, client.text_to_model(args.prompt), not args.no_wait, args.out)
    elif args.cmd == "image":
        _finish(client, client.image_to_model(args.path), not args.no_wait, args.out)
    elif args.cmd == "rig":
        _finish(client, client.rig(args.model_task_id), not args.no_wait, args.out)
    elif args.cmd == "animate":
        _finish(
            client,
            client.animate(args.rig_task_id, args.animation),
            not args.no_wait,
            args.out,
        )
    elif args.cmd == "status":
        print(json.dumps(client.get_task(args.task_id), indent=2, ensure_ascii=False))
    elif args.cmd == "download":
        client.download_outputs(client.get_task(args.task_id), args.out)


if __name__ == "__main__":
    main()
