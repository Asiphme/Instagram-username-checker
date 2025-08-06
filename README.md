# Instagram Username Checker

Bu - Telegram orqali boshqariladigan, proksi yordamida Instagram foydalanuvchi nomlarini avtomatik tekshiruvchi skript. Loyiha asinxron operatsiyalar, maʼlumotlar bazasini boshqarish va xato qayta ishlash kabi professional amaliyotlarni oʻz ichiga oladi.

## ⚙️ Loyiha tuzilmasi

- `data/`: Kirish uchun fayllar joylashgan papka (`usernames.txt`, `proxies.txt`).
- `output/`: Natijalar, hisobotlar va metamaʼlumotlar saqlanadigan papka (`results.db`, `metrics.json`, `run_metadata.json`).
- `scripts/`: Loyihaning asosiy kodlari joylashgan papka.
- `logs/`: Faoliyat va xatoliklar yozib boriladigan fayllar (`checker.log`, `errors.log`).
- `.env`: Maxfiy maʼlumotlar va sozlamalar uchun fayl.
- `README.md`: Loyiha haqida asosiy maʼlumotlar.

## 🚀 Oʻrnatish

Loyihani ishga tushirish uchun quyidagi qadamlarni bajaring:

### 1. Kutubxonalarni oʻrnatish

Barcha kerakli kutubxonalarni oʻrnatish uchun quyidagi buyruqni kiriting:
```bash
pip install -r requirements.txt
