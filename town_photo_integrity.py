#!/usr/bin/env python3
"""Shared denylist for town photos proven to depict a different locality."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


# (intended town slug, local archive filename, Wikimedia source title, actual place)
REJECTED_TOWN_PHOTOS = frozenset(
    {
        (
            "bloomfield",
            "bloomfield-2.webp",
            "File:Home Depot (Bloomfield, Connecticut) (51688036059).jpg",
            "Bloomfield, Connecticut",
        ),
        (
            "east-brunswick",
            "east-brunswick-2.webp",
            "File:166 Main Street, Old Bridge, NJ.jpg",
            "Old Bridge, New Jersey",
        ),
        (
            "south-bound-brook",
            "south-bound-brook-1.webp",
            "File:Downtown South Bristol, Maine.jpg",
            "South Bristol, Maine",
        ),
        (
            "south-brunswick",
            "south-brunswick-1.webp",
            "File:Downtown South Bristol, Maine.jpg",
            "South Bristol, Maine",
        ),
        (
            "south-plainfield",
            "south-plainfield-1.webp",
            "File:Downtown South Bristol, Maine.jpg",
            "South Bristol, Maine",
        ),
        (
            "south-plainfield",
            "south-plainfield-2.webp",
            "File:Raritan River Bridge, Highland Park, NJ.jpg",
            "Highland Park, New Jersey",
        ),
        (
            "south-river",
            "south-river-2.webp",
            "File:Downtown South Bristol, Maine.jpg",
            "South Bristol, Maine",
        ),
    }
)

REJECTED_TOWN_PHOTO_FILES = frozenset(
    (town, filename) for town, filename, _source, _actual_place in REJECTED_TOWN_PHOTOS
)
REJECTED_TOWN_PHOTO_SOURCES = frozenset(
    (town, source) for town, _filename, source, _actual_place in REJECTED_TOWN_PHOTOS
)


def is_rejected_source(town: str, source: str) -> bool:
    return (town, source) in REJECTED_TOWN_PHOTO_SOURCES


def is_rejected_photo(town: str, photo: Mapping[str, Any]) -> bool:
    return (
        (town, str(photo.get("file", ""))) in REJECTED_TOWN_PHOTO_FILES
        or is_rejected_source(town, str(photo.get("source", "")))
    )


def filter_photo_credits(
    credits: Mapping[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Return a copy with every exact off-location pairing removed."""
    return {
        town: [dict(photo) for photo in photos if not is_rejected_photo(town, photo)]
        for town, photos in credits.items()
    }
