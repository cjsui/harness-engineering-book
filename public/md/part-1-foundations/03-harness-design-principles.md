# 第 3 章：Harness 的核心設計原則

## 章節導言

知道 agent system 有哪些元件，和知道一個好的 harness 應該怎麼設計，仍然是兩回事。前一章回答的是「它由什麼組成」；這一章要回答的則是「它應該遵守哪些原則」。如果沒有這一層原則意識，你很容易把一個能動的 demo 誤認成一個可長期維護的 system。它可能暫時能跑，但一遇到權限邊界、長對話、上下文混亂、工具失敗或測試需求，就會迅速失控。

本章會把後續整本書不斷重複出現的五個設計原則先拉到前台：`環境感知`、`工具編排`、`Guardrails`、`Session state`、以及 `可觀測性與可測試性`。這五者其實不是附加功能，而是把模型轉變成可工作的 agent harness 所需要的基本條件。少掉其中任何一個，系統都可能還能「看起來能用」，但很難穩定、可控、可擴充。

你也可以把這一章視為一個判準工具。之後不管是在讀 `claw-code`，還是在設計自己的 `mini harness`，都可以反過來問：這個設計是否處理了環境感知？工具是否被清楚編排？權限邊界是否明確？session 是否能維持狀態？系統是否能被觀測與驗證？如果答案模糊，通常就表示這還不是一個成熟的 harness。

## 學習目標
- 能說明一個好的 harness 至少應具備哪些核心設計原則
- 能用 `claw-code` 的實作對照這些原則如何落地
- 能判斷哪些原則在 `mini harness` 中必須保留、哪些可以先縮減

## 核心概念講解
### 環境感知

一個沒有環境感知的模型，只能被動等待人類餵資料。這種系統即使加上了再多 prompt 技巧，本質上仍然是聊天式輔助，而不是工作型 agent。好的 harness 會替模型提供可讀取的工作環境：目前在哪個 workspace、有哪些檔案、有哪些 project rules、是否存在 session history、系統 prompt 應該注入哪些上下文。`claw-code` 的 `runtime` crate 一開頭就把 session persistence、permission evaluation、prompt assembly 放在核心責任說明中，這其實就是在告訴你：環境不是背景，而是 runtime 本身的一部分。

環境感知並不代表把所有東西都塞給模型。真正重要的是有選擇地暴露環境。太少，模型像瞎子；太多，模型會被噪音淹沒、成本上升，甚至混淆目前任務。好的 harness 不只是讓模型「看得到」，還要決定它「該看到什麼」。

### 工具編排

模型要能工作，必須有手腳；但有手腳不代表會工作。工具設計的重點，不只是列出一串可呼叫能力，而是要把工具納入穩定的控制流。工具需要有明確的 schema、清楚的名稱、可預期的輸入輸出格式，以及一致的 dispatch 路徑。這樣 runtime 才能判斷何時呼叫工具、怎麼把結果送回模型、怎麼處理錯誤與停止條件。

因此，好的 harness 不是「工具越多越好」，而是「工具界面越清楚越好」。當工具被編排成穩定的 capability layer，模型的推理才有可靠的落點。否則就算表面上支援很多能力，整體行為也可能非常脆弱。

### Guardrails

工具越強，guardrails 就越重要。這是 agent harness 和一般聊天系統最關鍵的分水嶺之一。`claw-code` 在 `permissions.rs` 裡不是只定義一個簡單的 allow / deny 開關，而是把 `PermissionMode`、`PermissionOutcome`、`PermissionPolicy`、rule matching、以及 prompt-based approval flow 一起納進來。這顯示 guardrails 不是單點機制，而是一整條治理流程。

為什麼需要這麼做？因為模型的問題從來不只是「會不會犯錯」，而是「犯錯時會造成什麼後果」。讀檔錯了，可能只是理解偏差；寫檔錯了，可能直接改壞工作區；跑 shell 錯了，可能造成更大的副作用。因此 guardrails 的作用，不是阻止模型做事，而是把能力放進有邊界的制度中，讓高風險行為要嘛被拒絕，要嘛被明確批准後才執行。

### Session state

沒有 session state 的 agent，只能活在當下。每一輪都重新開始，意味著先前的決策、工具結果、對話脈絡與工作目標都必須重新組裝，這不只低效，也容易產生漂移。好的 harness 會把 session 當成真正的系統狀態容器，而不只是聊天記錄。它要能支援 resume、轉存 transcript、必要時 compact，甚至在長對話中保留足夠的可追溯性。

這個原則很重要，因為 agent work 常常不是一輪完成，而是跨多個回合逐步收斂。若沒有 session state，系統就很難形成穩定的工作記憶；若 session state 設計得太重，又會拖慢系統、增加維護負擔。因此好的設計永遠是在保留必要脈絡與避免上下文膨脹之間找平衡。

