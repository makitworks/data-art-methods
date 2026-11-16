# In Point — TOKYO / Traffic Signals

This edition uses an OpenStreetMap snapshot dated **2026-11-16T05:08:38Z**.

Data © OpenStreetMap contributors. The dataset reproduced using this method is available under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/). See the [OpenStreetMap copyright and attribution page](https://www.openstreetmap.org/copyright).

## Reproduce the data

Run the [dated query](snapshot.overpassql) on an Overpass instance with historical data. The following command was verified with the endpoint shown. The `date` in the query determines the snapshot. The response header may instead report the server’s newer replication timestamp. With Python 3, run the script to produce a CSV of the projected points and contributing OpenStreetMap node IDs.

```sh
curl --fail --show-error --data-urlencode "data@snapshot.overpassql" \
  https://maps.mail.ru/osm/tools/overpass/api/interpreter -o overpass.json
python3 reproduce.py overpass.json > points.csv
```

The script expects 27,450 source nodes and checks the SHA-256 of their IDs and coordinates. All 27,450 IDs and coordinates matched the saved source when checked on 2026-11-16. The expected CSV contains 18,822 data rows. Its SHA-256 is `7abbb8d8fa06ab1c3060aaa2840262eb3f1d1a2dbe4c857fd494e087853bf357`.

The method projects coordinates with a spherical azimuthal equidistant projection centred at 35.6768601° N, 139.7638947° E, using a sphere of radius 6,371,008.8 m. It keeps both axes within ±18,250 m, including the boundaries, then rounds east and north separately to 0.001 m using Python's `round(value, 3)`. Identical coordinate pairs are grouped and their source IDs are retained. No traffic-signal locations were added, moved, or corrected. The point dataset uses no other data source.

## Original acquisition query

The original query used the server's then-current data. The dated query above requests the original response's recorded snapshot time explicitly.

```text
[out:json][timeout:50];(node["highway"="traffic_signals"](35.44461603,139.47799180,35.90910417,140.04979760););out body center;
```
