import requests
from dotenv import load_dotenv
import os

# 載入環境變數
load_dotenv()

# 準備檔案和參數
files = {
    'file': open('data/raw_data/vedio/youtube_5_records.xlsx', 'rb')
}

parser_api_key = os.getenv("PARSER_API_KEY")
augment_api_key = os.getenv("AUGMENTER_API_KEY")

data = {
    'parser_api_key': parser_api_key,
    'augmenter_api_key': augment_api_key,
    'parser_model': 'openai/gpt-oss-20b:free',
    'augmenter_model': 'openai/gpt-oss-20b:free'
}

# 發送請求
response = requests.post(
    'http://localhost:8000/api/v1/data_augment',
    files=files,
    data=data
)

# 處理回應
result = response.json()
print(result)
print(f"Success: {result['success']}")
print(f"Total Count: {result['total_count']}")
print(f"Output Path: {result['augmented_queries_path']}")