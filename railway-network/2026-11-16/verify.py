"""Verify an archived Railway Network edition and recover the complete geometry."""
import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path
from struct import pack


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("edition", type=Path, help="city directory containing edition.json")
    parser.add_argument("--geometry", action="store_true", help="write the verified geometry and attribution JSON to stdout")
    options = parser.parse_args()

    manifest = json.loads((options.edition / "edition.json").read_bytes())
    compressed = (options.edition / "geometry.json.gz").read_bytes()
    if len(compressed) != manifest["download_bytes"] or sha(compressed) != manifest["download_sha256"]:
        raise SystemExit("Downloaded file does not match the edition manifest.")
    data = gzip.decompress(compressed)
    if sha(data) != manifest["database_sha256"]:
        raise SystemExit("Decoded database does not match the edition manifest.")
    database = json.loads(data)
    if database["city"] != options.edition.name or database["source_snapshots"] != {
        name: source["snapshot"] for name, source in manifest["source"].items()
    }:
        raise SystemExit("City or snapshot does not match.")
    if (database["attribution"], database["licence"], database["copyright"]) != (
        "© OpenStreetMap contributors", "https://opendatacommons.org/licenses/odbl/1-0/",
        "https://www.openstreetmap.org/copyright",
    ):
        raise SystemExit("OSM attribution or licence is missing.")
    geom = database["geometry"]
    if set(geom) != {"summary", "routes", "stations", "coast", "context"}:
        raise SystemExit("The geometry layers are incomplete.")
    style = database["route_styles"]
    if len(style) != len(geom["routes"]) or [x["draw_order"] for x in style] != sorted(x["draw_order"] for x in style):
        raise SystemExit("Route styles or group order do not match.")
    ctx = geom["context"]
    if set(ctx) != {"roads", "rivers", "water_outlines", "water_polygons"} or set(ctx["roads"]) != {
        "motorway", "trunk", "primary", "secondary"
    }:
        raise SystemExit("The background layers are incomplete.")
    route_digest = hashlib.sha256()
    for group in geom["routes"]:
        for a, b in group:
            route_digest.update(pack("<dddd", *a, *b))
    counts = {
        "route_geometry_sha256": route_digest.hexdigest(),
        "station_count": len(geom["stations"]),
        "coast_segment_count": len(geom["coast"]),
        "context_road_segment_count": sum(map(len, ctx["roads"].values())),
        "context_river_segment_count": len(ctx["rivers"]),
        "context_water_segment_count": len(ctx["water_outlines"]),
        "context_water_polygon_count": len(ctx["water_polygons"]),
    }
    if geom["summary"] != manifest["expected"] or any(geom["summary"][key] != value for key, value in counts.items()):
        raise SystemExit("The route fingerprint or a layer count does not match.")
    geometry_json = json.dumps(geom, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
    if sha(geometry_json) != manifest["geometry_sha256"]:
        raise SystemExit("The full geometry does not match the recorded edition.")
    if options.geometry:
        sys.stdout.buffer.write(data + b"\n")
    else:
        print(options.edition.name, "verified", manifest["geometry_sha256"])


if __name__ == "__main__":
    main()
