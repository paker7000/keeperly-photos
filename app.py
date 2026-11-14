import streamlit as st
import json
import os
import shutil
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="Keeperly Photos", layout="wide")

st.title("📸 Keeperly Photos Review Dashboard")
st.markdown("Inspect categorized photos, review duplicates or blurry shots, and safely move unwanted files to a staging trash folder.")

REPORT_PATH = "analysis_report.json"

if not os.path.exists(REPORT_PATH):
    st.warning(f"No `{REPORT_PATH}` found. Please run `python analyzer.py <directory_path>` first to generate the report.")
    st.stop()

with open(REPORT_PATH, "r", encoding="utf-8") as f:
    report = json.load(f)

# Sidebar Overview
st.sidebar.header("Library Statistics")
st.sidebar.text(f"Total Scanned: {report.get('scanned_count', 0)}")
st.sidebar.text(f"Scan Time: {report.get('timestamp', 'N/A')[:19]}")

categories = report.get("categories", {})
tabs = st.tabs([
    "Duplicates & Bursts",
    "Blurry Photos",
    "Screenshots",
    "Documents & Receipts",
    "General Scenery"
])

selected_for_trash = []

def render_category_tab(cat_key, tab_name):
    items = categories.get(cat_key, [])
    st.subheader(f"{tab_name} ({len(items)} items flagged)")
    if not items:
        st.info("No items found in this category.")
        return

    cols = st.columns(3)
    for idx, item in enumerate(items):
        path = item.get("path")
        reason = item.get("reason") or item.get("laplacian_score") or ""
        
        with cols[idx % 3]:
            if os.path.exists(path):
                try:
                    img = Image.open(path)
                    st.image(img, use_container_width=True)
                except Exception:
                    st.error("Could not load image thumbnail.")
            else:
                st.warning("File no longer exists on disk.")
            
            st.text(os.path.basename(path))
            st.caption(f"Details: {reason}")
            
            is_selected = st.checkbox("Select for Trash", key=f"chk_{cat_key}_{idx}")
            if is_selected:
                selected_for_trash.append(path)
            st.markdown("---")

with tabs[0]:
    render_category_tab("duplicates_and_bursts", "Duplicates & Bursts")
with tabs[1]:
    render_category_tab("blurry", "Blurry Photos")
with tabs[2]:
    render_category_tab("screenshots", "Screenshots")
with tabs[3]:
    render_category_tab("documents_and_receipts", "Documents & Receipts")
with tabs[4]:
    render_category_tab("scenery_or_objects", "General Scenery")

st.markdown("---")
st.header("Action Center")
st.markdown(f"**Total files currently selected for safe removal:** {len(selected_for_trash)}")

if st.button("Move Selected Files & Export Search List", type="primary"):
    if not selected_for_trash:
        st.warning("Please check at least one file to move.")
    else:
        trash_dir = "_review_trash"
        os.makedirs(trash_dir, exist_ok=True)
        manifest = []
        summary_lines = [
            "==========================================",
            "   KEEPERLY PHOTOS - WEB CLEANUP LIST     ",
            "==========================================",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Files: {len(selected_for_trash)}",
            "------------------------------------------",
            ""
        ]
        
        for path in selected_for_trash:
            if os.path.exists(path):
                filename = os.path.basename(path)
                dest_path = os.path.join(trash_dir, filename)
                
                # Get file modification/capture date approximation
                try:
                    mtime = os.path.getmtime(path)
                    file_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
                except Exception:
                    file_date = "Date Unknown"

                # Prevent filename collision in trash folder
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(trash_dir, f"{base}_{counter}{ext}")
                    counter += 1
                    
                shutil.move(path, dest_path)
                manifest.append({
                    "original_path": path,
                    "trash_path": dest_path,
                    "date": file_date,
                    "moved_at": datetime.now().isoformat()
                })
                
                summary_lines.append(f"• Date: {file_date}  |  Filename: {filename}")

        # Save audit manifest JSON
        with open("deletion_manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # Save clean text search list
        summary_text = "\n".join(summary_lines)
        summary_file_path = "cleanup_search_list.txt"
        with open(summary_file_path, "w", encoding="utf-8") as f:
            f.write(summary_text)

        st.success(f"Successfully moved {len(manifest)} files to `{trash_dir}/` and generated `{summary_file_path}`!")
        
        # Provide direct download button for the text list in the UI
        st.download_button(
            label="📥 Download Web Cleanup Search List (.txt)",
            data=summary_text,
            file_name="cleanup_search_list.txt",
            mime="text/plain"
        )
        st.balloons()