### 可觀測性與可測試性

對 agent harness 而言，能跑不等於能維護。你必須能看見系統做了什麼、花了多少 token、做過哪些工具呼叫、為什麼被 permission deny、為什麼在某個 scenario 失敗。這就是可觀測性的價值。`runtime` crate 會重新匯出 `SessionTracer`、`HookRunner`、usage tracking 等能力，表示系統作者不是把執行視為黑箱，而是把觀測點做進核心層。

而可測試性則是更進一步的要求。`mock_parity_harness.rs` 的存在代表 `claw-code` 不滿足於「人工跑起來看起來沒問題」，而是用 deterministic mock service 與 scenario-based assertions 來驗證行為。這背後的原則是：如果你無法穩定重現 agent 行為，就很難真正改進 agent 系統。對一個好的 harness 來說，測試不是善後工作，而是架構設計的一部分。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/rust/crates/runtime/src/lib.rs`
- `claw-code/rust/crates/runtime/src/permissions.rs`
- `claw-code/rust/crates/rusty-claude-cli/tests/mock_parity_harness.rs`

### 閱讀順序
1. 先看 `runtime/src/lib.rs` 頂端的 crate 說明與 `pub use` 範圍
2. 再看 `permissions.rs` 中的 `PermissionMode`、`PermissionOutcome`、`PermissionPolicy`
3. 最後看 `mock_parity_harness.rs` 的 scenario 名稱與 assertion 函式

### 閱讀重點
- `runtime` crate 不只負責 conversation loop，也同時持有 prompt、permissions、session、remote、usage 等關鍵責任，這說明環境感知與狀態管理是 runtime 設計的一部分
- `permissions.rs` 把 allow / deny / ask 做成可組合的政策層，反映 guardrails 是制度設計，而不是零散 if/else
- `mock_parity_harness.rs` 的 `streaming_text`、`read_file_roundtrip`、`write_file_denied`、`bash_permission_prompt_approved` 等 scenario，展示了系統如何把可測試性內建進 harness

## 設計取捨分析

這五個原則之所以難，不是因為它們概念複雜，而是因為它們彼此拉扯。環境感知越強，可能越耗 token、越容易引入噪音；工具越多，能力越強，但治理也越困難；guardrails 越嚴，安全性越高，但互動摩擦也可能增加；session state 越完整，resume 越方便，但上下文負擔也更重；觀測點與測試越多，可靠性越高，但實作成本也更大。

所以好的 harness 設計，不是把每一項原則都拉到最大，而是判斷在當前目標下要做到哪個程度。`claw-code` 作為真實系統，傾向把這些原則做得較完整；本書後面的 `mini harness`，則會保留原則本身，但刻意縮小實作規模。這種「保留本質、壓縮規模」的能力，正是學習 harness engineering 的關鍵。

## Mini Harness 連結點

到了 Part III，我們會用 Python 重做一個教學版系統，而這五個原則會變成實作的最低檢核表。`mini harness` 也需要基本的 project context、需要明確而少量的工具、需要簡化版 permission policy、需要 JSON 或 JSONL 形式的 session state，還需要幾個可重現的測試案例。也就是說，教學版可以更小，但不能失去這些原則；否則做出來的就只是包了幾個 function 的聊天程式，而不是 harness。

## 本章小結

好的 harness 不只是讓模型能回答，而是讓模型能在可理解的環境裡工作、透過清楚的工具採取行動、在 guardrails 中受控、依靠 session 維持狀態，並且整個過程能被觀測與測試。這五個原則共同決定了一個 agent system 是不是只是「看起來很厲害」，還是真正能長期維護與持續擴充。

## 章末練習
1. 比較「環境感知」與「人工貼上下文」兩種工作方式的差異。
2. 為一個只有 `read`、`write`、`bash` 三個工具的 agent system 設計最小 guardrail 策略。
3. 解釋為什麼「可測試性」應該被視為 harness 設計原則，而不是開發後期才補的工作。

## 反思問題

- 你覺得在真實工作情境中，哪一個原則最容易被初學者忽略？為什麼？
- 如果只能在第一版系統裡保留三個原則，你會選哪三個？你願意承擔另外兩個被削弱後的什麼代價？
- 你是否曾經用過「看起來很聰明，但其實很難信任」的 AI 工具？現在回頭看，它缺的是哪個原則？

## 延伸閱讀 / 下一章預告

下一章我們要從原則走向方法，正式討論：當你面對一個像 `claw-code` 這樣的真實大型 repo，應該怎麼讀才不會迷路。換句話說，第 4 章要教你的不是某個 API，而是閱讀 agent harness 的策略本身。
