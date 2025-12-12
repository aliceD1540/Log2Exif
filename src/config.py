import json
import os

CONFIG_FILE = "config.json"

class Config:
    def __init__(self):
        self.json_path = ""
        self.source_folder = ""
        self.dest_folder = ""
        self.overwrite = False

    @staticmethod
    def load():
        config = Config()
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    config.json_path = data.get("json_path", "")
                    config.source_folder = data.get("source_folder", "")
                    config.dest_folder = data.get("dest_folder", "")
                    config.overwrite = data.get("overwrite", False)
            except Exception as e:
                print(f"Error loading config: {e}")
        return config

    def save(self):
        data = {
            "json_path": self.json_path,
            "source_folder": self.source_folder,
            "dest_folder": self.dest_folder,
            "overwrite": self.overwrite
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
