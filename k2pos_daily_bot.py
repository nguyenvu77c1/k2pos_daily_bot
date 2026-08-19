import os
import json
import urllib.request
import time
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8868046428:AAEsMGZkFYDhIhymTq4fsQ8Yv8wfbGf9o9o")
CHAT_IDS = ["8109199757", "1631933427"]
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MASTER_PROMPT = """
Bạn là Content Marketing Leader cho K2POS (phần mềm quản lý quán Cafe, Trà sữa, Nhà hàng tại Việt Nam).
Hôm nay là: {current_date}.

Hãy tạo nội dung theo đúng cấu trúc sau (viết văn phong tự nhiên, súc tích, chạm đúng nỗi đau của chủ quán, KHÔNG dùng bảng biểu):

PHẦN 1: 💡 3 Ý TƯỞNG CONTENT HÔM NAY
- Nêu ngắn gọn 3 ý tưởng (mỗi ý tưởng gồm: Tên chủ đề/Pain point, Hook thu hút).

PHẦN 2: 🏆 BÀI VIẾT FACEBOOK ĐĂNG NGAY (Chọn ý tưởng tốt nhất)
- Hook mạnh mẽ (1-2 dòng đầu).
- Nỗi đau/tình huống thực tế của quán F&B.
- Góc nhìn/bài học kinh nghiệm thực tế.
- Lồng ghép K2POS tự nhiên như người bạn đồng hành (tính năng: bán hàng tại quầy, theo dõi thời gian chờ, kiểm soát món đã trả/chưa trả, hóa đơn điện tử). Tuyệt đối không bịa thêm tính năng khác.
- Call to Action (kêu gọi bình luận hoặc lưu bài).
- Hashtags liên quan.

PHẦN 3: 🎨 TÀI NGUYÊN VISUAL
- Text trên ảnh (ngắn gọn 3-7 từ).
- Gợi ý bố cục thiết kế ảnh (đơn giản, dễ nhìn).
- AI Image Prompt (tiếng Anh chi tiết để tạo ảnh).
- Kịch bản Reel ngắn 15-20s (Hook 0-3s, Vấn đề 3-7s, Giải pháp 7-15s, CTA 15-20s).

Quy tắc: Ngắn gọn, rõ ràng, dễ hiểu, chia nhỏ đoạn để dễ đọc trên điện thoại.
"""

def send_telegram_message(bot_token, chat_id, text):
    """Gửi tin nhắn an toàn đến Telegram."""
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
                print(f"-> Gửi thành công tới ID {chat_id}")
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
    
    # Tách thông minh giữa bài viết chính và phần Visual để gửi làm 2 tin nhắn gọn gàng
    today_str = datetime.now().strftime("%d/%m/%Y")
    header = f"🔥 *K2POS CONTENT RADAR – {today_str}*\n\n"
    
    if "PHẦN 3:" in raw_content:
        parts = raw_content.split("PHẦN 3:")
        msg_part1 = header + parts[0].strip()
        msg_part2 = f"🎨 *TÀI NGUYÊN VISUAL & VIDEO ({today_str})*\n\n" + parts.strip()
        messages = [msg_part1, msg_part2]
    else:
        # Nếu không tìm thấy điểm ngắt, tự động chia theo độ dài an toàn (< 3000 ký tự)
        chunks = [raw_content[i:i+3000] for i in range(0, len(raw_content), 3000)]
        messages = [header + chunks[0]] + chunks[1:]

    for chat_id in CHAT_IDS:
        for msg in messages:
            send_telegram_message(TELEGRAM_BOT_TOKEN, chat_id, msg)
            time.sleep(1) # Nghỉ 1s giữa các tin nhắn để Telegram không bị nghẽn

if __name__ == "__main__":
    main()
