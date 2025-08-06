#!/bin/bash

# Log fayllari joylashgan papka
LOG_DIR="logs/"

# 7 kundan eski log fayllarni zip qilib arxivlash
find "$LOG_DIR" -type f -name "*.log" -mtime +7 -exec gzip {} \;

# 30 kundan eski log fayllarni o'chirish
find "$LOG_DIR" -type f -name "*.gz" -mtime +30 -exec rm {} \;

echo "Eski loglar tozalandi va arxivlandi."
