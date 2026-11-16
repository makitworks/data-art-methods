# Railway Network — Nagoya

This is the map geometry used in the Nagoya print edition. Data © OpenStreetMap contributors. The downloadable database is available under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/). See the [OpenStreetMap copyright and attribution page](https://www.openstreetmap.org/copyright).

## Download and verify

Download [geometry.json.gz](geometry.json.gz) (8,179,145 bytes) and [edition.json](edition.json) to a folder named `nagoya`. Place [verify.py](../verify.py) next to that folder. Python 3's standard library is sufficient.

```sh
python3 verify.py nagoya
python3 verify.py nagoya --geometry > nagoya-geometry.json
```

The JSON contains the ordered railway line groups and their styles, station points, coast segments, roads, rivers, water outlines and water polygons. Coordinates are millimetres measured from the top left of the A2 sheet, with x increasing to the right and y increasing down. The verified geometry has 98 source route relations, 4,363 selected ways and 423 station points. [The manifest](edition.json) records all layer counts, processing settings and SHA-256 checksums.

## Source snapshots and method

| Layer | OpenStreetMap snapshot time (UTC) | Historical query | Recorded input elements |
| --- | --- | --- | ---: |
| Railway and coast | `2026-07-28T02:16:18Z` | [network.overpassql](network.overpassql) | 31,132 |
| Road and water context | `2026-09-07T06:49:56Z` | [context.overpassql](context.overpassql) | 365,514 |

The historical queries preserve the saved selectors and add the snapshot date from the archived Overpass response. The downloadable geometry provides the data used in the print even when a historical Overpass server cannot return a full response. It contains the processed geometry and styles used to draw the map. The raw Overpass responses, relation labels, unused tags and poster images are outside this download.

To replay the transformation with matching Overpass responses, install Matplotlib in a Python 3 environment and use [reproduce.py](../reproduce.py) with [map_viewport.py](../map_viewport.py) beside it.

```sh
python3 reproduce.py nagoya/edition.json network.json context.json > nagoya-replayed.json
```

The script checks both input element collections against their recorded fingerprints before projecting, selecting, grouping and clipping the layers in this edition. Osaka retains its original fixed-frame projection. The manifest identifies the projection used for each edition.
