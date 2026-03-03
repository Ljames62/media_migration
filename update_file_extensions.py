import subprocess
from pathlib import Path

FOLDER_PATH = Path(r"J:\My Drive\Photos\2001")

def update_file_extensions(folder_path: Path):
    extension_mapping = {
        '.jpeg': '.jpg',
    }

    for file_path in folder_path.iterdir():
        if not file_path.is_file():
            continue

        ext = file_path.suffix.lower()

        if ext in extension_mapping:
            ext = extension_mapping[ext]

        new_file_path = file_path.with_name(file_path.stem + ext)

        if new_file_path.name != file_path.name:
            # Handle Windows case-swap quirk (renaming 'A.JPG' to 'A.jpg' directly can fail)
            temp_file = file_path.with_name(file_path.name + ".tmp")
            file_path.rename(temp_file)
            temp_file.rename(new_file_path)
            
            print(f"{file_path.name} → {new_file_path.name}")

def run_exiftool_date_sync(folder_path: Path):
    cmd = [
        "exiftool",
        "-AllDates<DateTimeOriginal",
        "-FileModifyDate<DateTimeOriginal",
        #"-FileCreateDate<DateTimeOriginal",
        "-overwrite_original",
        str(folder_path)
    ]

    print("Running ExifTool date sync...")
    subprocess.run(cmd, check=True)
    print("ExifTool date sync completed.")

def main():
  update_file_extensions(FOLDER_PATH)  
  run_exiftool_date_sync(FOLDER_PATH)

if __name__ == "__main__":
  main()