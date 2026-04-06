# 第 5 章：從 CLI 入口看整個系統

## 章節導言

要理解一個真實 harness，最自然的入口往往不是最深的 runtime 原始碼，而是 `CLI`。原因很簡單：CLI 是人真正碰到系統的第一層，也是很多系統責任第一次顯形的地方。你會在這裡看到有哪些 subcommands、有哪些旗標、什麼情況下進 REPL、什麼情況下走 one-shot prompt、以及哪些能力其實只是查詢系統狀態而不會啟動完整 agent loop。

對 `claw-code` 來說，這一層尤其重要，因為 `rusty-claude-cli/src/main.rs` 不只是單純解析參數，它同時把 mode routing、resume flow、輸出格式、permission mode、allowed tools、status/sandbox/skills/mcp/system-prompt 等 surface action 整理成一個可操作的前台。換句話說，它不是「外面包一層 command line」而已，而是整個系統如何向人類暴露自身能力的地方。

本章要做的，就是從 CLI surface 反推整個系統邏輯。你會看到，真實 harness 的入口層其實已經透露很多架構訊號：哪些東西是執行核心，哪些是檢視或管理功能，哪些是 session continuation，哪些是環境快照。讀懂這一層，你後面再回頭看 runtime，就比較不會把所有功能都混成單一 agent loop。

> ### 📋 本章速覽
> 
> 讀完本章，你將會學到：
> - CLI 不只是「輸入文字的地方」，而是整個系統功能的總覽大廳
> - subcommands 如何把不同系統責任切成獨立操作入口
> - one-shot prompt 與 REPL 的差異不只是 UX，而是不同的系統操作模型
> - mode routing 如何在入口層就決定系統該走哪條路
> - 為什麼成熟的 agent 工具需要狀態檢查、環境診斷等「非執行型」命令

## 學習目標
- 能說明 `claw-code` 的 CLI surface 如何映射到不同系統責任
- 能區分 subcommands、one-shot prompt、REPL 與 resume 模式
- 能理解 mode routing 為什麼是大型 harness 不可缺少的入口層能力

### 📝 先備知識檢查

在開始本章之前，請確認你已經了解以下概念：

- [ ] 知道什麼是 CLI（Command-Line Interface），用過終端機輸入指令
- [ ] 理解 REPL 的基本概念（輸入 → 執行 → 輸出 → 等待下一次輸入的循環）
- [ ] 知道什麼是 subcommand（例如 `git commit`、`git push` 中的 `commit` 和 `push`）
- [ ] 大致了解前幾章提到的 harness 概念（不需記住所有細節）

## 核心概念講解
### CLI entry

`claw-code` 的 CLI 不是單一「問模型一個問題」的介面，而是一個多模式系統入口。從 `USAGE.md` 與 `main.rs` 可看出，使用者可以用 interactive REPL、`prompt` one-shot、shorthand prompt、`--resume`、`status`、`sandbox`、`agents`、`mcp`、`skills`、`system-prompt`、`login`、`logout` 等多種方式進入系統。這說明 CLI 層不只是 command parser，而是整個 harness 的 front door。

從架構角度看，這一點很重要。因為一個成熟 harness 並不只有「執行任務」這一種工作。它還要能顯示狀態、檢查環境、恢復 session、輸出 system prompt、管理認證。把這些能力都放在 CLI surface，不是讓系統更雜，而是讓不同責任有清楚的人類操作入口。

> 💡 **生活化比喻**：想像 CLI 就像一棟大樓的「總服務台」。你不會期望服務台只能幫你按電梯，它還能幫你查房間號碼（status）、看訪客紀錄（resume）、確認大門是否鎖好（sandbox）、甚至重新登記你的身份（login/logout）。CLI 做的就是這種「多功能總服務台」的角色，讓你不用每次都跑進大樓深處才能做事。

### subcommands

`main.rs` 裡的 `CliAction` 很值得讀，因為它幾乎就是一張系統功能清單。像 `CliAction::Prompt` 會進入一次性任務執行；`CliAction::Status` 與 `CliAction::Sandbox` 則偏向觀測與快照；`CliAction::Agents`、`CliAction::Mcp`、`CliAction::Skills` 屬於能力檢視；`CliAction::PrintSystemPrompt` 則讓 prompt assembly 可被獨立檢查；`Login` / `Logout` 則屬於認證生命週期。

這表示 subcommands 並不是隨便長出來的功能分頁，而是把不同系統責任切成可直接操作的視角。從教學角度看，這很有幫助，因為它提醒你：真實 harness 的使用者需求不只有「請模型做事」，還包括理解系統狀態與診斷環境。

> 💡 **生活化比喻**：subcommands 就像手機主畫面上的不同 App。你打開「設定」是管理系統、打開「相簿」是看資料、打開「訊息」是溝通。它們都住在同一支手機（CLI）裡，但各自負責不同的事。把所有功能塞進一個 App 裡反而會讓人搞不清楚自己在做什麼。

### one-shot vs REPL

`USAGE.md` 很清楚區分了 interactive REPL 與 one-shot prompt。REPL 適合多輪工作，會持續保留 session；one-shot prompt 則適合腳本化、自動化或單次查詢。這種區分並不只是 UX 差異，而是系統操作模型的差異。REPL 假設你要和一個持續中的 conversation runtime 互動；one-shot 則假設你要快速完成一個單輪任務。

