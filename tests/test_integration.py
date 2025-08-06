import os
import shutil
import pytest
from unittest.mock import patch
import responses
import tempfile
import asyncio
from pathlib import Path
import sqlite3

# Loyiha papkasini PYTHONPATHga qo'shamiz
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Kerakli modullarni import qilish
from scripts.run_all import main as run_main
from scripts.db_manager import DBManager

# Asosiy test funksiyasi
@responses.activate
@pytest.mark.asyncio
async def test_end_to_end_integration():
    """
    Loyiha ish oqimini to'liq sinovdan o'tkazadi:
    Fayllar yaratish -> Checker ishga tushirish -> Natijalarni tekshirish.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        base = Path(temp_dir)
        
        # Test uchun fayl va papkalar yaratish
        (base / "data").mkdir()
        (base / "output").mkdir()
        (base / "logs").mkdir()

        # Test fayllarini yo'lini belgilash
        proxies_path = base / "data" / "proxies.txt"
        usernames_path = base / "data" / "usernames.txt"
        db_path = base / "output" / "results.db"
        metadata_path = base / "output" / "run_metadata.json"
        log_path = base / "logs" / "checker.log"

        # Test ma'lumotlarini fayllarga yozish
        proxies_path.write_text("http://127.0.0.1:8080\n")
        usernames_path.write_text("available_user\ntaken_user\n")

        # Soxta (mock) javoblarni sozlash
        responses.add(
            responses.GET,
            "https://www.instagram.com/available_user/",
            body="Page Not Found",
            status=200
        )
        responses.add(
            responses.GET,
            "https://www.instagram.com/taken_user/",
            body="<body>User Profile Page</body>",
            status=200
        )

        # .env faylini soxtalashtirish
        with patch.dict(os.environ, {
            'PROXY_LIST_PATH': str(proxies_path),
            'USERNAME_LIST_PATH': str(usernames_path),
            'OUTPUT_DB_PATH': str(db_path),
            'METADATA_PATH': str(metadata_path),
            'LOG_FILE_PATH': str(log_path),
        }):
            # Asosiy funksiyani ishga tushirish
            await run_main()

        # ----------------- Natijalarni tekshirish -----------------

        # 1. DB fayli yaratilganini tekshirish
        assert db_path.exists(), "Natija ma'lumotlar bazasi yaratilmagan"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 2. Ma'lumotlar bazasi integrity checkdan o'tganini tekshirish
        cursor.execute("PRAGMA integrity_check;")
        assert cursor.fetchone()[0] == 'ok', "Ma'lumotlar bazasi buzilgan"
        
        # 3. Yozuvlar sonini va holatini tekshirish
        cursor.execute("SELECT username, status FROM results ORDER BY username")
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 2, f"2 ta yozuv kutilgan, topilgani: {len(rows)}"
        assert rows[0] == ('available_user', 'available')
        assert rows[1] == ('taken_user', 'taken')

        # 4. Log fayli yaratilganini tekshirish
        assert log_path.exists(), "Log fayli yaratilmagan"
        log_content = log_path.read_text()
        assert "Loyiha muvaffaqiyatli yakunlandi!" in log_content
        assert "Ma'lumotlar bazasi butunligi tekshiruvidan o'tdi." in log_content

        # 5. Metadata fayli yaratilganini tekshirish
        assert metadata_path.exists(), "Metadata fayli yaratilmagan"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            assert metadata['total_usernames_checked'] == 2

