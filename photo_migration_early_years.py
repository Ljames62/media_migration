import json
import os
import re
import subprocess

import dateutil
from dateutil import parser

from datetime import datetime
from pathlib import Path
from PIL import Image, ExifTags

DEFAULT_DATE = datetime(1900, 1, 1, 0, 0, 0)
DEFAULT_YEAR = DEFAULT_DATE.strftime("%Y")

FOLDER_PATH = Path(r"C:\Users\johnk\Downloads\Stage")
BASE_GOOGLE_DRIVE_PATH = "etavern_gdrive:Media"

NAME_LIST = [
    "alex",
    "ginnie",
    "john",
    "oscar",
    "lorene",    
    "bob",
    "marlene",
    "doug",
    "lisa",
    "cameron",
    "kyle",
    "jackson",
    "beth",
    "don",
    "sam",
    "keith",
    "nikki",
    "june",
    "aunt june",
    "joe",
    "sandy",
    "carin",
    "laura",    
    "ann",
    "patty"
]

MONTH_LIST = [
    "january", "february", "march", "april",
    "may", "june", "july", "august",
    "september", "october", "november", "december"
]

def cleanup_duplicate_r_files(folder_path: Path):
    # We convert to a list so we aren't mutating the directory while iterating over the live generator
    files = [f for f in folder_path.iterdir() if f.is_file()]

    for file_a in files:
        for file_b in files:
            # Skip comparing the file to itself
            if file_a == file_b:
                continue
            
            # Check if both files exist (in case one was deleted in a previous loop)
            if not file_a.exists() or not file_b.exists():
                continue

            # Logic: 
            # 1. Extensions must match (e.g., both .jpg or both .txt)
            # 2. file_b stem must be file_a stem + "r"
            # Example: file_a = "photo.jpg", file_b = "photor.jpg"
            
            if (file_a.suffix.lower() == file_b.suffix.lower() and 
                file_b.stem == file_a.stem + "r"):
                
                try:
                    print(f"Deleting duplicate: {file_b.name} (Original: {file_a.name})")
                    file_b.unlink()
                except Exception as e:
                    print(f"Error deleting {file_b.name}: {e}")

def capitalize_first_letter(text: str) -> str:
    for i, ch in enumerate(text):
        if ch.isalpha():
            return text[:i] + ch.upper() + text[i + 1:]
    return text

def capitalize_words(text: str, words: list[str]) -> str:
    for name in sorted(words, key=len, reverse=True):
        pattern = re.compile(rf'\b{re.escape(name)}\b', re.IGNORECASE)
        text = pattern.sub(name.title(), text)
    return text

def get_photo_date_time_original(photo_path: Path) -> datetime:
    try:
        with Image.open(photo_path) as img:
            exif = img._getexif()
            if not exif:
                raise ValueError("No EXIF data")

            # Find DateTimeOriginal tag
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id)
                if tag == "DateTimeOriginal":
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                
    except Exception:
        return datetime.fromtimestamp(os.path.getmtime(photo_path))

def detect_year_from_folder(folder_path: Path, default_year=DEFAULT_YEAR) -> str:
    years = []

    for file_path in folder_path.iterdir():
        if not file_path.is_file():
            continue

        try:
            date = get_photo_date_time_original(file_path)
            years.append(date.year)
        except Exception:
            pass

    return str(min(years, default=DEFAULT_YEAR))

def strip_leading_number_prefix(name: str) -> str:
    if not name or not name[0].isdigit():
        return name

    for i, ch in enumerate(name):
        if ch.isspace():
            return name[i + 1:]  # strip up to and including first whitespace

    return name  # no whitespace found

