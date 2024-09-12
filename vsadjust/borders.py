from __future__ import annotations

from itertools import chain
from typing import Sequence
from vstools import CustomEnum, CustomValueError, FunctionUtil, KwargsT, NotFoundEnumValue, PlanesT, core, vs

__all__ = [
    'bore'
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
