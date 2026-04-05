# 第 5 章：從 CLI 入口看整個系統

## 章節導言

要理解一個真實 harness，最自然的入口往往不是最深的 runtime 原始碼，而是 `CLI`。原因很簡單：CLI 是人真正碰到系統的第一層，也是很多系統責任第一次顯形的地方。你會在這裡看到有哪些 subcommands、有哪些旗標、什麼情況下進 REPL、什麼情況下走 one-shot prompt、以及哪些能力其實只是查詢系統狀態而不會啟動完整 agent loop。

對 `claw-code` 來說，這一層尤其重要，因為 `rusty-claude-cli/src/main.rs` 不只是單純解析參數，它同時把 mode routing、resume flow、輸出格式、permission mode、allowed tools、status/sandbox/skills/mcp/system-prompt 等 surface action 整理成一個可操作的前台。換句話說，它不是「外面包一層 command line」而已，而是整個系統如何向人類暴露自身能力的地方。

本章要做的，就是從 CLI surface 反推整個系統邏輯。你會看到，真實 harness 的入口層其實已經透露很多架構訊號：哪些東西是執行核心，哪些是檢視或管理功能，哪些是 session continuation，哪些是環境快照。讀懂這一層，你後面再回頭看 runtime，就比較不會把所有功能都混成單一 agent loop。

## 學習目標
- 能說明 `claw-code` 的 CLI surface 如何映射到不同系統責任
- 能區分 subcommands、one-shot prompt、REPL 與 resume 模式
- 能理解 mode routing 為什麼是大型 harness 不可缺少的入口層能力

## 核心概念講解
### CLI entry

`claw-code` 的 CLI 不是單一「問模型一個問題」的介面，而是一個多模式系統入口。從 `USAGE.md` 與 `main.rs` 可看出，使用者可以用 interactive REPL、`prompt` one-shot、shorthand prompt、`--resume`、`status`、`sandbox`、`agents`、`mcp`、`skills`、`system-prompt`、`login`、`logout` 等多種方式進入系統。這說明 CLI 層不只是 command parser，而是整個 harness 的 front door。

從架構角度看，這一點很重要。因為一個成熟 harness 並不只有「執行任務」這一種工作。它還要能顯示狀態、檢查環境、恢復 session、輸出 system prompt、管理認證。把這些能力都放在 CLI surface，不是讓系統更雜，而是讓不同責任有清楚的人類操作入口。

### subcommands

`main.rs` 裡的 `CliAction` 很值得讀，因為它幾乎就是一張系統功能清單。像 `CliAction::Prompt` 會進入一次性任務執行；`CliAction::Status` 與 `CliAction::Sandbox` 則偏向觀測與快照；`CliAction::Agents`、`CliAction::Mcp`、`CliAction::Skills` 屬於能力檢視；`CliAction::PrintSystemPrompt` 則讓 prompt assembly 可被獨立檢查；`Login` / `Logout` 則屬於認證生命週期。

這表示 subcommands 並不是隨便長出來的功能分頁，而是把不同系統責任切成可直接操作的視角。從教學角度看，這很有幫助，因為它提醒你：真實 harness 的使用者需求不只有「請模型做事」，還包括理解系統狀態與診斷環境。

### one-shot vs REPL

`USAGE.md` 很清楚區分了 interactive REPL 與 one-shot prompt。REPL 適合多輪工作，會持續保留 session；one-shot prompt 則適合腳本化、自動化或單次查詢。這種區分並不只是 UX 差異，而是系統操作模型的差異。REPL 假設你要和一個持續中的 conversation runtime 互動；one-shot 則假設你要快速完成一個單輪任務。

真實 harness 為什麼要同時保留這兩種模式？因為它們服務的場景不同。REPL 更適合探索、修補、反覆修正；one-shot 更適合 automation、CI、簡短分析或 shell pipeline。若只有 REPL，腳本整合會變差；若只有 one-shot，很多 agentic workflow 會被迫重新組 session。CLI surface 把兩者都納入，等於承認 agent 工具不只有一種使用型態。

### mode routing

`mode routing` 是這一章真正的架構重點。從 `main.rs` 的參數解析可看到，系統會先處理像 `--output-format`、`--permission-mode`、`--allowedTools`、`--resume` 等旗標，再決定最終進入哪一條執行路徑。也就是說，CLI 層不是被動轉發，而是先把使用者意圖翻譯成較高層的執行模式。

