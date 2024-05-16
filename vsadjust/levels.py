from typing import Sequence

from vsmasktools import rekt_partial
from vstools import (
    ColorRange, ColorRangeT, DitherType, FunctionUtil, PlanesT, depth, get_lowest_value, get_lowest_values,
    get_peak_value, get_peak_values, normalize_seq, scale_value, vs
)

__all__ = [
    'fix_levels', 'fix_range_levels',

    'fix_double_range'
]


def fix_levels(
    clip: vs.VideoNode, gamma: float = 0.88,
    min_in: int | float | Sequence[int | float] | None = None,
    min_out: int | float | Sequence[int | float] | None = None,
    max_in: int | float | Sequence[int | float] | None = None,
    max_out: int | float | Sequence[int | float] | None = None,
    input_depth: int | None = 8, planes: PlanesT = 0
) -> vs.VideoNode:
    func = FunctionUtil(clip, fix_levels, planes, vs.YUV, 32)

    if not any(x is not None for x in (min_in, min_out, max_in, max_out)):
        return fix_range_levels(clip, gamma, ColorRange.LIMITED, planes)

    color_range = ColorRange.from_video(clip, False, fix_range_levels)

    def_min = get_lowest_values(clip, color_range)
    def_max = get_peak_values(clip, color_range)

    min_in, min_out, max_in, max_out = [
        (None if x is None else normalize_seq(x))
        for x in (min_in, min_out, max_in, max_out)
    ]

    min_in = min_in or min_out or def_min
    max_in = max_in or max_out or def_max

    min_out = min_out or min_in
    max_out = max_out or max_in

    min_in, min_out, max_in, max_out = [
        list(
            (y if y <= 1.0 else scale_value(y, input_depth or clip, 32, scale_offsets=True, chroma=i != 0))
            for i, y in enumerate(x)
        ) for x in (min_in, min_out, max_in, max_out)
    ]

    fix_lvls: vs.VideoNode = func.work_clip

    if func.luma:
        fix_lvls = fix_lvls.std.Levels(min_in[0], max_in[0], gamma, min_out[0], max_out[0], 0)

    if func.chroma:
        cmin_in, cmin_out, cmax_in, cmax_out = [x[1:] for x in (min_in, min_out, max_in, max_out)]

        if all(len(set(x)) == 1 for x in (cmin_in, cmin_out, cmax_in, cmax_out)):
            print(fix_lvls, cmin_in[0], cmax_in[0], gamma, cmin_out[0], cmax_out[0], func.chroma_pplanes)
            fix_lvls = fix_lvls.std.Levels(
                cmin_in[0], cmax_in[0], gamma, cmin_out[0], cmax_out[0], func.chroma_pplanes
            )
        else:
            for i in func.chroma_pplanes:
                fix_lvls = fix_lvls.std.Levels(
                    cmin_in[i - 1], cmax_in[i - 1], gamma, cmin_out[i - 1], cmax_out[i - 1], i
                )

    return func.return_clip(fix_lvls)


def fix_range_levels(
    clip: vs.VideoNode, gamma: float = 0.88, range_in: ColorRangeT = ColorRange.LIMITED, planes: PlanesT = 0
) -> vs.VideoNode:
    color_range = ColorRange.from_param(range_in, fix_range_levels)

    if not color_range:
        color_range = ColorRange.from_video(clip, False, fix_range_levels)

    min_in = min_out = get_lowest_values(clip, color_range)
    max_in = max_out = get_peak_values(clip, color_range)

    return fix_levels(clip, gamma, min_in, min_out, max_in, max_out, None, planes)


def fix_double_range(clip: vs.VideoNode) -> vs.VideoNode:
    fix = depth(
        clip, range_in=ColorRange.LIMITED, range_out=ColorRange.FULL, dither_type=DitherType.ERROR_DIFFUSION
    )

    return ColorRange.LIMITED.apply(fix)


def fix_line_brightness(
    clip: vs.VideoNode,
    rows: dict[int, float] = {},
    columns: dict[int, float] = {},
) -> vs.VideoNode:
    """
    Fix darkened or brightened luma rows or columns using manual level adjustments.

    Adjustments are fix_levels calls where max/min in is moved by adjustment / 100 * peak - low.
    As such, adjustment values must lie in (-100, 100).

    :param clip: The clip to process.
    :param rows: Rows and their adjustment values. Rows < 0 are counted from the bottom.
    :param columns: Columns and their adjustment values. Columns < 0 are counted from the left.

    :return: Clip with adjusted rows and columns.
    """
    func = FunctionUtil(clip, fix_line_brightness, 0, vs.GRAY, 32)

    fix = func.work_clip
    color_range = ColorRange.from_video(fix)
    peak = get_peak_value(fix, False, color_range)
    low = get_lowest_value(fix, False, color_range)
    low_to_peak = peak - low

    def _fix_line(clip: vs.VideoNode, is_row: bool, num: int, adjustment: float) -> vs.VideoNode:
        if 100 < adjustment < -100:
            raise ValueError("fix_line_brightness: adjustment values must be in (-100, 100)")

        if adjustment > 0:
            adj = lambda c: fix_levels(c, max_in=peak - low_to_peak * adjustment / 100, max_out=peak)  # noqa: E731
        elif adjustment < 0:
            adj = lambda c: fix_levels(c, min_in=low + low_to_peak * adjustment / 100, min_out=low)  # noqa: E731
        else:
            return clip
        if is_row:
            return rekt_partial(clip, top=num, bottom=clip.height - num - 1, func=adj)
        return rekt_partial(clip, left=num, right=clip.width - num - 1, func=adj)

    for row, adj in rows.items():
        if row < 0:
            row += clip.height
        fix = _fix_line(fix, True, row, adj)
    for col, adj in columns.items():
        if col < 0:
            col += clip.width
        fix = _fix_line(fix, False, col, adj)

    return func.return_clip(fix)
