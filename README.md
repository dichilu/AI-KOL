# AI-KOL｜台灣工控 B2B KOL 情報與聯繫系統

自動搜尋、評估、管理台灣工業控制領域的 YouTube 頻道主與 Facebook 社團版主。

## 系統架構

```
GitHub Actions（每週自動觸發）
    ↓
資料收集（YouTube Data API / Facebook Playwright）
    ↓
CrewAI 三 Agent 評估（內容分析師 / 數據分析師 / 推薦決策師）
    ↓
寫入 Google Sheets（YouTube_KOL / Facebook_KOL）
    ↓
GitHub Pages Dashboard（行銷人員操作介面）
```

## 版本

目前版本：v0.1.0

## 文件

- [核心功能介紹 v0.1.0](docs/核心功能介紹_v0.1.0.md)
- [版本控管](docs/版本控管.md)
