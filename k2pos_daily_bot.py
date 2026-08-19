import os
import json
import urllib.request
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8868046428:AAEsMGZkFYDhIhymTq4fsQ8Yv8wfbGf9o9o")
CHAT_IDS = ["8109199757", "1631933427"]
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MASTER_PROMPT = """
Bạn là AI Content Marketing & Trend Research Agent riêng cho K2POS.
Hôm nay là: {current_date}.

Nhiệm vụ:
1. Nghiên cứu & phân tích các vấn đề, khó khăn, xu hướng thực tế của chủ quán F&B (quán cafe, trà sữa, nhà hàng, ăn uống) tại Việt Nam gần đây.
2. Chấm điểm và đưa ra 3 ý tưởng nội dung theo đúng format K2POS Content Radar.
3. Chọn 1 Best Idea và viết bài đăng Facebook hoàn chỉnh (Hook mạnh -> Vấn đề -> Insight -> Giải pháp vận hành -> K2POS -> CTA).
4. Cung cấp Text trên ảnh, Ý tưởng thiết kế ảnh, Prompt AI tạo ảnh (tiếng Anh) và Kịch bản Reel ngắn.
5. Luôn tuân thủ: K2POS đồng hành cùng chủ quán, không tự ý bịa tính năng ngoài bán hàng tại quầy, quản lý đơn, phân loại món nước/ăn, kiểm soát món đã trả/chưa trả, theo dõi thời gian chờ và hóa đơn điện tử.
"""

def send_telegram_message(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    max_length = 4000
    chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    
    for chunk in chunks:
        payload = {"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as res:
                if res.status == 200:
                    print(f"Đã gửi thành công tới ID {chat_id}")
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
        print("Lỗi: Thiếu biến môi trường GEMINI_API_KEY")
        return
    content = generate_daily_content(GEMINI_API_KEY)
    full_message = f"🔥 *K2POS DAILY CONTENT AGENT – {datetime.now().strftime('%d/%m/%Y')}*\n\n" + content
    for chat_id in CHAT_IDS:
        send_telegram_message(TELEGRAM_BOT_TOKEN, chat_id, full_message)

if __name__ == "__main__":
    main()
