# 第 9 章：Session、Transcript、Memory

## 章節導言

一個 agent 若每一輪都從零開始，理論上仍能回答問題，但很難成為真正可工作的系統。因為真實任務往往不是一輪完成，而是跨多輪逐步收斂：讀檔、執行工具、修正、再問、再比對。這時候，`session` 就不只是方便功能，而是 agent 能不能維持工作脈絡的核心機制。

`claw-code` 的 session 設計很值得學，因為它不是把 conversation history 當成一塊模糊字串，而是把每筆訊息、tool result、usage metadata、compaction 狀態與 fork provenance 都做成結構化資料。這讓 `transcript` 不只是可讀記錄，同時也是 runtime 可以恢復、追蹤與壓縮的狀態容器。

本章要處理四個核心問題：什麼是 `session persistence`、什麼是 `transcript`、`resume` 為什麼能成立、以及長對話時為什麼需要 `compaction`。理解這四者後，你會更清楚 agent 的「記憶」其實不是單一 feature，而是狀態保存、重播、摘要與使用成本管理一起構成的系統能力。

## 學習目標
- 能解釋 `session`、`transcript`、`resume`、`compaction` 在 `claw-code` 中的角色
- 能說明結構化 session 為什麼比單純聊天記錄更適合 agent harness
- 能判斷 `mini harness` 應保留哪些 session 能力，哪些可暫時簡化

## 核心概念講解
### session persistence

`session.rs` 裡的 `Session` 不是只有一個 message list。它至少包含版本、`session_id`、建立與更新時間、`messages`、`compaction`、`fork`，以及可選的 persistence path。這說明 session 在 `claw-code` 裡不是暫時對話快取，而是一個正式的持久化狀態物件。

更重要的是，它真的會寫到檔案。`save_to_path()` 會把當前 session snapshot 寫出，`with_persistence_path()` 與 `append_persisted_message()` 則讓新訊息能被追加到持久化檔案中。也就是說，session 不是靠「程式還活著」才存在，而是被設計成可中斷、可恢復、可重播的狀態容器。這正是 `session persistence` 的意義。

### transcript

很多人會把 transcript 理解成「聊天紀錄」，但在 agent harness 裡，transcript 更像「行為紀錄與狀態日誌」。`ConversationMessage` 不是只有 user 與 assistant 文本，它還可以包含 `ContentBlock::ToolUse` 與 `ContentBlock::ToolResult`。這表示 transcript 會記住模型曾要求什麼工具、工具回了什麼結果、那個結果是否是 error。

這個差異很重要。若 transcript 只保存最後的人類可讀文字，很多 agent 行為就無法被重建。runtime 不知道上一輪執行過什麼工具，testing 也難以還原 bug。正因為 transcript 是結構化的，所以它同時服務於使用者理解、runtime resume、以及後續 debugging。

### resume

`resume` 之所以能成立，不是因為有一個神奇命令，而是因為系統一直有在保存結構化 session。`USAGE.md` 明確寫到 REPL turns 會持久化在當前 workspace 的 `.claw/sessions/` 底下，而 CLI 也提供 `--resume latest` 之類的入口。當使用者恢復 session 時，系統不是只把一段文字再貼回 prompt，而是重新載入先前的結構化狀態。

`Session::load_from_path()` 更進一步展現了這點：它可以從 JSON object 或 JSONL 內容載入 session，再配上 persistence path。這意味著 resume flow 本質上是「讀取並重建狀態」，而不是「重新開始並希望模型自己記得」。從 harness engineering 的角度看，這正是狀態管理與單純聊天 UI 的分界之一。

### compaction

只保存狀態還不夠，因為長對話會讓上下文不斷膨脹。這時候 `compaction` 就變得重要。`SessionCompaction` 與 runtime 中的 auto-compaction 機制說明，`claw-code` 並沒有假裝上下文可以無限累積，而是承認 session 需要被摘要與瘦身。這讓系統能在維持工作記憶的同時，控制 token 成本與 prompt 長度。

