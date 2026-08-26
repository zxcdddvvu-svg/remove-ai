"""Route a file or byte stream to the image or video pipeline.

The routers (inspect_file, clean_file) and the audits (audit_lib) all need the
same answer: given a path or bytes, which pipeline owns it? That decision used
to live in three copies with subtly different extension tables and sniffing.
This module is the single interface for it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from av_meta import detect_av_format
from image_meta import detect_format as detect_image_format

Kind = Literal["image", "av", "unknown"]

#: Bytes read for header-only sniffing. Every supported image/container
#: magic lives in the prefix; zip-based containers (docx/odt/...) need the
#: full central directory, which sits at the end of the archive, so only a
#: PK header triggers a whole-file read.
CLASSIFY_HEADER_BYTES = 4096

IMAGE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".avif",
    ".heic",
    ".heif",
    ".bmp",
    ".gif",
    ".tiff",
    ".tif",
}
VIDEO_EXTS = {".mp4", ".mov", ".m4v"}
AUDIO_EXTS = {".m4a", ".wav", ".mp3", ".flac"}


def classify_bytes(data: bytes, suffix: str | None = None) -> Kind:
    """Classify *data* by extension first, then by magic bytes.

    The extension wins when it names a known format; otherwise the bytes are
    sniffed for image/container signatures. Unrecognized bytes classify as
    "unknown" — callers that must not mangle unknown binaries refuse unless
    the user explicitly forces a kind (--as / --force-text).

    *data* must cover the whole file: zip-based containers (docx/odt) are
    detected from their central directory, which sits at the end of the bytes.
    """
    ext = (suffix or "").lower()
    detected_av = detect_av_format(data)
    if detected_av in {"wav", "mp3", "flac"}:
        return "unknown"
    if ext in IMAGE_EXTS:
        return "image"
    # Explicit audio extensions must not fall through to magic-byte sniffing.
    if ext in AUDIO_EXTS:
        return "unknown"
    if ext in VIDEO_EXTS:
        return "av"
    if detect_image_format(data) in ("png", "jpeg", "webp", "avif", "heic", "bmp", "gif", "tiff"):
        return "image"
    # Header-only ISO-BMFF detection cannot reliably distinguish an audio-only
    # MP4 from video. Accept generic MP4 bytes only when there is no explicit
    # audio suffix; known audio signatures remain unsupported.
    if detected_av == "mp4":
        return "av"
    return "unknown"


def classify(path: Path) -> Kind:
    """Classify a file on disk by extension, then by its bytes.

    Known extensions are routed without reading the file. For unknown
    extensions a 4096-byte header is sniffed once; only when the header is a
    zip local header (PK) is the whole file read, because the container
    signature (docx/xlsx/pptx/odt/epub) lives in the central directory at
    the end of the archive.
    """
    ext = path.suffix.lower()
    with path.open("rb") as fh:
        head = fh.read(CLASSIFY_HEADER_BYTES)
    detected_av = detect_av_format(head)
    if detected_av in {"wav", "mp3", "flac"}:
        return "unknown"
    if ext in IMAGE_EXTS:
        return "image"
    if ext in AUDIO_EXTS:
        return "unknown"
    if ext in VIDEO_EXTS:
        return "av"
    if detect_image_format(head) in ("png", "jpeg", "webp", "avif", "heic", "bmp", "gif", "tiff"):
        return "image"
    if detected_av == "mp4":
        return "av"
    return "unknown"
