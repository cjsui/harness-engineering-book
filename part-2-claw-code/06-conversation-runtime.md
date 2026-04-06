# 第 6 章：Conversation Runtime：Agent Loop 的心臟

## 章節導言

如果說前面的章節是在替你建立地圖，那麼從這一章開始，我們就正式走進 `claw-code` 的核心機房。在一個 agent harness 裡，最關鍵的問題不是「模型能不能回答」，而是「整個系統如何把一次任務變成一個可持續執行、可呼叫工具、可更新狀態、可安全停止的 turn loop」。這個問題的答案，就集中在 `ConversationRuntime` 周圍。

`claw-code` 的 runtime 設計很有代表性，因為它沒有把 conversation 視為單純的 chat transcript，而是把它當成一個持續運作的執行回圈。這個回圈需要組 request、接收 event stream、判斷是否有 tool use、做 permission 檢查、執行工具、把結果寫回 session、追蹤 usage、必要時 compact session，最後再決定下一輪要不要繼續。換句話說，conversation 在這裡不是對話表面，而是整個 agent system 的運轉形式。

本章的目標，是讓你真正讀懂這個 loop 的最小骨架。你不需要在第一次閱讀就記住所有細節，但你一定要看清楚幾個核心契約：`ApiRequest` 是什麼、`AssistantEvent` 為什麼是事件流、`ApiClient` 與 `ToolExecutor` 各自負責哪個邊界、`ConversationRuntime<C, T>` 為何要做成 generic，以及 turn loop 在什麼條件下持續、停止、或失敗。當你理解這些之後，很多看似分散的 agent 行為就會突然連成一條線。

> ### 📋 本章速覽
> 
> 讀完本章，你將會學到：
> - `ConversationRuntime` 是 agent 系統的「心臟」，負責驅動整個執行回圈
> - `ApiRequest` 不是一段字串，而是結構化的模型請求封包
> - `AssistantEvent` 把模型回應變成可處理的事件流，而不是一整段文字
> - `ApiClient` 與 `ToolExecutor` 是 runtime 對外的兩個關鍵邊界
> - turn loop 的停止條件是「沒有新的工具呼叫」，不是「模型停止輸出」

## 學習目標
- 能解釋 `ConversationRuntime` 在 agent system 中扮演的角色
- 能說明 `ApiRequest`、`AssistantEvent`、`ApiClient`、`ToolExecutor` 之間的資料流
- 能指出 turn loop 的停止條件、迭代機制與縮減版 `mini harness` 該保留的本質

### 📝 先備知識檢查

在開始本章之前，請確認你已經了解以下概念：

- [ ] 理解第 5 章的 CLI 入口概念，知道系統有多種進入方式
- [ ] 知道什麼是 API request/response（送請求、收回應的基本模式）
- [ ] 了解「事件流（event stream）」的概念——資料是一點一點來的，不是一次全部到齊
- [ ] 知道什麼是 generic type（泛型），至少理解「可替換元件」的概念
- [ ] 理解「迴圈」的基本程式概念（反覆執行直到條件滿足才停止）

## 核心概念講解
### `ApiRequest`

`conversation.rs` 一開始就定義了 `ApiRequest`：

- `system_prompt: Vec<String>`
- `messages: Vec<ConversationMessage>`

這個型別看起來很簡單，但它非常關鍵，因為它揭示了 runtime 對模型呼叫的基本理解：送給模型的不是「一個字串 prompt」，而是一個已經被組裝好的請求物件。這代表 system instructions 和 conversation messages 在結構上被明確分開，也代表 prompt assembly 早已不是零散字串拼接，而是 runtime 可管理的輸入邊界。

從資料流角度看，`ApiRequest` 是 turn loop 每次進模型前的總封包。它把目前 system prompt 與 session 內的 messages 一起送進 `ApiClient`。如果這一層被拿掉，系統就只剩下模糊的「把某些字串送給模型」，而失去可測試、可推理的 request 邊界。

> 💡 **生活化比喻**：`ApiRequest` 就像你去看醫生時填的「掛號單」。上面分成兩區：「基本資料」（system prompt，告訴醫生你是誰、有什麼固定背景）和「今天的症狀描述」（messages，本次對話的內容）。醫生不會叫你把所有資訊全寫在一張便條紙上，而是用結構化的表單讓雙方都能清楚處理。

### `AssistantEvent`

`AssistantEvent` 是另一個極具代表性的設計。它不是單一「最終回答」，而是一串 streamed events，包含：

