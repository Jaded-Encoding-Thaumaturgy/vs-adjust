from typing import Any

from vstools import vs, Matrix, Transfer, Primaries, ColorRange
from vskernels import Point

__all__ = [
    'colorspace_conversion'
]


def colorspace_conversion(
        clip: vs.VideoNode,
        matrix: Matrix = None,
        transfer: Transfer = None,
        primaries: Primaries = None,
        range: ColorRange = None,
        matrix_in: Matrix = None,
        transfer_in: Transfer = None,
        primaries_in: Primaries = None,
        range_in: ColorRange = None,
) -> vs.VideoNode:

    resample_kwargs = dict[str, Any]()

    if matrix is not None:
        if matrix_in is not None:
            clip = Matrix.from_param(matrix_in).apply(clip)
        resample_kwargs |= dict(matrix=matrix)

    if transfer is not None:
        if transfer_in is not None:
            clip = Transfer.from_param(transfer_in).apply(clip)
        resample_kwargs |= dict(transfer=transfer)

    if primaries is not None:
        if primaries_in is not None:
            clip = Primaries.from_param(primaries_in).apply(clip)
        resample_kwargs |= dict(primaries=primaries)

    if range is not None:
        if range_in is not None:
            clip = ColorRange.from_param(range_in).apply(clip)
        resample_kwargs |= dict(range=range.value_zimg)
    
    converted = Point.resample(clip, clip, **resample_kwargs)

    return converted
