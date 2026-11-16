"""Reproduce the point data used in In Point — TOKYO / Traffic Signals."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

CENTER_LATITUDE = 35.6768601
CENTER_LONGITUDE = 139.7638947
EARTH_RADIUS_M = 6_371_008.8
HALF_SIDE_M = 18_250
SOURCE_COUNT = 27_450
SOURCE_SHA256 = "390cf8913d8cc023799c7eebd8739c48ef403e418a0ed7fcb4edcbf8e6b5b58a"
POINT_COUNT = 18_822


def source_nodes(response):
    if response.get("remark") or not isinstance(response.get("elements"), list):
        raise ValueError("The Overpass response is incomplete.")
    nodes = response["elements"]
    if len(nodes) != SOURCE_COUNT:
        raise ValueError(f"Expected {SOURCE_COUNT} source nodes, got {len(nodes)}.")
    result = {}
    for node in nodes:
        node_id, latitude, longitude = node["id"], node["lat"], node["lon"]
        if (
            node["type"] != "node"
            or node["tags"].get("highway") != "traffic_signals"
            or type(node_id) is not int
            or node_id <= 0
            or node_id in result
            or type(latitude) not in (int, float)
            or type(longitude) not in (int, float)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            raise ValueError(f"Invalid or duplicated traffic-signal node: {node_id}.")
        result[node_id] = (latitude, longitude)
    return result


def project(latitude, longitude):
    phi0, phi = map(math.radians, (CENTER_LATITUDE, latitude))
    dl = math.radians(longitude - CENTER_LONGITUDE)
    x = math.cos(phi) * math.sin(dl)
    y = math.cos(phi0) * math.sin(phi) - math.sin(phi0) * math.cos(phi) * math.cos(dl)
    dot = math.sin(phi0) * math.sin(phi) + math.cos(phi0) * math.cos(phi) * math.cos(dl)
    angle = math.atan2(math.hypot(x, y), dot)
    factor = EARTH_RADIUS_M * (angle / math.sin(angle) if angle else 1)
    return factor * x, factor * y


def point_rows(nodes):
    groups = {}
    for node_id, (latitude, longitude) in nodes.items():
        east, north = project(latitude, longitude)
        if max(abs(east), abs(north)) <= HALF_SIDE_M:
            key = (round(east, 3), round(north, 3))
            groups.setdefault(key, []).append(f"n{node_id}")
    if len(groups) != POINT_COUNT:
        raise ValueError(f"Expected {POINT_COUNT} points, got {len(groups)}.")
    return [(east, north, sorted(ids)) for (east, north), ids in sorted(groups.items())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("response", type=Path, help="Overpass JSON response")
    args = parser.parse_args()
    try:
        nodes = source_nodes(json.loads(args.response.read_text(encoding="utf-8")))
        canonical_nodes = [
            (node_id, *nodes[node_id]) for node_id in sorted(nodes)
        ]
        fingerprint = hashlib.sha256(
            json.dumps(canonical_nodes, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if fingerprint != SOURCE_SHA256:
            raise ValueError(f"Source ID/coordinate SHA-256 does not match: {fingerprint}.")
        rows = point_rows(nodes)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(1, f"{exc}\n")

    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["east_m", "north_m", "osm_node_ids"])
    for east, north, ids in rows:
        writer.writerow([east, north, " ".join(ids)])


if __name__ == "__main__":
    main()
