import os
import shutil
import datetime
from PIL import Image
import piexif

def get_image_timestamp(image_path):
    """
    Reads local file time or basic EXIF DateTime.
    Returns datetime object.
    Priority: EXIF DateTimeOriginal > EXIF DateTime > File Modified Time
    """
    try:
        img = Image.open(image_path)
        exif_dict = piexif.load(img.info.get("exif", b""))
        
        # 36867 is DateTimeOriginal, 306 is DateTime
        time_str = None
        if 36867 in exif_dict.get("Exif", {}):
            time_str = exif_dict["Exif"][36867].decode('utf-8')
        elif 306 in exif_dict.get("0th", {}):
            time_str = exif_dict["0th"][306].decode('utf-8')

        if time_str:
            # EXIF format is "YYYY:MM:DD HH:MM:SS"
            return datetime.datetime.strptime(time_str, "%Y:%m:%d %H:%M:%S")
    except Exception as e:
        # print(f"Warning: Could not read EXIF for {image_path}: {e}")
        pass

    # Fallback to file system time
    timestamp = os.path.getmtime(image_path)
    return datetime.datetime.fromtimestamp(timestamp)

def to_deg(value, loc):
    """
    Converts decimal coordinates to EXIF rational format (Degrees, Minutes, Seconds)
    """
    if value < 0:
        loc_value = loc[1]
    else:
        loc_value = loc[0]
    
    abs_value = abs(value)
    deg = int(abs_value)
    t1 = (abs_value - deg) * 60
    min = int(t1)
    sec = round((t1 - min) * 60, 4) # Rounding to 4 decimal places for precision

    # Function to convert float to fraction (num, den) tuple
    def to_fraction(val):
        val = int(val * 10000)
        return (val, 10000)

    return (
        ((deg, 1), (min, 1), to_fraction(sec)),
        loc_value
    )

def add_gps_to_exif(image_path, lat, lon, dest_folder, overwrite=False):
    """
    Adds GPS data to the image and saves it to dest_folder.
    If GPS already exists:
      - if overwrite is True: replace it.
      - if overwrite is False: skip (copy original?). 
        Design says: "Positions that are already set -> Checkbox to overwrite".
        Implies if not checked, don't overwrite.
    """
    try:
        os.makedirs(dest_folder, exist_ok=True)
        filename = os.path.basename(image_path)
        dest_path = os.path.join(dest_folder, filename)

        img = Image.open(image_path)
        try:
            exif_dict = piexif.load(img.info.get("exif", b""))
        except:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

        # Check if GPS exists
        has_gps = bool(exif_dict.get("GPS"))
        
        if has_gps and not overwrite:
            # Just move/copy without changes
            # Design says "Move processed files".
            # If we don't process, do we move?
            # Design: "3. 処理の終わった画像ファイルを処理後フォルダに移動する" (Move processed image files)
            # If configured NOT to overwrite, and it has GPS, strictly speaking it's not "processed" with new data.
            # However, typically users want *all* files in the destination.
            # Let's assume we maintain the file as is but move it.
            # But 'move' is destructive to source.
            pass
        else:
            # Create GPS data
            lat_deg = to_deg(lat, ["N", "S"])
            lon_deg = to_deg(lon, ["E", "W"])

            # GPS tag IDs: 1: LatRef, 2: Lat, 3: LonRef, 4: Lon
            exif_dict["GPS"][1] = lat_deg[1].encode('utf-8')
            exif_dict["GPS"][2] = lat_deg[0]
            exif_dict["GPS"][3] = lon_deg[1].encode('utf-8')
            exif_dict["GPS"][4] = lon_deg[0]
            
            # Write EXIF
            exif_bytes = piexif.dump(exif_dict)
            
            # Save to new location
            img.save(dest_path, "jpeg", exif=exif_bytes)
            return True, dest_path  # Processed and saved

        # If we didn't save above (because has_gps and not overwrite), we copy the original.
        shutil.copy2(image_path, dest_path)
        return False, dest_path

    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return False, None

def get_image_files(folder):
    """
    Recursively finds all JPEG images in a folder.
    """
    extensions = {".jpg", ".jpeg", ".JPG", ".JPEG"}
    image_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if os.path.splitext(file)[1] in extensions:
                image_files.append(os.path.join(root, file))
    return image_files
