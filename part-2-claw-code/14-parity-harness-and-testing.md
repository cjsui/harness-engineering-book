# 第 14 章：Parity Harness 與測試哲學

## 章節導言

到了這裡，你已經看過 runtime、tools、permissions 等核心結構，也大致理解 `claw-code` 怎麼把模型變成可行動的 agent。接下來最重要的一個問題是：你怎麼知道這套系統真的可靠？如果 agent system 會跨越模型輸出、工具執行、權限檢查、session persistence、CLI 表面與 JSON 輸出，那麼只靠人工點幾次、跑幾個 happy path，通常遠遠不夠。

`claw-code` 的一個關鍵成熟訊號，就是它沒有把驗證停留在「我手動試過，感覺可以」，而是建立了 deterministic 的 mock parity harness。這種做法的重點，不只是測試有沒有過，而是把 agent 行為拆成一組具體 scenario，然後對每一個 scenario 設定可重現的輸入、可檢查的輸出、可比對的 side effect 與可追蹤的 parity 目標。這比一般單元測試更接近真實 agent harness 的需求。

本章會先說明為什麼手動測試不夠，再討論 mock service 的價值、scenario-based verification 的設計思路，以及 deterministic harness 為何對 agent 系統特別重要。你會看到，測試在這裡不是單純的 QA 程序，而是架構的一部分。

## 學習目標
- 能說明為什麼 agent harness 需要 deterministic 的 parity 驗證
- 能解釋 mock service、scenario manifest、assertion functions 如何共同構成測試系統
- 能把 `claw-code` 的測試哲學轉譯成 `mini harness` 的基本驗證策略

## 核心概念講解
### 為什麼手動測試不夠

agent harness 的特殊之處，在於它不是只有一個函式輸入與輸出，而是多層次互動：模型可能先輸出文字、再發出 tool use、再根據工具結果給出最後回答；中間還可能牽涉 permission prompt、session 更新、token usage、甚至 auto compaction。這樣的系統如果只靠人工測試，很容易出現三個問題：第一，覆蓋不完整；第二，不容易重現；第三，很難比較回歸差異。

例如你今天手動試到 `write_file` 正常，不代表 `write_file_denied`、`multi_tool_turn_roundtrip`、`token_cost_reporting` 也正常。更麻煩的是，即使人工測到問題，你也不一定能在同樣條件下穩定重現。這對 agent 系統特別致命，因為很多 bug 不是靜態語法錯誤，而是流程錯誤、狀態錯誤、或邊界條件錯誤。

### mock service 的價值

`claw-code` 的 mock parity harness 不是只寫幾個 assertion，而是先建立 deterministic mock Anthropic-compatible service，再讓 CLI harness 在乾淨環境中對這個 mock 服務發出請求。這樣做的價值很高，因為它把模型供應者的變動性從測試中隔離出來。你不是在和一個真實、隨時可能漂移的外部模型服務比較，而是在和一個可控制、可腳本化的回應源頭互動。

這使得很多 agent-specific 行為終於能被穩定測。像 `streaming_text` 可以專注驗證 streamed text；`read_file_roundtrip` 可以驗證 tool execution 後的最終 synthesis；`bash_permission_prompt_approved` 與 `bash_permission_prompt_denied` 可以檢查同一條 permission path 在不同 approval 下是否行為分岔正確。mock service 的價值，不是「比較省 API 錢」而已，而是讓系統回到可工程化驗證的狀態。

### scenario-based verification

`mock_parity_scenarios.json` 把 parity harness 的核心思想寫得很清楚：每個測試不是抽象功能點，而是一個有名字、有類別、有描述、有 parity 參照的 scenario。裡面列出的場景包括：

- `streaming_text`
- `read_file_roundtrip`
- `grep_chunk_assembly`
- `write_file_allowed`
- `write_file_denied`
- `multi_tool_turn_roundtrip`
- `bash_stdout_roundtrip`
- `bash_permission_prompt_approved`
- `bash_permission_prompt_denied`
- `plugin_tool_roundtrip`
- `auto_compact_triggered`
- `token_cost_reporting`

這些場景之所以有教學價值，是因為它們把系統拆成可對話的能力斷面。例如 `write_file_allowed` 與 `write_file_denied` 不是兩個重複案例，而是用來檢查同一個工具在不同 permission mode 下是否遵守邊界；`multi_tool_turn_roundtrip` 則不是單純多做幾次工具，而是在驗證同一 assistant turn 中多個工具往返的控制流是否正確；`auto_compact_triggered` 則把長對話下的 session 維護能力拉進測試範圍。這就是真正的 scenario-based verification：不是測功能名詞，而是測行為情境。

