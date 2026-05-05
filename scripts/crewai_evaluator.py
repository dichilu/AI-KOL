import json
import os
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

MOCK_MODE = True  # True=本機測試  False=真實 Anthropic API


# ---- Mock 模式 ----

def load_mock_evaluations() -> dict:
    mock_path = Path(__file__).parent / "mock_data" / "crewai_mock.json"
    with open(mock_path, "r", encoding="utf-8") as f:
        return {e["頻道名稱"]: e for e in json.load(f)["evaluations"]}


def mock_evaluate(channels: list) -> list:
    mock_data = load_mock_evaluations()
    for ch in channels:
        result = mock_data.get(ch["頻道名稱"], {})
        ch["AI推薦等級"] = result.get("grade", "C")
        ch["AI推薦理由"] = result.get("reason", "")
    return channels


# ---- 真實 CrewAI 模式 ----

def build_crew():
    from crewai import Agent, Crew, LLM, Process, Task

    llm = LLM(
        model="claude-sonnet-4-6",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    content_analyst = Agent(
        role="工控KOL內容與專業度分析師",
        goal="判斷YouTube頻道是否真正聚焦於工業控制領域，以及頻道主是否具備真實工程師專業",
        backstory=(
            "你是資深工控產業顧問，有20年工廠自動化經驗。"
            "你能一眼分辨真正的工程師內容與只是掛關鍵字的表面科普。"
            "你熟悉PLC、SCADA、HMI、Modbus、CNC、變頻器等工控技術。"
        ),
        llm=llm,
        verbose=False,
    )

    data_analyst = Agent(
        role="KOL數據健康度分析師",
        goal="評估KOL的訂閱數、觀看率與互動率趨勢，識別假帳號或殭屍粉跡象",
        backstory=(
            "你是專業的社群媒體數據分析師，熟悉工控小眾領域的正常數據範圍。"
            "你知道工控頻道的互動率天生低於娛樂頻道，不會以娛樂標準錯誤判斷。"
        ),
        llm=llm,
        verbose=False,
    )

    decision_maker = Agent(
        role="KOL合作推薦決策師",
        goal="綜合內容分析與數據報告，給出A/B/C推薦等級與一句推薦理由",
        backstory=(
            "你是行銷團隊的最終決策者，負責判斷哪些KOL值得投入資源聯繫。"
            "A級代表強烈推薦立即聯繫，B級代表值得觀察列入暖身名單，C級代表不建議接觸。"
            "你會參考歷史合作經驗來校準你的判斷標準。"
        ),
        llm=llm,
        verbose=False,
    )

    return content_analyst, data_analyst, decision_maker


def real_evaluate_single(channel: dict, historical_feedback: list) -> dict:
    from crewai import Crew, Process, Task

    content_analyst, data_analyst, decision_maker = build_crew()

    channel_info = (
        f"頻道名稱：{channel['頻道名稱']}\n"
        f"頻道連結：{channel['頻道連結']}\n"
        f"訂閱數：{channel['訂閱數']:,}\n"
        f"平均觀看數：{channel['平均觀看數']:,}\n"
        f"平均留言數：{channel['平均留言數']}\n"
        f"互動率：{channel['互動率']}\n"
        f"主題標籤：{channel['主題標籤']}\n"
    )

    history_text = ""
    if historical_feedback:
        history_text = "\n\n【歷史合作參考案例】\n"
        for h in historical_feedback[-5:]:
            history_text += (
                f"- {h.get('頻道名稱', '')}｜"
                f"AI等級：{h.get('AI推薦等級', '')}｜"
                f"合作評價：{h.get('合作評價', '')}顆星｜"
                f"行銷人員建議：{h.get('行銷人員建議', '')}\n"
            )

    task1 = Task(
        description=f"分析以下YouTube頻道的內容相關性與專業深度：\n{channel_info}",
        expected_output="一段100字以內的分析，說明內容是否真正聚焦工控領域，以及頻道主是否為真實工程師。",
        agent=content_analyst,
    )

    task2 = Task(
        description=f"分析以下YouTube頻道的數據健康度：\n{channel_info}",
        expected_output="一段100字以內的分析，說明數據是否健康，有無假帳號跡象。",
        agent=data_analyst,
    )

    task3 = Task(
        description=(
            f"根據內容分析師與數據分析師的報告，給出最終推薦決策。{history_text}\n"
            f"請以以下格式回覆：\n等級：A 或 B 或 C\n理由：一句話說明"
        ),
        expected_output="等級（A/B/C）與一句推薦理由。",
        agent=decision_maker,
        context=[task1, task2],
    )

    crew = Crew(
        agents=[content_analyst, data_analyst, decision_maker],
        tasks=[task1, task2, task3],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    output = str(result).strip()

    grade = "C"
    reason = output
    for line in output.split("\n"):
        if line.startswith("等級："):
            grade = line.replace("等級：", "").strip()
        if line.startswith("理由："):
            reason = line.replace("理由：", "").strip()

    channel["AI推薦等級"] = grade
    channel["AI推薦理由"] = reason
    return channel


def evaluate(channels: list, historical_feedback: list = None) -> list:
    if MOCK_MODE:
        return mock_evaluate(channels)

    results = []
    for ch in channels:
        print(f"  評估中：{ch['頻道名稱']}...")
        evaluated = real_evaluate_single(ch, historical_feedback or [])
        results.append(evaluated)
    return results


# ---- 主程式 ----

if __name__ == "__main__":
    from youtube_collector import collect

    print("步驟 1：收集 YouTube 頻道資料...")
    channels = collect()

    print(f"\n步驟 2：CrewAI 評估 {len(channels)} 個頻道（{'Mock 模式' if MOCK_MODE else '真實 API'}）...")
    evaluated = evaluate(channels)

    print("\n========== 評估結果 ==========\n")
    for ch in evaluated:
        grade_label = {"A": "🔴 A 強烈推薦", "B": "🟡 B 值得觀察", "C": "⚪ C 不建議"}.get(ch["AI推薦等級"], ch["AI推薦等級"])
        print(f"【{grade_label}】{ch['頻道名稱']}")
        print(f"  訂閱數：{ch['訂閱數']:,}  互動率：{ch['互動率']}  Email：{ch['聯絡Email'] or '無'}")
        print(f"  理由：{ch['AI推薦理由']}")
        print()
