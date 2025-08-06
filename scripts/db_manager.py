# scripts/db_manager.py

import sqlite3
import logging
from datetime import datetime
import shutil
import os

class DBManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db_timeout = 30  # SQLite lock uchun timeout
        self._backup_db()
        self._create_table()
        self._check_integrity()

    def _backup_db(self):
        # ... (oldingi kod o'zgarmadi)
        if os.path.exists(self.db_path):
            backup_path = f"{self.db_path}.bak"
            try:
                shutil.copyfile(self.db_path, backup_path)
                logging.info(f"Ma'lumotlar bazasi zaxira nusxasi yaratildi: {backup_path}")
            except IOError as e:
                logging.error(f"Ma'lumotlar bazasini zahiralashda xato: {e}")

    def _create_table(self):
        try:
            with sqlite3.connect(self.db_path, timeout=self.db_timeout) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS results (
                        username TEXT NOT NULL UNIQUE,
                        status TEXT NOT NULL,
                        checked_at TEXT NOT NULL
                    )
                """)
                conn.commit()
                logging.info("Ma'lumotlar bazasi jadvallari tayyor.")
        except sqlite3.Error as e:
            logging.critical(f"Ma'lumotlar bazasi jadvalini yaratishda xato: {e}")

    def _check_integrity(self):
        # ... (oldingi kod o'zgarmadi)
        try:
            with sqlite3.connect(self.db_path, timeout=self.db_timeout) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                result = cursor.fetchone()
                
                if result[0] == 'ok':
                    logging.info("Ma'lumotlar bazasi butunligi tekshiruvidan o'tdi.")
                else:
                    logging.critical(f"‼️ Jiddiy xato: Ma'lumotlar bazasi butunligi buzilgan: {result[0]}")
        except sqlite3.Error as e:
            logging.critical(f"‼️ Jiddiy xato: Ma'lumotlar bazasi butunligini tekshirishda xato yuz berdi: {e}")

    def save_result(self, username, status):
        try:
            with sqlite3.connect(self.db_path, timeout=self.db_timeout) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO results (username, status, checked_at) VALUES (?, ?, ?)",
                    (username, status, datetime.now().isoformat())
                )
                conn.commit()
        except sqlite3.IntegrityError:
            logging.warning(f"Username '{username}' ma'lumotlar bazasida allaqachon mavjud.")
        except sqlite3.Error as e:
            logging.error(f"Ma'lumotlar bazasiga yozishda xato yuz berdi: {e}")
