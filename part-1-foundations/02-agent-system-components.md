# 第 2 章：AI Agent 系統的基本構成

## 章節導言

理解了「為什麼要從 prompt 走向 harness」之後，下一個問題就是：一個 agent harness 到底由哪些部分構成？很多初學者會把 agent system 想成「模型加上一些工具」，但這樣的理解太扁平了。真正能讓系統穩定工作的，不只是模型本身，也不只是把幾個 function 暴露給模型，而是這些元件之間如何形成分工、邊界與控制關係。

這一章的目標，是替你建立一張高階架構圖。你要能看出 model、runtime、tools、permissions、session、config、testing 各自扮演什麼角色，也要能說明它們為什麼不能互相取代。當你之後進入 `claw-code` 的各章拆解時，這張圖會成為你的導航地圖；當你在 Part III 真的動手做 `mini harness` 時，這張圖則會幫你判斷哪些元件一定要保留，哪些能力可以先省略。

也可以說，這一章在做一件很重要的事：把「一個會回話的模型」和「一個可運作的 agent system」清楚分開。只有把這個差異講清楚，後面你看到 `ConversationRuntime`、`ToolSpec`、`PermissionPolicy`、`Session`、`ConfigLoader` 等名詞時，才不會把它們誤以為只是一些分散的小模組。

> **📋 本章速覽**
>
> 讀完這一章，你將會學到：
> - 為什麼「模型 ≠ 整個系統」，模型只是系統中的一個元件
> - Runtime 如何扮演整個 agent 系統的流程控制中心
> - Tooling 與 Permissions 為什麼必須「成對出現」互相制衡
> - Session、Prompt Assembly、Testing 為何不是附加功能，而是核心結構
> - 這些元件在 `mini harness` 中哪些必須保留、哪些可以先省略

## 學習目標
- 能畫出 agent system 的高階架構圖
- 能說明 model、runtime、tools、permissions、session、config、testing 的關係
- 能指出哪些元件是 `mini harness` 必須保留的核心

### 先備知識檢查

在開始本章之前，請確認你已經具備以下基礎：

- [ ] 讀完第 1 章，理解 Prompt Engineering 與 Harness Engineering 的差異
- [ ] 知道 Harness Engineering 的目標是「為模型搭建可操作的工作系統」
- [ ] 聽過「runtime」「tools」「permissions」「session」「testing」這些詞（即使還不完全理解）
- [ ] 願意接受「模型不等於整個系統」這個前提

## 核心概念講解
### Model 不是整個系統

在 agent harness 裡，model 很重要，但它不是整個系統。模型擅長的是推理、語言生成、從上下文中決定下一步；但它本身不保存你的專案規則、不管理工具清單、不決定哪些工具可用、不負責 session persistence，也不替你保證輸出一定安全。把模型想成「大腦」或許有幫助，但大腦若沒有感官、記憶、手腳與邊界控制，也無法穩定完成工作。

這也是為什麼只談 model choice 永遠不夠。你可以換更強的模型，但若 runtime 沒有把上下文組好、工具回圈沒有設計好、permission layer 過鬆或過緊、session 無法恢復、測試又不足，系統仍然會不穩。模型能力會影響天花板，但系統工程決定地板。

從教學角度看，這個觀念非常重要。因為本書不是教你如何挑一個最強模型，而是教你如何讓「任何具有一定推理能力的模型」能在一個可控環境裡工作。這正是 harness engineering 的核心。

> 💡 **生活化比喻**：模型就像一位醫術高超的醫生。但一位再厲害的醫生，如果沒有醫院（runtime）、沒有手術器具（tools）、沒有用藥規範（permissions）、沒有病歷系統（session）、沒有醫療品質審查（testing），他也無法穩定地治好每一個病人。Agent 系統就是替這位醫生搭建的「完整醫療體系」。

### Runtime 為什麼是執行核心

