#!/usr/bin/env python3
import math
import os
import struct
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from shapely import affinity
from shapely.geometry import GeometryCollection, LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import triangulate, unary_union


Vec2 = Tuple[float, float]
Vec3 = Tuple[float, float, float]
Tri = Tuple[Vec3, Vec3, Vec3]


def to_v3(p: Vec2, z: float) -> Vec3:
    return (float(p[0]), float(p[1]), float(z))


def quad(a: Vec3, b: Vec3, c: Vec3, d: Vec3, flip: bool = False) -> List[Tri]:
    if flip:
        return [(a, c, b), (a, d, c)]
    return [(a, b, c), (a, c, d)]


def signed_area(loop: Sequence[Vec2]) -> float:
    area = 0.0
    for i in range(len(loop)):
        x1, y1 = loop[i]
        x2, y2 = loop[(i + 1) % len(loop)]
        area += x1 * y2 - x2 * y1
    return area / 2.0


def ensure_orientation(loop: Sequence[Vec2], ccw: bool) -> List[Vec2]:
    pts = [(float(x), float(y)) for x, y in loop]
    if len(pts) < 3:
        return pts
    is_ccw = signed_area(pts) > 0
    if is_ccw != ccw:
        pts.reverse()
    return pts


def contour_area(loop: Sequence[Vec2]) -> float:
    return signed_area(loop)


def side_walls(loop: Sequence[Vec2], z0: float, z1: float, outward: bool) -> List[Tri]:
    pts = ensure_orientation(loop, ccw=True)
    tris: List[Tri] = []
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        p0b = to_v3(pts[i], z0)
        p1b = to_v3(pts[j], z0)
        p1t = to_v3(pts[j], z1)
        p0t = to_v3(pts[i], z1)
        tris += quad(p0b, p1b, p1t, p0t, flip=not outward)
    return tris


def iter_polygons(geom) -> Iterable[Polygon]:
    if geom.is_empty:
        return
    if isinstance(geom, Polygon):
        yield geom
        return
    if isinstance(geom, MultiPolygon):
        for poly in geom.geoms:
            yield poly
        return
    if isinstance(geom, GeometryCollection):
        for child in geom.geoms:
            yield from iter_polygons(child)


def surface_tris(geom, z: float, flip: bool = False) -> List[Tri]:
    tris: List[Tri] = []
    for poly in iter_polygons(geom):
        for tri in triangulate(poly):
            if not poly.covers(tri):
                continue
            pts = ensure_orientation(list(tri.exterior.coords)[:-1], ccw=True)
            a, b, c = [to_v3(p, z) for p in pts[:3]]
            tris.append((a, c, b) if flip else (a, b, c))
    return tris


def wall_tris_from_geom(geom, z0: float, z1: float) -> List[Tri]:
    tris: List[Tri] = []
    for poly in iter_polygons(geom):
        tris += side_walls(list(poly.exterior.coords)[:-1], z0, z1, outward=True)
        for hole in poly.interiors:
            tris += side_walls(list(hole.coords)[:-1], z0, z1, outward=False)
    return tris


def rounded_rect(width: float, height: float, radius: float, resolution: int) -> Polygon:
    if radius <= 0:
        return box(-width / 2.0, -height / 2.0, width / 2.0, height / 2.0)
    core = box(-width / 2.0 + radius, -height / 2.0 + radius, width / 2.0 - radius, height / 2.0 - radius)
    return core.buffer(radius, resolution=resolution, join_style=1)


def design_outer_profile(body_w: float, body_h: float, body_r: float) -> Polygon:
    body = rounded_rect(body_w, body_h, body_r, resolution=24)

    ring_center = (-body_w / 2.0 - 6.7, body_h / 2.0 - 7.6)
    accent_center = (ring_center[0] - 1.8, ring_center[1] + 4.2)
    bridge = LineString(
        [
            (-body_w / 2.0 + 1.8, body_h / 2.0 - 10.8),
            (-body_w / 2.0 - 4.6, body_h / 2.0 - 7.4),
            (ring_center[0] + 1.9, ring_center[1] - 0.3),
        ]
    ).buffer(4.35, resolution=24, cap_style=1, join_style=1)

    ear_shell = unary_union(
        [
            Point(*ring_center).buffer(7.9, resolution=48),
            Point(*accent_center).buffer(4.9, resolution=48),
            bridge,
        ]
    ).buffer(0.7, resolution=24).buffer(-0.7, resolution=24)

    outer = unary_union([body, ear_shell]).buffer(0)
    hole = Point(ring_center[0] - 0.2, ring_center[1] - 0.4).buffer(3.1, resolution=48)
    return outer.difference(hole).buffer(0)


