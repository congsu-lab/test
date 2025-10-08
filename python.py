import streamlit as st
import pandas as pd
import google.generativeai as genai

# ===============================
# ⚙️ Cấu hình trang
# ===============================
st.set_page_config(
    page_title="Phân Tích Báo Cáo Tài Chính - Agribank",
    layout="wide"
)

# ===============================
# 🎨 CSS GIAO DIỆN AGRIBANK
# ===============================
st.markdown("""
<style>
/* Nền chính */
[data-testid="stAppViewContainer"] {
    background-color: #ffffff;
}

/* Header */
.agri-header {
    background-color: #8B0000;
    padding: 1.8rem 0 2.2rem 0;
    text-align: center;
    border-radius: 0 0 25px 25px;
    color: white;
    box-shadow: 0 3px 10px rgba(0,0,0,0.25);
}
.agri-header img {
    width: 130px;
    margin-bottom: 0.8rem;
}
.agri-header h1 {
    font-size: 1.9rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
}
.agri-header h3 {
    font-size: 1.1rem;
    font-weight: 400;
    color: #f5f5f5;
    margin-bottom: 0.3rem;
}
.agri-header h4 {
    color: #FFD700;
    font-size: 1.05rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* Khối nội dung chính */
.main-box {
    background-color: #ffffff;
    border-radius: 15px;
    padding: 25px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.1);
    margin-top: 25px;
}

/* Nút */
.stButton>button {
    background-color: #8B0000 !important;
    color: white !important;
    font-weight: bold;
    border-radius: 8px;
}
.stButton>button:hover {
    background-color: #A52A2A !important;
}

/* Chat box */
[data-testid="stChatInput"] {
    background-color: #f7f7f7 !important;
    border-radius: 10px;
}

/* Footer */
.agri-footer {
    background-color: #8B0000;
    color: white;
    text-align: center;
    padding: 1.2rem;
    border-radius: 25px 25px 0 0;
    margin-top: 40px;
    font-size: 0.95rem;
}
.agri-footer img {
    width: 70px;
    vertical-align: middle;
    margin-right: 10px;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# 🏦 HEADER AGRIBANK (LOGO FIX)
# ===============================
# Dùng logo Agribank dạng base64 (hiển thị ổn định trên mọi host)
logo_url = "https://raw.githubusercontent.com/dataprofessor/data/master/agribank_logo.png"
# (bạn có thể thay bằng logo nội bộ khác nếu muốn)

st.markdown(f"""
<div class="agri-header">
    <img src="{logo_url}" alt="Agribank Logo">
    <h1>Ngân hàng Nông nghiệp và Phát triển Nông thôn Việt Nam (Agribank)</h1>
    <h3>Ứng dụng Phân Tích Báo Cáo Tài Chính 📊</h3>
    <h4>“Mang phồn thịnh đến khách hàng”</h4>
</div>
""", unsafe_allow_html=True)

# ===============================
# 📂 Upload & xử lý dữ liệu
# ===============================
@st.cache_data
def process_financial_data(df):
    df['Năm trước'] = pd.to_numeric(df['Năm trước'], errors='coerce').fillna(0)
    df['Năm sau'] = pd.to_numeric(df['Năm sau'], errors='coerce').fillna(0)
    df['Tốc độ tăng trưởng (%)'] = ((df['Năm sau'] - df['Năm trước']) / df['Năm trước'].replace(0, 1e-9)) * 100
    tong_ts = df[df['Chỉ tiêu'].str.contains('TỔNG CỘNG TÀI SẢN', case=False, na=False)]
    if tong_ts.empty: raise ValueError("Thiếu chỉ tiêu 'TỔNG CỘNG TÀI SẢN'")
    ts_n1, ts_n = tong_ts.iloc[0]['Năm trước'], tong_ts.iloc[0]['Năm sau']
    ts_n1, ts_n = ts_n1 or 1e-9, ts_n or 1e-9
    df['Tỷ trọng Năm trước (%)'] = (df['Năm trước']/ts_n1)*100
    df['Tỷ trọng Năm sau (%)'] = (df['Năm sau']/ts_n)*100
    return df

st.markdown('<div class="main-box">', unsafe_allow_html=True)
st.subheader("📁 Tải và Phân tích Báo cáo")
uploaded_file = st.file_uploader("Tải file Excel (Chỉ tiêu | Năm trước | Năm sau)", type=['xlsx', 'xls'])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = ['Chỉ tiêu', 'Năm trước', 'Năm sau']
        dfp = process_financial_data(df)

        st.subheader("📊 Kết quả phân tích")
        st.dataframe(dfp.style.format({
            'Năm trước': '{:,.0f}', 'Năm sau': '{:,.0f}',
            'Tốc độ tăng trưởng (%)': '{:.2f}%',
            'Tỷ trọng Năm trước (%)': '{:.2f}%',
            'Tỷ trọng Năm sau (%)': '{:.2f}%'
        }), use_container_width=True)

    except Exception as e:
        st.error(f"Lỗi xử lý file: {e}")
else:
    st.info("⬆️ Vui lòng tải file Excel để bắt đầu phân tích.")
st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# 💬 Chat với Gemini
# ===============================
st.markdown('<div class="main-box">', unsafe_allow_html=True)
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
st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# 🏁 Footer
# ===============================
st.markdown(f"""
<div class="agri-footer">
    <img src="{logo_url}" alt="Agribank">
    Agribank Chi nhánh Huyện Cư M’gar – Bắc Đắk Lắk<br>
    © 2025 – Phát triển bởi Bộ phận Công nghệ & Phân tích dữ liệu
</div>
""", unsafe_allow_html=True)
