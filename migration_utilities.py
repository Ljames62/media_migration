import json
import olefile
import os
import re
import subprocess

import dateutil
import shutil
from dateutil import parser

from datetime import datetime
from pathlib import Path
from PIL import Image, ExifTags

import pywintypes
import win32file
import win32con

PHOTO_EXTENSIONS = [    
    '.jpg', '.jpeg', '.tiff', '.tif', # Formats with strong EXIF support
    '.png', '.webp',                  # Supported, but metadata varies by source
    '.heic', '.heif',                 # Modern Mobile Formats (Requires modern Pillow versions)
    '.bmp'                            # Standard Bitmap
]

VIDEO_EXTENSIONS = [
    '.mp4', '.mkv', '.mov', '.m4v',            # Modern Universal
    '.webm', '.flv', '.ogv',                   # Web Optimized
    '.avi', '.wmv', '.asf',                    # Windows Legacy
    '.mpg', '.mpeg', '.mts', '.m2ts', '.vob',  # Camera/Disc Raw
    '.3gp'                                     # Mobile Legacy
]

DATE_FORMATS = [
    '%Y-%m-%dT%H:%M:%S%z',     # ISO 8601 with Timezones (+0500)
    '%Y-%m-%dT%H:%M:%S.%f%z',  # ISO 8601 with Timezones and subseconds (+0500)
    '%Y-%m-%dT%H:%M:%SZ',      # ISO 8601 with UTC (Z)
    '%Y:%m:%d %H:%M:%S.%f',    # EXIT with subseconds

    '%Y:%m:%d %H:%M:%S',       # EXIF
    '%Y-%m-%d %H:%M:%S',       # Common datetime format 
    '%Y-%m-%dT%H:%M:%S',       # ISO 8601
    '%Y/%m/%d %H:%M:%S',       # Alternative with slashes
     
    '%m.%d.%Y %H:%M',          # US (day.month.year hour:minute)
    '%d.%m.%Y %H:%M',          # European (day.month.year hour:minute)
    '%Y:%m:%d %H:%M',          # EXIF without seconds
    '%Y-%m-%dT%H:%M',          # ISO 8601 without seconds
    '%Y-%m-%d %H:%M',          # Common datetime format without seconds
    '%Y/%m/%d %H:%M',          # Alternative with slashes without seconds
    '%Y%m%d_%H%M%S'            # smartphone apps filename date IMG_20230101_120000.jpg
]

FOLDER_PATH = Path(rf'C:\Users\johnk\Downloads\Stage\2008 0228 Birthday')
GOOGLE_FOLDER = rf'etavern_gdrive:Media/2007.7-2008.6 1st 6-7'

# Step 3 and 4 Find files in A that are NOT in B
COMPARE_FOLDER_A_PATH = Path(rf'C:\Users\johnk\Downloads\PicLoadQueue\2007.7-2008.6 1st 6-7')
COMPARE_FOLDER_B_PATH = Path(rf'J:\My Drive\Pictures\2007.7-2008.6 1st 6-7')
COMPARE_TYPE = 'photos'
#COMPARE_TYPE = 'videos'

# Step 7 Copy with rclone
SOURCE_FOLDER = r'J:\My Drive\Media\2006.7-2007.6 K 5-6'
DEST_FOLDER = r'D:\Media\2006.7-2007.6 K 5-6'

NEW_DATE = '2008:05:03 10:01:00' # Not coded yet. For files without date taken or creation date
GROUP_NAME = ''

# 1=Update timestamps 2=Update timestamps recursive 3=Flatten folders
# 4=Compare 5=Compare recursive 6=Rename 7=Rename recursive
# 8-Rename Remote 9=Move with rclone 10=Copy with rclone
step = 2

def parse_date(value):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    
    print(f"Could not parse date string: {value}")
    return None

