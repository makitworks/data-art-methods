# in-point — OpenStreetMap data and method

Download [the complete processed dataset](data.json.gz) as gzip-compressed JSON. The dataset is available free of charge under the [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright).

Use `gzip -dc data.json.gz > data.json` to unpack it. The uncompressed SHA-256 is `data_sha256` in `edition.json`. Rows contain east and north in metres and the contributing OSM IDs.

For independent replay, the dated Overpass queries identify the original inputs. Save the responses under the filenames below and run Python 3. The script checks the source features and the output SHA-256. The downloadable dataset remains available without an Overpass request.

```sh
python3 reproduce.py osm-data.json > reproduced.json
```