這裡 `usage.rs` 也扮演關鍵角色。`UsageTracker::from_session()` 會從現有 session 重建累積 usage，表示 usage 並不是和 session 分離的後置報表，而是 session management 的一部分。因為只有知道累積 token 與成本，runtime 才能更合理地決定何時需要 compaction。這也是為什麼本章同時讀 `session.rs` 與 `usage.rs` 特別有意義。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/rust/crates/runtime/src/session.rs`
- `claw-code/rust/crates/runtime/src/usage.rs`
- `claw-code/USAGE.md`

### 閱讀順序
1. 先讀 `USAGE.md` 的 session management 段落
2. 再讀 `session.rs` 的 `Session`、`ConversationMessage`、`ContentBlock`
3. 最後讀 `usage.rs` 的 `UsageTracker`，看 usage 如何從 session 回建

### 閱讀重點
- `session` 如何被保存、載入與追加寫入
- `transcript` 為什麼包含 tool use / tool result，而不只是純文字
- `resume` 為什麼是狀態重建，而不是簡單重新開聊
- `compaction` 與 usage tracking 如何共同處理長對話成本

## 設計取捨分析

session 系統的最大取捨，是「保存越完整」與「維護越複雜」之間的平衡。若只保留簡單文字紀錄，系統容易做，但 agent 狀態很難真正恢復；若把每個 message、tool result、usage、fork、compaction 都結構化保存，系統可恢復性與可除錯性會更好，但格式設計、載入相容性與維護成本也會上升。`claw-code` 明顯選擇了後者，因為它面向的是真實長流程工作，而不是短暫聊天。

另一個取捨則是 compaction。若完全不做，系統邏輯簡單，但長期成本與上下文負擔會持續增加；若過度積極 compaction，又可能失去對後續推理很重要的細節。因此成熟 harness 必須把 `session`、`transcript`、`resume`、`usage` 一起看，而不是把它們當成互不相干的小功能。

## Mini Harness 連結點

`mini harness` 在 session 這一層最值得保留的，是結構化訊息、最小 persistence、以及簡單的 `resume`。教學版大概不需要一開始就做 rotation、fork provenance、完整 compaction metadata 或較細的 usage 成本估算；但至少應該讓學生看到：`session` 不是一個列表暫存，而是一個會被寫出、再讀回、讓系統繼續工作的狀態容器。完整 `claw-code` 加上的，則是更成熟的 transcript 結構與長對話維護能力。

## 本章小結

在 `claw-code` 裡，`session` 不只是保存聊天內容，而是承載 `transcript`、tool results、usage、resume、compaction 等能力的核心狀態容器。它讓 agent work 可以跨回合延續，也讓 runtime 與測試能基於結構化紀錄重建先前行為。理解這一層，才能真正明白為什麼多輪 agent 系統不能只靠「模型記得剛剛在說什麼」。

## 章末練習
1. 解釋為什麼 agent transcript 需要保存 tool use 與 tool result，而不只是最終回答。
2. 說明 `resume` 為什麼依賴 session persistence，而不是只依賴 prompt wording。
3. 如果你要為 `mini harness` 設計最小 session 格式，你會保留哪些欄位？哪些先不做？

## 反思問題

- 你覺得很多人為什麼會把 session 問題低估成「只是聊天記錄」？
- 若一個系統只有 resume、沒有 compaction，長期最可能出現什麼問題？
- 如果 transcript 足夠完整，你認為它除了 resume 之外，還能支援哪些工程工作？

## 延伸閱讀 / 下一章預告

第 9 章處理的是系統如何保存自己；下一章要處理的，則是系統如何向模型描述自己所處的世界。第 10 章會進入 `Prompt Assembly` 與 `ProjectContext`，看 `claw-code` 如何把 `CLAUDE.md`、git 狀態、工作目錄與動態環境資訊組進 system prompt。
