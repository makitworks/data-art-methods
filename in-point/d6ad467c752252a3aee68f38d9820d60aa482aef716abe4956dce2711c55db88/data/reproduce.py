import hashlib
import json
import sys
from pathlib import Path
EDITION = json.loads(Path(__file__).with_name('edition.json').read_text())

import math
from collections import defaultdict
from itertools import pairwise
RADIUS_M = 6371008.8
def project(latitude, longitude, plan):
    phi0, phi = map(math.radians, (plan['latitude'], latitude))
    dl = math.radians(longitude - plan['longitude'])
    x = math.cos(phi) * math.sin(dl)
    y = math.cos(phi0) * math.sin(phi) - math.sin(phi0) * math.cos(phi) * math.cos(dl)
    angle = math.atan2(math.hypot(x, y), math.sin(phi0) * math.sin(phi) + math.cos(phi0) * math.cos(phi) * math.cos(dl))
    factor = RADIUS_M * (angle / math.sin(angle) if angle else 1)
    return factor * x, factor * y

def coordinates(value, plan):
    lat, lon = value.get('lat'), value.get('lon')
    if not all(type(v) in (float, int) and math.isfinite(v) and abs(v) <= limit for v, limit in ((lat, 90), (lon, 180))):
        raise ValueError('OSM原本の緯度経度が不正です')
    return project(lat, lon, plan)

def point_features(elements, plan):
    groups = defaultdict(list)
    for element in elements:
        kind = element['type']
        coordinate = element if kind == 'node' else element.get('center')
        if kind not in {'node', 'way', 'relation'} or not isinstance(coordinate, dict):
            raise ValueError('OSM原本に種別または代表点がありません')
        x, y = coordinates(coordinate, plan)
        if max(abs(x), abs(y)) <= plan['side_m'] / 2:
            groups[round(x, 3), round(y, 3)].append(f"{kind[0]}{element['id']}")
    return [(x, y, sorted(ids)) for (x, y), ids in sorted(groups.items())]

def source_fingerprint(response, *, points_only):
    if response.get("remark") or not isinstance(response.get("elements"), list):
        raise ValueError("Incomplete Overpass response")
    elements = response["elements"]
    if points_only:
        by_id = {(row["type"], row["id"]): (row.get("lat"), row.get("lon"), row.get("center")) for row in elements}
        if len(by_id) != len(elements):
            raise ValueError("Duplicate OSM IDs")
        records = [[*key, *coords] for key, coords in sorted(by_id.items())]
    else:
        records = sorted(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in elements)
    return hashlib.sha256(json.dumps(records, separators=(",", ":")).encode()).hexdigest()

points_only = True
if len(sys.argv) != len(EDITION["sources"]) + 1:
    raise SystemExit("Supply the Overpass JSON files in README order")
inputs = [json.loads(Path(path).read_bytes()) for path in sys.argv[1:]]
for data, source in zip(inputs, EDITION["sources"], strict=True):
    if source_fingerprint(data, points_only=points_only) != source["features_sha256"]:
        raise SystemExit("Source fingerprint differs from the recorded edition")
result = point_features(inputs[0]['elements'], EDITION['parameters'])
raw = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
if hashlib.sha256(raw).hexdigest() != EDITION["data_sha256"]:
    raise SystemExit("Reproduced output differs from the production data")
sys.stdout.buffer.write(raw)
