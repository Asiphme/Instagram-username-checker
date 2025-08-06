import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_message(self, message):
        if not self.bot_token or not self.chat_id:
            return False
        
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message
            }
            requests.post(self.api_url, data=payload)
            return True
        except requests.exceptions.RequestException as e:
            print(f"Telegram'ga xabar yuborishda xato: {e}")
            return False
