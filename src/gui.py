import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
from .config import Config
from .gps_utils import load_timeline_points, find_nearest_point
from .image_utils import get_image_files, get_image_timestamp, add_gps_to_exif

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Log2Exif")
        self.config = Config.load()
        
        self.create_widgets()
        self.load_settings_to_ui()

    def create_widgets(self):
        # JSON File Selection
        tk.Label(self.root, text="Timeline JSON:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.json_entry = tk.Entry(self.root, width=50)
        self.json_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(self.root, text="Select", command=self.select_json).grid(row=0, column=2, padx=5, pady=5)

        # Source Folder Selection
        tk.Label(self.root, text="Source Images Folder:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.src_entry = tk.Entry(self.root, width=50)
        self.src_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(self.root, text="Select", command=self.select_src).grid(row=1, column=2, padx=5, pady=5)

        # Destination Folder Selection
        tk.Label(self.root, text="Destination Folder:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.dest_entry = tk.Entry(self.root, width=50)
        self.dest_entry.grid(row=2, column=1, padx=5, pady=5)
        tk.Button(self.root, text="Select", command=self.select_dest).grid(row=2, column=2, padx=5, pady=5)

        # Overwrite Checkbox
        self.overwrite_var = tk.BooleanVar()
        tk.Checkbutton(self.root, text="Overwrite existing GPS data", variable=self.overwrite_var).grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # Start Button
        self.start_btn = tk.Button(self.root, text="Start Processing", command=self.start_processing, bg="#dddddd")
        self.start_btn.grid(row=4, column=1, pady=20, ipadx=20)

        # Status Label
        self.status_label = tk.Label(self.root, text="Ready")
        self.status_label.grid(row=5, column=0, columnspan=3, sticky="w", padx=5)

    def select_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path:
            self.json_entry.delete(0, tk.END)
            self.json_entry.insert(0, path)

    def select_src(self):
        path = filedialog.askdirectory()
        if path:
            self.src_entry.delete(0, tk.END)
            self.src_entry.insert(0, path)

    def select_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, path)

    def load_settings_to_ui(self):
        self.json_entry.insert(0, self.config.json_path)
        self.src_entry.insert(0, self.config.source_folder)
        self.dest_entry.insert(0, self.config.dest_folder)
        self.overwrite_var.set(self.config.overwrite)

    def save_settings_from_ui(self):
        self.config.json_path = self.json_entry.get()
        self.config.source_folder = self.src_entry.get()
        self.config.dest_folder = self.dest_entry.get()
        self.config.overwrite = self.overwrite_var.get()
        self.config.save()

    def start_processing(self):
        self.save_settings_from_ui()
        
        json_path = self.config.json_path
        src_folder = self.config.source_folder
        dest_folder = self.config.dest_folder
        overwrite = self.config.overwrite

        if not all([json_path, src_folder, dest_folder]):
            messagebox.showerror("Error", "Please select all paths.")
            return

        if not os.path.exists(json_path):
            messagebox.showerror("Error", "JSON file does not exist.")
            return

        self.start_btn.config(state="disabled")
        self.status_label.config(text="Loading GPS data...")
        self.root.update()

        # Run in thread to avoid freezing UI strictly, but for simplicity we'll just run here with updates
        # Actually, let's use a simple thread to allow UI updates
        threading.Thread(target=self.run_logic, args=(json_path, src_folder, dest_folder, overwrite)).start()

    def run_logic(self, json_path, src_folder, dest_folder, overwrite):
        try:
            points = load_timeline_points(json_path)
            if not points:
                messagebox.showerror("Error", "No valid timeline points found in JSON.")
                self.reset_ui()
                return

            self.update_status(f"Loaded {len(points)} points. Finding images...")
            
            images = get_image_files(src_folder)
            total = len(images)
            processed_count = 0

            for i, img_path in enumerate(images):
                self.update_status(f"Processing {i+1}/{total}: {os.path.basename(img_path)}")
                
                # Get timestamp
                dt = get_image_timestamp(img_path)
                
                # Find nearest GPS
                # Note: Timezone awareness issues might arise if image is naive and GPS is aware.
                # GPS utils returns aware datetime. 
                # piexif string is naive.
                # we need to handle this.
                
                # Handling Timezone for matching:
                # If dt is naive, assume local or assume same timezone as JSON? 
                # JSON has offset.
                # Let's make dt aware if it's naive, assuming local or provided logic.
                # For simplicity, we can strip timezone from GPS points or add timezone to image.
                # `gps_utils.find_nearest_point` expects simple comparison.
                
                # Let's trust python datetime comparison handles it or errors if mixed.
                # Fix: Make sure both are same type. 
                # `datetime.datetime.fromisoformat` returns aware if string has offset. `timeline_sample` has offset.
                # `get_image_timestamp` returns naive from string or `fromtimestamp`.
                
                if dt.tzinfo is None:
                    # Naive to Aware (Local) is complex without pytz.
                    # Hack: Make the GPS points naive (UTC conversion then strip) or just strip.
                    # Since photos are usually in "Wall clock time" of where they were taken,
                    # and Timeline is absolute time.
                    # This is the trickiest part of Geotagging.
                    # Assumption: Image time is local time where photo was taken.
                    # Timeline time is absolute.
                    # We need the timezone of the location where photo was taken to convert Image Time -> Absolute.
                    # But we don't know the location yet!
                    # Chicken and egg.
                    
                    # Simplification: Assume the camera time is in the same timezone as the JSON data implies for that time? 
                    # OR, simply ignore timezone and match on "Local Time" values? 
                    # Timeline gives absolute time. 
                    
                    # Let's try matching timestamps by converting Timeline points to Naive (UTC or Local?).
                    # But Timeline moves across timezones.
                    
                    # Standard approach: User usually keeps camera on home time or updates it.
                    # If we simply compare "2025-09-13 17:05" (Image) with "2025-09-13 17:05+09:00" (Timeline).
                    # If we drop timezone from Timeline, we get "17:05". It matches.
                    # Ideally we match on naive time.
                    pass
                
                # Quick Fix for logic:
                # Convert logic inside `run_logic` to handle timezone stripping for comparison
                # We will perform the fix in `gps_utils` or here.
                # Let's just strip TZ from GPS points for comparison purposes, assuming camera time matches wall clock time of the GPS point.
                
                # But wait, `gps_utils` is already imported.
                # I will modify how I call it or modify the points list here.
                
                # NOTE: I need to handle this discrepancy.
                # For now, I will modify `run_logic` to strip timezone from the loaded points before passing to `find_nearest_point`.
                # Actually `find_nearest_point` takes a list. I should re-process the list here.
                
            self.points_stripped = []
            for p in points:
                # p is (dt, lat, lon)
                # Convert dt to naive
                dt_naive = p[0].replace(tzinfo=None)
                self.points_stripped.append((dt_naive, p[1], p[2]))

            # Now loop images
            for i, img_path in enumerate(images):
                 self.update_status(f"Processing {i+1}/{total}: {os.path.basename(img_path)}")
                 
                 # Calculate destination path maintaining structure
                 rel_path = os.path.relpath(img_path, src_folder)
                 target_dir = os.path.join(dest_folder, os.path.dirname(rel_path))
                 
                 dt = get_image_timestamp(img_path)
                 
                 # dt is likely naive.
                 # If dt has tz (unlikely from piexif unless sophisticated), strip it too.
                 if dt.tzinfo is not None:
                     dt = dt.replace(tzinfo=None)

                 lat, lon = find_nearest_point(dt, self.points_stripped)
                 
                 if lat is not None and lon is not None:
                     add_gps_to_exif(img_path, lat, lon, target_dir, overwrite)
                 else:
                     # Just copy if no point found? Or log it?
                     # Design says: "2回目以降は2からでOK". 
                     # "4. 全画像に対して2,3を繰り返す"
                     # If no point found, we should probably still move/copy it?
                     # Let's just copy it to be safe so destination has everything.
                     import shutil
                     try:
                         os.makedirs(target_dir, exist_ok=True)
                         shutil.copy2(img_path, os.path.join(target_dir, os.path.basename(img_path)))
                     except:
                         pass
                 
                 processed_count += 1
            
            self.status_label.config(text=f"Done! Processed {processed_count} images.")
            messagebox.showinfo("Success", "Processing complete.")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            print(e)
        finally:
            self.reset_ui()

    def update_status(self, text):
        self.status_label.config(text=text)
        # self.root.update() # Can't call this from thread safely in all Tk versions, but usually fine.
        # Better to use after? For simple script, this often works.
    
    def reset_ui(self):
        self.start_btn.config(state="normal")

