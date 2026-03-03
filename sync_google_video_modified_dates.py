import subprocess
import json

GOOGLE_DRIVE_PATH = "etavern_gdrive:Media/2004"

def update_google_timestamps():
    cmd_list = ['rclone', 'lsjson', GOOGLE_DRIVE_PATH, '--metadata', '--files-only']
    result = subprocess.run(cmd_list, capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode != 0:
        print(f"Error fetching files: {result.stderr}")
        return

    files = json.loads(result.stdout)
    print(f"Found {len(files)} files. Starting update...")

    for file in files:
        filename = file.get('Path')
        raw_btime = file.get('Metadata', {}).get('btime')
        
        if raw_btime and filename:
            clean_timestamp = raw_btime.split('.')[0] # .000Z for rclone
            # The full path to the file on the remote
            file_remote_path = f"{GOOGLE_DRIVE_PATH}/{filename}"
            
            print(f"Updating: {filename} -> {clean_timestamp}")
            
            # 2. Apply the timestamp to the Google API
            # This updates 'mtime' and the Web UI 'Modified' label
            subprocess.run([
                'rclone', 'touch', 
                '--timestamp', clean_timestamp, 
                file_remote_path
            ])

    print("\nSuccess: All files have been synchronized.")

if __name__ == "__main__":
    update_google_timestamps()