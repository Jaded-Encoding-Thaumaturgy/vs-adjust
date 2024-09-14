from __future__ import annotations

from itertools import chain
from typing import Sequence

from vsmasktools import rekt_partial
from vstools import (
    CustomEnum, CustomValueError, FunctionUtil, KwargsT, NotFoundEnumValue,
    PlanesT, ColorRange, get_peak_value, get_lowest_value, core, vs
)

from .levels import fix_levels

__all__ = [
    'bore',
    'fix_line_brightness'
]


class bore(CustomEnum):
    FIX_BRIGHTNESS: bore = object()  # type:ignore
    """Multiply every pixel by an average ratio of each pixel in a line to its nearest pixel in the next line."""

    BALANCE: bore = object()  # type:ignore
    """Uses linear least squares to calculate the best multiplier for each line."""

    def __call__(
        self, clip: vs.VideoNode,
        left: int | Sequence[int] = 0,
        right: int | Sequence[int] = 0,
        top: int | Sequence[int] = 0,
        bottom: int | Sequence[int] = 0,
        planes: PlanesT = None, **kwargs: KwargsT
    ) -> vs.VideoNode:
        """
        BB-mod style border deringer.

        :param clip:        Clip to process.
        :param left:        Number of pixels to adjust on the left border.
        :param right:       Number of pixels to adjust on the right border.
        :param top:         Number of pixels to adjust on the top border.
        :param bottom:      Number of pixels to adjust on the bottom border.
        :param planes:      Planes to process. Default: All planes.

        :return:            Clip with borders adjusted.
        """

        func = FunctionUtil(clip, self.__class__, planes, (vs.YUV, vs.GRAY), 32)

        values = list(zip(*map(func.norm_seq, (left, right, top, bottom))))

        if any(x < 0 for x in chain(*values)):
            raise CustomValueError('Negative values are not allowed!', func.func)

        if not any(x != 0 for x in chain(*values)):
            return clip

        try:
            if self == self.FIX_BRIGHTNESS:
                plugin = core.bore.FixBrightness
            elif self == self.BALANCE:
                plugin = core.bore.Balance
            else:
                raise NotFoundEnumValue
        except AttributeError:
            raise CustomValueError(
                'Could not find this bore function! Make sure you\'re using an up-to-date version of Bore.',
                func.func, dict(function=self)
            )
        except NotFoundEnumValue:
            raise NotFoundEnumValue(
                'Invalid bore enum!', func.func, dict(member=self, valid_function=bore.__members__.keys())
            )

        proc_clip: vs.VideoNode = func.work_clip

        for plane in func.norm_planes:
            plane_values = values[plane]

            if not any(x != 0 for x in plane_values):
                continue

            proc_clip = plugin(proc_clip, *plane_values, plane=plane, **kwargs)

        return func.return_clip(proc_clip)


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
