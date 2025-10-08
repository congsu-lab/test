import streamlit as st
import pandas as pd
import google.generativeai as genai
from google.generativeai import types

# ==============================
# 🎨 Cấu hình Giao diện
# ==============================
st.set_page_config(
    page_title="Phân Tích Báo Cáo Tài Chính - Agribank",
    layout="wide"
)

# CSS nền màu đỏ bordeaux + logo + style
st.markdown("""
    <style>
    body {
        background-color: #8B0000; /* Đỏ bordeaux Agribank */
        color: white;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #8B0000;
        color: white;
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    [data-testid="stSidebar"] {
        background-color: #A40000;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        background-color: #A40000;
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #B22222;
        color: #fff;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================
# 🏦 Logo & Tiêu đề
# ==============================
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Agribank_logo.png", width=110)
with col_title:
    st.title("Ngân hàng Nông nghiệp và Phát triển Nông thôn Việt Nam (Agribank)")
    st.markdown("### Ứng dụng Phân Tích Báo Cáo Tài Chính 📊")

# ==============================
# ⚙️ Hàm xử lý dữ liệu
# ==============================
@st.cache_data
def process_financial_data(df):
    numeric_cols = ['Năm trước', 'Năm sau']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['Tốc độ tăng trưởng (%)'] = (
        (df['Năm sau'] - df['Năm trước']) / df['Năm trước'].replace(0, 1e-9)
    ) * 100

    tong_tai_san_row = df[df['Chỉ tiêu'].str.contains('TỔNG CỘNG TÀI SẢN', case=False, na=False)]
    if tong_tai_san_row.empty:
        raise ValueError("Không tìm thấy chỉ tiêu 'TỔNG CỘNG TÀI SẢN'.")

    tong_tai_san_N_1 = tong_tai_san_row['Năm trước'].iloc[0]
    tong_tai_san_N = tong_tai_san_row['Năm sau'].iloc[0]
    divisor_N_1 = tong_tai_san_N_1 if tong_tai_san_N_1 != 0 else 1e-9
    divisor_N = tong_tai_san_N if tong_tai_san_N != 0 else 1e-9

    df['Tỷ trọng Năm trước (%)'] = (df['Năm trước'] / divisor_N_1) * 100
    df['Tỷ trọng Năm sau (%)'] = (df['Năm sau'] / divisor_N) * 100

    return df

# ==============================
# 📁 Upload file
# ==============================
uploaded_file = st.file_uploader(
    "📂 Tải file Excel Báo cáo Tài chính (Chỉ tiêu | Năm trước | Năm sau)",
    type=['xlsx', 'xls']
)

if uploaded_file is not None:
    try:
        df_raw = pd.read_excel(uploaded_file)
        df_raw.columns = ['Chỉ tiêu', 'Năm trước', 'Năm sau']
        df_processed = process_financial_data(df_raw.copy())

        st.subheader("2️⃣ Phân tích Tăng trưởng & Tỷ trọng Cơ cấu Tài sản")
        st.dataframe(
            df_processed.style.format({
                'Năm trước': '{:,.0f}',
                'Năm sau': '{:,.0f}',
                'Tốc độ tăng trưởng (%)': '{:.2f}%',
                'Tỷ trọng Năm trước (%)': '{:.2f}%',
                'Tỷ trọng Năm sau (%)': '{:.2f}%'
            }),
            use_container_width=True
        )

        # ---- Chỉ số tài chính ----
        st.subheader("3️⃣ Chỉ số Thanh toán Hiện hành")
        try:
            tsnh_n = df_processed[df_processed['Chỉ tiêu'].str.contains('TÀI SẢN NGẮN HẠN', case=False, na=False)]['Năm sau'].iloc[0]
            tsnh_n_1 = df_processed[df_processed['Chỉ tiêu'].str.contains('TÀI SẢN NGẮN HẠN', case=False, na=False)]['Năm trước'].iloc[0]
            no_ngan_han_N = df_processed[df_processed['Chỉ tiêu'].str.contains('NỢ NGẮN HẠN', case=False, na=False)]['Năm sau'].iloc[0]
            no_ngan_han_N_1 = df_processed[df_processed['Chỉ tiêu'].str.contains('NỢ NGẮN HẠN', case=False, na=False)]['Năm trước'].iloc[0]

            thanh_toan_hien_hanh_N = tsnh_n / no_ngan_han_N
            thanh_toan_hien_hanh_N_1 = tsnh_n_1 / no_ngan_han_N_1

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Thanh toán Hiện hành (Năm trước)", f"{thanh_toan_hien_hanh_N_1:.2f} lần")
            with col2:
                st.metric("Thanh toán Hiện hành (Năm sau)", f"{thanh_toan_hien_hanh_N:.2f} lần",
                          delta=f"{thanh_toan_hien_hanh_N - thanh_toan_hien_hanh_N_1:.2f}")
        except IndexError:
            st.warning("Thiếu chỉ tiêu 'TÀI SẢN NGẮN HẠN' hoặc 'NỢ NGẮN HẠN'.")

        # ---- Nhận xét AI ----
        st.subheader("4️⃣ Nhận xét từ AI Gemini")
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("⚠️ Chưa cấu hình GEMINI_API_KEY trong secrets.")
        else:
            genai.configure(api_key=api_key)
            if st.button("✨ Phân tích bằng Gemini"):
                with st.spinner("Đang phân tích dữ liệu..."):
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    prompt = f"""
                    Bạn là chuyên gia tài chính. Hãy nhận xét ngắn gọn (3-4 đoạn) về tình hình tài chính dựa trên:
                    {df_processed.to_markdown(index=False)}
                    """
                    response = model.generate_content(prompt)
                    st.info(response.text)

    except Exception as e:
        st.error(f"Lỗi xử lý file: {e}")
else:
    st.info("⬆️ Vui lòng tải file Excel để bắt đầu phân tích.")

# ==============================
# 💬 Chat Box với Gemini
# ==============================
st.markdown("---")
st.header("💬 Trò chuyện với Gemini")

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ Chưa cấu hình GEMINI_API_KEY trong secrets.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    if "chat_session" not in st.session_state:
        st.session_state.chat_session = model.start_chat(history=[])

    user_input = st.chat_input("Hỏi Gemini về tài chính, kế toán hoặc phân tích dữ liệu...")

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        try:
            response = st.session_state.chat_session.send_message(user_input)
            reply = response.text
        except Exception as e:
            reply = f"⚠️ Lỗi khi gọi Gemini: {e}"

        with st.chat_message("assistant"):
            st.markdown(reply)
