# 📋 Hướng dẫn: Điền Google Form có nhiều trang

## 🎯 Vấn đề và Giải pháp

### Vấn đề
- Google Form được chia thành **nhiều trang** khi trả lời
- Nhưng khi vào **link editor** (người chỉnh sửa), **tất cả câu hỏi được hiển thị trên 1 trang**
- Tool cần thu thập tất cả câu hỏi từ đầu, sau đó tự động chuyển trang khi trả lời

### Giải pháp
✅ **Sử dụng link "người chỉnh sửa"** để lấy tất cả câu hỏi  
✅ **Tự động bấm nút "Tiếp"** khi trả lời qua các trang  
✅ **Tự động gửi form** khi hoàn tất

---

## 🚀 Hướng dẫn Chi Tiết

### Bước 1: Lấy Link Editor (Người Chỉnh Sửa)

1. Mở Google Form của bạn
2. Bấm **"Gửi"** ở góc trên phải
3. Bấm **"Sao chép liên kết"** (hoặc copy URL)
4. **Sửa URL** từ `/viewform` thành `/edit`

**Ví dụ:**
```
Từ: https://docs.google.com/forms/d/abc123xyz/viewform
Sang: https://docs.google.com/forms/d/abc123xyz/edit
```

### Bước 2: Chạy Tool

```bash
python interactive_filler.py
```

### Bước 3: Nhập Link Editor

```
📌 Nhập URL Google Form (editor link): https://docs.google.com/forms/d/abc123xyz/edit
```

### Bước 4: Xem Tất Cả Câu Hỏi

Tool sẽ hiển thị **tất cả câu hỏi** được lấy từ link editor:

```
🔍 Đang lấy thông tin form...
✓ Tìm thấy 15 câu hỏi

📋 Câu 1: Tên của bạn là gì?
   Loại: Trả lời ngắn
   
📋 Câu 2: Chọn tuổi của bạn
   Loại: Chọn một lựa chọn
   Lựa chọn:
      1. 18-25
      2. 26-35
      3. 36+
...
```

### Bước 5: Nhập Đáp Án

Bạn chỉ cần nhập 1 lần - tool sẽ sử dụng cùng đáp án cho tất cả responses:

```
📝 NHẬP ĐÁP ÁN CHO CÁC CÂU HỎI
==================================================

Câu 1: Tên của bạn là gì?
→ Nhập đáp án: Nguyễn Văn A
  ✓ Đã lưu

Câu 2: Chọn tuổi của bạn
  1. 18-25
  2. 26-35
  3. 36+
→ Chọn số (1-3): 1
  ✓ Đã chọn: 18-25
```

### Bước 6: Chọn Số Lượng Responses

```
❓ Bạn muốn tạo bao nhiêu responses? (nhập số): 5
✓ Sẽ tạo 5 responses
```

### Bước 7: Tool Tự Động Điền

Tool sẽ tự động:
1. ✅ Điền câu trả lời trên trang đầu
2. ✅ Bấm nút **"Tiếp"** để chuyển trang
3. ✅ Điền tiếp các câu hỏi trên trang tiếp theo
4. ✅ Lặp lại cho đến trang cuối
5. ✅ Bấm nút **"Gửi"** để hoàn tất

```
📤 ĐANG GỬI RESPONSES
==================================================

💡 Lưu ý:
- Khi trả lời form, nó có thể chia thành nhiều trang
- Tool sẽ tự động bấm 'Tiếp' để chuyển trang
- Cuối cùng sẽ bấm 'Gửi' để hoàn tất response

📮 Response 1/5
📄 Trang 1
  → Tên của bạn là gì?: ✓
  → Chọn tuổi của bạn: ✓
📄 Trang 2
  → Câu hỏi 3: ✓
  → Câu hỏi 4: ✓
  ✅ Trang cuối cùng - Gửi form
✅ Form đã gửi
⏳ Chờ 2 giây trước response tiếp theo...

📮 Response 2/5
...

✅ Hoàn tất! Đã gửi tất cả responses
```

---

## 🔧 Tính Năng Chính

### 1. **Thu thập tất cả câu hỏi**
- Sử dụng link editor (1 trang)
- Lấy đầy đủ các loại câu hỏi

