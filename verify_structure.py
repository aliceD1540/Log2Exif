import os
import datetime
import shutil
from PIL import Image
from src.gui import App # Import to test method indirectly or just emulate logic?
# Since logic is in App.run_logic, and it's coupled with UI, I'll emulate the logic block exactly as I changed it.

def create_dummy_image(path, timestamp):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new('RGB', (100, 100), color = 'red')
    
    # Set DateTimeOriginal (36867)
    import piexif
    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    time_str = timestamp.strftime("%Y:%m:%d %H:%M:%S")
    exif_dict["Exif"][36867] = time_str.encode('utf-8')
    exif_bytes = piexif.dump(exif_dict)
    
    img.save(path, "jpeg", exif=exif_bytes)

def verify_folder_structure():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_folder = os.path.join(base_dir, "test_input")
    dest_folder = os.path.join(base_dir, "test_output")

    # Cleanup
    if os.path.exists(src_folder): shutil.rmtree(src_folder)
    if os.path.exists(dest_folder): shutil.rmtree(dest_folder)

    # 1. Create Structure
    # src/20251201/A.jpg
    # src/B.jpg
    sub_dir = os.path.join(src_folder, "20251201")
    img_a = os.path.join(sub_dir, "A.jpg")
    img_b = os.path.join(src_folder, "B.jpg")
    
    create_dummy_image(img_a, datetime.datetime(2025, 9, 13, 17, 5, 0)) # Should match
    create_dummy_image(img_b, datetime.datetime(2025, 1, 1, 0, 0, 0))   # Should not match (copy)

    # 2. Emulate Logic (simplified from gui.py)
    # We need to test the path calculation logic specifically.
    
    from src.image_utils import get_image_files, add_gps_to_exif
    
    images = get_image_files(src_folder)
    print(f"Found images: {images}")
    
    for img_path in images:
        rel_path = os.path.relpath(img_path, src_folder)
        target_dir = os.path.join(dest_folder, os.path.dirname(rel_path))
        
        # Determine if we match (Mocking the GPS lookup for simplicity)
        # IF A.jpg (has time matching sample data, but let's just force add_gps_to_exif for A)
        
        if "A.jpg" in img_path:
             # Add GPS
             add_gps_to_exif(img_path, 35.0, 139.0, target_dir)
        else:
             # Copy
             os.makedirs(target_dir, exist_ok=True)
             shutil.copy2(img_path, os.path.join(target_dir, os.path.basename(img_path)))

    # 3. Verify
    dest_a = os.path.join(dest_folder, "20251201", "A.jpg")
    dest_b = os.path.join(dest_folder, "B.jpg")
    
    if os.path.exists(dest_a):
        print("Structure Test A (Subdir): OK")
    else:
        print(f"Structure Test A (Subdir): FAIL. Expected {dest_a}")

    if os.path.exists(dest_b):
        print("Structure Test B (Root): OK")
    else:
        print(f"Structure Test B (Root): FAIL. Expected {dest_b}")

if __name__ == "__main__":
    verify_folder_structure()
