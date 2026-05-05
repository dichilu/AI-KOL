import json
import os
import re
from datetime import datetime
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ---- 設定區 ----
KEYWORDS = [
    "PLC 教學",
    "工業自動化 工程師",
    "SCADA HMI 台灣",
    "Modbus 實作",
    "工控 電氣 台灣",
    "CNC 程式 教學",
    "西門子 三菱 PLC",
]

RECENT_VIDEOS_COUNT = 15
MOCK_MODE = True  # True=本機測試  False=真實 YouTube API


def load_mock_data():
    mock_path = Path(__file__).parent / "mock_data" / "youtube_mock.json"
    with open(mock_path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_youtube_channels():
    if MOCK_MODE:
        return load_mock_data()["channels"]
    # TODO: 換成真實 YouTube Data API 呼叫
    raise NotImplementedError("真實 API 模式尚未實作")


def extract_contact_info(description: str) -> dict:
    email_pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    phone_pattern = r"(?:\+886|0)[0-9\-\s]{8,12}"

    emails = re.findall(email_pattern, description)
    phones = re.findall(phone_pattern, description)

    return {
        "email": emails[0] if emails else "",
        "phone": phones[0].strip() if phones else "",
    }


def calculate_averages(videos: list) -> dict:
    recent = videos[:RECENT_VIDEOS_COUNT]
    if not recent:
        return {"avg_views": 0, "avg_comments": 0}

    avg_views = sum(v["view_count"] for v in recent) // len(recent)
    avg_comments = sum(v["comment_count"] for v in recent) // len(recent)

    return {"avg_views": avg_views, "avg_comments": avg_comments}


def calculate_engagement_rate(avg_comments: int, subscribers: int) -> str:
    if subscribers == 0:
        return "0.00%"
    rate = (avg_comments / subscribers) * 100
    return f"{rate:.2f}%"


def collect() -> list:
    raw_channels = fetch_youtube_channels()
    results = []

    for ch in raw_channels:
        contact = extract_contact_info(ch.get("description", ""))
        averages = calculate_averages(ch.get("recent_videos", []))
        engagement = calculate_engagement_rate(
            averages["avg_comments"], ch.get("subscribers", 0)
        )

        record = {
            "頻道名稱": ch.get("name", ""),
            "訂閱數": ch.get("subscribers", 0),
            "平均觀看數": averages["avg_views"],
            "平均留言數": averages["avg_comments"],
            "互動率": engagement,
            "主題標籤": ", ".join(ch.get("tags", [])),
            "資料更新日期": datetime.today().strftime("%Y-%m-%d"),
            "頻道連結": ch.get("url", ""),
            "聯絡Email": contact["email"],
            "聯絡電話": contact["phone"],
            "AI推薦等級": "",
            "AI推薦理由": "",
            "聯繫狀態": "未聯繫",
            "負責人": "",
            "備註": "",
            "最後聯繫日期": "",
            "實際合作意願": "",
            "合作評價": "",
            "行銷人員建議": "",
        }
        results.append(record)

    return results


if __name__ == "__main__":
    data = collect()
    print(f"\n收集到 {len(data)} 個頻道\n")
    print(f"{'頻道名稱':<20} {'訂閱數':>8} {'互動率':>8} {'Email':<35} {'電話'}")
    print("-" * 90)
    for d in data:
        print(
            f"{d['頻道名稱']:<20} {d['訂閱數']:>8,} {d['互動率']:>8} "
            f"{d['聯絡Email']:<35} {d['聯絡電話']}"
        )
