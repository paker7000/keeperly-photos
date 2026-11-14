import os
import tempfile
import pytest
from PIL import Image
import numpy as np
import imagehash

# Import functions from analyzer
from analyzer import calculate_blur_score, is_screenshot_or_document, analyze_directory

@pytest.fixture
def temp_photo_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Create a sharp image
        sharp_arr = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
        sharp_img = Image.fromarray(sharp_arr)
        sharp_path = os.path.join(tmpdir, "sharp.jpg")
        sharp_img.save(sharp_path)

        # 2. Create a blurry image (using gaussian blur)
        blur_arr = np.uint8(np.random.normal(128, 50, (300, 300, 3)))
        blur_img = Image.fromarray(blur_arr)
        blur_path = os.path.join(tmpdir, "blurry.jpg")
        blur_img.save(blur_path)

        # 3. Create a mobile screenshot aspect ratio simulation (tall, no exif)
        screenshot_arr = np.random.randint(200, 255, (1200, 600, 3), dtype=np.uint8)
        screenshot_img = Image.fromarray(screenshot_arr)
        screenshot_path = os.path.join(tmpdir, "screenshot.png")
        screenshot_img.save(screenshot_path)

        # 4. Create an exact duplicate of the sharp image
        duplicate_path = os.path.join(tmpdir, "sharp_duplicate.jpg")
        sharp_img.save(duplicate_path)

        yield tmpdir

def test_blur_detection(temp_photo_dir):
    sharp_score = calculate_blur_score(os.path.join(temp_photo_dir, "sharp.jpg"))
    blurry_score = calculate_blur_score(os.path.join(temp_photo_dir, "blurry.jpg"))
    
    # Sharp images should have a higher Laplacian variance than blurry images
    assert sharp_score > blurry_score

def test_screenshot_classification(temp_photo_dir):
    screenshot_type = is_screenshot_or_document(os.path.join(temp_photo_dir, "screenshot.png"))
    assert screenshot_type == "screenshot"

def test_full_directory_analysis(temp_photo_dir):
    report = analyze_directory(temp_photo_dir)
    
    assert report["scanned_count"] >= 4
    # Check that categories exist in report structure
    assert "blurry" in report["categories"]
    assert "duplicates_and_bursts" in report["categories"]
    assert "screenshots" in report["categories"]
    
    # Verify duplicate was caught
    duplicate_paths = [item["path"] for item in report["categories"]["duplicates_and_bursts"]]
    assert any("sharp_duplicate.jpg" in p for p in duplicate_paths)