import subprocess
from pathlib import Path

#FOLDER_PATH = Path(r"J:\My Drive\Media\2004")
FOLDER_PATH = Path(r"C:\Users\johnk\Downloads\PicLoadQueue\2006.7-2007.6 K 5-6")

def update_file_group_name(folder_path: Path, OLD_GROUP_NAME: str, NEW_GROUP_NAME: str):
    for file_path in folder_path.iterdir():
        if not file_path.is_file():
            continue

        if OLD_GROUP_NAME in file_path.name:
            new_name = file_path.name.replace(OLD_GROUP_NAME, NEW_GROUP_NAME)
            new_file_path = file_path.with_name(new_name)

            if new_file_path.name != file_path.name:
                # Handle Windows case-swap quirk (renaming 'A.JPG' to 'A.jpg' directly can fail)
                temp_file_path = file_path.with_name(file_path.name + ".tmp")
                file_path.rename(temp_file_path)
                temp_file_path.rename(new_file_path)
            
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

OLD_GROUP_NAME = " - Keuka Lake - "
NEW_GROUP_NAME = " - "

def main():
  update_file_group_name(FOLDER_PATH, OLD_GROUP_NAME, NEW_GROUP_NAME)  
  #run_exiftool_date_sync(FOLDER_PATH)

if __name__ == "__main__":
  main()