- `TextDelta`
- `ToolUse`
- `Usage`
- `PromptCache`
- `MessageStop`

這意味著 runtime 不是等模型整段輸出完成後才開始理解結果，而是把模型回應視為一個事件序列。文字增量可以逐步累積、tool use 可以在中途被攔截並執行、usage 可被記錄、prompt cache telemetry 可被保存，而 `MessageStop` 則告訴 runtime 一次 assistant turn 已完成。

這種事件流設計的最大價值，在於它把模型回應從「被動顯示文字」變成「可被系統消化的控制訊號」。如果沒有 `AssistantEvent` 這種抽象，tool use 幾乎只能靠後處理字串解析，usage tracking 也很難穩定整合，整個 runtime 會退化成較脆弱的一次性 chat wrapper。

> 💡 **生活化比喻**：想像你在看一場足球比賽的即時轉播。`AssistantEvent` 就像即時比分板上的事件通知——「進球！」「換人！」「黃牌！」「比賽結束！」。你不用等整場比賽結束才知道發生了什麼，每個事件一發生，系統就可以立刻反應（更新分數、記錄數據、觸發慶祝動畫）。如果沒有事件流，你就只能在 90 分鐘後拿到一份靜態的比賽報告。

### `ApiClient` 與 `ToolExecutor`

`ApiClient` 與 `ToolExecutor` 是 runtime 對外界兩個最重要的抽象介面。前者只承諾一件事：`stream(request)`，也就是拿到 `ApiRequest` 後，回傳一串 `AssistantEvent`。後者也只承諾一件事：`execute(tool_name, input)`，也就是根據工具名稱與輸入執行本地能力，回傳結果或錯誤。

這種設計非常乾淨。它把「和模型供應者互動」與「在本地執行工具」兩件事分開，也讓 `ConversationRuntime<C, T>` 可以只依賴抽象，不依賴某個特定 API 實作或某個固定工具集合。也因此，runtime 真正扮演的是協調者，而不是把所有外部責任硬塞進自己內部。

從教學角度看，這兩個 trait 也是 `mini harness` 最值得保留的部分。因為它們迫使你清楚定義：模型邊界在哪裡，工具邊界又在哪裡。只要這兩層分清楚，之後就算更換模型供應者、調整工具集合、加入 mock client 做測試，也不會把整個系統拆壞。

> 💡 **生活化比喻**：`ApiClient` 就像你手機裡的「翻譯 App」——你把問題丟給它，它回傳翻譯結果，你不需要知道它背後是用 Google 還是 DeepL。`ToolExecutor` 就像你的「工具箱」——裡面有螺絲起子、鉗子、尺，你說「我要用螺絲起子」它就遞給你。Runtime 則是「你本人」——負責決定什麼時候查翻譯、什麼時候拿工具，以及做完後下一步要幹嘛。

> ⚠️ **初學者常見誤區**：不要把 `ApiClient` 和 `ToolExecutor` 混為一談。`ApiClient` 是「問模型問題」的通道，`ToolExecutor` 是「在你的電腦上做事」的通道。前者連到雲端 AI 模型，後者在本地執行。它們是 runtime 的兩隻手臂，各自伸向不同方向。

### `ConversationRuntime`

`ConversationRuntime<C, T>` 本身就是本章主角。它的欄位很值得細看：`session`、`api_client`、`tool_executor`、`permission_policy`、`system_prompt`、`max_iterations`、`usage_tracker`、`hook_runner`、`auto_compaction_input_tokens_threshold`、`hook_abort_signal`、`hook_progress_reporter`、`session_tracer`。這個列表幾乎就是一個成熟 runtime 的責任清單。

最值得注意的是兩件事。第一，它是 generic over `C` and `T`，也就是把模型流與工具執行抽象成可替換元件。第二，它不只管「跑一輪」，還同時持有 usage tracking、hooks、auto compaction、session tracing 等 scale-induced 能力。這表示 `ConversationRuntime` 不是課本上的最小 loop，而是一個真實系統裡逐漸長出周邊能力的執行核心。

因此，讀 `ConversationRuntime` 時不要只盯著它的欄位多不多，而要問：哪些是本質，哪些是規模化附加能力？本質通常是 session、api client、tool executor、permission policy、system prompt、iterations；規模化能力則包括 hooks、prompt cache telemetry、session tracer、auto compaction 等。這種區分，會直接影響你後面如何設計 `mini harness`。

