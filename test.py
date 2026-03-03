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
            return datetime.strptime(value, fmt)
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
    
print(get_photo_date_time_original(Path(r'C:\Users\johnk\Downloads\Stage\2008 0228 Birthday\030108Weaver Cook 445 group.jpg')))