def build_text_geometry(
    text: str,
    *,
    font_path: Path,
    target_width: float,
    target_height: float,
    center: Vec2 = (0.0, 0.0),
    mirror_x: bool = False,
) -> Polygon:
    path = TextPath((0, 0), text, size=1, prop=FontProperties(fname=str(font_path)))
    outers: List[Polygon] = []
    holes: List[Polygon] = []
    for contour in path.to_polygons():
        if len(contour) < 3:
            continue
        coords = [(float(x), float(y)) for x, y in contour]
        ring = Polygon(coords).buffer(0)
        if ring.is_empty or ring.area <= 0:
            continue
        if contour_area(coords) < 0:
            outers.append(Polygon(ensure_orientation(list(ring.exterior.coords)[:-1], ccw=True)))
        else:
            holes.append(Polygon(ensure_orientation(list(ring.exterior.coords)[:-1], ccw=True)))

    letter_polys: List[Polygon] = []
    for outer in outers:
        inner_loops = []
        for hole in holes:
            probe = hole.representative_point()
            if outer.contains(probe):
                inner_loops.append(list(hole.exterior.coords)[:-1])
        letter_polys.append(Polygon(list(outer.exterior.coords)[:-1], inner_loops))

    geom = unary_union(letter_polys).buffer(0)
    min_x, min_y, max_x, max_y = geom.bounds
    width = max_x - min_x
    height = max_y - min_y
    scale = min(target_width / width, target_height / height)
    geom = affinity.scale(geom, xfact=-scale if mirror_x else scale, yfact=scale, origin=(0, 0))
    min_x, min_y, max_x, max_y = geom.bounds
    geom = affinity.translate(
        geom,
        xoff=center[0] - (min_x + max_x) / 2.0,
        yoff=center[1] - (min_y + max_y) / 2.0,
    )
    return geom.buffer(0)


def solid_tris(geom, z0: float, z1: float) -> List[Tri]:
    return wall_tris_from_geom(geom, z0, z1) + surface_tris(geom, z1, flip=False) + surface_tris(geom, z0, flip=True)


def write_binary_stl(path: Path, tris: Sequence[Tri], name: str) -> None:
    header = name[:80].encode("ascii", errors="ignore").ljust(80, b" ")
    with path.open("wb") as handle:
        handle.write(header)
        handle.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            handle.write(struct.pack("<3f", 0.0, 0.0, 0.0))
            handle.write(struct.pack("<3f", *a))
            handle.write(struct.pack("<3f", *b))
            handle.write(struct.pack("<3f", *c))
            handle.write(struct.pack("<H", 0))


def bbox(tris: Sequence[Tri]) -> Tuple[Vec3, Vec3]:
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    for tri in tris:
        for x, y, z in tri:
            mins[0] = min(mins[0], x)
            mins[1] = min(mins[1], y)
            mins[2] = min(mins[2], z)
            maxs[0] = max(maxs[0], x)
            maxs[1] = max(maxs[1], y)
            maxs[2] = max(maxs[2], z)
    return (mins[0], mins[1], mins[2]), (maxs[0], maxs[1], maxs[2])


def build_keychain(plate_number: str) -> None:
    out = Path(f"3d/HeyRent_keychain_{plate_number}.stl")
    font_path = Path.home() / "Library/Fonts/Poppins-Bold.ttf"

    body_w = 66.0
    body_h = 28.0
    body_r = 4.8
    thickness = 4.2

    pocket_margin = 3.3
    pocket_depth = 0.9
    pocket_r = 3.1
    pocket_padding = 1.4
    text_height = 0.58
    badge_height = 0.32

    z_top = thickness / 2.0
    z_bot = -thickness / 2.0
    z_top_floor = z_top - pocket_depth
    z_bot_floor = z_bot + pocket_depth

    outer_profile = design_outer_profile(body_w, body_h, body_r)
    pocket = rounded_rect(body_w - 2 * pocket_margin, body_h - 2 * pocket_margin, pocket_r, resolution=24)
    top_surface = outer_profile.difference(pocket).buffer(0)

    pocket_w = body_w - 2 * pocket_margin - 2 * pocket_padding
    pocket_h = body_h - 2 * pocket_margin - 2 * pocket_padding

    plate_text = build_text_geometry(
        plate_number,
        font_path=font_path,
        target_width=pocket_w * 0.87,
        target_height=pocket_h * 0.44,
        center=(0.65, 1.1),
        mirror_x=False,
    )
    badge_text = build_text_geometry(
        "HeyRent!",
        font_path=font_path,
        target_width=pocket_w * 0.56,
        target_height=pocket_h * 0.19,
        center=(0.65, -7.25),
        mirror_x=False,
    )
    tris: List[Tri] = []
    tris += wall_tris_from_geom(outer_profile, z_bot, z_top)
    tris += surface_tris(top_surface, z_top, flip=False)
    tris += surface_tris(outer_profile, z_bot, flip=True)
    tris += wall_tris_from_geom(pocket, z_top_floor, z_top)
    tris += surface_tris(pocket, z_top_floor, flip=False)
    tris += solid_tris(plate_text, z_top_floor, z_top_floor + text_height)
    tris += solid_tris(badge_text, z_top_floor, z_top_floor + badge_height)

    write_binary_stl(out, tris, name=f"HeyRent keychain {plate_number}")
    mn, mx = bbox(tris)
    print(f"Wrote {out} with {len(tris)} triangles")
    print(f"BBox min={mn} max={mx} size={(mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2])}")


def main() -> None:
    build_keychain("GC397WD")
    build_keychain("FZ687HJ")


if __name__ == "__main__":
    main()
