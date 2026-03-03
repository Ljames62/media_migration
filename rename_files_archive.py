from pathlib import Path
import os
from datetime import datetime
from PIL import Image, ExifTags

FOLDER_PATH = Path(r"C:\Users\johnk\Downloads\Stage")

def get_date_taken(file_path: Path) -> datetime:
    try:
        with Image.open(file_path) as img:
            exif = img._getexif()
            if not exif:
                raise ValueError("No EXIF data")

            # Find DateTimeOriginal tag
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id)
                if tag == "DateTimeOriginal":
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass

    # Fallback: last modified time
    return datetime.fromtimestamp(os.path.getmtime(file_path))

def strip_leading_number_prefix(name: str) -> str:
    if not name or not name[0].isdigit():
        return name

    for i, ch in enumerate(name):
        if ch.isspace():
            return name[i + 1:]  # strip up to and including first whitespace

    return name  # no whitespace found

def rename_files_in_folder(folder_path):
    for file_path in folder_path.iterdir():
        if not file_path.is_file():
            continue

        dt = get_date_taken(file_path)

        timestamp = dt.strftime("%Y%m%d_%H%M%S")
        clean_stem = strip_leading_number_prefix(file_path.stem)
        base_name = f"{timestamp} - {clean_stem}"
        #base_name = f"{timestamp} - {file_path.stem}"
        new_file_path = file_path.with_name(base_name + file_path.suffix)

        # Handle duplicate filenames
        counter = 1
        while new_file_path.exists():
            new_file_path = file_path.with_name(
                f"{base_name}_{counter}{file_path.suffix}"
            )
            counter += 1

        #file.rename(new_file)
        print(f"{file_path.name} → {new_file_path.name}")

def main():
  rename_files_in_folder(FOLDER_PATH)

if __name__ == "__main__":
  main()