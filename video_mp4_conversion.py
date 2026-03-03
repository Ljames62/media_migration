import os
import subprocess
from pathlib import Path

# Configuration
input_dir = Path(r"C:\Users\johnk\Downloads\StageHold02")  # Current directory
output_dir = Path(r"C:\Users\johnk\Downloads\StageHold02/converted")
output_dir.mkdir(exist_ok=True)

# Find all AVI files
avi_files = list(input_dir.glob("*.AVI")) + list(input_dir.glob("*.avi"))

for avi_path in avi_files:
    mp4_path = output_dir / f"{avi_path.stem}.mp4"
    print(f"--- Processing: {avi_path.name} ---")

    # 1. Convert Video with FFmpeg
    # -crf 18: High quality
    # -pix_fmt yuv420p: Maximum compatibility for Google Drive
    ffmpeg_cmd = [
        "ffmpeg", "-i", str(avi_path),
        "-c:v", "libx264", "-crf", "16", "-preset", "slo",
        "-pix_fmt", "yuv420p",
        "-c:a copy",
        str(mp4_path), "-y"
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"Successfully converted to {mp4_path.name}")

        # This copies 'Date Created' ($btime$) and internal media dates
        exif_cmd = [
            "exiftool",
            "-tagsFromFile", str(avi_path),
            "-allDates",
            "-overwrite_original", str(mp4_path)
        ]
        subprocess.run(exif_cmd, check=True)
        print(f"Metadata synced for {mp4_path.name}")

        exif_cmd = [
            "exiftool", 
            "-overwrite_original",
            "-FileCreateDate<CreateDate", 
            "-FileModifyDate<CreateDate", str(mp4_path)
        ]
        subprocess.run(exif_cmd, check=True)
        print(f"Metadata synced for {mp4_path.name}")

    except subprocess.CalledProcessError as e:
        print(f"Error processing {avi_path.name}: {e}")

print("\nDone! Your converted files are in the 'converted' folder.")