# Google Form Interactive Filler - Công cụ Điền Khảo Sát Tự Động

Tool thông minh giúp bạn tự động điền Google Forms với khả năng:
- 🔍 **Tự động trích xuất** câu hỏi từ form
- ❓ **Hỏi người dùng** nhập câu trả lời cho mỗi câu hỏi
- 🔄 **Tạo multiple responses** theo số lượng người dùng chỉ định
- 📤 **Tự động gửi** tất cả responses

## 🚀 Tính năng

### Interactive Mode (Chế độ tương tác) - **ĐƯỢC KHUYÊN DÙNG** ⭐
- ✅ Tự động nhận dạng và trích xuất tất cả câu hỏi
- ✅ Hỏi người dùng nhập đáp án cho mỗi câu hỏi
- ✅ Người dùng chỉ định số lượng responses cần tạo
- ✅ Tự động gửi multiple responses

### Hỗ trợ loại câu hỏi
- 📝 Short Answer (Trả lời ngắn)
- 📄 Long Answer (Trả lời dài)
- 🔘 Multiple Choice (Chọn một)
- ☑️ Checkboxes (Chọn nhiều)
- 📋 Dropdown (Chọn từ danh sách)

### Công cụ bổ trợ
- 🔎 **Inspect Form** - Xem chi tiết câu hỏi
- 📊 **JSON Export** - Lưu thông tin form
- 🎯 **Flexible Data** - Hỗ trợ JSON hoặc interactive input

## 📋 Yêu cầu

- Python 3.7+
- Chrome/Chromium (đã cài sẵn trên macOS)
- pip

## 🔧 Cài đặt

```bash
# Cài đặt dependencies
pip install -r requirements.txt
```

## 🎯 Cách sử dụng (INTERACTIVE MODE) ⭐

### Phương pháp 1: Chế độ tương tác (ĐƯỢC KHUYÊN) 
**Ưu điểm:** Tự động trích xuất câu hỏi, hỏi người dùng nhập đáp án, tự động tạo responses

```bash
python interactive_filler.py
```

**Quy trình:**
1. Nhập URL Google Form
2. Tool sẽ **tự động trích xuất tất cả câu hỏi** và hiển thị
3. Bạn **nhập đáp án** cho mỗi câu hỏi
4. Chỉ định **số lượng responses** muốn tạo
5. Tool sẽ **tự động gửi** tất cả responses

**Ví dụ:**
```
📌 Nhập URL Google Form: https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform

🔍 Đang lấy thông tin form...
✓ Tìm thấy 4 câu hỏi

📋 Câu 1: Tên của bạn?
   Loại: Trả lời ngắn
   
📋 Câu 2: Email của bạn?
   Loại: Trả lời ngắn
   
📋 Câu 3: Bạn đồng ý với ý kiến này?
   Loại: Chọn một lựa chọn
   Lựa chọn:
      1. Có
      2. Không
      3. Không rõ

📋 Câu 4: Đánh giá dịch vụ?
   Loại: Chọn một lựa chọn
   Lựa chọn:
      1. Rất tốt
      2. Tốt
      3. Bình thường

============================================================
📝 NHẬP ĐÁP ÁN CHO CÁC CÂU HỎI
============================================================

Câu 1: Tên của bạn?
→ Nhập đáp án: Nguyễn Văn A
  ✓ Đã lưu

Câu 2: Email của bạn?
→ Nhập đáp án: nguyena@example.com
  ✓ Đã lưu

Câu 3: Bạn đồng ý với ý kiến này?
  1. Có
  2. Không
  3. Không rõ
→ Chọn số (1-3): 1
  ✓ Đã chọn: Có

Câu 4: Đánh giá dịch vụ?
  1. Rất tốt
  2. Tốt
  3. Bình thường
→ Chọn số (1-3): 1
  ✓ Đã chọn: Rất tốt

============================================================
❓ Bạn muốn tạo bao nhiêu responses? (nhập số): 5
✓ Sẽ tạo 5 responses

============================================================
📤 ĐANG GỬI RESPONSES
============================================================

📮 Response 1/5
✓ Form đã được gửi thành công
⏳ Chờ 2 giây trước response tiếp theo...

📮 Response 2/5
✓ Form đã được gửi thành công
...

✅ Hoàn tất! Đã gửi tất cả 5 responses
```Sử dụng Interactive Mode trong code
```python
from interactive_filler import InteractiveGoogleFormFiller

# Chế độ tương tác - hiển thị browser
filler = InteractiveGoogleFormFiller("YOUR_FORM_URL", headless=False)
filler.run_interactive()

# Chế độ headless - chạy ngầm
filler = InteractiveGoogleFormFiller("YOUR_FORM_URL", headless=True)
filler.run_interactive()
```

