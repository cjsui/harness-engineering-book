# 第 10 章：Prompt Assembly 與 Project Context

## 章節導言

很多初學者一聽到 system prompt，就直覺想到一大段固定文字。但在真實 harness 裡，`Prompt Assembly` 幾乎從來不是靜態字串。它通常是一個動態組裝流程，會把工作目錄、日期、平台資訊、instruction files、git 狀態、設定檔內容與附加章節一起拼成模型真正看到的上下文。也就是說，prompt 在這裡不是文案，而是 runtime 建構出來的環境描述。

`claw-code` 的 `prompt.rs` 很值得學，因為它把這個流程寫得很明確。它不只提供 `load_system_prompt()`，還定義了 `ProjectContext`、`ContextFile`、`SystemPromptBuilder`、instruction-file discovery、environment section、config section、以及 `CLAUDE.md` 記憶的注入方式。這些設計共同說明一件事：高品質 agent prompt，來自系統化 context injection，而不是只靠人臨時補充背景。

本章要回答的核心問題有四個：什麼是 system prompt、什麼是 project context、context injection 到底注入了什麼、以及 `CLAUDE.md` / instruction files 為何能被視為一種專案記憶。理解這四點，你就會知道 prompt assembly 其實是 harness 裡最容易被低估、但又最影響 agent 表現穩定度的核心層之一。

> **📋 本章速覽**
>
> 讀完本章後，你將能夠：
> - 理解 system prompt 不是一段寫死的文字，而是被動態組裝出來的
> - 知道 `ProjectContext` 包含哪些工作環境資訊（路徑、日期、git 狀態等）
> - 理解 context injection 如何把不同來源的資訊有秩序地注入 prompt
> - 了解 `CLAUDE.md` 為什麼算是一種專案記憶機制
> - 判斷 mini harness 的 prompt assembly 該保留哪些最小功能

## 學習目標
- 能說明 `Prompt Assembly` 與單純寫一段 system prompt 的差異
- 能解釋 `ProjectContext`、instruction files、git 狀態如何被注入模型上下文
- 能判斷 `mini harness` 應保留哪些 prompt assembly 能力，哪些可先簡化

### 先備知識檢查

開始本章前，請確認你已經了解以下內容：

- [ ] 知道什麼是 system prompt（語言模型接收到的背景指令）
- [ ] 對 git 有基本認識（知道 `git status`、`git diff` 大概在看什麼）
- [ ] 讀過第 9 章，了解 session 如何保存工作狀態
- [ ] 知道什麼是 Markdown 格式（`CLAUDE.md` 就是用 Markdown 寫的）

## 核心概念講解
### system prompt

在 `prompt.rs` 裡，system prompt 並不是一個常數，而是 `SystemPromptBuilder` 建出來的一組 sections。這些 sections 包含 intro、system section、doing-tasks section、actions section，再加上一條 `SYSTEM_PROMPT_DYNAMIC_BOUNDARY`，把靜態 scaffold 和動態 context 切開。這個邊界設計很重要，因為它明確承認 prompt 有兩個來源：一部分是長期穩定的系統規則，一部分是當下環境與專案脈絡。

這種做法的價值在於可維護性。你可以比較清楚地知道哪一段是普遍規則，哪一段是這次工作才有的 context，也更容易獨立檢視 prompt assembly 是否正確。這和「把所有東西複製貼上一大段」的差別非常大。

> 💡 **生活化比喻**：System prompt 就像你交給新進員工的「入職手冊」。如果手冊是一張固定的紙，無論員工被分到哪個部門都看同一份，那效果一定不好。真正好用的入職手冊會有「通用規章」（靜態部分）加上「你的部門介紹、座位位置、目前進行中的專案」（動態部分）。Prompt Assembly 就是那個自動幫你組合出完整入職手冊的流程。

> ⚠️ **初學者常見誤區**
>
> - **誤區一**：以為 system prompt 寫一次就好——其實每次啟動 agent 時，system prompt 都是根據當前環境重新組裝的。你換個資料夾工作，模型看到的 prompt 就不一樣。
> - **誤區二**：以為模型自己會去「看」檔案——模型只能看到 harness 主動餵給它的資訊。如果 harness 沒把 git 狀態放進 prompt，模型就不會知道你的程式碼有沒有改過。

### project context

`ProjectContext` 是這一章的主角之一。它至少包含：

- `cwd`
- `current_date`
- `git_status`
- `git_diff`
- `instruction_files`

