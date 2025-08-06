# scripts/run_all.py

import os
import sys
import logging
from dotenv import load_dotenv
import asyncio
import random
from datetime import datetime, timezone, timedelta
from tqdm import tqdm
from colorama import Fore, Style, init
import re
from typing import Iterator, List

# Tizim yo'lini yangilash
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Barcha kerakli modullarni import qilish
from scripts.proxy_handler import ProxyHandler
from scripts.username_checker import check_username_with_retries
from scripts.db_manager import DBManager
from scripts.error_handler import safe_execute, log_exception, notify_critical
from scripts.metadata_manager import MetadataManager
from scripts.report_manager import ReportManager
from scripts.telegram_notifier import TelegramNotifier
from scripts.system_monitor import get_system_status
from scripts.config_validator import ConfigValidator

# Konfiguratsiya faylini yuklash
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Loglash tizimini sozlash
log_file = os.getenv("LOG_FILE_PATH", "logs/checker.log")
error_log_file = os.getenv("ERROR_LOG_PATH", "logs/errors.log")
if not os.path.exists("logs"): os.makedirs("logs")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

error_file_handler = logging.FileHandler(error_log_file)
error_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
error_file_handler.setLevel(logging.ERROR)
logger.addHandler(error_file_handler)

init()

def username_generator(filepath: str) -> Iterator[str]:
    with open(filepath, 'r') as f:
        for line in f:
            yield line.strip()

def chunkify(iterable: Iterator[str], size: int) -> Iterator[List[str]]:
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk

async def main():
    logging.info("Loyiha ishga tushdi.")

    validator = ConfigValidator(os.path.join(os.path.dirname(__file__), '..', '.env'))
    if validator.validate():
        notify_critical("Loyiha konfiguratsiya xatolari tufayli to'xtatildi.")
        return

    proxies_path = os.getenv("PROXY_LIST_PATH")
    usernames_path = os.getenv("USERNAME_LIST_PATH")
    output_db_path = os.getenv("OUTPUT_DB_PATH")
    metadata_path = os.getenv("METADATA_PATH", "output/run_metadata.json")
    if not os.path.exists("output"): os.makedirs("output")
    
    notifier = TelegramNotifier()
    
    system_alerts = get_system_status()
    if system_alerts:
        alert_message = "\n".join(system_alerts)
        notifier.send_message(f"🚨 Tizimda muammo aniqlandi:\n{alert_message}")
        logging.warning(f"Tizimda muammo aniqlandi:\n{alert_message}")

    proxy_handler = ProxyHandler(proxies_path)
    db_manager = DBManager(output_db_path)
    metadata_manager = MetadataManager(metadata_path)
    report_manager = ReportManager(output_db_path, templates_dir=os.path.join(os.path.dirname(__file__), '..', 'templates'))
    
    try:
        with open(usernames_path, 'r') as f:
            total_lines = sum(1 for line in f if line.strip())
    except FileNotFoundError:
        notify_critical(f"Xato: Foydalanuvchi nomlari fayli topilmadi: {usernames_path}")
        return

    if total_lines == 0:
        logging.warning("Foydalanuvchi nomlari fayli bo'sh. Loyiha yakunlanmoqda.")
        # "Waiting" rejimiga o'tish mumkin, bu yerda dastur to'xtaydi
        return

    metadata = metadata_manager.get_metadata("total_usernames_checked")
    start_index = metadata if metadata is not None else 0
    
    if start_index >= total_lines:
        start_index = 0
        metadata_manager.update_metadata("total_usernames_checked", 0)
        metadata_manager.save_metadata()

    chunk_size = 50
    available_count = 0 
    taken_count = 0
    checked_count = 0

    try:
        with tqdm(total=total_lines,
                  initial=start_index,
                  desc=f"{Fore.CYAN}Tekshirilmoqda{Style.RESET_ALL}",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]",
                  unit=" username",
                  dynamic_ncols=True,
                  colour='green') as pbar:

            username_stream = username_generator(usernames_path)
            
            if start_index > 0:
                for _ in range(start_index):
                    next(username_stream, None)

            for chunk in chunkify(username_stream, size=chunk_size):
                
                # Agar proksi tugagan bo'lsa, loyihani to'xtatish
                if not (proxy_handler.proxies - proxy_handler.bad_proxies):
                    notify_critical("Jiddiy xato: Barcha proksilar ishlamayapti. Loyiha to'xtatildi.")
                    notifier.send_message("‼️ Jiddiy xato: Barcha proksilar ishlamayapti. Loyiha to'xtatildi.")
                    break
                    
                sanitized_chunk = [u for u in chunk if re.match(r"^[a-zA-Z0-9._]+$", u)]
                
                if not sanitized_chunk:
                    continue

                tasks = []
                for user in sanitized_chunk:
                    proxy = proxy_handler.get_random_proxy()
                    if proxy:
                        tasks.append(check_username_with_retries(user, proxy))
                    else:
                        logging.warning(f"Username '{user}' proksi yo'qligi sababli tekshirilmadi.")
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for j, result in enumerate(results):
                    username = sanitized_chunk[j]
                    if isinstance(result, Exception):
                        log_exception(result, f"Username '{username}'ni tekshirishda xato")
                        proxy_handler.mark_as_unusable(proxy_handler.get_random_proxy())
                        continue

                    status = result
                    if status:
                        safe_execute(db_manager.save_result, username, status)
                        
                        if status == 'available':
                            available_count += 1
                        elif status == 'taken':
                            taken_count += 1

                        checked_count += 1
                        metadata_manager.update_metadata("last_checked_username", username)
                
                pbar.update(len(chunk))
                pbar.set_postfix(available=available_count, taken=taken_count, checked=checked_count)

                metadata_manager.update_metadata("total_usernames_checked", pbar.n)
                metadata_manager.save_metadata()
                
                await asyncio.sleep(random.uniform(1.5, 4.0))

    except Exception as e:
        log_exception(e, "Faylni o'qishda umumiy xato")
        notifier.send_message(f"‼️ Loyiha kutilmagan xato tufayli to'xtadi: {e}")
    finally:
        report_manager.generate_report()
        end_time = datetime.now(timezone.utc)
        metadata_manager.update_metadata("last_run_time", end_time.isoformat())
        metadata_manager.update_metadata("status", "completed")
        metadata_manager.update_metadata("next_run_estimate", (end_time + timedelta(hours=24)).isoformat())
        metadata_manager.save_metadata()

    logging.info("Loyiha yakunlandi.")
    notifier.send_message("✅ Loyiha muvaffaqiyatli yakunlandi!")

if __name__ == "__main__":
    asyncio.run(main())