> 💡 **生活化比喻**：`ConversationRuntime` 就像一間餐廳的「廚房總指揮」。他手下有負責採購食材的人（`ApiClient`）、有負責使用刀具設備的人（`ToolExecutor`）、有出菜順序的規則（`permission_policy`）、有今天的菜單（`system_prompt`）、有最多出幾道菜的限制（`max_iterations`）。成熟的餐廳還會有成本追蹤（`usage_tracker`）和品質檢查員（`hooks`），但一間剛開的小餐廳可以先從最基本的角色做起。

### turn loop、iterations、stop reason

真正的精華在 turn loop。從 `conversation.rs` 的流程來看，一次 runtime turn 大致會經過以下步驟：

1. 增加 `iterations` 計數，先檢查是否超過 `max_iterations`
2. 用 `system_prompt` 與目前 `session.messages()` 組成 `ApiRequest`
3. 呼叫 `api_client.stream(request)` 取得 `AssistantEvent` 序列
4. 把事件組裝成 assistant message，並記錄 `usage_tracker`
5. 從 assistant message 中抽出 `pending_tool_uses`
6. 若沒有 tool use，代表這一輪可正常停止
7. 若有 tool use，逐一執行 pre-hook、permission evaluation、tool execution、post-hook，並把 `tool_result` 寫回 session
8. 回到下一次 iteration，直到沒有 pending tool use
9. turn 結束後，視 token 門檻決定是否 `maybe_auto_compact()`

這裡最值得你掌握的是「停止條件」的性質。runtime 並不是看到 `MessageStop` 就一定整輪結束，而是要進一步看 assistant message 裡是否仍有 pending tool uses。若有，這其實只是模型一輪輸出完成，不是整個 agent turn 完成。真正的 stop reason 比較接近：「沒有新的工具呼叫，或已觸發錯誤 / iteration 上限 / policy 阻擋」。這種 distinction 很重要，因為它是 agent loop 與普通 chat completion 最大的差別之一。

如果把這整個 turn loop 拿掉，`claw-code` 會發生什麼事？系統就只剩下單次 request-response 的文字互動，失去 agent 最核心的特徵：模型不能在本輪中觸發工具、觀察工具結果、再做下一輪推理。換句話說，沒有 runtime loop，就沒有真正的 agentic workflow。

> 💡 **生活化比喻**：turn loop 就像一個偵探辦案。偵探不會只問一個問題就結案，而是：問問題 → 拿到線索 → 決定要不要去搜證（tool use）→ 搜到證據後再問新問題 → 直到案件破了（沒有更多線索要追）或超過辦案期限（max_iterations）。`MessageStop` 只是偵探說完一句話，不代表案子結了——還要看他有沒有指示下一步行動。

