"""Spellings of an output name that lands outside the workspace."""

import pathlib

from conftest import rel_from


def spell(shape: str, base: pathlib.Path, target: pathlib.Path) -> str:
    """Name that, joined onto base, designates target."""
    if shape == 'absolute':
        return str(target)
    if shape == 'parent':
        return rel_from(base, target)
    if shape == 'nested_parent':
        return 'sub/' + rel_from(base / 'sub', target)
    raise ValueError(shape)
