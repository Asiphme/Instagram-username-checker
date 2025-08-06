# scripts/username_checker.py

import httpx
import logging
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, before_sleep_log
from httpx import ReadTimeout, ConnectError, HTTPStatusError
import random

checker_logger = logging.getLogger(__name__)

# Turli xil User-Agentlar ro'yxati
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36",
]

async def check_username(username: str, proxy: str) -> str:
    url = f"https://www.instagram.com/{username}/"
    headers = {
        'User-Agent': random.choice(USER_AGENTS) # User-Agent rotatsiyasi
    }
    
    try:
        async with httpx.AsyncClient(proxies={'http://': proxy, 'https://': proxy},
                                     timeout=15,
                                     follow_redirects=True) as client:
            checker_logger.info(f"Tekshirilmoqda: {username} (proksi: {proxy})")
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            if "Page Not Found" in response.text:
                return 'available'
            else:
                return 'taken'
    except (ReadTimeout, ConnectError) as e:
        checker_logger.error(f"Username {username}ni tekshirishda tarmoq xatosi: {e}")
        raise
    except HTTPStatusError as e:
        if e.response.status_code == 429:
            checker_logger.warning(f"Username {username} uchun 'Too Many Requests' (429) xatosi.")
            raise
        else:
            checker_logger.error(f"Username {username} uchun HTTP status xatosi: {e}")
            return None
    except Exception as e:
        checker_logger.critical(f"Kutilmagan xato yuz berdi: {e}")
        raise

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ReadTimeout, ConnectError, HTTPStatusError)),
    before_sleep=before_sleep_log(checker_logger, logging.WARNING)
)
async def check_username_with_retries(username: str, proxy: str) -> str:
    return await check_username(username, proxy)

