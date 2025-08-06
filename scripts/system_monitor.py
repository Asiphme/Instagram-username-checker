# scripts/system_monitor.py

import psutil
import shutil
import logging

def get_system_status(disk_threshold=10, ram_threshold=90, cpu_threshold=90):
    """
    Tizim resurslari (disk, RAM, CPU) holatini tekshiradi.
    Biron bir resurs belgilangan chegara (threshold) dan oshsa, ogohlantirish matnini qaytaradi.
    """
    alerts = []

    # Disk holatini tekshirish
    try:
        total, used, free = shutil.disk_usage("/")
        percent_free = (free / total) * 100
        if percent_free < disk_threshold:
            alerts.append(f"❗Diskda bo'sh joy kam: {percent_free:.2f}% qoldi!")
            logging.warning(f"Diskda bo'sh joy kam: {percent_free:.2f}% qoldi.")
    except Exception as e:
        logging.error(f"Disk holatini tekshirishda xato yuz berdi: {e}")

    # RAM holatini tekshirish
    try:
        ram = psutil.virtual_memory()
        if ram.percent > ram_threshold:
            alerts.append(f"❗RAM to'lib bormoqda: {ram.percent}% ishlatilmoqda!")
            logging.warning(f"RAMdan foydalanish yuqori: {ram.percent}%.")
    except Exception as e:
        logging.error(f"RAM holatini tekshirishda xato yuz berdi: {e}")

    # CPU holatini tekshirish (1 soniya davomida)
    try:
        if psutil.cpu_percent(interval=1) > cpu_threshold:
            alerts.append("❗CPUdan foydalanish juda yuqori!")
            logging.warning("CPUdan foydalanish juda yuqori.")
    except Exception as e:
        logging.error(f"CPU holatini tekshirishda xato yuz berdi: {e}")

    return alerts

