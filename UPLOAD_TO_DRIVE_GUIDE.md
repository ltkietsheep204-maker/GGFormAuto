# 📱 Hướng Dẫn Tải Google Form Auto Filler Lên Google Drive

## **1️⃣ Chuẩn Bị File**

### **Cho macOS:**
```bash
bash build_macos_app.sh
```
Sẽ tạo ra: `dist/Google Form Auto Filler.app`

### **Cho Windows:**
```cmd
build_windows_app.bat
```
Sẽ tạo ra: `dist/Google Form Auto Filler` (folder)

---

## **2️⃣ Đóng Gói File**

### **macOS - Tạo ZIP:**
```bash
cd dist
zip -r "Google Form Auto Filler macOS.zip" "Google Form Auto Filler.app"
```

### **Windows - Tạo ZIP:**
```cmd
Chuột phải folder "Google Form Auto Filler" → Compress → "Google Form Auto Filler Windows.zip"
```

---

## **3️⃣ Upload Lên Google Drive**

1. **Vào Google Drive:** https://drive.google.com
2. **Tạo folder mới:** "Google Form Auto Filler"
3. **Upload file ZIP:**
   - Kéo thả file ZIP vào folder
   - Hoặc: Click "New" → "File upload"
4. **Share link:**
   - Chuột phải file → "Share"
   - Thay đổi từ "Restricted" → "Anyone with the link"
   - Copy link

---

## **4️⃣ Hướng Dẫn Cho User**

Khi user tải về file ZIP:

### **macOS:**
```
1. Giải nén file → Xuất hiện thư mục "Google Form Auto Filler.app"
2. Kéo vào folder "Applications"
3. Mở "Applications" → Double-click ứng dụng
4. (Lần đầu) Chuột phải → "Open" → "Open" (bỏ qua cảnh báo)
5. Ứng dụng tự động mở!
```

### **Windows:**
```
1. Giải nén file → Xuất hiện thư mục "Google Form Auto Filler"
2. Vào thư mục
3. Double-click "Google Form Auto Filler.exe"
4. Ứng dụng tự động chạy!
```

---

## **5️⃣ Thay Thế Phiên Bản Mới**

Khi cập nhật công cụ:
```bash
# macOS
bash build_macos_app.sh
cd dist && zip -r "Google Form Auto Filler macOS.zip" "Google Form Auto Filler.app"

# Windows  
build_windows_app.bat
# Zip folder "Google Form Auto Filler" thủ công
```

Xóa file cũ trên Drive, upload file mới.

---

## **🔍 Kiểm Tra Thành Công**

Sau khi user tải về và chạy:
- ✅ App mở bình thường
- ✅ GUI hiển thị đúng
- ✅ Có thể paste link form và submit

---

## **📊 Download Stats**

Bạn có thể kiểm tra số lần tải bằng cách:
1. Google Drive → Chuột phải file
2. "Details" → xem "Downloads"

---

## **💡 Lưu Ý**

- Mỗi OS cần file riêng (không dùng chung)
- File ZIP sẽ lớn (~500MB) vì chứa Python + Selenium + Chrome
- Tốc độ download phụ thuộc vào kết nối internet
- Nếu file quá lớn, có thể nén thêm bằng WinRAR hoặc 7-Zip

---

## **🚀 Tối Ưu Hóa (Tùy Chọn)**

Để giảm kích thước file, có thể:
1. Loại bỏ các file không cần trong `dist/`
2. Nén file bằng 7-Zip thay vì ZIP (giảm 20-30%)
3. Chia thành 2 file nhỏ hơn

Liên hệ nếu cần hỗ trợ!
