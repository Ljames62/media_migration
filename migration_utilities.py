import json
import olefile
import os
import re
import subprocess

import shutil
import dateutil
from dateutil import parser

from datetime import datetime, timedelta
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
    '%Y-%m-%dT&H:%M:%S+00:00'  # MP4 Conversion
    '%Y:%m:%d %H:%M:%S%z'      # H264 MTS
    '%Y:%m:%d %H:%M',          # EXIF without seconds
    '%Y-%m-%dT%H:%M',          # ISO 8601 without seconds
    '%Y-%m-%d %H:%M',          # Common datetime format without seconds
    '%Y/%m/%d %H:%M',          # Alternative with slashes without seconds
    '%Y%m%d_%H%M%S'            # smartphone apps filename date IMG_20230101_120000.jpg
]

# 1,2 Find files in A that are NOT in B
COMPARE_FOLDER_A_PATH = Path(r'C:\Users\johnk\Downloads\PicLoadQueue\2014.7-2015.6 8th 13-14')
COMPARE_FOLDER_B_PATH = Path(r'J:\My Drive\Movies\2014.7-2015.6 8th 13-14')
COMPARE_TYPE = 'photos'
#COMPARE_TYPE = 'videos' 

# 11-18 25-27     Must match for 25, 26
FOLDER_PATH = Path(r'J:\My Drive\Pictures\2015.7-2016.6 9th 14-15')
# 21-27
GOOGLE_FOLDER = r'etavern_gdrive:/Media/2015-16 Grd 9 Yr 14-15'

# Step 28 rclone copy folder (recursive)
SOURCE_FOLDER = r'J:\My Drive\Movies\2011.7-2012.6 5th 10-11'
DEST_FOLDER = r'D:\Media\2011.7-2012.6 5th 10-11\Videos'

# Step 29 rclone copyto file
SOURCE_FILE = r'C:\Users\johnk\Downloads\PicLoadQueue\2010.7-2011.6 4th 9-10'
DEST_FILE = r'D:\Media\2010.7-2011.6 4th 9-10'

NEW_DATE = '2014:07:07 14:00:00'    # 13 For files without date taken or creation date
OLD_GROUP_NAME = '- Colorado -'     # Step 17, 18, 23, 24
NEW_GROUP_NAME = '-'     # Step 17, 18, 23, 24

# 1-Compare 2-Compare recursive
# 11-Update timestamps 12-Update timestamps recursive 13-Update timestamps with new date 14-Flatten folders
# 15-Rename 16-Rename recursive 17-Update group name 18-Update group name recursive
# 21-Rename Remote 22-Rename Remote recursive 23-Update Remote group name 24-Update Remote group name recursive
# 25-Sync Remote timestamps 26-Sync Remote timestamps recursive 27-Move with rclone
# 31-Copy with rclone 32-Copyto file with rclone
GROUP_NAME = ' - ' #' - '     ' - Colorado - '     ' - Kiawah '
step = 2

def parse_date(value):
    for fmt in DATE_FORMATS:
        try:
            clean_value = re.sub(r'/', '', value)
            clean_value = re.sub(r'\s+', ' ', clean_value).strip()
            if len(clean_value) == 25 and clean_value.count(':') == 5:
                clean_value = clean_value[:-6]
            return datetime.strptime(clean_value, fmt)
        except ValueError:
            continue
    
    print(f'Could not parse date string: {value}')
    return None

