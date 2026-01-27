# 📋 Tóm Tắt Cập Nhật: Chế Độ Chọn Ngẫu Nhiên (Random Mode)

## ✨ Tính Năng Mới Được Thêm

### 1. **🎲 Bật/Tắt Chế Độ Random**
   - **Vị trí**: Tab "Chọn Đáp Án"
   - **Hiển thị**: Checkbox "🎲 Chế Độ Chọn Ngẫu Nhiên (Random Mode)"
   - **Chức năng**: Chuyển đổi giữa chế độ chọn đơn (normal) và chế độ random

### 2. **☑️ Giao Diện Thích Ứng**
   
   **Khi Random Mode = OFF (Bình Thường):**
   ```
   Câu 1: Bạn thích mầu gì?
   ⦿ Đỏ        (Radio button - chọn 1)
   ○ Xanh
   ○ Vàng
   ```

   **Khi Random Mode = ON (Ngẫu Nhiên):**
   ```
   Câu 1: Bạn thích mầu gì?
   ☑ Đỏ        Tỉ lệ (%):  [30]
   ☑ Xanh      Tỉ lệ (%):  [40]
   ☐ Vàng      Tỉ lệ (%):  [30]
        ↑           ↑
   Checkboxes   Spinboxes
   ```

### 3. **📊 Tỉ Lệ Phần Trăm**
   - Mỗi đáp án được chọn có thể được gán một tỉ lệ (0-100%)
   - Tổng tỉ lệ của tất cả đáp án được chọn **PHẢI = 100%**
   - Ứng dụng sẽ kiểm tra và cảnh báo nếu tổng ≠ 100%

### 4. **🎯 Lựa Chọn Ngẫu Nhiên Dựa Trên Tỉ Lệ**
   - Cho mỗi submission, bot chọn **1 đáp án ngẫu nhiên** từ các đáp án được chọn
   - Xác suất được chọn dựa trên tỉ lệ phần trăm được thiết lập
   - Ví dụ: Nếu "A = 20%", thì trong 100 submissions, "A" sẽ được chọn khoảng 20 lần

---

## 🔧 Chi Tiết Kỹ Thuật Được Thay Đổi

### File: `gui_app_v3.py`

#### 1. **Thêm biến `random_mode` vào Constructor**
```python
def __init__(self):
    # ...
    self.random_mode = False  # Toggle random mode
```

#### 2. **Cập Nhật Tab "Chọn Đáp Án" - `createAnswersTab()`**
- Thêm checkbox bật/tắt Random Mode
- Kết nối tín hiệu `stateChanged` để gọi `onRandomModeToggled()`

#### 3. **Thêm Xử Lý Toggle - `onRandomModeToggled()`**
```python
def onRandomModeToggled(self, state):
    """Xử lý toggle chế độ random"""
    self.random_mode = (state == Qt.Checked)
    if self.questions:
        self.createAnswerInputs()  # Tái tạo UI
```

#### 4. **Cập Nhật `createAnswerInputs()` - Hỗ Trợ Random Mode**
- **Khi Random Mode = ON**: Hiển thị checkboxes + percentage spinboxes cho mỗi option
- **Khi Random Mode = OFF**: Hiển thị radio buttons (bình thường)
- Lưu trữ dữ liệu: `self.answer_widgets[idx] = ('random', checkbox_list)`
  - `checkbox_list = [(checkbox, percent_spinbox, option_text), ...]`

#### 5. **Cập Nhật `getAnswersFromWidgets()` - Xử Lý Random Data**
```python
if isinstance(widget, tuple) and widget[0] == 'random':
    # Lấy các option được chọn + tỉ lệ
    random_answer = [
        {'text': option_text, 'percentage': percent_value},
        ...
    ]
    # Kiểm tra tổng tỉ lệ = 100%
    answers[idx] = ('random', random_answer)
```

#### 6. **Cập Nhật `_fill_form()` trong SubmissionWorker**
- Phát hiện nếu answer là tuple với `('random', options_list)`
- Gọi `_select_by_percentage()` để chọn random
- Sau đó click vào option được chọn

#### 7. **Thêm Hàm `_select_by_percentage()` - Thuật Toán Random**
```python
def _select_by_percentage(self, options_list: List[Dict]) -> str:
    """Chọn option dựa trên tỉ lệ phần trăm"""
    weighted_options = []
    for option_data in options_list:
        text = option_data['text']
        percentage = option_data['percentage']
        weighted_options.extend([text] * percentage)  # Repeat theo %
    
    selected = random.choice(weighted_options)  # Random chọn
    return selected
```

