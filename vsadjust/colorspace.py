from typing import Any

from vskernels import Point
from vstools import (ColorRange, ColorRangeT, DitherType, Matrix, MatrixT,
                     Primaries, PrimariesT, Transfer, TransferT, vs)

__all__ = [
    'colorspace_conversion'
]


def colorspace_conversion(
        clip: vs.VideoNode,
        matrix: MatrixT | None = None, transfer: TransferT | None = None,
        primaries: PrimariesT | None = None, color_range: ColorRangeT | None = None,
        matrix_in: MatrixT | None = None, transfer_in: TransferT | None = None,
        primaries_in: PrimariesT | None = None, color_range_in: ColorRangeT | None = None,
        dither_type: DitherType = DitherType.AUTO,
) -> vs.VideoNode:

    resample_kwargs = dict[str, Any](dither_type=dither_type)

    if matrix is not None:
        if matrix_in is not None:
            clip = Matrix.from_param(matrix_in).apply(clip)

        matrix = Matrix.from_param(matrix, colorspace_conversion)

        resample_kwargs |= dict(matrix=matrix)

    if transfer is not None:
        if transfer_in is not None:
            clip = Transfer.from_param(transfer_in).apply(clip)

        transfer = Transfer.from_param(transfer, colorspace_conversion)

        resample_kwargs |= dict(transfer=transfer)

    if primaries is not None:
        if primaries_in is not None:
            clip = Primaries.from_param(primaries_in).apply(clip)

        primaries = Primaries.from_param(primaries, colorspace_conversion)

        resample_kwargs |= dict(primaries=primaries)

    if color_range is not None:
        if color_range_in is not None:
            clip = ColorRange.from_param(color_range_in).apply(clip)

        color_range = ColorRange.from_param(color_range, colorspace_conversion)

        resample_kwargs |= dict(range=color_range.value_zimg)

    return Point.resample(clip, clip, **resample_kwargs)
