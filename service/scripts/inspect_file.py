#!/usr/bin/env python3
"""Inspect supported images and videos for AI/C2PA provenance metadata."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from av_meta import inspect_av
from common import (
    MAX_INPUT_BYTES,
    classify_finding_confidence,
    emit_json,
    eprint,
)
from format_dispatch import classify
from image_meta import inspect_image


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", type=Path, help="File to inspect")
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--as",
        dest="force_type",
        choices=("image", "av", "auto"),
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
    file_label = str(args.path.resolve())

    if kind == "unknown":
        note = "unsupported input; only image and video files are accepted"
        if args.json:
            emit_json({"kind": "unknown", "path": file_label, "note": note})
        else:
            print(f"File: {file_label}")
            print("Kind: unknown")
            print(note)
        return 2

    if kind == "image":
        report = inspect_image(args.path)
        if args.json:
            emit_json({"kind": "image", "path": file_label, **report.to_dict()})
        else:
            print(f"File: {file_label}")
            print("Kind: image")
            print(f"Path: {report.path}")
            print(f"Format: {report.format}")
            print(f"C2PA: {report.has_c2pa}")
            print(f"AI metadata: {report.has_ai_metadata}")
            for f in report.findings:
                print(f"  - [{classify_finding_confidence(f)}] {f}")
        return 0 if not (report.has_c2pa or report.has_ai_metadata) else 1

    if kind == "av":
        report = inspect_av(args.path)
        if args.json:
            emit_json({"kind": "av", "path": file_label, **report.to_dict()})
        else:
            print(f"File: {file_label}")
            print("Kind: av")
            print(f"Path: {report.path}")
            print(f"Format: {report.format}")
            print(f"C2PA: {report.has_c2pa}")
            print(f"AI metadata: {report.has_ai_metadata}")
            for f in report.findings:
                print(f"  - [{classify_finding_confidence(f)}] {f}")
        return 0 if not (report.has_c2pa or report.has_ai_metadata) else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
