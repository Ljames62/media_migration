# Protect numeric dashes (digit-digit)
#stem = re.sub(r'(\d)-(\d)', r'\1__DASH__\2', stem)

# Remove unwanted characters (keep letters, numbers, space)
#stem = re.sub(r'[^A-Za-z0-9 ]+', '', stem)

# Restore numeric dashes
#stem = stem.replace('__DASH__', '-')

# Fallback: last modified time
#return datetime.fromtimestamp(os.path.getmtime(file_path))

# Get the current Modification Time
#mtime = os.path.getmtime(str_path) 

# python -m pip install Pillow
# python -m pip install python-dateutil
# python -m pip install pywin32
# python -m pip install olefile
# python -m pip install yt-dlp

# Restart VSCode after installing library or updating path

# Set up windows to show Name, Date Modified, Size

# def update_google_timestamps(google_folder: str):
#     cmd_list = ['rclone', 'lsjson', google_folder, '--metadata', '--files-only']
#     result = subprocess.run(cmd_list, capture_output=True, text=True, encoding='utf-8')
    
#     if result.returncode != 0:
#         print(f"Error fetching files: {result.stderr}")
#         return

#     files = json.loads(result.stdout)
#     print(f"Found {len(files)} files. Starting update...")

#     for file in files:
#         filename = file.get('Path')
#         raw_btime = file.get('Metadata', {}).get('btime')
        
#         if raw_btime and filename:
#             clean_timestamp = raw_btime.split('.')[0] # .000Z for rclone
#             # The full path to the file on the remote
#             file_remote_path = f"{google_folder}/{filename}"
            
#             print(f"Updating: {filename} -> {clean_timestamp}")
            
#             # 2. Apply the timestamp to the Google API
#             # This updates 'mtime' and the Web UI 'Modified' label
#             subprocess.run([
#                 'rclone', 'touch', 
#                 '--timestamp', clean_timestamp, 
#                 file_remote_path
#             ])

#             print(f"Updating Success: {filename} -> {clean_timestamp}")

# def run_exiftool_date_sync(usb_folder: str):
#     cmd = [
#         "exiftool",
#         # 1. First, try to sync everything to the File's System Modified Date (the fallback)
#         "-AllDates<FileModifyDate",
#         "-FileCreateDate<FileModifyDate",
        
#         # 2. Then, try to sync everything to DateTimeOriginal. If this exists, it will overwrite the assignments above.
#         "-AllDates<DateTimeOriginal",
#         "-FileModifyDate<DateTimeOriginal",
#         "-FileCreateDate<DateTimeOriginal",
        
#         "-overwrite_original",
#         usb_folder
#     ]

# print(f"Metadata tags for {video_path.name}: {tags}")
        # print(f"Metadata format for {video_path.name}: {metadata.get('format', {})}")
        # print(f"Metadata streams for {video_path.name}: {metadata.get('streams', [])}")
        # print(f"Metadata format tags for {video_path.name}: {metadata.get('format', {}).get('tags', {})}")
        # print(f"Metadata stream tags for {video_path.name}: {[stream.get('tags', {}) for stream in metadata.get('streams', [])]}")

#raw_btime = file.get('Metadata', {}).get('btime')
#clean_timestamp = raw_btime.split('.')[0] # .000Z for rclone