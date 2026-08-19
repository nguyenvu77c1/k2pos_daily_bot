import os
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8868046428:AAEsMGZkFYDhIhymTq4fsQ8Yv8wfbGf9o9o")
CHAT_IDS = ["8109199757", "1631933427"]
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MASTER_PROMPT = """
Bạn là Giám đốc Chiến lược Nội dung cho K2POS (Phần mềm quản lý quán Cafe, Trà sữa, Nhà hàng tại Việt Nam).
Hôm nay là ngày: {current_date}.

Nhiệm vụ: Phân tích xu hướng F&B và tạo bài viết theo 3 phần:

PHẦN 1: 💡 Ý TƯỞNG & PHÂN TÍCH TẠI SAO HAY
- Tên ý tưởng & Góc nhìn (Angle).
- Nỗi đau/Tâm lý của chủ quán F&B.
- Tại sao ý tưởng này thu hút chủ quán dừng lại đọc.

PHẦN 2: ✍️ BÀI VIẾT FACEBOOK ĐĂNG NGAY
- Hook giật tít thực tế (1-2 dòng đầu).
- Câu chuyện/tình huống vận hành thực tế.
- Đúc kết giải pháp & lồng ghép K2POS tự nhiên (bán hàng tại quầy, theo dõi thời gian chờ, quản lý món đã trả/chưa trả, hóa đơn điện tử).
- CTA & Hashtags.

PHẦN 3: 🎨 HƯỚNG DẪN VISUAL & VIDEO
- Text trên ảnh (3-7 từ).
- Gợi ý hình ảnh & AI Image Prompt tiếng Anh.
- Kịch bản Reel ngắn 15s.

Yêu cầu: Viết súc tích, ngắt đoạn ngắn, không dùng bảng biểu phức tạp.
"""

def send_telegram_message(chat_id, text):
    """Gửi tin nhắn về Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
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
            pass
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")

def generate_daily_content():
    """Gọi Gemini API tạo nội dung."""
    today_str = datetime.now().strftime("%d/%m/%Y")
    prompt = MASTER_PROMPT.format(current_date=today_str)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    with urllib.request.urlopen(req) as res:
        result = json.loads(res.read().decode("utf-8"))
        return result["candidates"][0]["content"]["parts"][0]["text"]

def deliver_content(target_chat_id=None):
    """Xử lý và gửi bài viết."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Đang tạo nội dung...")
    try:
        raw_content = generate_daily_content()
        today_str = datetime.now().strftime("%d/%m/%Y")
        header = f"🔥 *K2POS CONTENT RADAR – {today_str}*\n\n"
        
        if "PHẦN 3:" in raw_content:
            parts = raw_content.split("PHẦN 3:", 1)
            msg1 = header + parts[0].strip()
            # Use the second part (index 1) which contains PHẦN 3 content
            part3 = parts[1].strip() if len(parts) > 1 else ""
            msg2 = f"🎨 *HƯỚNG DẪN VISUAL & VIDEO ({today_str})*\n\nPHẦN 3:\n" + part3
            messages = [msg1, msg2]
        else:
            chunks = [raw_content[i:i+3000] for i in range(0, len(raw_content), 3000)]
            messages = [header + chunks[0]] + chunks[1:]

        recipients = [target_chat_id] if target_chat_id else CHAT_IDS
        for cid in recipients:
            for msg in messages:
                send_telegram_message(cid, msg)
                time.sleep(1)
        print("-> Đã gửi thành công!")
    except Exception as e:
        print(f"Lỗi tạo nội dung: {e}")
        if target_chat_id:
            send_telegram_message(target_chat_id, "⚠️ Có lỗi xảy ra khi tạo nội dung, vui lòng thử lại sau!")

def get_updates(offset=None):
    """Lắng nghe tin nhắn mới từ Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=30"
    if offset:
        url += f"&offset={offset}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=35) as res:
            return json.loads(res.read().decode("utf-8"))
    except Exception:
        return None

def main():
    if not GEMINI_API_KEY:
        print("Lỗi: Thiếu GEMINI_API_KEY.")
        return

    print("🚀 K2POS Bot 24/7 đang chạy... Bạn có thể gõ /start hoặc /idea trên Telegram!")
    
    last_update_id = None
    sent_slots = set()

    while True:
        try:
            # 1. Kiểm tra lịch tự động (9:00 và 16:00 VN)
            now = datetime.now()
            current_time_str = now.strftime("%H:%M")
            today_date_str = now.strftime("%Y-%m-%d")
            
            # Khung giờ 09:00 và 16:00
            for slot in ["09:00", "16:00"]:
                slot_key = f"{today_date_str}_{slot}"
                if current_time_str == slot and slot_key not in sent_slots:
                    print(f"⏰ Đến lịch hẹn {slot}! Đang tự động gửi bài...")
                    deliver_content()
                    sent_slots.add(slot_key)

            # 2. Lắng nghe tin nhắn người dùng gõ
            updates = get_updates(last_update_id)
            if updates and updates.get("ok"):
                for item in updates.get("result", []):
                    last_update_id = item["update_id"] + 1
                    message = item.get("message", {})
                    text = message.get("text", "").strip().lower()
                    chat_id = str(message.get("chat", {}).get("id"))

                    # Khi gõ /start hoặc /idea
                    if text in ["/start", "/idea", "idea", "/tao"]:
                        send_telegram_message(chat_id, "⏳ Đang phân tích xu hướng và tạo nội dung K2POS cho bạn, vui lòng đợi vài giây...")
                        deliver_content(target_chat_id=chat_id)
            
            time.sleep(1)

        except Exception as e:
            print(f"Lỗi vòng lặp: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
