from __future__ import annotations

from itertools import chain
from typing import Sequence

from vstools import CustomStrEnum, CustomValueError, FunctionUtil, KwargsT, PlanesT, core, vs

__all__ = [
    'bore'
]


class _bore(CustomStrEnum):
    FIX_BRIGHTNESS: _bore = 'fix_brightness'  # type:ignore
    BALANCE: _bore = 'balance'  # type:ignore

    def __call__(
        self, clip: vs.VideoNode,
        left: int | Sequence[int] = 0, right: int | Sequence[int] = 0,
        top: int | Sequence[int] = 0, bottom: int | Sequence[int] = 0,
        planes: PlanesT = None, **kwargs: KwargsT
    ) -> vs.VideoNode:
        func = FunctionUtil(clip, 'bore', planes, vs.YUV, 32)

        values = list(map(func.norm_seq, (left, right, top, bottom)))

        if any(x < 0 for x in chain(*values)):
            raise CustomValueError('Negative values are not allowed!', func.func)

        if not any(x != 0 for x in chain(*values)):
            return clip

        try:
            if self == 'fix_brightness':
                plugin = core.bore.FixBrightness
            elif self == 'balance':
                plugin = core.bore.Balance
            else:
                raise AttributeError
        except AttributeError:
            raise CustomValueError(
                'Could not find this bore function! Make sure you\'re using an up-to-date version of Bore.',
                func.func, dict(function=self.value)
            )

        proc_clip: vs.VideoNode = func.work_clip

        for plane in func.norm_planes:
            plane_values = values[plane]

            if not any(x != 0 for x in plane_values):
                continue

            proc_clip = plugin(proc_clip, *plane_values, plane=plane, **kwargs)  # type:ignore

        return func.return_clip(proc_clip)


bore = _bore.FIX_BRIGHTNESS
