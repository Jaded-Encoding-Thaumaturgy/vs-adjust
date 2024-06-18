from __future__ import annotations

from vstools import (CustomStrEnum, CustomValueError, FunctionUtil, KwargsT,
                     PlanesT, core, vs)

__all__ = [
    'bore'
]


class _bore(CustomStrEnum):
    FIX_BRIGHTNESS: _bore = 'fix_brightness'  # type:ignore
    BALANCE: _bore = 'balance'  # type:ignore

    def __call__(
        self, clip: vs.VideoNode,
        left: int | list[int] = 0, right: int | list[int] = 0,
        top: int | list[int] = 0, bottom: int | list[int] = 0,
        planes: PlanesT = None, **kwargs: KwargsT
    ) -> vs.VideoNode:
        func = FunctionUtil(clip, 'bore', planes, vs.YUV, 32)

        for param in ('left', 'right', 'top', 'bottom', 'plane'):
            kwargs.pop(param, None)

        if any((left, right, top, bottom)) < 0:
            raise CustomValueError('Negative values are not allowed!', func.func)

        if not any((left, right, top, bottom)):
            return clip

        try:
            if self.value == 'fix_brightness':
                plugin = core.bore.FixBrightness  # type:ignore
            else:  # elif self.value == 'balance':
                plugin = core.bore.Balance  # type:ignore
        except AttributeError:
            raise CustomValueError(
                f'Could not find function for \"{self.value}\"! '
                'Make sure you\'re using an up-to-date version of Bore.',
                func.func, self.value
            )

        left, right, top, bottom = tuple([
            i if isinstance(i, list) else [i] * func.num_planes
            for i in (left, right, top, bottom)
        ])

        proc_clip: vs.VideoNode = func.work_clip

        for plane, l, r, t, b in zip(func.norm_planes, left, right, top, bottom):
            proc_clip = plugin(l, r, t, b, plane=plane, **kwargs)  # type:ignore

        return func.return_clip(proc_clip)


bore = _bore.FIX_BRIGHTNESS
