#!/usr/bin/env python3
"""Clean AI/C2PA provenance metadata from supported images and videos."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from av_meta import clean_av
from common import (
    MAX_INPUT_BYTES,
    backup_path,
    cleaned_path,
    eprint,
)
from format_dispatch import classify
from image_meta import clean_image


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", type=Path)
    p.add_argument("-o", "--output", type=Path)
    p.add_argument("--in-place", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--keep-non-ai-metadata",
        action="store_true",
        help="Only drop C2PA/AI-looking image or video metadata",
    )
    p.add_argument(
        "--as",
        dest="force_type",
        choices=("auto", "image", "av"),
        default="auto",
    )
    args = p.parse_args()

    if not args.path.is_file():
        eprint(f"not a file: {args.path}")
        return 2

    if args.path.stat().st_size > MAX_INPUT_BYTES:
        eprint(f"refusing input larger than {MAX_INPUT_BYTES} bytes: {args.path}")
        return 2

    kind = args.force_type if args.force_type != "auto" else classify(args.path)

    # classify() reports "unknown" for bytes that match no supported format.
    # Never mutate those in auto mode: a binary with valid UTF-8 runs would
    # be decoded and written back mangled. --as text / --force-text are the
    # explicit opt-ins and both route through the text pipeline below.
    if kind == "unknown":
        eprint(f"unsupported input: {args.path}; only image and video files are accepted")
        return 2

    if args.in_place:
        bak, created = backup_path(args.path)
        if not created:
            eprint(f"backup {bak} already exists from an earlier run; keeping the original backup")
        dest = args.path
        src = bak
    else:
        src = args.path
        dest = args.output or cleaned_path(args.path)

    if kind == "image":
        try:
            result = clean_image(
                src,
                dest,
                strip_all_metadata=not args.keep_non_ai_metadata,
            )
        except Exception as e:
            eprint(f"error: {e}")
            return 1
        result = {"kind": "image", **result}
        residual = result["still_has_c2pa"] or result["still_has_ai_metadata"]
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            eprint(f"wrote {result['output']} ({result['bytes_in']} -> {result['bytes_out']})")
            for a in result["actions"]:
                eprint(f"  - {a}")
            if residual:
                eprint("warning: residual C2PA/AI signals may remain")
        return 1 if residual else 0

    if kind == "av":
        try:
            result = clean_av(
                src,
                dest,
                strip_all_metadata=not args.keep_non_ai_metadata,
            )
        except Exception as e:
            eprint(f"error: {e}")
            return 1
        result = {"kind": "av", **result}
        residual = result["still_has_c2pa"] or result["still_has_ai_metadata"]
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            eprint(f"wrote {result['output']} ({result['bytes_in']} -> {result['bytes_out']})")
            for a in result["actions"]:
                eprint(f"  - {a}")
            if residual:
                eprint("warning: residual C2PA/AI signals may remain")
        return 1 if residual else 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