例如：有 `--resume` 時會走 `parse_resume_args()` 與 resumed command flow；有 `system-prompt` 時會走 prompt rendering；輸入 `status` 或 `sandbox` 則走 snapshot path；沒指定 subcommand 時，甚至可能直接把剩餘字串視為 prompt。這些 routing 規則讓系統 surface 看起來自然，但內部仍保持相對清楚的模式分流。

這個分流若被拿掉會怎樣？系統會變成一個只會「把文字交給模型」的大入口，許多 operational functions 不是消失，就是被迫塞進互動式 session 內，結果人和系統都更難操作。對真實 harness 來說，入口分流就是可用性與可維運性的第一層設計。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/USAGE.md`
- `claw-code/rust/README.md`
- `claw-code/rust/crates/rusty-claude-cli/src/main.rs`

### 閱讀順序
1. 先讀 `USAGE.md`，看使用者視角下有哪些操作模式
2. 再讀 `rust/README.md`，確認 `rusty-claude-cli` 在 workspace 裡的責任
3. 最後讀 `main.rs`，追 `CliAction`、參數解析與 mode routing

### 閱讀重點
- `CLI` entry 如何承載 subcommands 與 operational surfaces
- `prompt`、interactive REPL、`--resume` 如何對應不同工作模式
- `permission-mode`、`allowedTools`、`output-format` 為何在入口層就要先決定
- `system-prompt`、`status`、`sandbox` 這些命令如何透露 runtime 以外的系統面能力

## 設計取捨分析

CLI surface 的最大取捨，是「簡單入口」與「多責任入口」之間的平衡。若只保留單一 prompt 入口，系統會看起來很單純，但很多狀態檢查、環境診斷與 session 恢復工作都會變得笨重；若把所有能力都做成獨立命令，則入口會變厚、學習成本也會上升。`claw-code` 的做法，是接受入口層較豐富的複雜度，換取更完整的 operational surface。

另一個取捨則是 CLI 是否應該過早知道太多 runtime 細節。`claw-code` 沒有讓 CLI 完全變成薄殼，因為像 mode routing、resume、system-prompt rendering 這些本來就屬於入口層責任；但它也沒有把 runtime loop 細節全塞進 `main.rs`。這種分層值得學，因為它說明「入口負責決定去哪裡，不負責成為所有業務邏輯本身」。

## Mini Harness 連結點

`mini harness` 不需要一開始就複製整個 CLI surface，但至少應該保留一個很小的 entry model，例如：`run`、`prompt`、`resume` 三種最基本模式。也就是說，教學版仍然要讓學生看到 `CLI` 不是單純收字串，而是系統如何決定要開新 session、恢復舊 session、或執行一次性任務的地方。完整 `claw-code` 多做的部分，是更豐富的 operational commands 與 mode routing；教學版則保留其中最能教會人的骨架。

## 本章小結

從 `CLI` 入口看 `claw-code`，你會發現它不是單一 prompt 工具，而是一個有 subcommands、有 one-shot / REPL 差異、有 resume flow、有狀態與環境命令的完整系統 surface。入口層的價值，不只是讓人按下開始，而是把不同的系統責任整理成可操作模式。理解這一層，後面讀 session、prompt assembly、config 時都會更有方向。

## 章末練習
1. 說明為什麼 `status`、`sandbox`、`system-prompt` 這類命令對 harness 來說不是可有可無。
2. 比較 one-shot prompt 與 REPL 在 session 與使用情境上的差異。
3. 如果你要為 `mini harness` 設計最小 CLI surface，你會保留哪三個命令或模式？為什麼？

## 反思問題

- 你過去是否把 CLI 想成只是輸入 prompt 的外殼？現在回頭看，這種理解少了哪一層系統視角？
- 如果一個 agent 工具完全沒有 resume mode，你覺得最受影響的是哪類工作流？
- 對教學版來說，你會先教 subcommands 還是先教 runtime？兩者順序會影響理解方式嗎？

## 延伸閱讀 / 下一章預告

既然入口層已經告訴我們系統有 `--resume`、有多輪工作流，那下一章就自然要問：這些狀態到底保存在哪裡，又如何被帶回來？第 9 章會進入 `session`、`transcript`、`resume` 與 `compaction`，把 agent 的持續性講清楚。
