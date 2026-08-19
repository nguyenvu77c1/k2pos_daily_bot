import os
import json
import urllib.request
import time
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8868046428:AAEsMGZkFYDhIhymTq4fsQ8Yv8wfbGf9o9o")
CHAT_IDS = ["8109199757", "1631933427"]
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MASTER_PROMPT = """
Bạn là Giám đốc Chiến lược Nội dung cho K2POS (Giải pháp phần mềm quản lý quán Cafe, Trà sữa, Nhà hàng tại Việt Nam).
Hôm nay là: {current_date}.

Nhiệm vụ của bạn là nghiên cứu các vấn đề thực tế của chủ quán F&B tại Việt Nam hôm nay và trả về báo cáo theo đúng 3 phần sau:

PHẦN 1: 💡 Ý TƯỞNG & PHÂN TÍCH TẠI SAO HAY
- Tên ý tưởng & Góc nhìn (Angle).
- Tại sao chọn ý tưởng này? (Phân tích nỗi đau tâm lý, khó khăn thực tế của chủ quán F&B).
- Điểm đắt giá của ý tưởng: Tại sao chủ quán sẽ dừng lại đọc và tương tác thay vì lướt qua?

PHẦN 2: ✍️ BÀI VIẾT FACEBOOK ĐĂNG NGAY
- Hook giật tít thực tế (1-2 dòng đầu, đánh trúng tim đen).
- Kể câu chuyện/tình huống thực tế ngắn gọn.
- Bài học đúc kết về quy trình vận hành.
- Lồng ghép K2POS như một giải pháp hỗ trợ đồng hành (chỉ dùng các tính năng: bán hàng tại quầy, theo dõi thời gian chờ, quản lý món đã trả/chưa trả, h[...]
- Kêu gọi hành động (CTA) và Hashtags.

PHẦN 3: 🎨 HƯỚNG DẪN VISUAL & VIDEO
- Text ngắn trên ảnh (3-7 từ).
- Concept thiết kế hình ảnh.
- AI Image Prompt tiếng Anh (để đưa vào Midjourney/DALL-E).
- Kịch bản Reel ngắn 15s (Tình huống -> Cao trào -> Giải pháp K2POS).

Yêu cầu: Không dùng bảng biểu phức tạp. Ngắt đoạn ngắn gọn để dễ đọc trên điện thoại.
"""

def send_telegram_message(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as res:
            if res.status == 200:
                print(f"-> Đã gửi thành công tới ID {chat_id}")
    except Exception as e:
        print(f"Lỗi gửi tới ID {chat_id}: {e}")

def generate_daily_content(api_key):
    today_str = datetime.now().strftime("%d/%m/%Y")
    prompt = MASTER_PROMPT.format(current_date=today_str)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    with urllib.request.urlopen(req) as res:
        result = json.loads(res.read().decode("utf-8"))
        return result["candidates"][0]["content"]["parts"][0]["text"]

def main():
    if not GEMINI_API_KEY:
        print("Lỗi: Thiếu GEMINI_API_KEY")
        return
    
    print("Đang tạo nội dung K2POS...")
    raw_content = generate_daily_content(GEMINI_API_KEY)
    
    today_str = datetime.now().strftime("%d/%m/%Y")
    header = f"🔥 *K2POS STRATEGY & CONTENT RADAR – {today_str}*\n\n"
    
    # Chia làm 2 tin nhắn hợp lý: Tin 1 (Idea + Bài viết), Tin 2 (Visual & Video)
    if "PHẦN 3:" in raw_content:
        parts = raw_content.split("PHẦN 3:", 1)
        msg1 = header + parts[0].strip()
        msg2 = f"🎨 *HƯỚNG DẪN VISUAL & VIDEO ({today_str})*\n\n" + parts[1].strip()
        messages = [msg1, msg2]
    elif "PHẦN 3" in raw_content:
        parts = raw_content.split("PHẦN 3", 1)
        msg1 = header + parts[0].strip()
        msg2 = f"🎨 *HƯỚNG DẪN VISUAL & VIDEO ({today_str})*\n\n" + parts[1].strip()
        messages = [msg1, msg2]
    else:
        chunks = [raw_content[i:i+3000] for i in range(0, len(raw_content), 3000)]
        messages = [header + chunks[0]] + chunks[1:]

    for chat_id in CHAT_IDS:
        for msg in messages:
            send_telegram_message(TELEGRAM_BOT_TOKEN, chat_id, msg)
            time.sleep(1)

if __name__ == "__main__":
    main()
