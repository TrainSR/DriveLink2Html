import streamlit as st
from yt_dlp import YoutubeDL
import tempfile
import os
import re
from PIL import Image
import requests
from io import BytesIO
from streamlit_cropper import st_cropper
import numpy as np
import drive_module.drive_ops as drive_ops


if "file_name_om" not in st.session_state:
    st.session_state.file_name_om = ""

# Hàm để reset input sau khi tải
def reset_filename():
    st.session_state.file_name_om = ""

    
def get_largest_crop_fit(img_width, img_height, aspect_ratio):
    """
    Tìm khung crop lớn nhất với tỉ lệ aspect_ratio (w/h),
    sao cho không vượt ra ngoài ảnh và ít nhất 1 chiều đạt max (rộng hoặc cao).
    Trả về: crop_width, crop_height, (min_cx, max_cx, min_cy, max_cy)
    """
    a, b = aspect_ratio
    crop_width_by_height = int(img_height * a / b)

    if crop_width_by_height <= img_width:
        # Chiều cao chiếm tối đa
        crop_width = crop_width_by_height
        crop_height = img_height
    else:
        # Chiều rộng chiếm tối đa
        crop_width = img_width
        crop_height = int(img_width * b / a)

    # Giới hạn tâm khung để khung không vượt biên
    min_cx = crop_width // 2
    max_cx = img_width - crop_width // 2
    min_cy = crop_height // 2
    max_cy = img_height - crop_height // 2

    center_range = (min_cx, max_cx, min_cy, max_cy)

    return crop_width, crop_height, center_range

def get_crop_center(rect):
    left = rect[0]
    top = rect[1]
    width = rect[2]
    height = rect[3]

    center_x = left + width / 2
    center_y = top + height / 2

    return center_x, center_y

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

import streamlit as st

# Function extract_file_id assumed defined
# Function drive_ops.select_working_folder assumed defined
# Function drive_ops.get_images_in_folder(folder_id) should return list of (name, file_id) tuples

# App sidebar: Select folder and show images
with st.sidebar:
    folder_id = drive_ops.select_working_folder()

    selected_image_id = None
    image_list = []
    if folder_id:
        image_list = drive_ops.get_images_in_folder(folder_id)  # List of tuples: (name, file_id)

        if image_list:
            st.markdown("### 📂 Ảnh trong thư mục:")
            image_names = [f"{name} ({file_id})" for name, file_id in image_list]
            selected_name = st.selectbox("Chọn ảnh để chèn vào tab1:", image_names)

            # Extract selected file_id
            selected_index = image_names.index(selected_name)
            selected_image_id = image_list[selected_index][1]

            # Share selected image ID through session state
            st.session_state["selected_file_id"] = selected_image_id

# Tabs
tab1, tab2, tab3 = st.tabs(["Drive Link", "Crop Image", "Download YouTube Video"])
with tab1:
    st.title("Google Drive Image Link Formatter")

    # Load selected file_id from sidebar (if any)
    default_link = ""
    if "selected_file_id" in st.session_state:
        fid = st.session_state["selected_file_id"]
        default_link = f"https://drive.google.com/file/d/{fid}/view"

    drive_link = st.text_input("Nhập link ảnh từ Google Drive:", value=default_link)

    if drive_link:
        file_id = extract_file_id(drive_link)
        if file_id:
            thumbnail_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=s800"
            html_code = f"<img src='{thumbnail_url}' alt='Preview'>"
            markdown_code = f'![Preview]({thumbnail_url})'

            st.markdown("### ✅ Ảnh xem trước:")
            st.markdown(html_code, unsafe_allow_html=True)

            st.markdown("### URL Ảnh:")
            st.code(thumbnail_url)
            st.markdown("### 📋 HTML:")
            st.code(html_code, language="html")
            st.markdown("### 📋 Markdown:")
            st.code(markdown_code, language="markdown")
        else:
            st.error("❌ Không thể trích xuất file_id từ link đã nhập.")




with tab2:
    demo_url = st.text_input("Dán URL ảnh vào đây:", value="")

    return_type = st.checkbox("Chế Độ Auto?", value=True)
    ratio_choice = st.selectbox("Chọn tỉ lệ crop:", ["3:2", "1:1", "4:3", "16:9", "3:4", "9:16"])
    aspect_dict = {
        "1:1": (1, 1),
        "16:9": (16, 9),
        "4:3": (4, 3),
        "3:4": (3, 4),
        "2:3": (2, 3),
        "9:16": (9, 16),
        "3:2":(3,2)
    }
    aspect_ratio = aspect_dict[ratio_choice]

    if demo_url:
        response = requests.get(demo_url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            
        img_width, img_height = img.size
        raw_image = np.asarray(img).astype('uint8')
        rect = st_cropper(
            img,
            realtime_update=True,
            box_color="#0000FF",
            aspect_ratio=aspect_ratio,
            return_type="box",
            stroke_width=1
        )
        left, top, width, height = tuple(map(int, rect.values()))

        if return_type:
            crop_width, crop_height, center_range = get_largest_crop_fit(img_width, img_height, aspect_ratio)
            center = get_crop_center(tuple(map(int, rect.values())))

            clamped_x = max(center_range[0], min(center[0], center_range[1]))
            clamped_y = max(center_range[2], min(center[1], center_range[3]))
            crop_left = int(clamped_x - crop_width / 2)
            crop_top = int(clamped_y - crop_height / 2)

            # Cắt ảnh theo đúng rect đã chọn
            cropped_np = raw_image[crop_top:crop_top + crop_height, crop_left:crop_left + crop_width]
        else:
            cropped_np = raw_image[top:top + height, left:left + width]

        cropped_img = Image.fromarray(cropped_np)
        st.write("Preview")
        st.image(cropped_img)
        # Save the cropped image to a BytesIO buffer in PNG format
        buf = BytesIO()
        cropped_img.save(buf, format="PNG")
        buf.seek(0)

        st.text_input("Tên ảnh khi tải xuống:", key="file_name_om")

        if st.session_state.file_name_om:
            file_name = f"{st.session_state.file_name_om}.png"
            st.download_button(
                label="Download Cropped Image",
                data=buf,
                file_name=file_name,
                mime="image/png",
                on_click=reset_filename  # Reset sau khi tải
            )
with tab3: 
    st.title("YouTube Downloader bằng yt-dlp")

    url = st.text_input("Nhập link YouTube:")

    if not url.strip():
        st.error("⚠️ Vui lòng nhập link.")
    else:
        with st.spinner("Đang tải video..."):
            # Tạo file tạm để chứa video
            temp_dir = tempfile.mkdtemp()
            ydl_opts = {
                "format": "bestvideo+bestaudio/best",
                "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
                "noplaylist": True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            # Đọc file và cho phép tải về
            with open(filename, "rb") as f:
                st.download_button(
                    label="⬇️ Tải video về máy",
                    data=f,
                    file_name=os.path.basename(filename),
                    mime="video/mp4"
                )