---

## 📊 So Sánh Chế Độ

| Tiêu Chí | Normal Mode | Random Mode |
|----------|------------|------------|
| **UI** | Radio buttons | Checkboxes + % input |
| **Chọn** | 1 đáp án | Nhiều đáp án |
| **Mỗi submission** | Cùng 1 đáp án | Chọn random 1 từ danh sách |
| **Tỉ Lệ** | N/A | Dựa trên % được thiết lập |
| **Kết Quả 10 submissions** | 10 × cùng đáp án | Khác nhau theo % |

---

## 🚀 Cách Sử Dụng

### Bước 1: Tải Form & Chọn Tab
```
1. Nhập URL → Nhấn "📥 Tải Thông Tin Form"
2. Chuyển sang tab "Chọn Đáp Án"
```

### Bước 2: Bật Random Mode
```
Tìm checkbox "🎲 Chế Độ Chọn Ngẫu Nhiên (Random Mode)" → Nhấn vào
```

### Bước 3: Chọn & Thiết Lập Tỉ Lệ
```
Cho mỗi câu hỏi:
  1. ☑ Ticked các đáp án bạn muốn
  2. Nhập % cho mỗi đáp án
  3. Đảm bảo Tổng = 100%
```

### Bước 4: Gửi
```
1. Tab "Gửi Responses" → Nhập số lượng
2. Nhấn "📤 Bắt Đầu Gửi"
3. Xem log tiến trình
```

---

## ✅ Kiểm Thử

Hãy thử scenario này:
```
Form: https://forms.gle/KSkfKGw1jTvM2UA96

Random Mode ON:
- Q1: "em" = 25%, "anh" = 75%
- Q2: "oke" = 50%, "phe" = 50%

Gửi 20 responses

Kết quả dự kiến:
- Q1 "em": ~5 lần, "anh": ~15 lần
- Q2 "oke": ~10 lần, "phe": ~10 lần
```

---

## ⚠️ Lưu Ý Quan Trọng

1. **Tỉ Lệ PHẢI = 100%**
   - Nếu sai, ứng dụng sẽ báo lỗi
   - Ví dụ sai: 20% + 30% = 50% ❌
   - Ví dụ đúng: 20% + 30% + 50% = 100% ✅

2. **Áp Dụng Cho Multiple Choice**
   - Chỉ câu hỏi có options mới có Random Mode
   - Câu text input không bị ảnh hưởng

3. **Mỗi Submission = 1 Random Pick**
   - 10 submissions → có thể 10 đáp án khác nhau (hoặc có trùng)
   - Không phải "mỗi submission gửi tất cả"

4. **Toggle Sẽ Reset UI**
   - Bật/Tắt Random Mode → giao diện thay đổi
   - Dữ liệu trước không được lưu

---

## 🎯 Ưu Điểm Tính Năng

✅ **Tạo dữ liệu ngẫu nhiên tự nhiên**
- Thay vì 100 responses giống nhau, giờ có nhiều biến thể
- Google Forms sẽ không phát hiện spam pattern

✅ **Kiểm soát tỉ lệ**
- Bạn muốn 80% chọn A, 20% chọn B → Đặt tỉ lệ đó
- Dữ liệu sẽ tuân theo phân bố mong muốn

✅ **Linh hoạt**
- Tắt Random Mode để quay lại chế độ cơ bản
- Thay đổi tỉ lệ dễ dàng

---

## 📝 Log Ví Dụ

```
[WORKER] Random selection: "anh" (từ 2 options với percentages)
[WORKER] Random selection: "oke" (từ 2 options với percentages)
[LOOP 0] ✓ Response 1/10 submitted successfully
...
[LOOP 9] ✓ Response 10/10 submitted successfully
✅ Hoàn tất! Đã gửi 10 responses
```

---

## 🔗 Tài Liệu Chi Tiết

Xem file `RANDOM_MODE_GUIDE.md` để hướng dẫn chi tiết + ví dụ thực tế.

---

**Phiên Bản**: v3.1 (với Random Mode)  
**Ngày Cập Nhật**: Tháng 1, 2026  
**Trạng Thái**: ✅ Sẵn Sàng Sử Dụng
