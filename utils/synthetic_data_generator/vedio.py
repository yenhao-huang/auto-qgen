import pandas as pd
import random
import string
from openpyxl import Workbook

# Generate 100 fake YouTube records with 7 columns
def random_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

titles = [
    "AI Tutorial", "Travel Vlog Japan", "Cooking Pasta", "Fitness Routine", 
    "Gadget Review", "Music Video", "Tech News", "Daily Vlog", 
    "Gaming Highlights", "Product Unboxing"
]

channel_names = [
    "AI Lab", "World Traveler", "Kitchen Master", "FitnessPro",
    "TechZone", "MusicHub", "NewsDaily", "VlogLife",
    "GamerOne", "UnboxWorld"
]

data = {
    "video_id": [],
    "title": [],
    "channel": [],
    "length_minutes": [],
    "views": [],
    "likes": [],
    "upload_date": []
}

for _ in range(100):
    data["video_id"].append(random_id())
    data["title"].append(random.choice(titles))
    data["channel"].append(random.choice(channel_names))
    data["length_minutes"].append(round(random.uniform(3, 30), 2))
    data["views"].append(random.randint(1000, 2_000_000))
    data["likes"].append(random.randint(100, 200_000))
    # Generate random date in recent 3 years
    year = random.choice([2023, 2024, 2025])
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    data["upload_date"].append(f"{year}-{month:02d}-{day:02d}")

df = pd.DataFrame(data)

# Save file
filepath = "/mnt/data/youtube_100_records.xlsx"
df.to_excel(filepath, index=False)

filepath