> ⚠️ **初學者常見誤區**：很多人以為「模型回應完成 = agent turn 結束」，這是最常見的理解錯誤。實際上，模型回應可能包含工具呼叫，這些工具執行完後，模型還會看到結果並決定是否要再行動。只有在模型回應中不包含任何工具呼叫時，agent turn 才算真正結束。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/rust/crates/runtime/src/conversation.rs`
- `claw-code/rust/crates/runtime/src/lib.rs`

### 閱讀順序
1. 先讀 `conversation.rs` 前半部的型別與 trait 定義
2. 再讀 `ConversationRuntime` 的欄位與建構函式
3. 最後讀 turn loop 內處理 `pending_tool_uses`、usage tracking、auto compaction 的流程

### 閱讀重點
- request 組裝：`ApiRequest` 如何把 `system_prompt` 與 `messages` 包成模型輸入
- streamed events：`AssistantEvent` 為什麼用事件流而不是單一輸出物件
- tool use 事件：`pending_tool_uses` 如何驅動下一輪迭代
- usage tracking：`UsageTracker` 如何在每次 assistant 回應後累積 usage 與支援後續 compaction 判斷

## 設計取捨分析

`ConversationRuntime` 的設計有一個很鮮明的取捨：它把大量控制責任集中在同一個執行核心中。好處是資料流清楚，session、permission、tool execution、usage tracking 都在同一條生命週期裡被協調；壞處則是 runtime 會變成複雜度聚集點，閱讀成本也因此上升。

另一個取捨是事件流 vs 單次結果。事件流設計更接近真實 agent 需求，因為它能支援 `TextDelta`、`ToolUse`、`Usage`、`PromptCache` 等多種控制訊號；但它也迫使系統必須處理更多中間狀態。若只追求最小可行版本，單次結果模型當然更容易實作；但那也會直接失去工具回圈與細緻觀測能力。這正是 `claw-code` 作為真實 harness 與教學版 `mini harness` 之間的重要差別。

## Mini Harness 連結點

在 `mini harness` 裡，我們會保留 runtime 的本質，但縮小規模。也就是說，Python 版仍然應該有類似 `ApiClient` / `ToolExecutor` 的邊界、有 session + system prompt 組 request 的步驟、有最大迭代數、有 assistant 觸發 tool use 再回圈的邏輯。但我們大概不會一開始就做完整 hooks、prompt cache telemetry、session tracer、或自動 compaction。這些都屬於成熟系統的增量能力，而不是第一版教學系統的必要條件。

## 本章小結

`ConversationRuntime` 是 `claw-code` 的 agentic heart。它透過 `ApiRequest`、`AssistantEvent`、`ApiClient`、`ToolExecutor` 等契約，把模型呼叫、工具執行、權限檢查、session 更新、usage tracking 與停止條件整合成可持續運作的 turn loop。理解這個 loop，等於真正理解了 agent harness 與一般聊天系統的分界線。

### ✅ 學習自我檢核

完成本章後，請確認你是否能做到以下幾點：

- [ ] 我能畫出 `ApiRequest` → `ApiClient` → `AssistantEvent` → tool use → `ToolExecutor` → 下一輪的基本資料流
- [ ] 我能解釋為什麼 `ApiRequest` 是結構化物件而不是單純字串
- [ ] 我能區分 `MessageStop`（模型停止輸出）和「agent turn 真正結束」的差異
- [ ] 我能說明 `ApiClient` 和 `ToolExecutor` 各自負責什麼，以及為什麼要分開
- [ ] 我能區分 runtime 的「本質必要欄位」和「規模化附加能力」
- [ ] 我能解釋 turn loop 為什麼是 agent 和普通聊天系統的分界線

## 📖 關鍵概念速查表

| 術語 | 說明 |
|------|------|
| **ApiRequest** | 送給模型的結構化請求封包，包含 system prompt 與 messages |
| **AssistantEvent** | 模型回應的事件流，包含文字增量、工具呼叫、用量記錄等 |
| **TextDelta** | 模型逐步輸出的文字片段 |
| **ToolUse** | 模型要求執行某個工具的事件 |
| **MessageStop** | 模型一次輸出完成的訊號（不等於 agent turn 結束） |
| **ApiClient** | 負責與模型 API 互動的抽象介面，只做 `stream(request)` |
| **ToolExecutor** | 負責在本地執行工具的抽象介面，只做 `execute(tool_name, input)` |
| **ConversationRuntime** | 協調模型呼叫、工具執行、權限檢查、session 更新的執行核心 |
| **turn loop** | agent 的執行迴圈：送請求 → 收事件 → 執行工具 → 下一輪 |
| **max_iterations** | 迴圈上限，防止 agent 無限執行 |
| **pending_tool_uses** | 模型回應中尚未執行的工具呼叫清單 |
| **auto compaction** | 當 token 超過門檻時自動壓縮 session 的機制 |

## 章末練習
1. 解釋為什麼 `ApiRequest` 不是單純的一段 prompt 字串。
2. 比較 `MessageStop` 與「整個 agent turn 結束」之間的差異。
3. 如果你要為 `mini harness` 設計最小版 `ConversationRuntime`，你會保留哪些欄位？會先刪掉哪些欄位？

## 反思問題

- 你認為 runtime 中最不該和其他責任混在一起的是哪個邊界：模型、工具、還是 session？為什麼？
- 如果一個 agent 系統完全沒有 `max_iterations`，你覺得最可能出現什麼風險？
- 你會如何判斷某個 runtime 功能屬於「本質必要」還是「規模化附加」？

> ### 💬 本章一句話總結
> 
> **ConversationRuntime 是 agent 的心臟——它不只是「問模型問題」，而是一個「問問題 → 聽回答 → 用工具 → 再問問題」的持續執行迴圈。**

## 延伸閱讀 / 下一章預告

理解了 runtime 之後，下一步自然是問：模型到底有哪些手腳可以用？第 7 章會往另一個核心層走，拆解 `ToolSpec`、`GlobalToolRegistry`、`normalize_allowed_tools`、`definitions()` 這些工具系統設計，看看 `claw-code` 如何把能力表面管理成可供模型安全使用的工具空間。
