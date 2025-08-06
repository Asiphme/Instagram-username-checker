# scripts/config_validator.py

import os
import logging
import re
from typing import List

class ConfigValidator:
    def __init__(self, env_path: str):
        self.env_path = env_path
        self.errors = []

    def _check_env_vars(self):
        required_vars = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "PROXY_LIST_PATH", "USERNAME_LIST_PATH"]
        for var in required_vars:
            if not os.getenv(var):
                self.errors.append(f"❌ '{var}' .env faylida topilmadi.")

    def _check_file_paths(self):
        paths_to_check = [os.getenv("PROXY_LIST_PATH"), os.getenv("USERNAME_LIST_PATH")]
        for path in paths_to_check:
            if path and not os.path.exists(path):
                self.errors.append(f"❌ Fayl topilmadi: {path}")

    def _validate_proxies(self, proxies_path: str):
        if not proxies_path or not os.path.exists(proxies_path):
            return

        # Indentatsiya (joy tashlash) toʻgʻrilandi.
        with open(proxies_path, 'r') as f:
            for i, line in enumerate(f, 1):
                proxy = line.strip()
                if proxy and not (re.match(r'^\S+:\S+@\S+:\d+$', proxy) or re.match(r'^\S+:\d+$', proxy)):
                    self.errors.append(f"⚠️ Noto'g'ri proksi formati '{proxy}' (qator {i}). To'g'ri formatlar: http://user:pass@host:port yoki http://host:port")
                    break

    def validate(self) -> List[str]:
        self._check_env_vars()
        self._check_file_paths()
        self._validate_proxies(os.getenv("PROXY_LIST_PATH"))

        if self.errors:
            logging.error("Konfiguratsiya xatolari topildi:")
            for error in self.errors:
                logging.error(error)
        else:
            logging.info("Konfiguratsiya sozlamalari muvaffaqiyatli tekshiruvdan o'tdi.")

        return self.errors
