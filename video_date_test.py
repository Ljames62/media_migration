import subprocess
import json
import dateutil
from dateutil import parser

from datetime import datetime
from pathlib import Path

def get_creation_date(video_path):
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_entries", "format_tags=creation_time",
        video_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    metadata = json.loads(result.stdout)

    date_str = metadata.get("format", {}).get("tags", {}).get("creation_time")
    dt = parser.parse(date_str)

    return dt

video_path = Path(r"C:\Users\johnk\Downloads\StageHold01\CIMG0007.AVI")
print(get_creation_date(video_path))