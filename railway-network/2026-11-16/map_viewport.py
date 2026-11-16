"""One geographic viewport, fitted inside the fixed poster layout frame."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class MapViewport:
    left: float
    top: float
    width: float
    height: float

    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height

    @property
    def extent(self):
        return self.left, self.right, self.bottom, self.top

    def pixel_size(self, dpi):
        return max(1, round(self.width / 25.4 * dpi)), max(1, round(self.height / 25.4 * dpi))

    @classmethod
    def from_bbox(cls, bbox):
        south, west, north, east = bbox
        if not all(math.isfinite(v) for v in bbox) or not (-90 < south < north < 90 and -180 <= west < east <= 180):
            raise ValueError("Invalid geographic viewport bbox")
        width = (east - west) * math.cos(math.radians((south + north) / 2))
        height = north - south
        scale = min(MAP_FRAME.width / width, MAP_FRAME.height / height)
        width, height = width * scale, height * scale
        return cls(MAP_FRAME.left + (MAP_FRAME.width - width) / 2,
                   MAP_FRAME.top + (MAP_FRAME.height - height) / 2, width, height)

    def clip_segment(self, a, b):
        x0, y0 = a
        dx, dy = b[0] - x0, b[1] - y0
        t0, t1 = 0.0, 1.0
        for p, q in ((-dx, x0 - self.left), (dx, self.right - x0),
                     (-dy, y0 - self.top), (dy, self.bottom - y0)):
            if p == 0:
                if q < 0:
                    return None
                continue
            ratio = q / p
            if p < 0:
                if ratio > t1:
                    return None
                t0 = max(t0, ratio)
            else:
                if ratio < t0:
                    return None
                t1 = min(t1, ratio)
        return [(x0 + t0 * dx, y0 + t0 * dy), (x0 + t1 * dx, y0 + t1 * dy)]


# Layout allocation, not permission to paint beyond the observed source bbox.
MAP_FRAME = MapViewport(31.0, 53.0, 358.0, 443.0)
