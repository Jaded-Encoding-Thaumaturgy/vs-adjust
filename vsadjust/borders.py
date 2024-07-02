from __future__ import annotations

from itertools import chain
from typing import Sequence

from vstools import CustomEnum, CustomValueError, FunctionUtil, KwargsT, NotFoundEnumValue, PlanesT, core, vs

__all__ = [
    'bore'
]


class bore(CustomEnum):
    FIX_BRIGHTNESS: bore = object()  # type:ignore
    BALANCE: bore = object()  # type:ignore

    def __call__(
        self, clip: vs.VideoNode,
        left: int | Sequence[int] = 0, right: int | Sequence[int] = 0,
        top: int | Sequence[int] = 0, bottom: int | Sequence[int] = 0,
        planes: PlanesT = None, **kwargs: KwargsT
    ) -> vs.VideoNode:
        func = FunctionUtil(clip, self.__class__, planes, vs.YUV, 32)

        values = list(map(func.norm_seq, (left, right, top, bottom)))

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

            proc_clip = plugin(proc_clip, *plane_values, plane=plane, **kwargs)  # type:ignore

        return func.return_clip(proc_clip)
