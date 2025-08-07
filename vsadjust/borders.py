from __future__ import annotations

from itertools import chain
from typing import Any, Sequence, cast

from jetpytools import fallback
from vsmasktools import rekt_partial
from vstools import (
    ColorRange,
    CustomEnum,
    CustomValueError,
    FunctionUtil,
    NotFoundEnumValue,
    PlanesT,
    core,
    get_lowest_value,
    get_peak_value,
    vs,
)

from .levels import fix_levels

__all__ = ["bore", "fix_line_brightness"]


class bore(CustomEnum):  # noqa: N801
    FIX_BRIGHTNESS = cast("bore", object())
    """Multiply every pixel by an average ratio of each pixel in a line to its nearest pixel in the next line."""

    BALANCE = cast("bore", object())
    """Uses linear least squares to calculate the best multiplier for each line."""

    def __call__(
        self,
        clip: vs.VideoNode,
        left: int | Sequence[int] = 0,
        right: int | Sequence[int] = 0,
        top: int | Sequence[int] = 0,
        bottom: int | Sequence[int] = 0,
        planes: PlanesT = None,
        **kwargs: Any,
    ) -> vs.VideoNode:
        """
        BB-mod style border deringer.

        Args:
            clip: Clip to process.
            left: Number of pixels to adjust on the left border. Defaults to 0.
            right: Number of pixels to adjust on the right border. Defaults to 0.
            top: Number of pixels to adjust on the top border. Defaults to 0.
            bottom: Number of pixels to adjust on the bottom border. Defaults to 0.
            planes: Planes to process. Default: All planes. Defaults to None.

        Returns:
            Clip with borders adjusted.
        """

        func = FunctionUtil(clip, self.__class__, planes, (vs.YUV, vs.GRAY), 32)

        values = list(zip(*(func.norm_seq(x, 0) for x in (left, right, top, bottom))))

        if any(x < 0 for x in chain(*values)):
            raise CustomValueError("Negative values are not allowed!", func.func)

        if not any(x != 0 for x in chain(*values)):
            return clip

        if self is self.FIX_BRIGHTNESS:
            plugin = core.bore.FixBrightness
        elif self is self.BALANCE:
            plugin = core.bore.Balance
        else:
            raise NotFoundEnumValue

        proc_clip = func.work_clip

        for plane in func.norm_planes:
            plane_values = values[plane]

            if not any(x != 0 for x in plane_values):
                continue

            proc_clip = cast(vs.VideoNode, plugin(proc_clip, *plane_values, plane=plane, **kwargs))

        return func.return_clip(proc_clip)


def fix_line_brightness(
    clip: vs.VideoNode, rows: dict[int, float] | None = None, columns: dict[int, float] | None = None
) -> vs.VideoNode:
    """
    Fix darkened or brightened luma rows or columns using manual level adjustments.

    Adjustments are fix_levels calls where max/min in is moved by adjustment / 100 * peak - low.
    As such, adjustment values must lie in (-100, 100).

    Args:
        clip: The clip to process.
        rows: Rows and their adjustment values. Rows < 0 are counted from the bottom.
        columns: Columns and their adjustment values. Columns < 0 are counted from the left.

    Raises:
        ValueError: If adjustment values are not in the range (-100, 100) (exclusive).

    Returns:
        Clip with adjusted rows and columns.
    """
    func = FunctionUtil(clip, fix_line_brightness, 0, vs.GRAY, 32)

    fix = func.work_clip
    color_range = ColorRange.from_video(fix)
    peak = get_peak_value(fix, False, color_range)
    low = get_lowest_value(fix, False, color_range)
    low_to_peak = peak - low

    rows = fallback(rows, {})
    columns = fallback(columns, {})

    def _fix_line(clip: vs.VideoNode, is_row: bool, num: int, adjustment: float) -> vs.VideoNode:
        if 100 < adjustment < -100:
            raise ValueError("fix_line_brightness: adjustment values must be in (-100, 100)")

        if adjustment > 0:

            def func_adj(c: vs.VideoNode) -> vs.VideoNode:
                return fix_levels(c, max_in=peak - low_to_peak * adjustment / 100, max_out=peak)

        elif adjustment < 0:

            def func_adj(c: vs.VideoNode) -> vs.VideoNode:
                return fix_levels(c, min_in=low + low_to_peak * adjustment / 100, min_out=low)
        else:
            return clip

        if is_row:
            return rekt_partial(clip, func_adj, top=num, bottom=clip.height - num - 1)

        return rekt_partial(clip, func_adj, left=num, right=clip.width - num - 1)

    for row, adj in rows.items():
        if row < 0:
            row += clip.height
        fix = _fix_line(fix, True, row, adj)

    for col, adj in columns.items():
        if col < 0:
            col += clip.width
        fix = _fix_line(fix, False, col, adj)

    return func.return_clip(fix)
