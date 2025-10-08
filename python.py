# --- Khung Chat hỏi đáp Gemini (mở rộng) ---
st.subheader("Khung Chat Trực Tiếp với Gemini AI")

user_question = st.text_area("Nhập câu hỏi để hỏi Gemini AI:", height=100)

if st.button("Gửi câu hỏi"):
    api_key = st.secrets.get("GEMINI_API_KEY")
    if api_key:
        if user_question.strip():
            with st.spinner("Đang gửi câu hỏi và chờ Gemini trả lời..."):
                # Tạo prompt phù hợp với câu hỏi chat
                prompt_chat = f"Bạn là một trợ lý AI chuyên nghiệp. Trả lời câu hỏi sau một cách rõ ràng và súc tích:\n\n{user_question}"
                try:
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt_chat
                    )
                    st.markdown("**Phản hồi từ Gemini AI:**")
                    st.info(response.text)
                except APIError as e:
                    st.error(f"Lỗi gọi Gemini API: {e}")
                except Exception as e:
                    st.error(f"Đã xảy ra lỗi không xác định: {e}")
        else:
            st.warning("Vui lòng nhập câu hỏi trước khi gửi.")
    else:
        st.error("Lỗi: Không tìm thấy Khóa API 'GEMINI_API_KEY'. Vui lòng cấu hình trong Secrets.")