def rename_files_with_rules(folder_path: Path, GROUP_NAME: str):
    extension_mapping = {
        '.jpeg': '.jpg',
    }

    for file_path in folder_path.iterdir():
        if not file_path.is_file():
            continue

        stem = file_path.stem

        # Replace gin -> Ginnie (case-insensitive)
        stem = re.sub(r'gin(?![A-Za-z])', 'Ginnie', stem, flags=re.IGNORECASE)

        # Replace me -> Ginnie (case-insensitive)
        stem = re.sub(r'me(?![A-Za-z])', 'Ginnie', stem, flags=re.IGNORECASE)

        # Replace vac -> vacation (case-insensitive)
        stem = re.sub(r'vac(?![A-Za-z])', 'vacation', stem, flags=re.IGNORECASE)

        # Remove unwanted characters (keep letters, numbers, space)
        stem = re.sub(r'[^A-Za-z0-9 ]+', '', stem)

        # Capitalize first letter only
        if stem:
            stem = capitalize_first_letter(stem)

        # Capitalize names
        stem = capitalize_words(stem, NAME_LIST)
        
        # Capitalize months
        stem = capitalize_words(stem, MONTH_LIST)

        # Remove (A, B, or C) OR (space followed by a digit) at the end of the string
        stem = re.sub(r'([ABC]|\s\d)$', '', stem)

        # Final cleanup
        stem = re.sub(r'\s+', ' ', stem).strip()

        # Add datetime stamp to filename
        dt = get_photo_date_time_original(file_path)

        timestamp = dt.strftime("%Y%m%d_%H%M%S")
        clean_stem = strip_leading_number_prefix(stem)

        if not GROUP_NAME:
            base_name = f"{timestamp} - {clean_stem}"
        else:
            base_name = f"{timestamp} - {GROUP_NAME} - {clean_stem}"

        ext = file_path.suffix.lower()

        if ext in extension_mapping:
            ext = extension_mapping[ext]

         # Create the new filename
        new_file_path = file_path.with_name(base_name + ext)

        # update filename
        if new_file_path.name != file_path.name:
            file_path.rename(new_file_path)
            print(f"{file_path.name} → {new_file_path.name}")

def run_exiftool_date_update(folder_path: Path, new_date: str):
    cmd = [
        "exiftool",
        f"-AllDates={new_date}",
        "-overwrite_original",
        str(folder_path)
    ]

    print("Running ExifTool date update...")
    subprocess.run(cmd, check=True)
    print("ExifTool date update completed.")

def run_exiftool_date_sync(folder_path: Path):
    cmd = [
        "exiftool",
        # 1. First, try to sync everything to the File's System Modified Date (the fallback)
        "-AllDates<FileModifyDate",
        "-FileCreateDate<FileModifyDate",
        
        # 2. Then, try to sync everything to DateTimeOriginal. If this exists, it will overwrite the assignments above.
        "-AllDates<DateTimeOriginal",
        "-FileModifyDate<DateTimeOriginal",
        "-FileCreateDate<DateTimeOriginal",
        
        "-overwrite_original",
        #"-ext", "jpg", "-ext", "mp4", "-ext", "mov", # Add extensions you want to target
        str(folder_path)
    ]

    print("Running ExifTool date sync...")
    subprocess.run(cmd, check=True)
    print("ExifTool date sync completed.")

def run_exiftool_date_increment(folder_path: Path):
    cmd = [
        "exiftool",
        "-AllDates+<0:0:${filesequence;$_*=60}",
        "-FileCreateDate+<0:0:${filesequence;$_*=60}",
        "-FileModifyDate+<0:0:${filesequence;$_*=60}",
        "-fileorder", "FileName",
        "-overwrite_original",
        str(folder_path)
    ]

    print("Running ExifTool date increment...")
    subprocess.run(cmd, check=True)
    print("ExifTool date increment completed.")    

def run_rclone_move(folder_path: Path, google_drive_path: str):
    cmd = [
        "rclone", "move",
        str(folder_path),
        google_drive_path,
        "--fast-list",
        "--drive-chunk-size", "64M",
        "--buffer-size", "32M",
        "--checkers=16",
        "--transfers=8",
        "--metadata",
        #"--modify-window", "1s",
        "--checksum",
        "--progress"
    ]

    print(f"Running rclone move: {folder_path} → {google_drive_path}")
    subprocess.run(cmd, check=True)
    print("rclone move completed.")

NEW_DATE = "1999:01:14 10:01:00" # For folder without Date taken
GROUP_NAME = ""

def main():
  cleanup_duplicate_r_files(FOLDER_PATH)
  year = detect_year_from_folder(FOLDER_PATH)
  print(f"Folder Year: {year}")

  if year == DEFAULT_YEAR:
   run_exiftool_date_update(FOLDER_PATH, NEW_DATE)
   run_exiftool_date_sync(FOLDER_PATH)
   run_exiftool_date_increment(FOLDER_PATH)
  else:
   run_exiftool_date_sync(FOLDER_PATH)

  rename_files_with_rules(FOLDER_PATH, GROUP_NAME)  

  year = detect_year_from_folder(FOLDER_PATH)
  print(f"Google Path Folder Year: {year}")
  google_drive_path = f"{BASE_GOOGLE_DRIVE_PATH}/{year}"
  run_rclone_move(FOLDER_PATH, google_drive_path)
 
if __name__ == "__main__":
  main()