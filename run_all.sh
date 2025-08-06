#!/bin/bash

# Loyihaning asosiy papkasiga o'tish
cd "$(dirname "$0")" || exit

# Loglarni tozalash va arxivlash
./log_cleanup.sh

# Python skriptini ishga tushirish
python scripts/run_all.py