### deterministic harness 的意義

deterministic harness 的真正意義，是讓 agent 行為從「感覺上可用」變成「可證明地一致」。在 `mock_parity_harness.rs` 裡，每個 scenario 都對應一個 assertion function，例如 `assert_streaming_text`、`assert_read_file_roundtrip`、`assert_write_file_denied`、`assert_plugin_tool_roundtrip`、`assert_auto_compact_triggered`、`assert_token_cost_reporting`。這表示測試不是只有「有沒有跑完」，而是對每個情境明確指定要檢查什麼。

對 agent harness 來說，這種 deterministic 設計尤其重要，因為它讓你可以分清楚兩類變動：一類是預期內的架構變更，一類是非預期的行為回歸。如果沒有 deterministic harness，你很難知道某次改動是正確擴充、還是意外破壞某條 permission 路徑、某個 tool synthesis、或某個 JSON usage output。換句話說，determinism 不是奢侈品，而是讓 agent 系統能持續演化的前提。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/rust/crates/rusty-claude-cli/tests/mock_parity_harness.rs`
- `claw-code/rust/mock_parity_scenarios.json`

### 閱讀順序
1. 先讀 `mock_parity_scenarios.json`，看有哪些 scenario 類別與描述
2. 再讀 `mock_parity_harness.rs` 開頭的 scenario 註冊區段
3. 最後抽讀幾個 assertion function，例如 `assert_write_file_denied`、`assert_multi_tool_turn_roundtrip`、`assert_token_cost_reporting`

### 閱讀重點
- scenario list：有哪些情境被當成 parity coverage 的最低集合
- permission approved / denied paths：同一工具或能力在不同 approval 狀態下如何被驗證
- write_file allowed / denied：能力與 guardrail 如何被一起測
- token cost reporting：系統不只要功能對，還要把 usage / cost 等運維資訊輸出正確

## 設計取捨分析

parity harness 的設計成本不低。你需要 mock service、scenario manifest、乾淨環境包裝、assertion functions，還要維護它們與系統功能的一致性。從短期速度看，這當然比手動測試重得多。但它換來的，是 agent harness 極需要的三種能力：可重現、可回歸比較、可擴充驗證面。

另一個取捨是 scenario granularity。scenario 太粗，很多回歸會被藏起來；太細，維護成本會飆高。`claw-code` 的做法值得學，因為它挑的是一組對 agent 行為最關鍵的斷面：streaming、file tools、permission branching、multi-tool turns、plugin path、session compaction、token cost。這些不是任意挑選，而是直接對應一個真實 harness 最容易壞、也最值得保證的部分。

## Mini Harness 連結點

`mini harness` 不需要第一天就複製整套 parity harness，但它應該學這個哲學：不要只寫「函式回傳 1 或 0」的低價值測試，而要挑幾個能代表整體行為的 scenario。對教學版來說，至少可以保留三類：runtime turn 正常往返、permission denial、session persistence roundtrip。如果能再加入一個簡化的 multi-tool turn 測試，那就更接近真實 agent harness 的精神。重點不是測試數量，而是測試是否真的覆蓋行為邏輯。

## 本章小結

`claw-code` 的 parity harness 展示了 agent 測試哲學的成熟版本：用 deterministic mock service 固定模型側行為，用 scenario manifest 定義覆蓋範圍，再用 assertion functions 對每個行為情境做具體檢查。這讓 testing 不再只是補充程序，而成為保障 runtime、tools、permissions、session 與 usage layer 共同正確運作的架構機制。

## 章末練習
1. 說明為什麼手動測試不足以驗證一個真實 agent harness。
2. 比較 `write_file_allowed` 與 `write_file_denied` 這兩個 scenario 在測試哲學上的差異。
3. 為 `mini harness` 設計三個最小但有代表性的 scenario-based tests。

## 反思問題

- 你認為在 agent 系統裡，最值得優先 deterministic 化的行為是哪一類：工具往返、權限分支、session 管理，還是 usage/cost 輸出？為什麼？
- 如果某個團隊只測 happy path，不測 denied path 與 degraded path，長期最可能在哪裡踩雷？
- 你是否同意「測試其實是對系統邊界的再次設計」這句話？為什麼？

## 延伸閱讀 / 下一章預告

讀完第 14 章後，你應該更能理解：runtime、tools、permissions、session 不是孤立模組，而是一組需要共同被驗證的行為系統。之後當我們在第 15 章回頭把 `claw-code` 當成整體來理解時，這種「從 end-to-end 行為回看架構」的視角會變得特別重要。