### Kiểm tra câu hỏi trước khi chạy
```python
from interactive_filler import InteractiveGoogleFormFiller

filler = InteractiveGoogleFormFiller("YOUR_FORM_URL")
questions = filler.extract_questions()  # Hiển thị chi tiết câu hỏi
```

### Gửi responses theo lập trình (không interactive)
```python
from interactive_filler import InteractiveGoogleFormFiller

filler = InteractiveGoogleFormFiller("YOUR_FORM_URL")
answers = {
    0: "Tên người",
    1: "emaildelay giữa responses
Mở `interactive_filler.py`, tìm dòng:
```python
time.sleep(2)  # Chờ 2 giây
```
Thay đổi thành thời gian mong muốn (tính bằng giây)

### Chạy ở chế độ headless (không hiển thị browser)
```python
filler = InteractiveGoogleFormFiller("YOUR_FORM_URL", headless=True)
```

### Thay đổi timeout
Tìm trong `interactive_filler.py`:
```python
self.wait = WebDriverWait(self.driver, 10)  # 10 giây timeout

### Gửi với checkboxes (chọn nhiều)
```python
data = {
    0: "Tên người",
    1: "email@example.com",
    4: ["Thể thao", "Du lịch", "Âm nhạc"]  # Danh sách
}
filler.fill_and_submit(data)
```

### Chạy headless (không hiển thị browser)
```python
filler = GoogleFormsFiller(FORM_URL, headless=True)
filler.fill_multiple_submissions(data_list)
```

## ⚙️ Tùy chỉnh

### Thay đổi thời gian chờ
Mở `survey_filler.py` và tìm:
```python
selfKiểm tra chi tiết câu hỏi
```bash
python inspect_form.py
```
Sẽ lưu chi tiết trong `form_structure.json`

### Hiển thị browser khi chạy (dễ debug)
```bash
# Interactive mode sẽ hiển thị browser theo mặc định
python interactive_filler.py
```

### Xem chi tiết lỗiKhông gửi quá 100 responses trong 1 phút (Google có thể block)
4. **Kiểm tra dữ liệu** - Tool sẽ hỏi lại trước khi tạo > 100 responses
5. **Test trước** - Hãy test với 1-2 response trước

## 🆘 Troubleshooting

### "Chrome not found"
```bash
pip install webdriver-manager
# Hoặc cài Chrome: brew install google-chrome (macOS)
```

### Form không được điền
- Kiểm tra URL có chính xác không
- Chạy `python inspect_form.py` để xem chi tiết câu hỏi
- Sử dụng `headless=False` để thấy browser

### "TimeoutException"
- Kiểm tra kết nối internet
- Tăng timeout trong code

### Câu hỏi bị bỏ qua
- Nếu bạn để trống (không nhập), câu hỏi sẽ bị bỏ qua
- Nhập dữ liệu cho tất cả câu hỏi bắt buộcn bạn có quyền điền form này
2. **Tính hợp pháp** - Kiểm tra điều khoản dịch vụ Google Forms
3. **Rate limiting** - Đừng gửi quá nhiều form trong thời gian ngắn
4. **Chỉnh sửa dữ liệu** - Luôn kiểm tra dữ liệu trước khi gửi
5. **Test trước** - Hãy test với 1-2 response trước khi batch processing

## 🆘 Troubleshooting

### "Chrome not found"
```bash
# Cài ChromeDriver
pip install webdriver-manager
```

### "Element not found"
- Kiểm tra index câu hỏi (có thể câu ẩn hoặc bị cuộn)
- Sử dụng headless=False để xem browser

### "TimeoutException"
- Tăng thời gian chờ (10 -> 20 giây)
- Kiểm tra kết nối internet
- Công form có thể bị tối ưu hóa

## 📖 Tài liệu thêm

- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [Google Forms API](https://developers.google.com/forms/api)

## 📄 Giấy phép

MIT License

## 👨‍💻 Hỗ trợ

Có câu hỏi? Tạo issue hoặc liên hệ!

---

**Được tạo ngày 25/01/2026**
