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

def parse_date(value):
    for fmt in DATE_FORMATS:
        try:
            clean_value = re.sub(r'/', '', value)
            clean_value = re.sub(r'\s+', ' ', clean_value).strip()
            return datetime.strptime(clean_value, fmt)
        except ValueError:
            continue
    
    print(f'Could not parse date string: {value}')
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
                #print(f'Found EXIF DateTimeOriginal for {photo_path.name}: {val}')
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
        #print(f"Metadata creation_time for {video_path.name}: {tags.get('creation_time')}")
        return parse_date(tags.get('creation_time'))
    
    except Exception:
        return datetime.fromtimestamp(os.path.getmtime(video_path))

def update_photo_date_time_original(photo_path: Path, file_date: datetime):
    try:
        file_date_str = file_date.strftime('%Y:%m:%d %H:%M:%S')
        cmd = [
            'exiftool', '-F', '-m', '-overwrite_original',
            # Update EXIF dates
            f'-EXIF:DateTimeOriginal={file_date_str}',
            f'-EXIF:CreateDate={file_date_str}',
            f'-EXIF:ModifyDate={file_date_str}',
            # Update system dates
            f'-FileModifyDate={file_date_str}',
            f'-FileCreateDate={file_date_str}',
            str(photo_path)
        ]
        subprocess.run(cmd, check=True)
        print(f'Updated EXIF all dates for {photo_path} to {file_date_str}')

    except Exception as e:
        print(f'Error updating EXIF dates for {photo_path.name}: {e}')
        
def update_NTFS_timestamps(file_path: Path, file_date: datetime, recursive: bool = False):
      try:
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

#print(get_video_creation_date(Path(r'C:\Users\johnk\Downloads\PicLoadQueue\2008.7-2009.6 2nd 7-8\2009 03 12\CIMG2673.AVI')))
file_date = get_photo_date_time_original(Path(r'J:\My Drive\Pictures\2008.7-2009.6 2nd 7-8\2009 0101\Valentines9.jpg'))
update_NTFS_timestamps(Path(r'J:\My Drive\Pictures\2008.7-2009.6 2nd 7-8\2009 0101\Valentines9.jpg'), file_date)