這代表 `ProjectContext` 不只是「目前路徑在哪裡」，而是對當前工作環境的結構化描述。尤其是 `discover_with_git()` 會進一步把 git 狀態與 diff 帶進來，這表示模型看到的專案脈絡不只是靜態檔案規則，也包含工作區目前的變化狀態。對 coding agent 來說，這種 context injection 非常關鍵，因為它能直接影響模型如何理解任務與風險。

> 💡 **生活化比喻**：想像你要請一位代班同事幫你處理工作。如果你只說「麻煩幫我處理」，他一定搞不定。但如果你告訴他：「我的桌子在三樓（cwd）、今天是星期三（日期）、目前手上有三份報告改了但還沒交（git diff）、公司規定報告格式要用 A 模板（instruction files）」——他就能做對事。ProjectContext 就是這份「工作交接清單」。

### context injection

很多系統會說自己有 context，但 `claw-code` 展示的是比較嚴格的 `context injection`。`SystemPromptBuilder` 的 `with_project_context()`、`with_runtime_config()`、`append_section()` 等方法，讓不同來源的資訊能被有秩序地組進最終 prompt。從 `build()` 流程可看出，環境資訊、project context、instruction files、config section 都是被分段插入，而不是混成一塊。

這種結構化 injection 有兩個好處。第一，模型更容易接收有層次的資訊，而不是被一大段無結構文字淹沒。第二，系統更容易測與診斷。例如 CLI 提供 `system-prompt` 命令，本質上就是讓你把 prompt assembly 的結果單獨印出來檢查。這種可檢視性，是 prompt assembly 真正工程化的一個重要訊號。

> 💡 **生活化比喻**：Context injection 就像整理行李箱。你不會把衣服、盥洗用品、文件、充電器全部混在一起丟進去。好的整理方式是分格分袋：衣物一區、盥洗用品一區、電子設備一區。這樣找東西快、不會遺漏、也容易檢查有沒有漏帶。Prompt 的分段注入就是同樣道理——讓模型能有層次地接收資訊。

### CLAUDE.md memory

`prompt.rs` 的另一個關鍵點，是它會沿路搜尋 instruction files，例如：

- `CLAUDE.md`
- `CLAUDE.local.md`
- `.claw/CLAUDE.md`
- `.claw/instructions.md`

而且搜尋不是只看目前資料夾，而是從 `cwd` 一路往上追 parent directories，再去重與限制總字數。這表示 `CLAUDE.md memory` 在 `claw-code` 裡不是神秘長期記憶，而是一種 project-local instruction layer。它會把專案規則、工作原則、特定限制注入到 system prompt 中，使模型每次工作都能站在相對一致的規則脈絡上。

這種記憶方式很有意思，因為它兼具可讀、可編輯、可版控、可被 prompt assembly 載入的特性。從 harness engineering 的角度看，這比把所有規則埋在不可見程式碼裡更透明，也比每次都靠人手動重新說明更穩定。

> 💡 **生活化比喻**：`CLAUDE.md` 就像貼在辦公桌上的便利貼提醒。每次你坐下來工作（agent 啟動），你自然會看到這些提醒：「客戶 A 的案子用藍色模板」「這個專案不能用某個函式庫」。你不需要每次都重新告訴自己這些規則，因為它們就貼在那裡，系統會自動讀取。

