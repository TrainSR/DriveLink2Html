import streamlit as st
import re

st.title("Google Drive Image Link Formatter")

# Input: Google Drive image link
drive_link = st.text_input("Nhập link ảnh từ Google Drive:")

def extract_file_id(link):
    """
    Trích xuất file_id từ URL Google Drive
    """
    patterns = [
        r'drive\.google\.com\/file\/d\/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'drive\.google\.com\/open\?id=([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    return None

if drive_link:
    file_id = extract_file_id(drive_link)
    if file_id:
        thumbnail_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=s800"
        html_code = f'<img src="{thumbnail_url}" alt="Preview">'
        markdown_code = f'![Preview]({thumbnail_url})'

        st.markdown("### ✅ Ảnh xem trước:")
        st.markdown(f'<img src="{thumbnail_url}" alt="Preview">', unsafe_allow_html=True)


        st.markdown("### 📋 HTML:")
        st.code(html_code, language="html")

        st.markdown("### 📋 Markdown:")
        st.code(markdown_code, language="markdown")
    else:
        st.error("❌ Không thể trích xuất file_id từ link đã nhập.")
