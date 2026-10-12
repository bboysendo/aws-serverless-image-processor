import os
import sys
import tempfile

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "thumbnail_generator"))
from app import resize_image, THUMBNAIL_MAX_SIZE  # noqa: E402


def test_resize_image_shrinks_large_image_within_bounds():
    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, "src.jpg")
        dest_path = os.path.join(tmp, "dest.jpg")

        Image.new("RGB", (1000, 500), color="red").save(src_path, "JPEG")
        resize_image(src_path, dest_path)

        with Image.open(dest_path) as thumb:
            assert thumb.width <= THUMBNAIL_MAX_SIZE[0]
            assert thumb.height <= THUMBNAIL_MAX_SIZE[1]
            assert thumb.format == "JPEG"


def test_resize_image_preserves_aspect_ratio():
    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, "src.jpg")
        dest_path = os.path.join(tmp, "dest.jpg")

        Image.new("RGB", (800, 400), color="blue").save(src_path, "JPEG")
        resize_image(src_path, dest_path)

        with Image.open(dest_path) as thumb:
            assert abs((thumb.width / thumb.height) - 2.0) < 0.05


def test_resize_image_does_not_upscale_small_images():
    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, "src.jpg")
        dest_path = os.path.join(tmp, "dest.jpg")

        Image.new("RGB", (50, 50), color="green").save(src_path, "JPEG")
        resize_image(src_path, dest_path)

        with Image.open(dest_path) as thumb:
            assert thumb.width == 50
            assert thumb.height == 50
