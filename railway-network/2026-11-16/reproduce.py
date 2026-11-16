"""Reproduce Railway Network's line and point geometry from two Overpass responses."""

import argparse
import hashlib
from itertools import pairwise
import json
import math
from pathlib import Path
from struct import pack

from matplotlib.colors import is_color_like
from map_viewport import MAP_FRAME, MapViewport


def source_elements(path, expected=None):
    data = json.loads(path.read_bytes())
    if data.get("remark") or not isinstance(data.get("elements"), list):
        raise ValueError(f"Incomplete Overpass response: {path.name}")
    elements = data["elements"]
    if expected:
        normalized = "\n".join(sorted(
            json.dumps(row, sort_keys=True, separators=(",", ":")) for row in elements
        )).encode("utf-8")
        if len(elements) != expected["elements"] or hashlib.sha256(normalized).hexdigest() != expected["elements_sha256"]:
            raise ValueError(f"Source features do not match the recorded snapshot: {path.name}")
    return elements


def geometry(network, context, config):
    south, west, north, east = config["bbox"]
    viewport = MapViewport.from_bbox(config["bbox"])

    if config["projection"] == "legacy-frame":
        viewport = MAP_FRAME
        longitude_factor = math.cos(math.radians((south + north) / 2))
        width = (east - west) * longitude_factor
        height = north - south
        scale = min(viewport.width / width, viewport.height / height)
        left = viewport.left + (viewport.width - width * scale) / 2
        top = viewport.top + (viewport.height - height * scale) / 2

        def point(node):
            return left + (node["lon"] - west) * longitude_factor * scale, top + (north - node["lat"]) * scale

    else:
        def point(node):
            x = viewport.left + (node["lon"] - west) / (east - west) * viewport.width
            y = viewport.top + (north - node["lat"]) / (north - south) * viewport.height
            return x, y

    def way_points(way, nodes):
        return [point(nodes[node_id]) for node_id in way.get("nodes", []) if node_id in nodes]

    def clipped(points):
        return [segment for a, b in pairwise(points) if (segment := viewport.clip_segment(a, b))]

    def relation_style(relation):
        tags = relation.get("tags", {})
        identity = " ".join(str(tags.get(key, "")) for key in ("operator", "network", "name", "ref"))
        operator_colour = next(
            (entry["colour"] for entry in config["operator_colours"] if any(name in identity for name in entry["match"])),
            None,
        )
        if tags.get("route", "train") in config["relation_colour_routes"]:
            colour = tags.get("colour")
            if not colour or not is_color_like(colour):
                colour = operator_colour or config["fallback_transit"]
            return colour, config["line_widths"]["transit"], 3
        return operator_colour or config["fallback_train"], config["line_widths"]["train"], 2

    nodes = {row["id"]: row for row in network if row["type"] == "node"}
    ways = {row["id"]: row for row in network if row["type"] == "way"}
    relations = sorted((row for row in network if row["type"] == "relation"), key=lambda row: row["id"])
    stations = [point(row) for _, row in sorted(nodes.items()) if row.get("tags", {}).get("railway") in {"station", "halt"}]
    seen, selected_ways, route_groups = set(), set(), {}
    for relation in relations:
        style = relation_style(relation)
        for member in relation.get("members", []):
            if member["type"] != "way" or member.get("role") in {"platform", "stop"}:
                continue
            way_id = member["ref"]
            key = (way_id, style[0])
            if key in seen or way_id not in ways:
                continue
            selected_ways.add(way_id)
            seen.add(key)
            points = way_points(ways[way_id], nodes)
            if len(points) >= 2:
                route_groups.setdefault(style, []).extend(clipped(points))

    ordered_groups = sorted(route_groups.items(), key=lambda item: item[0][2])
    routes = [segments for _, segments in ordered_groups]
    digest = hashlib.sha256()
    for segments in routes:
        for a, b in segments:
            digest.update(pack("<dddd", *a, *b))
    coast = [
        segment
        for _, way in sorted(ways.items())
        if way.get("tags", {}).get("natural") == "coastline"
        for segment in clipped(way_points(way, nodes))
    ]

    context_nodes = {row["id"]: row for row in context if row["type"] == "node"}
    context_ways = sorted((row for row in context if row["type"] == "way"), key=lambda row: row["id"])
    roads = {key: [] for key in ("motorway", "trunk", "primary", "secondary")}
    rivers, water_outlines, water_polygons = [], [], []
    for way in context_ways:
        points = way_points(way, context_nodes)
        if len(points) < 2:
            continue
        tags = way.get("tags", {})
        highway = tags.get("highway")
        if highway in roads:
            roads[highway].extend(clipped(points))
        if tags.get("waterway") in {"river", "canal"}:
            rivers.extend(clipped(points))
        if tags.get("natural") == "water":
            water_outlines.extend(clipped(points))
            if len(points) >= 4 and points[0] == points[-1]:
                water_polygons.append(points)

    summary = {
        "route_geometry_sha256": digest.hexdigest(),
        "route_relation_count": len(relations),
        "route_way_count": len(selected_ways),
        "station_count": len(stations),
        "coast_segment_count": len(coast),
        "context_road_segment_count": sum(map(len, roads.values())),
        "context_river_segment_count": len(rivers),
        "context_water_segment_count": len(water_outlines),
        "context_water_polygon_count": len(water_polygons),
    }
    return {
        "summary": summary,
        "routes": routes,
        "route_styles": [{"colour": style[0], "width_pt": style[1], "draw_order": style[2]}
                         for style, _ in ordered_groups],
        "stations": stations,
        "coast": coast,
        "context": {"roads": roads, "rivers": rivers, "water_outlines": water_outlines, "water_polygons": water_polygons},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("edition", "network", "context"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    edition = json.loads(args.edition.read_bytes())
    checks = edition["source"]
    result = geometry(
        source_elements(args.network, checks["network"]),
        source_elements(args.context, checks["context"]),
        edition["processing"],
    )
    if result["summary"] != edition["expected"]:
        raise SystemExit("The reproduced geometry does not match the recorded edition.")
    print(json.dumps(result, separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    main()
