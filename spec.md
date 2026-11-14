# Keeperly Photos Specification (v0.2)

## Directory Structure
/photo_janitor_mvp
│
├── requirements.txt
├── analyzer.py          # Core processing engine (Duplicates, Bursts, Blur, Documents, EXIF)
├── app.py               # Streamlit review dashboard (to be built in v0.3)
├── test_app.py          # Pytest suite (to be built in v0.4)
└── README.md            # Setup & GitHub push guide

## Data Contracts (`analyzer.py` output -> `analysis_report.json`)
{
  "scanned_count": 150,
  "categories": {
    "duplicates_and_bursts": [{"path": "...", "reason": "Exact dHash duplicate of img_001.jpg", "cluster_id": "c1"}],
    "blurry": [{"path": "...", "laplacian_score": 12.4}],
    "screenshots": [{"path": "...", "reason": "Zero EXIF + Standard mobile aspect ratio"}],
    "documents_and_receipts": [{"path": "...", "matched_keywords": ["total", "iva", "fecha"]}],
    "scenery_without_people": [{"path": "...", "reason": "No faces detected + natural color ratio"}]
  }
}