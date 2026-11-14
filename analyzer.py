import os
import json
import argparse
from datetime import datetime
from PIL import Image, ExifTags
import cv2
import numpy as np
import imagehash

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

def get_exif_data(image_path):
    """Extracts EXIF metadata to distinguish real camera shots from screenshots."""
    try:
        image = Image.open(image_path)
        exif = image._getexif()
        if exif:
            return {ExifTags.TAGS.get(k, k): v for k, v in exif.items() if k in ExifTags.TAGS}
    except Exception:
        pass
    return {}

def calculate_blur_score(image_path):
    """Calculates Laplacian variance. Lower score means blurrier image."""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return 0.0
    return cv2.Laplacian(image, cv2.CV_64F).var()

def is_screenshot_or_document(image_path):
    """Checks dimensions, EXIF absence, and text density to flag screenshots/receipts."""
    try:
        img = Image.open(image_path)
        width, height = img.size
        exif = get_exif_data(image_path)
        
        # Common mobile screenshot resolutions / ratios
        aspect_ratio = height / width if width > 0 else 1
        is_mobile_ratio = aspect_ratio > 1.7 or aspect_ratio < 0.6
        has_no_exif = len(exif) == 0
        
        # Basic text check if tesseract is available and executable
        if HAS_TESSERACT and has_no_exif:
            try:
                text = pytesseract.image_to_string(img).lower()
                keywords = ["total", "subtotal", "invoice", "receipt", "factura", "ticket", "date", "fecha", "rfc", "iva"]
                matches = sum(1 for kw in keywords if kw in text)
                if matches >= 2:
                    return "document_or_receipt"
            except Exception:
                pass  # Tesseract binary not installed on system path

        if has_no_exif and is_mobile_ratio:
            return "screenshot"
            
    except Exception:
        pass
    return None

def analyze_directory(target_dir):
    supported_extensions = ('.jpg', '.jpeg', '.png', '.webp')
    image_paths = []
    
    for root, _, files in os.walk(target_dir):
        if "_review_trash" in root:
            continue
        for file in files:
            if file.lower().endswith(supported_extensions):
                image_paths.append(os.path.join(root, file))

    report = {
        "scanned_count": len(image_paths),
        "timestamp": datetime.now().isoformat(),
        "categories": {
            "duplicates_and_bursts": [],
            "blurry": [],
            "screenshots": [],
            "documents_and_receipts": [],
            "scenery_or_objects": []
        }
    }

    hash_map = {}
    file_timestamps = []

    for path in image_paths:
        # 1. Blur Check
        blur_score = calculate_blur_score(path)
        if blur_score < 45.0:  # Threshold for noticeable blur
            report["categories"]["blurry"].append({"path": path, "laplacian_score": round(blur_score, 2)})
            continue

        # 2. Document / Screenshot Check
        doc_type = is_screenshot_or_document(path)
        if doc_type == "document_or_receipt":
            report["categories"]["documents_and_receipts"].append({"path": path, "reason": "High text density / receipt keywords"})
            continue
        elif doc_type == "screenshot":
            report["categories"]["screenshots"].append({"path": path, "reason": "No EXIF + mobile aspect ratio"})
            continue

        # 3. Perceptual Hashing for Duplicates
        try:
            pil_img = Image.open(path)
            h = imagehash.dhash(pil_img)
            matched_cluster = None
            for existing_hash, ref_path in hash_map.items():
                if h - existing_hash <= 5:  # Hamming distance threshold
                    matched_cluster = ref_path
                    break
            
            if matched_cluster:
                report["categories"]["duplicates_and_bursts"].append({
                    "path": path, 
                    "reason": f"Visual duplicate of {os.path.basename(matched_cluster)}"
                })
                continue
            else:
                hash_map[h] = path
        except Exception:
            pass

        # 4. Default: Scenery / Object / General Photo
        report["categories"]["scenery_or_objects"].append({"path": path, "reason": "Passed primary cleanliness filters"})

    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Keeperly Photos Core Analyzer")
    parser.add_argument("directory", type=str, help="Path to photo directory to analyze")
    parser.add_argument("--output", type=str, default="analysis_report.json", help="Output JSON report path")
    
    args = parser.parse_args()
    print(f"Scanning directory with Keeperly Photos: {args.directory} ...")
    results = analyze_directory(args.directory)
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"Scan complete! Results saved to {args.output}")
    for cat, items in results["categories"].items():
        print(f" - {cat}: {len(items)} items flagged")