如果 model 不是整個系統，那誰在協調系統？答案通常是 `runtime`。Runtime 負責把使用者輸入、系統 prompt、過往訊息、工具結果、權限政策與停止條件串成一個可執行的回圈。它決定何時送 request 給模型、如何接收 streamed events、遇到 tool call 時怎麼 dispatch、完成後如何更新 session，以及什麼情況下結束這一輪。

你可以把 runtime 理解成 agent system 的「流程控制器」。在 `claw-code` 的 Rust workspace 裡，`runtime` crate 並不是只含一個小 loop，而是集中承載許多與執行有關的核心能力：`ConversationRuntime` agentic loop、session persistence、permission policy、MCP client、system prompt assembly、usage tracking 等。這意味著 runtime 不是單一 API wrapper，而是把多個系統責任組裝成一個能持續運作的中心。

這裡也能看出一個重要區別：`ApiClient` 不是 runtime，tool executor 也不是 runtime。它們是 runtime 協調下的子角色。模型客戶端只處理和模型服務互動的邊界；工具執行器只處理工具呼叫的邊界。Runtime 才是把這些邊界串接起來、讓整個 turn loop 成形的地方。

> 💡 **生活化比喻**：Runtime 就像是餐廳的「外場經理」。他不負責炒菜（model），不負責洗碗（tools），也不負責定菜單（config）。但他負責協調整個流程：客人點餐後把單子送進廚房、盯著出菜順序、確認餐點沒出錯、處理客訴、記錄今天的營業數據。沒有外場經理，餐廳就算有世界級廚師也會一團亂。

### Tooling 與 permissions 如何互相制衡

很多人第一次看 agent 系統，最興奮的部分通常是 tools，因為它們讓模型看起來真的「會做事」了。讀檔、搜尋、寫檔、跑 bash、查網頁、呼叫子代理，這些能力使模型從產生文字變成能影響世界的 agent。但 capability 增加的同時，風險也同步增加。能做得越多，出錯時破壞的範圍也越大。

所以 tooling 不能單獨存在，它必須和 `permissions` 一起看。Tool registry 決定系統有哪些手腳；permission policy 決定這些手腳在什麼條件下可以動。這兩者其實形成一種制衡關係。只有工具沒有權限控管，系統會變危險；只有權限控管沒有明確的工具界面，系統會變含糊，因為你根本不知道在控管什麼。

在 `claw-code` 的 `tools` crate 裡，`ToolSpec` 把工具名稱、描述、input schema、required permission 綁在一起。這是很有代表性的設計：工具不是只有「怎麼做」，還必須帶著「這個能力需要多高的權限」一起被宣告。也因此，tooling 與 permissions 不是兩個平行主題，而是同一個能力面與治理面的兩側。

> 💡 **生活化比喻**：想像你給一個實習生一把辦公室的萬能鑰匙（tools）。他可以開任何門、拿任何東西。但如果沒有搭配一份規定（permissions）——「倉庫門可以自己開，財務室的門要先問主管」——那遲早會出問題。好的系統不是不給鑰匙，而是鑰匙和規定一起發。

> ⚠️ **初學者常見誤區**：「工具越多越好」——其實不是。工具太多反而會讓模型困惑（不知道該用哪個），也會增加權限管理的複雜度。好的設計是「每個工具都有清楚的用途和邊界」，而不是堆砌功能。

### Session、prompt assembly、testing 的位置

初學者常把 session、prompt assembly、testing 當成後期附加功能，但在真實 harness 裡，它們是核心結構的一部分。`Session` 的作用，不只是保存聊天紀錄而已。它負責讓系統能 resume、能匯出 transcript、能做 compaction、能記錄先前工具結果，換句話說，它讓 agent 不是每一輪都在失憶狀態下重新開始。

`Prompt assembly` 也不是「把幾段字串黏起來」這麼簡單。系統 prompt、project context、專案規則、`CLAUDE.md` 記憶、allowed tools、當前 mode，這些資訊都要經過整理與注入，模型才會站在正確的位置上思考。若這一步做不好，再強的模型也會像被丟進陌生房間一樣工作。

