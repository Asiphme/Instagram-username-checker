# scripts/report_manager.py

import sqlite3
import logging
import json
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

class ReportManager:
    """
    Ma'lumotlar bazasidan hisobotlar yaratish uchun klass.
    """
    def __init__(self, db_path, templates_dir="templates"):
        self.db_path = db_path
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        self.template = self.env.get_template('report_template.html')

    def generate_report(self):
        """
        Ma'lumotlar bazasidan hisobot yaratadi va uni metrics.json va report.html fayllariga yozadi.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Natijalar sonini olish
                cursor.execute("SELECT COUNT(*) FROM results")
                total_checked = cursor.fetchone()[0]

                # Mavjud va band username'lar sonini olish
                cursor.execute("SELECT status, COUNT(*) FROM results GROUP BY status")
                status_counts = dict(cursor.fetchall())
                
                available_count = status_counts.get('available', 0)
                taken_count = status_counts.get('taken', 0)
                
                # Eng eski va eng yangi tekshirilgan vaqtni olish
                cursor.execute("SELECT MIN(checked_at), MAX(checked_at) FROM results")
                start_time_iso, end_time_iso = cursor.fetchone()

                start_time = datetime.fromisoformat(start_time_iso) if start_time_iso else None
                end_time = datetime.fromisoformat(end_time_iso) if end_time_iso else None
                
                duration = 0
                performance = 0
                if start_time and end_time:
                    duration = (end_time - start_time).total_seconds()
                    if duration > 0:
                        performance = total_checked / duration

                report_data = {
                    "start_time": start_time_iso,
                    "end_time": end_time_iso,
                    "duration_seconds": round(duration, 2),
                    "total_checked": total_checked,
                    "available_count": available_count,
                    "taken_count": taken_count,
                    "performance_usernames_per_second": round(performance, 2)
                }

                # Hisobotni JSON faylga yozish
                output_dir = os.path.dirname(self.db_path)
                metrics_path = os.path.join(output_dir, "metrics.json")
                with open(metrics_path, 'w') as f:
                    json.dump(report_data, f, indent=4)
                
                logging.info(f"JSON hisobot muvaffaqiyatli yaratildi: {metrics_path}")

                # Hisobotni HTML faylga yozish
                cursor.execute("SELECT username, status FROM results ORDER BY checked_at DESC LIMIT 50")
                results_list = [{"username": row[0], "status": row[1]} for row in cursor.fetchall()]
                
                html_report_path = os.path.join(output_dir, "report.html")
                html_output = self.template.render(
                    total_checked=total_checked,
                    available_count=available_count,
                    taken_count=taken_count,
                    start_time=start_time_iso,
                    end_time=end_time_iso,
                    duration_seconds=duration,
                    performance_usernames_per_second=performance,
                    results=results_list
                )
                with open(html_report_path, 'w', encoding='utf-8') as f:
                    f.write(html_output)
                
                logging.info(f"HTML hisobot muvaffaqiyatli yaratildi: {html_report_path}")

        except sqlite3.Error as e:
            logging.error(f"Hisobot yaratishda ma'lumotlar bazasi xatosi: {e}")
        except Exception as e:
            logging.error(f"Hisobot yaratishda kutilmagan xato: {e}")
