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
# 🎨 CSS giao diện Agribank
# ===============================
st.markdown("""
<style>
/* Nền tổng thể */
[data-testid="stAppViewContainer"] {
    background-color: #ffffff;
}

/* Header đỏ boóc-đô */
header {
    background-color: #8B0000 !important;
}

/* Logo + tiêu đề */
.agri-header {
    background-color: #8B0000;
    padding: 1.5rem 0;
    text-align: center;
    border-radius: 0 0 20px 20px;
    color: white;
}
.agri-header img {
    width: 120px;
    margin-bottom: 0.5rem;
}
.agri-header h1 {
    font-size: 1.8rem;
    margin-bottom: 0.3rem;
}
.agri-header h3 {
    font-size: 1.1rem;
    font-weight: 400;
    color: #f8f8f8;
}

/* Thẻ nội dung chính */
.main-box {
    background-color: #ffffff;
    border-radius: 15px;
    padding: 25px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-top: 20px;
}

/* Nút Agribank */
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
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# 🏦 Header Agribank
# ===============================
st.markdown("""
<div class="agri-header">
    <img src="https://upload.wikimedia.org/wikipedia/commons/1/19/Agribank_logo.png">
    <h1>Ngân hàng Nông nghiệp và Phát triển Nông thôn Việt Nam (Agribank)</h1>
    <h3>Ứng dụng Phân Tích Báo Cáo Tài Chính 📊</h3>
</div>
""", unsafe_allow_html=True)

# ===============================
# 📂 Tải file & xử lý dữ liệu
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

with st.container():
    st.markdown('<div class="main-box">', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("📂 Tải file Excel Báo cáo Tài chính (Chỉ tiêu | Năm trước | Năm sau)",
                                     type=['xlsx', 'xls'])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            df.columns = ['Chỉ tiêu', 'Năm trước', 'Năm sau']
            dfp = process_financial_data(df)

            st.subheader("📈 Bảng Phân tích")
            st.dataframe(dfp.style.format({
                'Năm trước': '{:,.0f}', 'Năm sau': '{:,.0f}',
                'Tốc độ tăng trưởng (%)': '{:.2f}%',
                'Tỷ trọng Năm trước (%)': '{:.2f}%', 'Tỷ trọng Năm sau (%)': '{:.2f}%'
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
