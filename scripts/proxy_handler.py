# scripts/proxy_handler.py

import random
import logging
import os
import time
from typing import List, Set, Dict

class ProxyHandler:
    def __init__(self, proxy_file_path: str):
        self.proxy_file_path = proxy_file_path
        self.bad_proxies_path = os.path.join(os.path.dirname(proxy_file_path), 'bad_proxies.txt')
        
        # Ro'yxatni set'ga o'zgartirdik, endi ularni bemalol ayirish mumkin
        self.proxies: Set[str] = self._load_proxies(self.proxy_file_path)
        self.bad_proxies: Set[str] = self._load_proxies(self.bad_proxies_path)
        self.proxy_usage: Dict[str, float] = {p: 0.0 for p in self.proxies}
        
        logging.info(f"{len(self.proxies)} ta proksi yuklandi. {len(self.bad_proxies)} ta yomon proksi topildi.")

    def _load_proxies(self, filepath: str) -> Set[str]:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return set(line.strip() for line in f if line.strip())
            except Exception as e:
                logging.error(f"Fayldan proksilarni yuklashda xato '{filepath}': {e}")
        return set()

    def _save_bad_proxies(self):
        try:
            with open(self.bad_proxies_path, 'w') as f:
                for proxy in self.bad_proxies:
                    f.write(f"{proxy}\n")
        except Exception as e:
            logging.error(f"Yomon proksilarni saqlashda xato: {e}")

    def get_random_proxy(self) -> str:
        cooldown_time = 120
        
        # Bu yerda list() funksiyasini qo'shib, set'ni list'ga o'tkazdik
        available_proxies = [
            p for p in list(self.proxies - self.bad_proxies) 
            if (time.time() - self.proxy_usage.get(p, 0) > cooldown_time)
        ]

        if not available_proxies:
            logging.warning("Mavjud proksilarning barchasi 'cooldown' holatida yoki ishlamaydi.")
            cooled_down_proxies = sorted(list(self.proxies), key=lambda p: self.proxy_usage.get(p, 0))
            if cooled_down_proxies:
                return cooled_down_proxies[0]
            
            logging.critical("Barcha proksilar ishlamayapti yoki tugagan.")
            return None
        
        proxy = random.choice(available_proxies)
        self.proxy_usage[proxy] = time.time()
        return proxy

    def mark_as_unusable(self, proxy: str):
        if proxy and proxy not in self.bad_proxies:
            self.bad_proxies.add(proxy)
            self._save_bad_proxies()
            logging.warning(f"Proksi ishlamayapti deb belgilandi: {proxy}. Qolgan proksilar: {len(self.proxies) - len(self.bad_proxies)}")