真實 harness 為什麼要同時保留這兩種模式？因為它們服務的場景不同。REPL 更適合探索、修補、反覆修正；one-shot 更適合 automation、CI、簡短分析或 shell pipeline。若只有 REPL，腳本整合會變差；若只有 one-shot，很多 agentic workflow 會被迫重新組 session。CLI surface 把兩者都納入，等於承認 agent 工具不只有一種使用型態。

> 💡 **生活化比喻**：REPL 就像去餐廳用餐——你坐下來、點餐、加點、慢慢吃、最後結帳，整個過程是持續的。one-shot 就像路邊攤外帶——你說「一份雞排」，付錢、拿走、結束。兩種都是「吃東西」，但運作方式完全不同。一個好的系統會同時提供兩種選擇，讓使用者依情境挑最適合的。

> ⚠️ **初學者常見誤區**：很多人以為 one-shot 就是「功能比較少的 REPL」，其實不是。one-shot 的設計重點在於「不留狀態、快速完成」，它天生更適合自動化腳本和 CI 流程。不要把 one-shot 當成 REPL 的閹割版，它們是服務不同場景的獨立模式。

### mode routing

`mode routing` 是這一章真正的架構重點。從 `main.rs` 的參數解析可看到，系統會先處理像 `--output-format`、`--permission-mode`、`--allowedTools`、`--resume` 等旗標，再決定最終進入哪一條執行路徑。也就是說，CLI 層不是被動轉發，而是先把使用者意圖翻譯成較高層的執行模式。

例如：有 `--resume` 時會走 `parse_resume_args()` 與 resumed command flow；有 `system-prompt` 時會走 prompt rendering；輸入 `status` 或 `sandbox` 則走 snapshot path；沒指定 subcommand 時，甚至可能直接把剩餘字串視為 prompt。這些 routing 規則讓系統 surface 看起來自然，但內部仍保持相對清楚的模式分流。

這個分流若被拿掉會怎樣？系統會變成一個只會「把文字交給模型」的大入口，許多 operational functions 不是消失，就是被迫塞進互動式 session 內，結果人和系統都更難操作。對真實 harness 來說，入口分流就是可用性與可維運性的第一層設計。

> 💡 **生活化比喻**：mode routing 就像機場的報到櫃台。你出示不同的條件（商務艙？經濟艙？線上報到？轉機？）櫃台就會引導你走不同的通道。你不需要知道背後有幾條通道，你只需要告訴系統你的意圖，它就會把你送到正確的地方。如果機場只有一個通道讓所有人擠，效率和體驗都會很差。

> ⚠️ **初學者常見誤區**：不要以為 mode routing 只是「方便使用者」的 UX 功能。它同時也是系統內部維持清晰架構的關鍵——讓不同邏輯走不同路徑，而不是全部擠在同一個 if/else 叢林裡。routing 的好壞直接影響系統的可維護性。

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

### ✅ 學習自我檢核

完成本章後，請確認你是否能做到以下幾點：

- [ ] 我能解釋為什麼 CLI 不只是「輸入 prompt 的外殼」，而是系統功能的總入口
- [ ] 我能區分 one-shot prompt 和 REPL 各自適合的使用場景
- [ ] 我能說出至少三種 subcommand 分別負責什麼樣的系統責任
- [ ] 我能解釋 mode routing 的作用——為什麼系統需要在入口層就決定執行路徑
- [ ] 我能說明 `--resume` 對 agent 工作流的重要性
- [ ] 我理解「入口負責分流，不負責成為業務邏輯本身」這個設計原則

## 📖 關鍵概念速查表

| 術語 | 說明 |
|------|------|
| **CLI（Command-Line Interface）** | 命令列介面，使用者透過文字指令操作系統的入口 |
| **subcommand** | CLI 下的子命令，例如 `status`、`prompt`、`login`，各自對應不同系統責任 |
| **REPL** | Read-Eval-Print Loop，互動式多輪對話模式，session 持續保留 |
| **one-shot prompt** | 一次性任務執行模式，適合腳本化與自動化 |
| **mode routing** | 入口層的模式分流機制，根據旗標與子命令決定走哪條執行路徑 |
| **resume flow** | 恢復先前中斷的 session 繼續工作的流程 |
| **operational surface** | 系統向使用者暴露的所有可操作功能的集合 |
| **CliAction** | `main.rs` 中定義的列舉型別，代表所有可能的 CLI 操作模式 |

## 章末練習
1. 說明為什麼 `status`、`sandbox`、`system-prompt` 這類命令對 harness 來說不是可有可無。
2. 比較 one-shot prompt 與 REPL 在 session 與使用情境上的差異。
3. 如果你要為 `mini harness` 設計最小 CLI surface，你會保留哪三個命令或模式？為什麼？

## 反思問題

- 你過去是否把 CLI 想成只是輸入 prompt 的外殼？現在回頭看，這種理解少了哪一層系統視角？
- 如果一個 agent 工具完全沒有 resume mode，你覺得最受影響的是哪類工作流？
- 對教學版來說，你會先教 subcommands 還是先教 runtime？兩者順序會影響理解方式嗎？

> ### 💬 本章一句話總結
> 
> **CLI 不是系統的外殼，而是系統責任的總覽大廳——從入口分流就開始決定整個系統怎麼運作。**

## 延伸閱讀 / 下一章預告

既然入口層已經告訴我們系統有 `--resume`、有多輪工作流，那下一章就自然要問：這些狀態到底保存在哪裡，又如何被帶回來？第 9 章會進入 `session`、`transcript`、`resume` 與 `compaction`，把 agent 的持續性講清楚。