def get_media_date(media_path: Path) -> datetime:
    try:
        cmd = [
            'exiftool',
            '-j',
            '-G',
           '-time:all',
           str(media_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)        
        metadata = json.loads(result.stdout)
        val = ''

        if metadata:            
            tags = metadata[0]
            #print(tags)
            # if 'File:FileModifyDate' in tags:
            #     val = tags['File:FileModifyDate']
            #     #print(f'Found File:FileModifyDate for {media_path.name}: {val}')
            if 'EXIF:DateTimeOriginal' in tags:
                val = tags['EXIF:DateTimeOriginal']
                #print(f'Found EXIF:DateTimeOriginal for {media_path.name}: {val}')
            elif 'EXIF:CreateDate' in tags:
                val = tags['EXIF:CreateDate']
                #print(f'Found EXIF:CreateDate for {media_path.name}: {val}')
            elif 'QuickTime:CreationDate' in tags:
                val = tags['QuickTime:CreationDate']
                #print(f'Found QuickTime:CreationDate for {media_path.name}: {val}')
            if 'H264:DateTimeOriginal' in tags:
                val = tags['H264:DateTimeOriginal']
                #print(f'Found H264:DateTimeOriginal for {media_path.name}: {val}')

            if val:
                val_str = str(val).strip()
                if val_str.startswith("0000"):
                    print(f"Invalid date value for {media_path.name}: {val_str}")
                else:
                    dt = parse_date(val_str)
                    if dt:
                        return dt
                
    except Exception as e:
        print(f"Error reading metadata for {media_path.name}: {e}")

    return datetime.fromtimestamp(os.path.getmtime(media_path))
 
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
        val = ''
        

        if metadata:
            tags = metadata.get('format', {}).get('tags', {})
            val = tags.get('creation_time')
            print(f"Metadata creation_time for {video_path.name}: {val}")

            if val:
                val_str = str(val).strip()
                if val_str.startswith("0000"):
                    print(f"Invalid date value for {video_path.name}: {val_str}")
                else:
                    dt = parse_date(val_str)
                    if dt:
                        return dt
    
    except Exception:
        return datetime.fromtimestamp(os.path.getmtime(video_path))
    
def get_ppt_creation_date(ppt_path: Path) -> datetime:
    try:
        with olefile.OleFileIO(ppt_path) as ole:
            metadata = ole.get_metadata()
            return parse_date(metadata.create_time)
            
    except Exception:
        return datetime.fromtimestamp(os.path.getmtime(ppt_path))

def update_photo_date_time_original(photo_path: Path, file_date: datetime):
    try:
        file_date_str = file_date.strftime('%Y:%m:%d %H:%M:%S')
        cmd = [
            'exiftool', '-m', '-overwrite_original', # '-F',
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

def update_video_create_date(video_path: Path, file_date: datetime):
    try:
        file_date_str = file_date.strftime('%Y:%m:%d %H:%M:%S')
        cmd = [
            'exiftool', '-api', 'QuickTimeUTC', '-m', '-overwrite_original', # '-F',
            # Quicktime dates
            f'-CreateDate={file_date_str}',
            f'-ModifyDate={file_date_str}',
            f'-TrackCreateDate={file_date_str}',
            f'-TrackModifyDate={file_date_str}',
            f'-MediaCreateDate={file_date_str}',
            f'-MediaModifyDate={file_date_str}',
            # Update system dates
            f'-FileModifyDate={file_date_str}',
            f'-FileCreateDate={file_date_str}',
            str(video_path)
        ]
        subprocess.run(cmd, check=True)
        print(f'Updated EXIF all dates for {video_path} to {file_date_str}')

    except Exception as e:
        print(f'Error updating EXIF dates for {video_path.name}: {e}')

def update_NTFS_timestamps(file_path: Path, file_date: datetime):
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

def update_timestamps(folder_path: Path, new_date: str = '', recursive: bool = False):
    files_path = sorted(
        folder_path.rglob('*') if recursive else folder_path.iterdir(),
        key=lambda x: x.name.lower()  # .lower() ensures a standard A-Z sort regardless of case
    )
    cnt = 0

    for file_path in files_path:
      if not file_path.is_file():
          continue
      
      try:
          ext = file_path.suffix.lower()
          cnt += 1

          if ext in PHOTO_EXTENSIONS:
              if new_date.strip():                  
                  parse_new_date = parse_date(new_date)
                  file_date = parse_new_date + timedelta(minutes=cnt)
              else:
                  file_date = get_media_date(file_path)

              update_photo_date_time_original(file_path, file_date)
              update_NTFS_timestamps(file_path, file_date)
          elif ext in VIDEO_EXTENSIONS:
              if new_date.strip():
                  parse_new_date = parse_date(new_date)
                  file_date = parse_new_date + timedelta(minutes=cnt)
              else:
                  file_date = get_media_date(file_path)

              if ext != '.mts':
                  update_video_create_date(file_path, file_date)
              update_NTFS_timestamps(file_path, file_date)
          elif ext in {'.ppt', '.pptx'}:
              if new_date.strip():
                  parse_new_date = parse_date(new_date)
                  file_date = parse_new_date + timedelta(minutes=cnt)
              else:
                  file_date = get_ppt_creation_date(file_path)

              update_NTFS_timestamps(file_path, file_date)
          else:
              print(f'[SKIP] Unknown Format: {file_path.name}')

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
        p.name
        for p in files_path_a
        if p.is_file()
        and p.suffix.lower() in valid_extensions
    }
    files_b = {
        p.name
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

def rename_files(folder_path: Path, group_name: str, recursive: bool = False):
    files_path = folder_path.rglob('*') if recursive else folder_path.iterdir()
    cnt = 0

    for file_path in files_path:
        if not file_path.is_file():
            continue

        filename = file_path.name
        stem = file_path.stem
        ext = file_path.suffix.lower()
        clean_stem = re.sub(r'\s+', ' ', stem).strip()
        cnt += 1

        pattern = r"^\d{8}_\d{6}\.(jpg|png|mp4|mov|avi|mts)$"
        if re.match(pattern, filename, re.IGNORECASE):
            new_name = f'{stem}{group_name}{cnt:02d}{ext}'
            new_file_path = file_path.with_name(new_name)
        else:
            # Add datetime stamp and group name to filename
            dt = get_media_date(file_path)
            timestamp = dt.strftime('%Y%m%d_%H%M%S')
            base_name = f'{timestamp}{group_name}{clean_stem}'
            new_file_path = file_path.with_name(base_name + ext)

        # update filename
        if new_file_path.name != file_path.name:
            file_path.rename(new_file_path)
            print(f'{file_path.name} → {new_file_path.name}')

def update_files_group_name(folder_path: Path, old_group_name: str, new_group_name: str, recursive: bool = False):
    files_path = folder_path.rglob('*') if recursive else folder_path.iterdir()

    for file_path in files_path:
        if not file_path.is_file():
            continue

        if old_group_name in file_path.name:
            new_filename = file_path.name.replace(old_group_name, new_group_name)
            new_file_path = file_path.with_name(new_filename)

            if new_file_path.name != file_path.name:
                # Handle Windows case-swap quirk (renaming 'A.JPG' to 'A.jpg' directly can fail)
                temp_file_path = file_path.with_name(file_path.name + ".tmp")
                file_path.rename(temp_file_path)
                temp_file_path.rename(new_file_path)
            
                print(f"{file_path.name} → {new_file_path.name}")

def rename_remote_files(remote_path: str, group_name: str, recursive: bool = False):
    # Fetch file list with metadata in JSON format. rclone lsjson is much faster than parsing text output
    if recursive:
        cmd = [
            'rclone',
            'lsjson',
            '--recursive',
            '--files-only',
            remote_path
        ]
    else:
        cmd = [
            'rclone',
            'lsjson',
            '--files-only',
            remote_path
        ]
        
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        if result.returncode != 0:
            print(f"Error fetching files: {result.stderr}")
            return
    
        files = json.loads(result.stdout)
        print(f"Found {len(files)} files. Starting update...")
    except subprocess.CalledProcessError as e:
        print(f'Error fetching file list: {e}')
        return

    for file_info in files:
        # Skip directories
        if file_info['IsDir']:
            continue

        old_rel_str = file_info['Path'] 
        old_rel_path = Path(old_rel_str)
        
        # Parse the modification date. rclone returns ISO 8601 format: 2023-10-27T14:30:05.123Z
        mod_time_str = file_info['ModTime'].split('.')[0] # Remove milliseconds
        mod_time = datetime.strptime(mod_time_str, '%Y-%m-%dT%H:%M:%S')
        formatted_date = mod_time.strftime('%Y%m%d_%H%M%S')

        # Build new name
        base_name = old_rel_path.stem

        base_name = old_rel_path.stem
        ext = old_rel_path.suffix.lower()
        new_filename = f'{formatted_date}{group_name}{base_name}{ext}'

        new_rel_path = old_rel_path.parent / new_filename
        
        # Execute the rename (moveto)
        if old_rel_path != new_rel_path:
            source = (Path(remote_path) / old_rel_path).as_posix()
            dest = (Path(remote_path) / new_rel_path).as_posix()

            print(f'Renaming: {source} -> {dest}')            
            subprocess.run(['rclone', 'moveto', source, dest], check=True)
            #subprocess.run(['rclone', 'moveto', source, dest,'--dry-run'], check=True)

def update_remote_files_group_name(remote_path: str, old_group_name: str, new_group_name: str, recursive: bool = False):
    # Fetch file list with metadata in JSON format. rclone lsjson is much faster than parsing text output
    if recursive:
        cmd = [
            'rclone',
            'lsjson',
            '--recursive',
            '--files-only',
            remote_path
        ]
    else:
        cmd = [
            'rclone',
            'lsjson',
            '--files-only',
            remote_path
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        if result.returncode != 0:
            print(f"Error fetching files: {result.stderr}")
            return
    
        files = json.loads(result.stdout)
        print(f"Found {len(files)} files. Starting update...")
    except subprocess.CalledProcessError as e:
        print(f'Error fetching file list: {e}')
        return

    for file_info in files:
        # Skip directories
        if file_info['IsDir']:
            continue

        old_filename = file_info['Name']
        
        if OLD_GROUP_NAME in old_filename:
            new_filename = old_filename.replace(old_group_name, new_group_name)

            # Execute the rename (moveto)
            if new_filename != old_filename:        
                old_file_path = f'{remote_path}/{old_filename}'
                new_file_path = f'{remote_path}/{new_filename}'
                
                print(f'Renaming: {old_filename} -> {new_filename}')
                #subprocess.run(['rclone', 'moveto', old_file_path, new_file_path,'--dry-run'], check=True)
                subprocess.run(['rclone', 'moveto', old_file_path, new_file_path], check=True)

def sync_remote_timestamps(remote_path: str, folder_path: Path, recursive: bool = False):
    if recursive:
        cmd = [
            'rclone',
            'lsjson',
            '--recursive',
            '--metadata',
            '--files-only',
            remote_path
        ]
    else:
        cmd = [
            'rclone',
            'lsjson',
            '--metadata',
            '--files-only',
            remote_path
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode != 0:
            print(f"Error fetching files: {result.stderr}")
            return

        files = json.loads(result.stdout)
        print(f"Found {len(files)} files. Starting update...")
    except subprocess.CalledProcessError as e:
            print(f'Error fetching file list: {e}')
            return

    for file in files:
        filename = file.get('Path')

        # Sync system timestamps
        file_path = Path(folder_path) / filename
        
        try:
            ext = file_path.suffix.lower()

            if ext in PHOTO_EXTENSIONS:
                file_date = get_media_date(file_path)
                update_NTFS_timestamps(file_path, file_date)
            elif ext in VIDEO_EXTENSIONS:
                file_date = get_media_date(file_path)
                update_NTFS_timestamps(file_path, file_date)
            elif ext in {'.ppt', '.pptx'}:
                file_date = get_ppt_creation_date(file_path)
                update_NTFS_timestamps(file_path, file_date)
            else:
                print(f'[SKIP] Unknown Format: {file_path.name}')
                continue
        except Exception as e:
            print(f'Error processing system timestamps {file_path}: {e}')
            continue       
        
        # Sync remote modification timestamps        
        print(file_date)
        try:
            if file_date and filename:
                iso_date_str = file_date.isoformat()
                if '+' in iso_date_str:
                    rclone_date_str = iso_date_str.split('+')[0]
                elif iso_date_str.endswith('Z'):
                    rclone_date_str = iso_date_str[:-1]
                else:
                    rclone_date_str = iso_date_str

                file_remote_path = f"{remote_path}/{filename}"
                
                print(f"Syncing: {filename} -> {rclone_date_str}")
                
                # Apply the timestamp to the Google API
                # This updates 'mtime', 'ModTime' and the Web UI 'Modified' label
                subprocess.run([
                    'rclone', 'touch', 
                    '--timestamp', rclone_date_str,
                    file_remote_path
                ])
        except Exception as e:
            print(f'Error processing remote timestamps {filename}: {e}')
            continue
        
    print("\nSuccess: All files have been synchronized.")

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

def run_rclone_copyto(source_file: str, dest_file: str):
    cmd = [
        'rclone', 'copyto',
        source_file,
        dest_file,
        '--metadata',
        '--checksum',
        '--progress',
    ]

    print(f'Running rclone copyto: {source_file} → {dest_file}')
    subprocess.run(cmd, check=True)
    print('rclone copyto completed.')

if __name__ == '__main__':
    match step:
        case 1:
            compare_folders(COMPARE_FOLDER_A_PATH, COMPARE_FOLDER_B_PATH, COMPARE_TYPE, recursive=False)
        case 2:
            compare_folders(COMPARE_FOLDER_A_PATH, COMPARE_FOLDER_B_PATH, COMPARE_TYPE, recursive=True)
        # Folder Path Tools
        case 11:
            update_timestamps(FOLDER_PATH, new_date='', recursive=False)
        case 12:
            update_timestamps(FOLDER_PATH, new_date='', recursive=True)
        case 13:
            update_timestamps(FOLDER_PATH, new_date=NEW_DATE, recursive=False)
        case 14:
            flatten_folders(FOLDER_PATH)        
        case 15:
            rename_files(FOLDER_PATH, group_name=GROUP_NAME, recursive=False)
        case 16:
            rename_files(FOLDER_PATH, group_name=GROUP_NAME, recursive=True)
        case 17:
            update_files_group_name(FOLDER_PATH, OLD_GROUP_NAME, NEW_GROUP_NAME, recursive=False)
        case 18:
            update_files_group_name(FOLDER_PATH, OLD_GROUP_NAME, NEW_GROUP_NAME, recursive=True)
        # Google Folder Tools
        case 21:
            rename_remote_files(GOOGLE_FOLDER, group_name=GROUP_NAME, recursive=False)
        case 22:
            rename_remote_files(GOOGLE_FOLDER, group_name=GROUP_NAME, recursive=True)
        case 23:
            update_remote_files_group_name(GOOGLE_FOLDER, OLD_GROUP_NAME, NEW_GROUP_NAME, recursive=False)
        case 24:
            update_remote_files_group_name(GOOGLE_FOLDER, OLD_GROUP_NAME, NEW_GROUP_NAME, recursive=True)
        case 25:
            sync_remote_timestamps(GOOGLE_FOLDER, FOLDER_PATH, recursive=False)
        case 26:
            sync_remote_timestamps(GOOGLE_FOLDER, FOLDER_PATH, recursive=True)
        case 27:
            run_rclone_move(FOLDER_PATH, GOOGLE_FOLDER)
        # Source Destination Tools      
        case 31:
            run_rclone_copy(SOURCE_FOLDER, DEST_FOLDER)
        case 32:
            run_rclone_copyto(SOURCE_FILE, DEST_FILE)
