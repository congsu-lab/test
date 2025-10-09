# ==========================================
# 💹 PHÂN TÍCH PHƯƠNG ÁN KINH DOANH - AGRIBANK
# Phiên bản 2.0: có biểu đồ & tải Excel
# ==========================================

import streamlit as st
import pandas as pd
import io
import tempfile
import fitz  # PyMuPDF
from docx import Document
from google import genai
from google.genai.errors import APIError
import matplotlib.pyplot as plt

# ---------- CẤU HÌNH TRANG ----------
st.set_page_config(page_title="Phân tích tài chính - Agribank", layout="wide")

st.markdown("""
<style>
body {background-color: #fff0f0;}
h1, h2, h3 {color: #9C0A0A;}
.stButton>button {background-color: #9C0A0A; color: white; border-radius: 8px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.image("https://upload.wikimedia.org/wikipedia/commons/2/25/Agribank_logo.svg", width=160)
st.title("💹 ỨNG DỤNG PHÂN TÍCH PHƯƠNG ÁN KINH DOANH - AGRIBANK")
st.caption("Tự động đọc dữ liệu, tính toán chỉ số tài chính & phân tích bằng AI (Gemini)")

# ---------- NHẬP API ----------
api_key = st.text_input("🔑 Nhập API Key Gemini:", type="password")
if not api_key:
    st.warning("Vui lòng nhập API Key trước khi tiếp tục.")
    st.stop()

client = genai.Client(api_key=api_key)

# ---------- UPLOAD ----------
uploaded_file = st.file_uploader("📎 Tải lên báo cáo tài chính (.xlsx, .csv, .pdf, .docx)", type=["xlsx", "csv", "pdf", "docx"])

if uploaded_file:
    if uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".pdf"):
        text = ""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded_file.read())
            doc = fitz.open(tmp.name)
            for page in doc:
                text += page.get_text()
        st.text_area("📄 Nội dung PDF:", text[:1000] + "...")
        df = None
    elif uploaded_file.name.endswith(".docx"):
        document = Document(uploaded_file)
        text = "\n".join([p.text for p in document.paragraphs])
        st.text_area("📄 Nội dung Word:", text[:1000] + "...")
        df = None

    if df is not None:
        st.subheader("📊 Dữ liệu đầu vào")
        st.dataframe(df)

        # ---------- TÍNH TOÁN ----------
        if "Năm trước" in df.columns and "Năm sau" in df.columns:
            df["Tăng trưởng"] = (df["Năm sau"] - df["Năm trước"]) / df["Năm trước"]

            try:
                total_asset = df.loc[df["Chỉ tiêu"] == "Tổng tài sản", "Năm sau"].values[0]
                total_liab = df.loc[df["Chỉ tiêu"] == "Tổng nguồn vốn", "Năm sau"].values[0]
            except:
                total_asset = total_liab = 1

            df["Tỷ trọng tài sản"] = df["Năm sau"] / total_asset
            df["Tỷ trọng nguồn vốn"] = df["Năm sau"] / total_liab

            try:
                current_asset = df.loc[df["Chỉ tiêu"] == "Tài sản ngắn hạn", "Năm sau"].values[0]
                short_debt = df.loc[df["Chỉ tiêu"] == "Nợ ngắn hạn", "Năm sau"].values[0]
                thanh_toan = current_asset / short_debt if short_debt != 0 else None
            except:
                thanh_toan = None
            df["Chỉ số thanh toán"] = thanh_toan

            st.subheader("📈 Kết quả tính toán")
            st.dataframe(df)

            # ---------- BIỂU ĐỒ ----------
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📊 Biểu đồ tăng trưởng")
                fig, ax = plt.subplots()
                ax.bar(df["Chỉ tiêu"], df["Tăng trưởng"], color="#9C0A0A")
                plt.xticks(rotation=45, ha="right")
                st.pyplot(fig)

            with col2:
                st.markdown("#### 🥧 Biểu đồ tỷ trọng tài sản")
                asset_data = df.set_index("Chỉ tiêu")["Tỷ trọng tài sản"].dropna()
                fig2, ax2 = plt.subplots()
                ax2.pie(asset_data, labels=asset_data.index, autopct="%1.1f%%", startangle=90)
                st.pyplot(fig2)

            # ---------- XUẤT EXCEL ----------
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Phân tích tài chính")
            st.download_button(
                label="📥 Tải kết quả Excel",
                data=output.getvalue(),
                file_name="ket_qua_phan_tich_taichinh.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # ---------- GỌI GEMINI ----------
            if st.button("🤖 Phân tích bằng AI (Gemini)"):
                prompt = f"""
                Hãy phân tích bảng dữ liệu báo cáo tài chính dưới đây:
                {df.to_markdown()}
                Tính toán và nhận xét:
                1. Xu hướng tăng trưởng, điểm nổi bật.
                2. Điểm mạnh - điểm yếu tài chính.
                3. Gợi ý cải thiện năng lực tài chính.
                """
                with st.spinner("🧠 AI đang phân tích..."):
                    try:
                        response = client.models.generate_content(
                            model="gemini-1.5-flash",
                            contents=prompt
                        )
                        st.success("✅ Phân tích hoàn tất!")
                        st.markdown("### 📘 Kết quả phân tích AI")
                        st.write(response.text)
                    except APIError as e:
                        st.error(f"Lỗi khi gọi API Gemini: {e}")
        else:
            st.warning("⚠️ File cần có cột 'Chỉ tiêu', 'Năm trước', 'Năm sau'.")