`Testing` 則回答另一個更根本的問題：你怎麼知道系統真的可靠？既然 agent system 會跨越模型、工具、權限、session 與 CLI 邊界，單靠手動試幾次通常不夠。這也是為什麼 `claw-code` 會有 mock parity harness 這類 deterministic 驗證方法。對 agent harness 而言，測試不是後來補上的品質保證，而是讓系統可維護的必要條件。

> 💡 **生活化比喻**：
> - **Session** 像是醫院的「病歷系統」。如果每次看診都從零開始、不知道上次開了什麼藥，治療就很難連貫。
> - **Prompt Assembly** 像是每天早上的「晨會簡報」。它把今天的病人狀況、注意事項、特殊規定整理好，讓醫生一上班就知道該注意什麼。
> - **Testing** 像是醫院的「品質稽核」。不是等出了醫療疏失才檢討，而是定期用模擬案例測試流程是否正確。

> ⚠️ **初學者常見誤區**：「測試是寫完程式後才做的事」——在 agent 系統中，測試應該和系統設計同步進行。因為 agent 的行為涉及多個元件互動，等到最後才測試，出了問題會很難追溯是哪個環節出錯。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/rust/README.md`
- `claw-code/rust/crates/runtime/src/lib.rs`
- `claw-code/rust/crates/tools/src/lib.rs`

### 閱讀順序
1. `rust/README.md`
2. `runtime/src/lib.rs`
3. `tools/src/lib.rs`

### 閱讀重點
- `rust/README.md` 的 crate responsibilities 幾乎就是一張高階 agent system 地圖；先把 `api`、`runtime`、`tools`、`rusty-claude-cli`、`telemetry` 的分工讀懂
- `runtime/src/lib.rs` 透過大量 `pub use` 告訴你 runtime 真正涵蓋的責任範圍：不只有 conversation loop，還有 permissions、session、prompt、remote、MCP、usage、hooks 等
- `tools/src/lib.rs` 則把工具層的核心抽象攤開來看：`ToolSpec` 說明單一工具要如何被宣告，`GlobalToolRegistry` 說明多種工具來源如何被統一管理
- `runtime` 與 `tools` 被拆開，不是因為它們無關，而是因為一個負責流程控制，一個負責能力定義；這樣的分層有助於測試、替換與權限治理

## 設計取捨分析

真實的 agent harness 幾乎不可能只用一個檔案或一個模組就寫完。`claw-code` 的 Rust workspace 把責任拆到 `api`、`runtime`、`tools`、`commands`、`telemetry`、`rusty-claude-cli` 等 crate，這樣的好處是邊界清楚、可獨立測試、也有利於團隊分工；代價則是初學者第一次閱讀時很容易迷路，因為同一個使用者行為往往會跨越多個 crate。

因此，教材在介紹這些元件時，不能直接照 repo 目錄逐一念過去，而是要先回到系統層次：哪些是推理邊界，哪些是流程邊界，哪些是能力邊界，哪些是治理邊界。這也是本章刻意先畫高階地圖，再讓你去看 `claw-code` 的原因。你需要先知道自己在找什麼，才不會把 crate 數量誤以為系統複雜度的全部來源。

另一個取捨則和 `mini harness` 有關。真實系統為了可用性與規模化，會加入 OAuth、telemetry、MCP、sub-agent orchestration、hooks、slash commands、config hierarchy 等能力；但若把這些全部帶進教學版實作，學生很可能還沒學會核心 loop，就先淹沒在周邊功能裡。因此後續重建時，我們會保留結構本質，刻意砍掉規模化附屬能力。

## Mini Harness 連結點

如果你要自己做一個 `mini harness`，本章就是你的元件清單。最少要保留的核心包括：模型邊界、runtime loop、tool dispatcher、permission policy、session persistence，以及能覆蓋基本行為的測試。你可以不先做 OAuth、不先做完整 config hierarchy、不先做 MCP，也不先做 parity harness 的全套場景，但你不能把 runtime 和 model 混成一團，也不能把 tooling 和 permission 當成兩個互不相干的小功能。

更實際地說，Part III 會把這些元件縮成較少的 Python 檔案，例如 `runtime.py`、`tools.py`、`permissions.py`。這不是在否定真實系統的分層，而是在教學上做有意識的壓縮。你要學到的不是「Rust repo 怎麼分 crate」，而是「一個 agent system 不管用什麼語言寫，都逃不掉哪些核心責任」。

## 本章小結

一個可運作的 agent harness，至少包含 model、runtime、tools、permissions、session、prompt assembly、config 與 testing 等核心元件。模型提供推理能力，runtime 負責協調流程，tools 提供行動能力，permissions 管治理邊界，session 與 prompt assembly 管脈絡延續，而 testing 負責驗證整體行為。理解這張高階地圖之後，你才真正準備好進入後續章節，把 `claw-code` 拆成可理解的系統，而不是一堆分散的檔名。

### 學習自我檢核

讀完本章後，請用以下清單確認自己的理解程度：

- [ ] 我能解釋為什麼「模型 ≠ 整個系統」
- [ ] 我能說明 Runtime 在 agent 系統中扮演什麼角色（流程控制中心）
- [ ] 我理解 Tooling 和 Permissions 為什麼要成對出現
- [ ] 我能區分 ApiClient、Tool Executor 和 Runtime 三者的職責
- [ ] 我知道 Session 不只是「聊天紀錄」，還承擔哪些責任
- [ ] 我能列出 mini harness 至少需要保留的五個核心元件
- [ ] 我理解為什麼真實系統要把責任拆分到不同模組

> 如果有超過兩項打不了勾，建議回頭重讀對應的小節。

## 關鍵概念速查表

| 術語 | 簡要定義 |
|------|----------|
| **Model** | 系統中的推理元件，負責語言理解、規劃與生成，但不是整個系統 |
| **Runtime** | Agent 系統的流程控制中心，協調模型、工具、權限、session 等元件 |
| **ConversationRuntime** | `claw-code` 中 runtime 的核心實作，負責 agentic loop |
| **Tool / Tooling** | 模型可呼叫的外部能力，讓 agent 能「做事」而非只「說話」 |
| **ToolSpec** | 工具的宣告格式，包含名稱、描述、輸入格式、所需權限等資訊 |
| **GlobalToolRegistry** | 統一管理所有工具來源的註冊中心 |
| **Permissions** | 控制工具在什麼條件下可以執行的權限政策層 |
| **Session** | 系統的狀態容器，支援對話恢復、transcript 匯出、上下文壓縮 |
| **Prompt Assembly** | 把系統規則、專案脈絡、工具清單等組裝成模型看到的上下文 |
| **Config** | 系統設定層，管理各種參數與行為配置 |
| **Testing** | 用確定性方法驗證系統行為，如 mock parity harness |
| **Crate** | Rust 語言中的模組單元，類似 Python 的 package |

## 章末練習
1. 畫出一張 agent system 基本構成圖。
2. 解釋為什麼 runtime 不等於 model client。
3. 指出 `mini harness` 最少必須保留的五個元件。

## 反思問題

- 你過去使用 AI coding 工具時，最常把哪個系統責任誤以為是模型本身在完成？
- 如果把 permissions 完全拿掉，tooling 會變成什麼？如果把 tooling 拿掉，runtime 又會剩下什麼？
- 你認為在教學版 `mini harness` 裡，哪個能力最不應該過早加入？為什麼？

### 本章一句話總結

> **Agent 系統不是「模型加幾個工具」，而是 model、runtime、tools、permissions、session、prompt assembly 與 testing 各司其職、互相制衡的完整工作體系。**

## 延伸閱讀 / 下一章預告

接下來的第 3 章會把本章的元件地圖進一步提煉成設計原則，討論一個好的 harness 應該如何處理環境感知、工具編排、guardrails、session state 與可測試性。也就是說，我們會從「它有哪些部分」進一步走到「它應該怎麼被設計」。
