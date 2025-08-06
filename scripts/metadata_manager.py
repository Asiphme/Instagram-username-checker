import os
import json
import logging
from datetime import datetime

class MetadataManager:
    def __init__(self, metadata_path):
        self.metadata_path = metadata_path
        self.metadata = self._load_metadata()

    def _load_metadata(self):
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logging.error(f"Metadata faylini yuklashda xato: {e}. Yangi fayl yaratilmoqda.")
                return self._default_metadata()
        else:
            return self._default_metadata()

    def _default_metadata(self):
        return {
            "last_run_time": datetime.now().isoformat(),
            "total_usernames_checked": 0,
            "last_checked_username": None,
            "status": "initial"
        }

    def save_metadata(self):
        try:
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=4)
            logging.info("Metadata muvaffaqiyatli saqlandi.")
        except IOError as e:
            logging.error(f"Metadata faylini saqlashda xato: {e}")

    def update_metadata(self, key, value):
        self.metadata[key] = value

    def get_metadata(self, key):
        return self.metadata.get(key)
