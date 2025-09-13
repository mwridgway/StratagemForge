"""Zone utilities: load zone polygons and assign zone names to points.

Supports two backends:
- shapely (fast, recommended): vector geometry + spatial index
- fallback ray casting (no deps): slower, OK for small batches
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from shapely.geometry import Point, Polygon  # type: ignore
    from shapely.strtree import STRtree  # type: ignore
    _HAS_SHAPELY = True
except Exception:  # pragma: no cover
    Point = Polygon = STRtree = None  # type: ignore
    _HAS_SHAPELY = False


@dataclass
class Zone:
    name: str
    polygon: List[Tuple[float, float]]
    priority: int = 0


def load_zones_json(path: str | Path) -> List[Zone]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    zones: List[Zone] = []
    for z in data.get("zones", []):
        name = z.get("name")
        poly = z.get("polygon") or []
        prio = int(z.get("priority", 0))
        if name and isinstance(poly, list) and len(poly) >= 3:
            zones.append(Zone(name=name, polygon=[(float(x), float(y)) for x, y in poly], priority=prio))
    return zones


def _point_in_poly_ray(x: float, y: float, poly: List[Tuple[float, float]]) -> bool:
    # Standard ray casting algorithm
    inside = False
    n = len(poly)
    px, py = x, y
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if ((y1 > py) != (y2 > py)):
            xinters = (py - y1) * (x2 - x1) / (y2 - y1 + 1e-12) + x1
            if px < xinters:
                inside = not inside
    return inside


def assign_zones(points: "list[tuple[float,float]] | np.ndarray", zones: List[Zone]) -> List[Optional[str]]:
    """Assign zone names to points.

    Returns a list of zone names (or None) matching input point order.
    """
    # Sort zones by descending priority so specific zones win overlaps
    zones_sorted = sorted(zones, key=lambda z: z.priority, reverse=True)

    if _HAS_SHAPELY and zones_sorted:
        polys = [Polygon(z.polygon) for z in zones_sorted]
        tree = STRtree(polys)
        names = [z.name for z in zones_sorted]
        result: List[Optional[str]] = []
        for (x, y) in points:
            pt = Point(float(x), float(y))
            candidates = tree.query(pt)
            chosen: Optional[str] = None
            # Respect priority order by scanning in zones_sorted order
            for i, poly in enumerate(polys):
                if poly in candidates and poly.contains(pt):
                    chosen = names[i]
                    break
            result.append(chosen)
        return result

    # Fallback: ray casting over all polygons (slower)
    result: List[Optional[str]] = []
    for (x, y) in points:
        chosen: Optional[str] = None
        for z in zones_sorted:
            if _point_in_poly_ray(float(x), float(y), z.polygon):
                chosen = z.name
                break
        result.append(chosen)
    return result

