import logging
import time
from .telegram_notifier import TelegramNotifier

try:
    notifier = TelegramNotifier()
except ImportError:
    notifier = None

def safe_execute(func, *args, retries=3, delay=5):
    for i in range(retries):
        try:
            return func(*args)
        except Exception as e:
            logging.error(f"Xato yuz berdi ({func.__name__}): {e}. Qayta urinish {i + 1}/{retries} dan so'ng.")
            time.sleep(delay)
    
    logging.error(f"Funksiya {func.__name__} {retries} marta qayta urinishdan keyin ham muvaffaqiyatsiz tugadi.")
    return None

def log_exception(e, message):
    logging.error(f"{message}: {e}")

def notify_critical(message):
    logging.critical(f"MUHIM XATO: {message}")
    if notifier:
        notifier.send_message(f"‼️ Jiddiy xato yuz berdi: {message}")
