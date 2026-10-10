import json

import boto3

BUCKET = "chhaya-delhi"
REQUIRED = ["h3", "ndvi", "population", "built_frac", "dust_idx", "school_count", "ward", "priority"]

s3 = boto3.client("s3")


def read(key):
    return s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()


raw = read("features/cells.geojson")
print("bytes:", len(raw))

if b"NaN" in raw:
    print("PROBLEM: file contains NaN, browsers cannot parse this JSON")

features = json.loads(raw)["features"]
print("cells:", len(features))

found = set()
missing_in_some = set()
for f in features:
    props = f["properties"]
    found.update(props.keys())
    for key in REQUIRED:
        if key not in props:
            missing_in_some.add(key)

print("keys in data:", sorted(found))
print("missing from at least one cell:", sorted(missing_in_some) or "none")
print("extra keys not in contract:", sorted(found - set(REQUIRED)) or "none")
print("pipeline_status.json:", read("features/pipeline_status.json").decode())