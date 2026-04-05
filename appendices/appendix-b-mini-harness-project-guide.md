# 附錄 B：`mini harness` 專題製作指南

## 這份附錄的用途

Part III 與第 19 章已經帶你把 `mini harness` 的核心骨架做出來，也帶你理解它和 `claw-code` 的關係。這份附錄的目的，是把那些章節內容整理成一份可直接執行的專題製作指南。換句話說，如果你想把這門教材轉成一個可提交、可展示、可迭代的作品，就從這裡開始。

## 專題目標

你的專題不需要重做 `claw-code`，但必須清楚展現你已經理解 Harness Engineering 的本質。最低要求是：做出一個可以跑多輪互動、能呼叫工具、會經過 permission policy、能保存 session、而且有基本測試的 `mini harness`。

## 最低交付物

建議至少交出以下內容：

1. 一個可執行的 `mini harness` 專案
2. 一份 `README.md`，說明系統定位、使用方式與設計取捨
3. 至少三類測試：runtime turn、permission denial、session persistence roundtrip
4. 一份簡短設計說明，解釋它如何對照 `claw-code`

## 建議的最低檔案樹

```text
mini-harness/
├── README.md
├── mini_harness/
│   ├── __init__.py
│   ├── runtime.py
│   ├── tools.py
│   └── permissions.py
└── tests/
    ├── test_runtime.py
    ├── test_tools.py
    └── test_permissions.py
```

如果你的 session logic 已經開始變多，也可以在第二階段再拆出 `session.py`。但第一版不必為了看起來完整而過早拆太多檔案。

## 建議的製作流程

### Step 1：先寫 scope contract

先用一頁文字寫清楚：

- Included: message loop、tool dispatch、permission policy、session persistence、basic tests
- Excluded for v1: full `MCP` support、remote execution、plugin lifecycle、full parity harness

沒有這一步，專題很容易變成持續膨脹的功能清單。

### Step 2：先把骨架搭對

在 `runtime.py`、`tools.py`、`permissions.py` 中先建立責任邊界，再補功能。不要一開始就把所有邏輯塞進單一檔案。因為這門專題真正要評估的，不只是能不能跑，而是你有沒有保留 harness 的分層思維。

### Step 3：先完成最小 roundtrip

先讓系統做到一件事：模型可以請求工具，runtime 真的執行工具，工具結果能回到下一輪，最後 assistant 能產生完成訊息。只要這條主鏈沒有打通，其他周邊能力都不應該先做。

### Step 4：再補 permission denial

加入一個至少會被拒絕的工具情境。這一步非常關鍵，因為它能證明你的系統不是把工具直接裸露給模型，而是真的有治理層。

### Step 5：最後補 session persistence 與 tests

把 message history 寫進 `jsonl` 或其他簡單格式，確保 session 能重新載入。然後補三類基本測試。這時候你的專題才真正從 demo 變成一個最小但完整的 harness。

## 最低完成標準

你的 `mini harness` 至少應達成以下條件：

- 能處理至少一次工具往返的多輪流程
- 至少有兩個工具，而且各自有 `required_permission`
- `read-only` 模式下至少有一個工具會被正確拒絕
- session 可以被寫出並重新載入
- 三類基本測試可以通過
- `README.md` 能清楚說明它和 `claw-code` 的關係

如果上述任何一項缺失，你的作品很可能仍比較像 demo script，而不是教學版 harness。

## 建議的 README 結構

你可以把專題說明寫成以下五段：

1. 這個 `mini harness` 的目標是什麼
2. 它對照 `claw-code` 保留了哪些核心概念
3. v1 刻意不做哪些能力
4. 如何安裝、執行與測試
5. 下一步升級路線是什麼

這樣的 README 不只幫助他人閱讀，也會反過來迫使你釐清自己的設計判斷。

## 自我檢查清單

在交付前，請至少問自己以下問題：

- 我的 runtime 是否真的掌控流程，而不是把所有事交給模型 stub？
- tool schema、dispatch 與 permission requirement 是否有被明確宣告？
- permission policy 是否真的在執行前被呼叫？
- session persistence 是否只是把資料 dump 出去，還是真的能支撐 resume？
- tests 是否在驗證高價值 scenario，而不是只測零碎函式？

## 常見失敗模式

1. 一開始就加太多工具，結果 registry 與權限邊界設計變得混亂。
2. 為了模仿 `claw-code` 而過早加入 `MCP`、remote 或 plugin 機制，最後核心 loop 反而不穩。
3. 只有 happy path，沒有 permission denial 或 session roundtrip。
4. 沒有寫設計說明，導致讀者看不出這個專題到底學到了什麼。

## 建議的加分方向

若你完成最低版本後還有餘力，可以再選一條 `v2` 路線：

- 加入更清楚的 CLI entry
- 加入簡單 config file 與 settings override
- 強化 prompt assembly 與 project context
- 補更多 scenario tests 或簡單 evaluation 指標
- 把 transcript 結構做得更清楚

這些方向都比一開始就跳去 deployment 或 multi-agent orchestration 更適合作為第一個升級台階。

## 最後提醒

這份專題指南的核心精神只有一句話：`保留本質，控制範圍`。你的 `mini harness` 不需要變成 `claw-code`，但它必須足夠完整，能證明你真的理解了 harness 為什麼不是單純 prompt wrapper。只要你能做到這點，這份專題就已經很有價值。
