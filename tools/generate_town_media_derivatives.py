#!/usr/bin/env python3
"""Build responsive derivatives from the verified Chatham Township source image."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "images/towns/chatham-township-2.webp"
SOURCE_SHA256 = "cf319352377b8cf7bac9bda8617e3ae3547d7914a80e2401ab90f4bd554c89a2"
QUALITY = 76
VARIANTS = {
    640: "chatham-township-2-640.webp",
    960: "chatham-township-2-960.webp",
}


def source_digest() -> str:
    return hashlib.sha256(SOURCE.read_bytes()).hexdigest()


def build(output_directory: Path) -> list[Path]:
    if source_digest() != SOURCE_SHA256:
        raise RuntimeError(
            "The verified Chatham Township source image changed; review its locality and "
            "attribution before rebuilding derivatives."
        )
    cwebp = shutil.which("cwebp")
    if not cwebp:
        raise RuntimeError("cwebp is required to rebuild town-media derivatives")

    output_directory.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for width, filename in VARIANTS.items():
        destination = output_directory / filename
        subprocess.run(
            [
                cwebp,
                "-quiet",
                "-q",
                str(QUALITY),
                "-m",
                "6",
                "-sharp_yuv",
                "-metadata",
                "none",
                "-resize",
                str(width),
                str(width),
                str(SOURCE),
                "-o",
                str(destination),
            ],
            check=True,
        )
        outputs.append(destination)
    return outputs


def check() -> list[Path]:
    with tempfile.TemporaryDirectory(prefix="jrg-town-media-") as temporary:
        generated = build(Path(temporary))
        for candidate in generated:
            checked_in = ROOT / "images/towns" / candidate.name
            if not checked_in.is_file() or candidate.read_bytes() != checked_in.read_bytes():
                raise RuntimeError(
                    f"{checked_in.relative_to(ROOT)} is stale; rebuild it with this script"
                )
    return [ROOT / "images/towns" / filename for filename in VARIANTS.values()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="rebuild in a temporary directory and compare with checked-in derivatives",
    )
    args = parser.parse_args()
    outputs = check() if args.check else build(ROOT / "images/towns")
    for output in outputs:
        print(f"{output.relative_to(ROOT)}: {output.stat().st_size} bytes")


if __name__ == "__main__":
    main()
