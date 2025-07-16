# components/submission_view.py

import streamlit as st
from PIL import Image
import os

def render_submission_preview(image_path: str, ocr_text: str):
    """
    Renders a preview of the user's submission, showing the uploaded image
    and the corresponding OCR text in a two-column layout.

    Args:
        image_path (str): The file path to the uploaded image.
        ocr_text (str): The text extracted by the OCR service.
    """
    if not os.path.exists(image_path):
        st.error("无法找到上传的图片文件。")
        return

    st.subheader("🔍 您上传的内容")
    col1, col2 = st.columns(2)

    with col1:
        try:
            image = Image.open(image_path)
            st.image(image, caption="上传的图片", use_column_width=True)
        except Exception as e:
            st.error(f"无法加载图片: {e}")

    with col2:
        st.text_area(
            label="识别出的文字：",
            value=ocr_text,
            height=250,
            disabled=True
        )
