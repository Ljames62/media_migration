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

video_path = Path(r"J:\My Drive\Movies\2011.7-2012.6 5th 10-11\2012 0303 Birthday\MP4 Conversions\20120303_140100 - 00000.mp4")
print(get_creation_date(video_path))