### 2. **Tự động chuyển trang**
- Tìm nút "Tiếp" và bấm tự động
- Xử lý được nhiều format nút

### 3. **Điền đáp án chính xác**
- ✅ Trả lời ngắn/dài
- ✅ Chọn một lựa chọn
- ✅ Chọn nhiều lựa chọn
- ✅ Dropdown

### 4. **Xử lý lỗi tốt**
- Bỏ qua câu hỏi nếu không tìm thấy
- Hiển thị cảnh báo để theo dõi

### 5. **Tạo nhiều responses**
- Chỉ cần nhập 1 lần
- Tự động tạo từ 2 đến 100+ responses

---

## 💡 Lưu Ý Quan Trọng

### ⚠️ Cần Chuyển từ Editor Link sang Response Link?

Nếu form yêu cầu response link thay vì editor link:

1. **Lấy URL từ editor**: `https://docs.google.com/forms/d/abc123xyz/edit`
2. **Chuyển sang response**: `https://docs.google.com/forms/d/abc123xyz/viewform`
3. **Nhập response link** vào tool

Tool sẽ vẫn hoạt động, nhưng:
- Chỉ lấy được câu hỏi trên trang hiện tại
- Không tự động chuyển trang

### ✅ Cách Tối Ưu

1. **Lúc lấy câu hỏi**: Sử dụng **editor link**
2. **Lúc trả lời**: Tool tự động chuyển sang **response link** (nếu cần)
3. **Tự động chuyển trang**: Tool xử lý tất cả

---

## 🐛 Xử Lý Lỗi

### Nếu tool không tìm thấy nút "Tiếp"

- Form có thể không chia thành nhiều trang
- Hoặc nút có CSS khác nhau
- Tool sẽ tự động bấm nút "Gửi" cuối cùng

### Nếu tool không tìm thấy câu hỏi

- Kiểm tra URL có chính xác không
- Thử dùng editor link thay vì response link
- Kiểm tra quyền truy cập

### Nếu điền sai câu hỏi nào đó

- Nhìn vào log để xác định câu hỏi nào
- Sửa lại đáp án và chạy lại

---

## 📊 Các Loại Câu Hỏi Được Hỗ Trợ

| Loại | Hỗ Trợ | Ghi Chú |
|------|--------|--------|
| Trả lời ngắn | ✅ | Điền text |
| Trả lời dài | ✅ | Điền textarea |
| Chọn một | ✅ | Radio button |
| Chọn nhiều | ✅ | Checkbox |
| Dropdown | ✅ | Select |
| Grid (1 select) | ⚠️ | Có thể cần sửa |
| Grid (nhiều) | ⚠️ | Có thể cần sửa |
| File upload | ❌ | Không hỗ trợ |
| Hình ảnh | ❌ | Không hỗ trợ |

---

## 🎓 Ví Dụ Thực Tế

### Ví dụ 1: Form khảo sát 2 trang

```
Trang 1:
  Câu 1: Tên của bạn?
  Câu 2: Tuổi của bạn?

Trang 2:
  Câu 3: Công việc của bạn?
  Câu 4: Email?
  [Nút Gửi]
```

**Cách sử dụng:**
```
1. Nhập editor link → Lấy được 4 câu hỏi
2. Nhập đáp án cho 4 câu
3. Chọn số lượng responses (ví dụ: 3)
4. Tool tự động:
   - Điền câu 1, 2 trên trang 1
   - Bấm "Tiếp"
   - Điền câu 3, 4 trên trang 2
   - Bấm "Gửi"
   - Lặp lại 2 lần nữa
```

### Ví dụ 2: Form đơn trang

```
Câu 1: Tên?
Câu 2: Email?
Câu 3: Lựa chọn?
[Nút Gửi]
```

**Cách sử dụng:**
```
1. Nhập editor link → Lấy được 3 câu hỏi
2. Nhập đáp án cho 3 câu
3. Tool điền và gửi ngay lập tức
```

---

## 📞 Hỗ Trợ

Nếu gặp lỗi, kiểm tra:
1. URL có chính xác không
2. Form có đang hoạt động không
3. Quyền truy cập có đủ không
4. Chrome version có tương thích không

---

**Cập nhật: 25/1/2026**  
**Version: 2.0 - Multi-page Support**
