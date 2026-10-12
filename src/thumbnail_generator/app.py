"""
Lambda handler: triggered by S3 ObjectCreated events under uploads/, creates
a resized JPEG thumbnail and writes it to thumbnails/ in the same bucket.

The resize logic is split into resize_image() so it can be unit tested
without any AWS dependency (see tests/test_app.py).
"""
import os
from urllib.parse import unquote_plus

import boto3
from PIL import Image

s3 = boto3.client("s3")

THUMBNAIL_MAX_SIZE = (200, 200)
SOURCE_PREFIX = "uploads/"
DEST_PREFIX = "thumbnails/"


def resize_image(local_src: str, local_dest: str, max_size: tuple[int, int] = THUMBNAIL_MAX_SIZE) -> None:
    """Shrinks local_src to fit within max_size (preserving aspect ratio)
    and writes it to local_dest as a JPEG."""
    with Image.open(local_src) as img:
        img.thumbnail(max_size)
        img.convert("RGB").save(local_dest, "JPEG", quality=85)


def handler(event, context):
    processed = []

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])

        if not key.startswith(SOURCE_PREFIX):
            print(f"Skipping {key}: not under {SOURCE_PREFIX}")
            continue

        filename = key[len(SOURCE_PREFIX):]
        if not filename:
            print(f"Skipping {key}: no filename after prefix (looks like a folder marker)")
            continue

        dest_key = f"{DEST_PREFIX}{filename.rsplit('.', 1)[0]}.jpg"
        local_src = f"/tmp/{os.path.basename(key)}"
        local_dest = f"/tmp/thumb-{os.path.basename(dest_key)}"

        try:
            s3.download_file(bucket, key, local_src)
            resize_image(local_src, local_dest)
            s3.upload_file(local_dest, bucket, dest_key, ExtraArgs={"ContentType": "image/jpeg"})
            print(f"Created thumbnail: s3://{bucket}/{dest_key}")
            processed.append(dest_key)
        finally:
            for path in (local_src, local_dest):
                if os.path.exists(path):
                    os.remove(path)

    return {"processed": processed}
