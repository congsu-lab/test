import streamlit as st
import pandas as pd
from google import genai
from google.genai.errors import APIError

# --- Cấu hình Trang Streamlit ---
st.set_page_config(
    page_title="App Phân Tích Báo Cáo Tài Chính",
    layout="wide"
)

st.title("Ứng dụng Phân Tích Báo Cáo Tài Chính 📊")

# --- Hàm tính toán chính ---
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


# --- Hàm gọi API Gemini ---
def get_ai_analysis(data_for_ai, api_key):
    try:
        client = genai.Client(api_key=api_key)
        model_name = 'gemini-2.5-flash'
        prompt = f"""
        Bạn là chuyên gia phân tích tài chính. Hãy nhận xét ngắn gọn (3-4 đoạn) về tình hình tài chính doanh nghiệp:
        {data_for_ai}
        """
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text

    except APIError as e:
        return f"Lỗi gọi Gemini API: {e}"
    except KeyError:
        return "Không tìm thấy khóa API 'GEMINI_API_KEY'."
    except Exception as e:
        return f"Lỗi khác: {e}"


# --- Chức năng 1: Upload file ---
uploaded_file = st.file_uploader(
    "1. Tải file Excel Báo cáo Tài chính (Chỉ tiêu | Năm trước | Năm sau)",
    type=['xlsx', 'xls']
)

if uploaded_file is not None:
    try:
        df_raw = pd.read_excel(uploaded_file)
        df_raw.columns = ['Chỉ tiêu', 'Năm trước', 'Năm sau']
        df_processed = process_financial_data(df_raw.copy())

        st.subheader("2. Tốc độ Tăng trưởng & 3. Tỷ trọng Cơ cấu Tài sản")
        st.dataframe(df_processed.style.format({
            'Năm trước': '{:,.0f}',
            'Năm sau': '{:,.0f}',
            'Tốc độ tăng trưởng (%)': '{:.2f}%',
            'Tỷ trọng Năm trước (%)': '{:.2f}%',
            'Tỷ trọng Năm sau (%)': '{:.2f}%'
        }), use_container_width=True)

        st.subheader("4. Các Chỉ số Tài chính Cơ bản")
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

        # --- Nhận xét AI ---
        st.subheader("5. Nhận xét Tình hình Tài chính (AI)")
        data_for_ai = df_processed.to_markdown(index=False)
        if st.button("Yêu cầu AI Phân tích"):
            api_key = st.secrets.get("GEMINI_API_KEY")
            if api_key:
                with st.spinner("Đang gửi dữ liệu..."):
                    ai_result = get_ai_analysis(data_for_ai, api_key)
                    st.info(ai_result)
            else:
                st.error("Thiếu GEMINI_API_KEY trong secrets.")

    except Exception as e:
        st.error(f"Lỗi khi xử lý file: {e}")
else:
    st.info("Vui lòng tải lên file Excel để bắt đầu phân tích.")


# ==========================
# 🔹 PHẦN MỚI: KHUNG CHAT VỚI GEMINI
# ==========================
st.markdown("---")
st.header("💬 Trò chuyện với Gemini")

# Lưu lịch sử hội thoại trong session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Ô nhập câu hỏi
user_input = st.text_input("Nhập câu hỏi của bạn về tài chính, kế toán, hoặc phân tích dữ liệu:")

if st.button("Gửi câu hỏi"):
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("Chưa cấu hình GEMINI_API_KEY trong secrets.")
    elif user_input.strip():
        try:
            client = genai.Client(api_key=api_key)
            model_name = 'gemini-2.5-flash'
            response = client.models.generate_content(
                model=model_name,
                contents=user_input
            )
            bot_reply = response.text
            st.session_state.chat_history.append(("👤 Bạn", user_input))
            st.session_state.chat_history.append(("🤖 Gemini", bot_reply))
        except Exception as e:
            st.error(f"Lỗi gọi API: {e}")

# Hiển thị lịch sử hội thoại
for speaker, msg in st.session_state.chat_history:
    if speaker == "👤 Bạn":
        st.markdown(f"**{speaker}:** {msg}")
    else:
        st.info(f"{speaker}: {msg}")
