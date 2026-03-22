# FBANK - Smart Financial Ecosystem

FBANK là hệ sinh thái tài chính thông minh dựa trên AI, giúp người dùng tối ưu hóa các khoản tiết kiệm và phân tích kinh tế vĩ mô thời gian thực.

## 🚀 Tính năng nổi bật
- **Phân tích Lợi nhuận AI**: Đề xuất ngân hàng có lãi suất tốt nhất dựa trên kỳ hạn.
- **Mô phỏng Kịch bản**: Giả lập các biến động tỷ giá và lạm phát để kiểm tra áp lực tài chính.
- **Giá Vàng & Ngoại tệ**: Dữ liệu trực tiếp từ Vietcombank và WebGia.
- **Quản lý Danh mục**: Theo dõi các khoản gửi và ngày đáo hạn.

## 🛠 Cài đặt & Chạy trên Cloud (Streamlit Cloud)
1. Đưa mã nguồn lên GitHub.
2. Truy cập [Streamlit Cloud](https://streamlit.io/cloud) và chọn Repository này.
3. **Quan trọng**: Cấu hình các "Secrets" sau trong Dashboard của Streamlit để hệ thống hoạt động:
   ```toml
   GEMINI_API_KEY = "Của_Bạn"
   SMTP_EMAIL = "Của_Bạn"
   SMTP_PASSWORD = "Của_Bạn"
   ```

## 💻 Chạy Local (Máy tính cá nhân)
1. Clone repo này.
2. Cài đặt thư viện: `pip install -r requirements.txt`.
3. Chạy ứng dụng: `streamlit run app.py`.

---
© 2026 FBANK - Financial Ecosystem
