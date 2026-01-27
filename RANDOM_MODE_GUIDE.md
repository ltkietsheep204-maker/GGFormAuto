# 🎲 Hướng Dẫn Chế Độ Chọn Ngẫu Nhiên (Random Mode)

## Tính Năng Mới

Ứng dụng Google Form Auto Filler giờ đây hỗ trợ **Chế Độ Chọn Ngẫu Nhiên (Random Mode)** cho phép:

1. **Chọn Nhiều Câu Trả Lời**: Người dùng có thể chọn đồng thời nhiều đáp án cho một câu hỏi
2. **Thiết Lập Tỉ Lệ Phần Trăm**: Mỗi đáp án được gán một tỉ lệ phần trăm (%)
3. **Tự Động Chọn Ngẫu Nhiên**: Bot sẽ tự động chọn đáp án dựa trên tỉ lệ được thiết lập cho mỗi submission

## Cách Sử Dụng

### Bước 1: Tải Form
1. Nhập URL của Google Form vào ô "URL Form"
2. Nhấn nút "📥 Tải Thông Tin Form"
3. Đợi form tải xong

### Bước 2: Chuyển Sang Tab "Chọn Đáp Án"
Chọn tab "Chọn Đáp Án (Click như Google Form)"

### Bước 3: Bật Chế Độ Random
- Tìm checkbox **🎲 Chế Độ Chọn Ngẫu Nhiên (Random Mode)** ở đầu tab
- **Nhấn vào checkbox** để bật chế độ random
- Giao diện sẽ tự động thay đổi: các radio button sẽ chuyển thành checkbox với ô nhập tỉ lệ phần trăm

### Bước 4: Chọn Đáp Án và Thiết Lập Tỉ Lệ
Cho mỗi câu hỏi có multiple choice:

1. **Ticked (✓) checkbox** cho các đáp án bạn muốn sử dụng
2. **Nhập tỉ lệ phần trăm** vào ô bên cạnh mỗi đáp án được chọn
3. **⚠️ Quan Trọng**: Tổng tỉ lệ của tất cả đáp án được chọn **PHẢI bằng 100%**

#### Ví Dụ:
```
Câu 1: Đánh giá dịch vụ
├─ ✓ Rất Tốt - 20%
├─ ✓ Tốt - 30%
├─ ✓ Bình Thường - 35%
└─ ✓ Tệ - 15%
    Tổng: 20 + 30 + 35 + 15 = 100% ✅

Câu 2: Nơi biết về sản phẩm
├─ ✓ Mạng xã hội - 40%
├─ ✓ Tìm kiếm Google - 35%
├─ ✓ Bạn bè giới thiệu - 20%
└─ ✓ Quảng cáo - 5%
    Tổng: 40 + 35 + 20 + 5 = 100% ✅
```

### Bước 5: Thiết Lập Số Responses
1. Chuyển sang tab **"Gửi Responses"**
2. Nhập số lượng responses cần gửi (VD: 10, 50, 100...)
3. **Lưu ý**: Nếu bạn muốn gửi > 100 responses, ứng dụng sẽ yêu cầu xác nhận

### Bước 6: Gửi
1. Nhấn **📤 Bắt Đầu Gửi**
2. Ứng dụng sẽ:
   - Mở trình duyệt Chrome tự động
   - **Mỗi lần submit**, bot sẽ **ngẫu nhiên chọn một đáp án** từ các đáp án được chọn, dựa trên tỉ lệ phần trăm
   - Ví dụ: Nếu "Rất Tốt" là 20%, nó sẽ được chọn khoảng 2 lần trong 10 submissions
3. Xem log tiến trình trong tab
4. Sau khi hoàn thành, Chrome sẽ tự động đóng

## Ví Dụ Cụ Thể

### Scenario: Gửi 100 Responses với Random Mode

**Form:**
```
Q1: Bạn bao nhiêu tuổi?
- 18-25: 25%
- 26-35: 35%
- 36-45: 25%
- 45+: 15%
Tổng: 100% ✅

Q2: Đánh giá sản phẩm?
- 5 sao: 30%
- 4 sao: 40%
- 3 sao: 30%
Tổng: 100% ✅
```

**Kết quả sau 100 submissions:**
- Q1 "18-25" sẽ được chọn khoảng 25 lần
- Q1 "26-35" sẽ được chọn khoảng 35 lần
- Q1 "36-45" sẽ được chọn khoảng 25 lần
- Q1 "45+" sẽ được chọn khoảng 15 lần
- Q2 "5 sao" sẽ được chọn khoảng 30 lần
- Q2 "4 sao" sẽ được chọn khoảng 40 lần
- Q2 "3 sao" sẽ được chọn khoảng 30 lần

