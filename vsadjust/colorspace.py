from vstools import FunctionUtil, Matrix, vs
from vskernels import Point

__all__ = [
    "fix_colorspace_conversion"
]


def fix_colorspace_conversion(
    clip: vs.VideoNode,
    matrix_src: Matrix | None = None,
    matrix_og: Matrix = Matrix.BT470BG,
) -> vs.VideoNode:
    """
    Function to fix improper colorspace conversions.

    An example of this would be a BT709 video that was converted
    to BT470BG during production and tagged as BT709.

    :param clip:        Clip to process.
    :param matrix_src:  The Matrix of the input clip. This will also be the output matrix.
    :param matrix_og:   The original Matrix that the input clip was converted from.

    :return:            Clip with converted Matrix.
    """
    func = FunctionUtil(clip, fix_colorspace_conversion, None, vs.YUV, 32)

    matrix_src = Matrix.from_param_or_video(matrix_src, clip, True, fix_colorspace_conversion)
    matrix_og = Matrix.from_param(matrix_og, fix_colorspace_conversion)

    if matrix_src == matrix_og:
        return clip

    clip_csp = Point.resample(func.work_clip, func.work_clip, matrix_og, matrix_src)
    clip_csp = matrix_src.apply(clip_csp)

    return func.return_clip(clip_csp)
