# ⚡ Quick Start - Cheat Sheet

## 🎯 5 Bước Nhanh

### 1️⃣ Chuẩn bị Link Editor
```
Google Form URL: https://docs.google.com/forms/d/XYZ/viewform
                                                        ^
                                      Thay 'viewform' thành 'edit'
                                                        v
Editor Link:    https://docs.google.com/forms/d/XYZ/edit
```

### 2️⃣ Chạy Tool
```bash
cd /Users/2apple_mgn_63_ram16/Desktop/GGform
python interactive_filler.py
```

### 3️⃣ Paste Link Editor
```
📌 Nhập URL Google Form (editor link): [Paste URL editor link ở đây]
```

### 4️⃣ Nhập Đáp Án
```
📝 NHẬP ĐÁP ÁN CHO CÁC CÂU HỎI
==================================================

Câu 1: Tên của bạn là gì?
→ Nhập đáp án: [Gõ tên]

Câu 2: Chọn tuổi
  1. 18-25
  2. 26-35
  3. 36+
→ Chọn số (1-3): [Gõ số]

... (nhập cho tất cả câu hỏi)
```

### 5️⃣ Chọn Số Lượng + Chờ Tool Hoàn Tất
```
❓ Bạn muốn tạo bao nhiêu responses? (nhập số): [Gõ số]
✅ Tool tự động điền tất cả responses
```

---

## 📌 Những Điều Cần Nhớ

| Điểm | Chi Tiết |
|-----|---------|
| 🔗 **Link** | Phải dùng `/edit` (editor) chứ không phải `/viewform` (response) |
| 📝 **Đáp án** | Chỉ nhập 1 lần - sẽ dùng cho tất cả responses |
| 🔄 **Trang** | Tool tự động bấm "Tiếp" để chuyển trang |
| 💾 **Gửi** | Tool tự động bấm "Gửi" khi trang cuối cùng |
| ⏰ **Thời gian** | 2 giây chờ giữa các responses |

---

## ❓ FAQ Nhanh

### ❓ Tôi có link `/viewform` (response), sao không dùng được?

**Trả lời:** Nếu form chia thành nhiều trang:
- Link `/viewform` chỉ lấy được câu hỏi trên trang đầu
- Link `/edit` lấy được tất cả câu hỏi từ 1 trang

**Cách fix:**
```
/viewform → /edit
```

### ❓ Tôi quên mất editor link?

**Trả lời:** Tạo lại:
1. Copy response link (URL bất kỳ của form)
2. Thay `viewform` → `edit`

### ❓ Tool không tìm thấy "Tiếp" button?

**Trả lời:** 
- Form có thể chỉ 1 trang (không cần "Tiếp")
- Hoặc button có CSS khác
- Tool sẽ tự động bấm "Gửi" cuối cùng

### ❓ Tôi muốn ngừng giữa chừng?

**Trả lời:** 
- Nhấn `Ctrl+C` trong terminal
- Hoặc đóng browser

### ❓ Làm sao biết tool đang chạy?

**Trả lời:** Xem terminal:
```
📮 Response 1/5
📄 Trang 1
  → Câu 1: ✓
  → Câu 2: ✓
📄 Trang 2
  → Câu 3: ✓
  → Câu 4: ✓
  ✅ Trang cuối cùng - Gửi form
✅ Form đã gửi
```

---

## 🛠️ Troubleshooting

| Lỗi | Nguyên nhân | Cách Fix |
|-----|-----------|---------|
| `URL không được để trống` | Forgot to paste URL | Paste URL editor link |
| `Không tìm thấy câu hỏi` | Link không đúng | Dùng editor link `/edit` |
| `Form đã được gửi` | Link response cũ | Refresh form hoặc tạo mới |
| `Selenium error` | Chrome không cài | Cài Chrome hoặc update |
| `Timeout` | Browser chậm | Check internet connection |

---

## 💡 Pro Tips

### ✅ Tip 1: Test Trước
- Chạy với 1 response trước
- Kiểm tra output có đúng không
- Rồi chạy với số lượng lớn

### ✅ Tip 2: Đáp Án Nhất Quán
- Tất cả responses sẽ giống nhau
- Tốt cho form survey/tính giá trị
- Xấu cho form tuỳy chọn với các đáp án khác nhau

### ✅ Tip 3: Kiểm Tra Quyền
- Link editor cần quyền edit
- Nếu không, sẽ không lấy được câu hỏi
- Hoặc lấy được nhưng incomplete

### ✅ Tip 4: Form Động
- Nếu form có logic (show/hide câu hỏi)
- Chỉ lấy được câu hỏi visible
- Có thể cần sửa code

### ✅ Tip 5: Multi-Language
- Tool hỗ trợ tiếng Việt
- Dễ dàng thêm ngôn ngữ khác
- Chỉ cần dịch các string UI

---

## 🚀 Ví Dụ Thực Tế

### Ví dụ 1: Form Khảo Sát 3 Trang

**Input:**
```
Link: https://docs.google.com/forms/d/abc123/edit
Đáp án: Tên "John", Tuổi "26", Công việc "Engineer"
Số responses: 10
```

**Output:**
```
✓ Lấy 12 câu hỏi
✓ Nhập đáp án
✓ Tạo 10 responses
- Response 1: Điền trang 1 → Tiếp → Điền trang 2 → Tiếp → Điền trang 3 → Gửi
- Response 2: (tự động lặp)
- ...
- Response 10: ✅ Gửi
✅ Hoàn tất!
```

### Ví dụ 2: Form 1 Trang

**Input:**
```
Link: https://docs.google.com/forms/d/xyz789/edit
Đáp án: Input 3 câu hỏi
Số responses: 5
```

**Output:**
```
✓ Lấy 3 câu hỏi
✓ Nhập đáp án
✓ Tạo 5 responses
- Response 1: Điền 3 câu → Gửi
- Response 2: (tự động lặp)
- ...
- Response 5: ✅ Gửi
✅ Hoàn tất!
```

---

## 📊 Performance

| Metrics | Con số |
|---------|--------|
| Thời gian lấy 20 câu hỏi | ~3 giây |
| Thời gian nhập 1 lần | ~1 phút |
| Thời gian điền 1 response | ~2-3 giây |
| Thời gian điền 10 responses | ~1-2 phút |
| Thời gian điền 100 responses | ~10-20 phút |

---

## 🎓 Tài Liệu Đầy Đủ

📖 **File hướng dẫn chi tiết:**
- `MULTI_PAGE_FORM_GUIDE.md` - Hướng dẫn đầy đủ
- `UPDATE_v2.0_SUMMARY.md` - Tóm tắt thay đổi
- `RANDOM_MODE_GUIDE.md` - Randomize đáp án

---

**Last Updated:** 25/1/2026  
**Tool Version:** 2.0 ✨  
**Status:** Ready to Use ✅
