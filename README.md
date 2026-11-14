# 📸 Keeperly Photos

A local-first, privacy-focused Python and Streamlit application designed to clean up photo archives, Google Takeout exports, or local directories to reclaim storage space. It uses local computer vision heuristics and perceptual hashing with **zero external paid API costs**.

## Features
- **Duplicate & Burst Detection:** Uses perceptual hashing (`imagehash`) to cluster near-identical photos and burst shots.
- **Blur Purge:** Evaluates Laplacian variance to isolate out-of-focus or accidental snapshot photos.
- **Screenshot & Document Isolation:** Checks EXIF metadata, mobile aspect ratios, and OCR text-density to separate receipts and screenshots.
- **Interactive Dashboard:** Inspect thumbnails side-by-side, filter by category, and execute safe moves to a staging trash folder (`_review_trash/`).
- **Auditable Safety:** Generates a `deletion_manifest.json` log for every file moved.

---

## Installation & Setup

1. **Clone or initialize your repository locally:**
   ```bash
   git init
   git branch -M main