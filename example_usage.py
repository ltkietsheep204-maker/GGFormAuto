"""
Ví dụ cách sử dụng Survey Filler Tool
"""

from survey_filler import GoogleFormsFiller
import json

# ============== BƯỚC 1: Lấy URL Form ==============
# Mở Google Form và copy URL từ thanh địa chỉ
# URL có dạng: https://docs.google.com/forms/d/e/1FAIpQLSd_8BsWu7WQXm_NR3q-t...../viewform

GOOGLE_FORM_URL = "YOUR_FORM_URL_HERE"  # ← Thay thế bằng URL của form bạn


# ============== BƯỚC 2: Chuẩn bị dữ liệu ==============
# Tạo danh sách dữ liệu với key là chỉ số câu hỏi (bắt đầu từ 0)

# Ví dụ Form Google có:
# Câu 0: Tên (Short Answer)
# Câu 1: Email (Short Answer)  
# Câu 2: Chọn một (Multiple Choice) - các lựa chọn là "Có", "Không", "Không rõ"
# Câu 3: Đánh giá (Multiple Choice) - các lựa chọn là "Rất tốt", "Tốt", "Bình thường"

data_list = [
    {
        0: "Nguyễn Văn A",
        1: "nguyena@example.com",
        2: "Có",
        3: "Rất tốt"
    },
    {
        0: "Trần Thị B",
        1: "tranb@example.com",
        2: "Không",
        3: "Tốt"
    },
    {
        0: "Lê Văn C",
        1: "levanc@example.com",
        2: "Không rõ",
        3: "Bình thường"
    },
]

# Ví dụ với checkboxes (chọn nhiều):
# Câu 4: Chọn nhiều sở thích - đáp án là danh sách
data_with_checkboxes = [
    {
        0: "Người dùng 1",
        1: "user1@example.com",
        2: "Có",
        3: "Rất tốt",
        4: ["Thể thao", "Du lịch"]  # ← Là danh sách
    },
    {
        0: "Người dùng 2",
        1: "user2@example.com",
        2: "Không",
        3: "Tốt",
        4: ["Âm nhạc", "Phim ảnh", "Đọc sách"]
    },
]


# ============== BƯỚC 3: Cấu hình và chạy ==============

def run_single_submission():
    """Gửi một response"""
    filler = GoogleFormsFiller(GOOGLE_FORM_URL, headless=False)
    
    answer = {
        0: "Nguyễn Văn A",
        1: "nguyena@example.com",
        2: "Có",
        3: "Rất tốt"
    }
    
    filler.fill_and_submit(answer)


def run_multiple_submissions():
    """Gửi nhiều responses"""
    filler = GoogleFormsFiller(GOOGLE_FORM_URL, headless=False)
    filler.fill_multiple_submissions(data_list)


def run_with_checkboxes():
    """Gửi với checkboxes"""
    filler = GoogleFormsFiller(GOOGLE_FORM_URL, headless=False)
    filler.fill_multiple_submissions(data_with_checkboxes)


def run_headless():
    """Chạy ở chế độ headless (không hiển thị browser)"""
    filler = GoogleFormsFiller(GOOGLE_FORM_URL, headless=True)
    filler.fill_multiple_submissions(data_list)


def run_from_json():
    """Đọc dữ liệu từ file JSON"""
    # Tạo file JSON chứa dữ liệu
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    filler = GoogleFormsFiller(GOOGLE_FORM_URL, headless=False)
    filler.fill_multiple_submissions(data)


# ============== HƯỚNG DẪN SỬ DỤNG ==============

"""
CÁCH 1: Chỉnh sửa trực tiếp trong file này
  1. Mở Google Form bạn muốn điền tự động
  2. Copy URL form và dán vào GOOGLE_FORM_URL
  3. Đếm số câu hỏi (bắt đầu từ 0)
  4. Chuẩn bị dữ liệu trong data_list
  5. Chạy: python example_usage.py

CÁCH 2: Sử dụng file JSON
  1. Tạo file data.json với dữ liệu cần điền
  2. Sử dụng hàm run_from_json()
  
  Ví dụ data.json:
  [
    {
      "0": "Tên người 1",
      "1": "email1@example.com",
      "2": "Có",
      "3": "Rất tốt"
    },
    {
      "0": "Tên người 2",
      "1": "email2@example.com",
      "2": "Không",
      "3": "Tốt"
    }
  ]

CÁCH 3: Tạo script tùy chỉnh
  from survey_filler import GoogleFormsFiller
  
  filler = GoogleFormsFiller("YOUR_FORM_URL", headless=False)
  filler.fill_multiple_submissions(your_data_list)

CHỮ Ý:
  - headless=False: Hiển thị trình duyệt (dễ debug)
  - headless=True: Chạy ngầm (nhanh hơn)
  - Cần cài đặt Chrome và chromedriver
"""


if __name__ == "__main__":
    print("Survey Filler - Ví dụ sử dụng")
    print("=" * 50)
    print()
    print("Hướng dẫn:")
    print("1. Thay đổi GOOGLE_FORM_URL bằng URL form của bạn")
    print("2. Chuẩn bị dữ liệu trong data_list")
    print("3. Bỏ comment dòng hàm bạn muốn chạy")
    print("4. Chạy: python example_usage.py")
    print()
    
    # Chọn một trong những hàm dưới đây để chạy
    # Bỏ comment hàm bạn muốn sử dụng:
    
    # run_single_submission()          # Gửi 1 response
    # run_multiple_submissions()       # Gửi nhiều responses
    # run_with_checkboxes()           # Gửi với checkboxes
    # run_headless()                  # Chạy headless
    # run_from_json()                 # Đọc từ JSON
    
    print("Vui lòng chỉnh sửa script và chạy hàm mong muốn")