def get_photo_date_time_original(photo_path: Path) -> datetime:
    try:
        cmd = [
            'exiftool',
            '-j',
            '-G',
           '-time:all',
           str(photo_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)        
        metadata = json.loads(result.stdout)

        if metadata:
            tags = metadata[0]
            if 'EXIF:DateTimeOriginal' in tags:
                val = tags['EXIF:DateTimeOriginal']
                print(f'Found EXIF DateTimeOriginal for {photo_path.name}: {val}')
            elif 'EXIF:CreateDate' in tags:
                val = tags['EXIF:CreateDate']
                #print(f'Found CreateDate for {photo_path.name}: {val}')
            elif 'QuickTime:CreationDate' in tags:
                val = tags['QuickTime:CreationDate']
                #print(f'Found QuickTime CreationDate for {photo_path.name}: {val}')

            if val:
                val_str = str(val).strip()
                if val_str.startswith("0000"):
                    print(f"Invalid date value for {photo_path.name}: {val_str}")
                else:
                    dt = parse_date(val_str)
                    if dt:
                        return dt
                
    except Exception as e:
        print(f"Error reading metadata for {photo_path.name}: {e}")

    return datetime.fromtimestamp(os.path.getmtime(photo_path))
 
def get_video_creation_date(video_path: Path) -> datetime:
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_entries', 'format_tags:stream_tags',
            video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        metadata = json.loads(result.stdout)
        tags = metadata.get('format', {}).get('tags', {})
        return parse_date(tags.get('creation_time'))
    
    except Exception:
        return datetime.fromtimestamp(os.path.getmtime(video_path))
    
def get_ppt_creation_date(ppt_path: Path) -> datetime:
    try:
        with olefile.OleFileIO(ppt_path) as ole:
            metadata = ole.get_metadata()
            return parse_date(metadata.create_time)
            
    except Exception:
        return datetime.fromtimestamp(os.path.getmtime(ppt_path))

def update_photo_date_time_original(photo_path: Path, new_date: datetime):
    try:
        new_date_str = new_date.strftime('%Y:%m:%d %H:%M:%S')
        cmd = [
            'exiftool', '-F',
            f'-AllDates={new_date_str}',
            f'-FileModifyDate={new_date_str}',
            f'-FileCreateDate={new_date_str}',
            '-overwrite_original',
            str(photo_path)
        ]
        subprocess.run(cmd, check=True)
        print(f'Updated EXIF all dates for {photo_path.name} to {new_date_str}')

    except Exception as e:
        print(f'Error updating EXIF dates for {photo_path.name}: {e}')

def update_timestamps(folder_path: Path, recursive: bool = False):
    files_path = folder_path.rglob('*') if recursive else folder_path.iterdir()

    for file_path in files_path:
      if not file_path.is_file():
          continue
      
      try:
          ext = file_path.suffix.lower()

          if ext in PHOTO_EXTENSIONS:
              file_date = get_photo_date_time_original(file_path)
              update_photo_date_time_original(file_path, file_date)
              continue
          elif ext in VIDEO_EXTENSIONS:
              file_date = get_video_creation_date(file_path)
          elif ext in {'.ppt', '.pptx'}:
              file_date = get_ppt_creation_date(file_path)
          else:
              print(f'[SKIP] Unknown Format: {file_path.name}')
              continue

          print(f'{file_path.name}: {file_date}')
          win_timestamp = pywintypes.Time(file_date)     # Convert to Windows API format
          str_file_path = str(file_path)                 # Convert Path object to string for Windows API

          handle = win32file.CreateFile(
              str_file_path,
              win32con.GENERIC_WRITE,
              win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
              None,
              win32con.OPEN_EXISTING,
              0,
              None
          )

          # Arguments: (handle, CreateTime, AccessTime, ModifyTime). Passing None keeps existing times
          win32file.SetFileTime(handle, win_timestamp, None, win_timestamp)
          
          handle.Close()
          print(f'NTFS "Date modified", "Date created" updated: {file_path.name} -> {file_date}')

      except Exception as e:
          print(f'Error processing {file_path}: {e}')

def flatten_folders(base_path: Path):    
    # 1. Iterate through all items in the base directory
    for subfolder in base_path.iterdir():
        if subfolder.is_dir():
            print(f'Processing: {subfolder.name}')
            
            # 2. Move every file from the subfolder to the base directory
            for file_path in subfolder.iterdir():
                # Construct the target path
                target_path = base_path / file_path.name
                
                # Move the file (shutil.move handles the 'cut and paste')
                shutil.move(str(file_path), str(target_path))
            
            # 3. Delete the subfolder now that it's empty
            subfolder.rmdir()
            print(f'Deleted empty folder: {subfolder.name}')

def compare_folders(folder_path_a: Path, folder_path_b: Path, compare_type: str, recursive: bool = False):
    files_path_a = folder_path_a.rglob('*') if recursive else folder_path_a.iterdir()
    files_path_b = folder_path_b.rglob('*') if recursive else folder_path_b.iterdir()

    if compare_type.lower() == 'photos':
        valid_extensions = PHOTO_EXTENSIONS
    elif compare_type.lower() == 'videos':
        valid_extensions = VIDEO_EXTENSIONS

    files_a = {
        p.name(folder_path_a)
        for p in files_path_a
        if p.is_file()
        and p.suffix.lower() in valid_extensions
    }
    files_b = {
        p.name(folder_path_b)
        for p in files_path_b
        if p.is_file()
        and p.suffix.lower() in valid_extensions
    }

    # Find files in A that are NOT in B
    missing_from_b = files_a - files_b

    if not missing_from_b:
        print('All files in Folder A are already present in Folder B.')
    else:
        print(f'Found {len(missing_from_b)} files in Folder A missing from Folder B:\n')
        for file in sorted(missing_from_b):
            print(f' - {file}')

def rename_files(folder_path: Path, GROUP_NAME: str, recursive: bool = False):
    files_path = folder_path.rglob('*') if recursive else folder_path.iterdir()

    for file_path in files_path:
        if not file_path.is_file():
            continue

        stem = file_path.stem
        clean_stem = re.sub(r'\s+', ' ', stem).strip()

        # Add datetime stamp and group name to filename
        dt = get_photo_date_time_original(file_path)
        timestamp = dt.strftime('%Y%m%d_%H%M%S')

        if not GROUP_NAME:
            base_name = f'{timestamp} - {clean_stem}'
        else:
            base_name = f'{timestamp} - {GROUP_NAME} - {clean_stem}'

        # Create the new filename
        ext = file_path.suffix.lower()         
        new_file_path = file_path.with_name(base_name + ext)

        # update filename
        if new_file_path.name != file_path.name:
            file_path.rename(new_file_path)
            print(f'{file_path.name} → {new_file_path.name}')

def rename_remote_files(remote_path: str):
    # 1. Fetch file list with metadata in JSON format
    # rclone lsjson is much faster than parsing text output
    try:
        result = subprocess.run(
            ['rclone', 'lsjson', remote_path],
            capture_output=True, text=True, check=True
        )
        files = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f'Error fetching file list: {e}')
        return

    for file_info in files:
        # Skip directories
        if file_info['IsDir']:
            continue

        original_name = file_info['Name']
        
        # 2. Parse the modification date
        # rclone returns ISO 8601 format: 2023-10-27T14:30:05.123Z
        mod_time_str = file_info['ModTime'].split('.')[0] # Remove milliseconds
        mod_time = datetime.strptime(mod_time_str, '%Y-%m-%dT%H:%M:%S')
        formatted_date = mod_time.strftime('%Y%m%d_%H%M%S')

        # 3. Handle Extension and New Name
        name_parts = original_name.rsplit('.', 1)
        if len(name_parts) > 1:
            base_name = name_parts[0]
            ext = name_parts[1].lower()
            new_name = f'{formatted_date} - {base_name}.{ext}'
        else:
            # Handle files with no extension
            new_name = f'{formatted_date} - {original_name}'

        # 4. Execute the rename (moveto)
        if original_name != new_name:
            old_path = f'{remote_path}/{original_name}'
            new_path = f'{remote_path}/{new_name}'
            
            print(f'Renaming: {original_name} -> {new_name}')
            #subprocess.run(['rclone', 'moveto', old_path, new_path,'--dry-run'], check=True)
            subprocess.run(['rclone', 'moveto', old_path, new_path], check=True)