(Số lần thực tế sẽ vary một chút do tính ngẫu nhiên)

## Chế Độ Bình Thường (Normal Mode) vs Random Mode

### Normal Mode (Tắt Random)
```
📋 Interface: Radio buttons (chọn 1)
💾 Mỗi submission gửi cùng một đáp án
📊 Kết quả: 10 responses → tất cả là đáp án được chọn
```

### Random Mode (Bật Random)
```
📋 Interface: Checkboxes (chọn nhiều) + Percentage inputs
💾 Mỗi submission chọn ngẫu nhiên dựa trên tỉ lệ
📊 Kết quả: 10 responses → khác nhau theo tỉ lệ được thiết lập
```

## ⚠️ Lưu Ý Quan Trọng

1. **Tỉ Lệ Phải Bằng 100%**
   - Nếu tổng tỉ lệ ≠ 100%, ứng dụng sẽ hiển thị lỗi
   - Bạn phải chỉnh sửa cho đúng trước khi gửi

2. **Chỉ Tính Cho Câu Hỏi Multiple Choice**
   - Random Mode chỉ áp dụng cho câu hỏi có các lựa chọn
   - Câu hỏi text input sẽ hoạt động như bình thường

3. **Toggle Chế Độ**
   - Khi toggle Random Mode on/off, giao diện sẽ tự động thay đổi
   - Checkbox -> Radio buttons hoặc ngược lại
   - Dữ liệu trước đó không được lưu

4. **Không Có Biến Thể Text**
   - Hiện tại, text responses (nếu có) sẽ giống nhau trong tất cả submissions
   - Để có biến thể text, bạn có thể chỉnh sửa thêm sau này

## Troubleshooting

### Lỗi: "Tổng tỉ lệ phải bằng 100%"
**Giải Pháp:**
- Kiểm tra tất cả các ô phần trăm
- Tính tổng cộng
- Điều chỉnh sao cho bằng 100%
- Ghi chú: Nếu bạn chỉ chọn 1 đáp án, tỉ lệ phải là 100%

### Không Thấy Ô Percentage
**Giải Pháp:**
- Chắc chắn Random Mode đã được bật
- Nếu vẫn không thấy, thử tắt và bật lại Random Mode

### Kết Quả Không Theo Tỉ Lệ
**Giải Pháp:**
- Với số lượng submissions lớn (100+), tỉ lệ sẽ càng chính xác
- Nếu gửi quá ít (5, 10), có thể xảy ra sai lệch random
- Ví dụ: 20% có thể là 0, 1, hay 2 lần trong 10 submissions (không phải đúng 2)

## Đặc Điểm Kỹ Thuật

### Thuật Toán Chọn Random
```python
# Nếu có 3 đáp án với tỉ lệ: A=20%, B=50%, C=30%
# Ứng dụng sẽ tạo danh sách:
options = ['A']*20 + ['B']*50 + ['C']*30
# = [A, A, ..., B, B, ..., C, C, ...] (100 phần tử)
# Sau đó random.choice() từ danh sách này
# → Xác suất A được chọn = 20%, B = 50%, C = 30%
```

### Logging
- Tất cả các lần chọn random được ghi lại trong log
- Bạn có thể xem "Random selection: [đáp án] (từ [số] options)" trong log

## FAQ

**Q: Tôi có thể chỉ chọn 1 đáp án với 100% tỉ lệ không?**
A: Có, nhưng khi đó nó tương tự như Normal Mode. Để dùng đúng Normal Mode, tắt Random Mode.

**Q: Nếu tỉ lệ là 33%, 33%, 34% có được không?**
A: Có, miễn sao tổng bằng 100%.

**Q: Tôi có thể thay đổi tỉ lệ sau khi bắt đầu gửi không?**
A: Không, bạn phải dừng lại, chỉnh sửa tỉ lệ, rồi gửi lại.

**Q: Nếu có 10 responses, mỗi response sẽ chọn random đúng không?**
A: Đúng! Mỗi lần gửi form, bot sẽ lấy random 1 đáp án dựa trên tỉ lệ.

---

**Phiên Bản**: v3.1 (có Random Mode)  
**Cập Nhật**: Tháng 1, 2026
