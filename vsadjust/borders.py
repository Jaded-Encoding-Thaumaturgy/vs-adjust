from __future__ import annotations

from itertools import chain
from typing import Sequence

from vstools import CustomEnum, CustomValueError, FunctionUtil, KwargsT, NotFoundEnumValue, PlanesT, core, depth, vs

__all__ = [
    'bore'
]


class bore(CustomEnum):
    SINGLE_PLANE: bore = object()  # type:ignore
    SINGLE_PLANE_LIMITED: bore = object()  # type:ignore
    SINGLE_PLANE_WEIGHTED: bore = object()  # type:ignore

    def __call__(
        self, clip: vs.VideoNode,
        left: int | Sequence[int] = 0, right: int | Sequence[int] = 0,
        top: int | Sequence[int] = 0, bottom: int | Sequence[int] = 0,
        ignore_mask: vs.VideoNode | Sequence[vs.VideoNode] | None = None,
        planes: PlanesT = None, **kwargs: KwargsT
    ) -> vs.VideoNode:
        func = FunctionUtil(clip, self.__class__, planes, vs.YUV, 32)

        values = list(map(func.norm_seq, (top, bottom, left, right)))

        if any(x < 0 for x in chain(*values)):
            raise CustomValueError('Negative values are not allowed!', func.func)

        if not any(x != 0 for x in chain(*values)):
            return clip

        try:
            if self == self.SINGLE_PLANE:
                plugin = core.bore.SinglePlane
            elif self == self.SINGLE_PLANE_LIMITED:
                plugin = core.bore.SinglePlaneLimited
            elif self == self.SINGLE_PLANE_WEIGHTED:
                plugin = core.bore.SinglePlaneWeighted
            else:
                raise NotFoundEnumValue
        except AttributeError:
            raise CustomValueError(
                'Could not find the given Bore function! Make sure you\'re using an up-to-date version of Bore.',
                func.func, dict(function=self)
            )
        except NotFoundEnumValue:
            raise NotFoundEnumValue(
                'Invalid Bore enum!', func.func, dict(member=self, valid_function=bore.__members__.keys())
            )

        ignore_masks = [
            depth(igmask, func.work_clip.format)
            if igmask else None
            for igmask in func.norm_seq(ignore_mask, null=None)
        ]

        proc_clip: vs.VideoNode = func.work_clip

        for plane in func.norm_planes:
            plane_values = values[plane]

            if not any(x != 0 for x in plane_values):
                continue

            proc_clip = plugin(  # type:ignore
                proc_clip, *plane_values, plane=plane, ignore_mask=ignore_masks[plane], **kwargs
            )

        return func.return_clip(proc_clip)