def run_rclone_move(folder_path: Path, google_drive_path: str):
    cmd = [
        'rclone', 'move',
        str(folder_path),
        google_drive_path,
        '--fast-list',
        '--drive-chunk-size', '64M',
        '--buffer-size', '32M',
        '--checkers=16',
        '--transfers=8',
        '--metadata',
        #'--modify-window', '1s',
        '--checksum',
        '--progress'
    ]

    print(f'Running rclone move: {folder_path} → {google_drive_path}')
    subprocess.run(cmd, check=True)
    print('rclone move completed.')

def run_rclone_copy(source_folder: str, dest_folder: str):
    cmd = [
        'rclone', 'copy',
        source_folder,
        dest_folder,
        '--fast-list',
        '--drive-chunk-size', '64M',
        '--buffer-size', '32M',
        '--checkers=16',
        '--transfers=8',
        '--metadata',
        #'--modify-window', '1s',
        '--checksum',
        '--progress',
    ]

    print(f'Running rclone copy: {source_folder} → {dest_folder}')
    subprocess.run(cmd, check=True)
    print('rclone copy completed.')

if __name__ == '__main__':
    match step:
        case 1:
            update_timestamps(FOLDER_PATH, recursive=False)
        case 2:
            update_timestamps(FOLDER_PATH, recursive=True)
        case 3:
            flatten_folders(FOLDER_PATH)
        case 4:
            compare_folders(COMPARE_FOLDER_A_PATH, COMPARE_FOLDER_B_PATH, COMPARE_TYPE, recursive=False)
        case 5:
            compare_folders(COMPARE_FOLDER_A_PATH, COMPARE_FOLDER_B_PATH, COMPARE_TYPE, recursive=True)
        case 6:
            rename_files(FOLDER_PATH, GROUP_NAME, recursive=False)
        case 7:
            rename_files(FOLDER_PATH, GROUP_NAME, recursive=True)            
        case 8:
            rename_remote_files(GOOGLE_FOLDER)
        case 9:
            run_rclone_move(FOLDER_PATH, GOOGLE_FOLDER)        
        case 10:
            run_rclone_copy(SOURCE_FOLDER, DEST_FOLDER)
