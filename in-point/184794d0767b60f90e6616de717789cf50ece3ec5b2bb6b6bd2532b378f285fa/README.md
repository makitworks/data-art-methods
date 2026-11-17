# in-point — OpenStreetMap data method

© OpenStreetMap contributors. The reproduced dataset is available under the [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). See [OpenStreetMap copyright and attribution](https://www.openstreetmap.org/copyright).

Run these historical queries, then use Python 3. The dataset and source checksums are in edition.json.

```sh
curl --fail --show-error --data-urlencode "data@osm-data.overpassql" https://maps.mail.ru/osm/tools/overpass/api/interpreter -o osm-data.json
python3 reproduce.py osm-data.json > reproduced.json
```