> ⚠️ **初學者常見誤區**
>
> - **誤區**：以為 `CLAUDE.md` 是一個特殊的系統檔案或神祕的 AI 記憶體——其實它就是一個普通的 Markdown 文字檔，只是 harness 會在啟動時自動讀取它的內容並放進 system prompt。任何人都可以打開它、編輯它、用 git 追蹤它的變更。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/rust/crates/runtime/src/prompt.rs`
- `claw-code/USAGE.md`

### 閱讀順序
1. 先看 `USAGE.md` 裡 `system-prompt` 的用法
2. 再讀 `prompt.rs` 中的 `ProjectContext`、`ContextFile`、`SystemPromptBuilder`
3. 最後讀 instruction-file discovery 與 `load_system_prompt()`

### 閱讀重點
- `Prompt Assembly` 為什麼是一個 builder 流程，而不是固定文本
- `ProjectContext` 如何把 `cwd`、日期、git 狀態與 instruction files 收束成模型上下文
- context injection 為什麼要分 environment / project / instruction / config 等不同 section
- `CLAUDE.md` memory 如何被載入、去重與限制長度

## 設計取捨分析

prompt assembly 的最大取捨，是資訊完整度與 prompt 負擔之間的平衡。你注入越多 context，模型越可能站在「正確世界」裡工作；但注入過多時，成本、噪音與認知負擔也會上升。`claw-code` 的做法很值得學，因為它不是盲目加資訊，而是透過 `ProjectContext` 與 instruction-file discovery 明確控制注入類型，還對 instruction file 字數設上限。

另一個取捨則是把專案規則寫在 code 還是寫在 `CLAUDE.md`。寫在 code 裡，系統更封閉，但規則可能較難被人檢查與維護；寫在 instruction files 裡，則更透明、更利於專案自定義，但也需要處理 discovery、dedupe 與長度控制。`claw-code` 選擇後者，這顯示它把 project memory 視為需要被顯性管理的上下文資源。

## Mini Harness 連結點

`mini harness` 在 prompt assembly 這一層最值得保留的，是簡化版 `ProjectContext` 與最基本的 instruction file 注入。教學版不一定要一開始就帶 `git_diff`、完整 config section、或多種 output style，但至少應該讓學生看到：系統 prompt 不是手寫一段固定話術，而是會根據 `cwd`、日期、專案規則與簡單環境資訊被動態組裝。完整 `claw-code` 多做的，則是更豐富的 context injection 與可診斷的 system-prompt rendering surface。

## 本章小結

`Prompt Assembly` 在 `claw-code` 裡不是文案技巧，而是一個正式的 runtime 建構流程。`ProjectContext` 提供工作脈絡，context injection 把環境與專案資訊結構化帶進模型上下文，而 `CLAUDE.md` 則作為 project-local memory 被穩定注入 system prompt。理解這一層，才能看清楚模型為何不是在「真空中回答」，而是在被 harness 主動描述過的工作世界裡推理。

### 學習自我檢核

讀完本章後，請確認以下每一項你都能做到：

- [ ] 我能說明 Prompt Assembly 和「手寫一段固定 system prompt」的本質差異
- [ ] 我知道 `ProjectContext` 至少包含哪些資訊（cwd、日期、git 狀態、instruction files）
- [ ] 我理解 context injection 為什麼要分段、分類型注入，而不是全部混成一大段
- [ ] 我能解釋 `CLAUDE.md` 如何作為專案記憶被 harness 自動讀取
- [ ] 我知道為什麼 system prompt 的可檢視性（能印出來看）是工程化的重要訊號
- [ ] 我能判斷 mini harness 的 prompt assembly 該保留哪些最小功能

### 關鍵概念速查表

| 術語 | 英文 | 簡要說明 |
|------|------|----------|
| System Prompt | System Prompt | 模型在開始對話前接收到的背景指令與環境描述 |
| Prompt 組裝 | Prompt Assembly | 動態將多種來源的資訊組合成最終 system prompt 的流程 |
| 專案脈絡 | Project Context | 對當前工作環境的結構化描述（路徑、日期、git 狀態等） |
| 上下文注入 | Context Injection | 將環境、專案、指令等資訊分段插入 prompt 的機制 |
| 指令檔案 | Instruction Files | 如 `CLAUDE.md`，包含專案規則與約定的文字檔 |
| 動態邊界 | Dynamic Boundary | 分隔 prompt 中靜態規則與動態 context 的標記線 |
| 去重 | Deduplication | 當多個 instruction files 有重複內容時，自動移除重複部分 |

## 章末練習
1. 解釋 `Prompt Assembly` 與「手寫一段 system prompt」有什麼本質差異。
2. 說明為什麼 `CLAUDE.md` 可以被視為一種 project memory。
3. 如果你要為 `mini harness` 設計最小 `ProjectContext`，你會保留哪些欄位？哪些先不保留？

## 反思問題

- 你是否曾經把模型回答錯誤歸因於模型不夠聰明，但其實是 context injection 不完整？
- 對 coding agent 來說，`git_status` 與 `git_diff` 這類資訊應該永遠注入嗎？還是要視任務而定？
- 若專案規則分散在多個 instruction files，中間甚至互相衝突，你覺得 harness 應該怎麼處理？

> **📝 本章一句話總結**
>
> 模型不是在真空中回答問題，而是在 harness 透過 Prompt Assembly 動態組裝出來的「工作世界描述」中進行推理。

## 延伸閱讀 / 下一章預告

第 10 章說明的是系統如何把世界描述給模型；下一章則要處理另一個同樣重要的問題：這個世界的設定是從哪裡來的，又怎麼依 scope 與環境覆寫？第 11 章會進入 `config hierarchy`、permission mode 設定與 environment-sensitive behavior。
