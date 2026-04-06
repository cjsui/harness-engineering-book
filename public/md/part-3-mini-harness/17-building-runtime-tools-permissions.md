# 第 17 章：實作最小 Runtime、Tools 與 Permissions

## 章節導言

到了這一章，我們終於不再只是替 `mini harness` 劃範圍，而是要把它轉成一個可執行的 Python 專案骨架。這一步最容易出現兩種失誤。第一種是做得太像教學玩具，只剩一個大檔案把 prompt、工具與權限全部混在一起，雖然短期能跑，但你幾乎學不到真正的 harness 分層。第二種則是過度模仿 `claw-code`，一開始就把模組拆得很細、抽象拉得很高，結果教學複雜度瞬間爆炸。

因此，本章的核心任務是做一種「有意識的壓縮」。我們要保留 `claw-code` 的結構精神，但把它收斂成幾個最少、最能教會人的 Python 檔案。重點不是 feature parity，而是 architectural parity。也就是說，你做出來的東西不需要有完整 CLI、MCP、remote、plugin lifecycle，但它應該已經能清楚展現 runtime loop、tool dispatch、permission gating 這三條主軸是如何彼此咬合的。

這一章會先定義 project skeleton，再逐一解釋每個檔案對應 Part II 的哪個概念。最後，我們會把這份骨架收斂成一組可操作的 build 任務，讓下一章能順勢接上 session persistence 與測試。

> **📋 本章速覽**
>
> 讀完本章，你將會：
> - 建立一個最小但結構正確的 Python 專案骨架（`mini-harness/`）
> - 理解 `runtime.py`、`tools.py`、`permissions.py` 各自負責什麼
> - 知道為什麼「先把結構對，再補功能」比一開始就寫萬能大檔案更好
> - 學會用 `claw-code` 的真實檔案對照你的教學版模組
> - 建立「測試從第一天就是系統一部分」的工程習慣

## 學習目標
- 能建立一個保留 harness 本質的 Python 專案骨架
- 能說明 `runtime.py`、`tools.py`、`permissions.py` 各自對應 Part II 的哪個系統責任
- 能在縮小版實作中維持清楚的能力邊界，而不把所有邏輯混成單一腳本

> **🔍 先備知識檢查**
>
> 開始本章之前，請確認你已經：
> - [ ] 讀過第 6 章，理解 runtime loop 的基本概念（模型回應 → 工具呼叫 → 結果回寫）
> - [ ] 讀過第 7 章，知道 `ToolSpec`、registry、dispatch 是什麼意思
> - [ ] 讀過第 8 章，明白 permission policy 為什麼不能只是裝飾
> - [ ] 對 Python 的 package 結構有基本認識（`__init__.py` 的作用）
> - [ ] 知道什麼是 JSON schema（至少看過一個例子）
>
> 如果以上有不確定的，建議先回去複習對應章節再來。

## 核心概念講解

若要把 `claw-code` 的核心精神濃縮成第一版 Python 實作，一個很合理的最小檔案樹會是：

```text
mini-harness/
├── mini_harness/__init__.py
├── mini_harness/runtime.py
├── mini_harness/tools.py
├── mini_harness/permissions.py
└── tests/
    ├── test_runtime.py
    ├── test_tools.py
    └── test_permissions.py
```

這個骨架之所以好，不是因為它最短，而是因為它剛好把三條最核心的責任線拉開。

> 💡 **生活化比喻**：把整個 `mini-harness` 想像成一家餐廳。`runtime.py` 是**外場經理**，負責控制點餐到上菜的整個流程；`tools.py` 是**廚房**，裡面有各種菜單與料理設備；`permissions.py` 是**食品安全稽查員**，確保每道菜上桌前都符合衛生標準。三者各司其職，才能讓整家餐廳順利運作。

### `__init__.py`：Package 入口

`mini_harness/__init__.py` 的角色很簡單，但仍然重要。它不需要承擔業務邏輯，而是作為 package 的明確出口，整理最值得對外暴露的型別與主物件。對教學來說，這可以幫學生建立一個清楚印象：系統不是靠檔案偶然拼在一起，而是一個有正式入口的 package。

### `runtime.py`：流程控制核心

`runtime.py` 對應的就是我們在第 6 章讀過的 `ConversationRuntime` 核心精神。當然，Python 版不需要一開始就複製 hooks、prompt cache、session tracer 與 auto compaction，但至少要有幾個本質成分：一個 `Runtime` 類別或主函式、可注入的 model client 邊界、message loop、最大迭代數、以及遇到 tool use 時會呼叫 tool dispatcher 並把結果送回下一輪。這個檔案的任務是控制流程，不是宣告工具細節，也不是決定權限規則。

> 💡 **生活化比喻**：`runtime.py` 就像一位**交響樂指揮**。指揮不會自己演奏樂器（那是工具的事），也不會決定哪首曲子能不能演（那是權限的事），但整個演出從開始到結束的節奏、順序、什麼時候該誰上場，全都由指揮控制。

> ⚠️ **初學者常見誤區**：很多人在寫 `runtime.py` 時，會不小心把工具的具體實作邏輯直接寫進去（例如直接在 runtime 裡面寫讀檔案、執行 shell 指令的程式碼）。請記住：**runtime 只負責「指揮」，不負責「演奏」**。如果你發現自己在 `runtime.py` 裡寫了具體的工具操作程式碼，那就是警訊。

### `tools.py`：能力宣告與 Dispatch

`tools.py` 對應的則是第 7 章的 tool system。這裡最值得保留的不是龐大的工具數量，而是 `ToolSpec` + registry + dispatch 這條骨架。也就是說，Python 版應該至少有：

- `ToolSpec`：包含 name、description、input schema、required permission
- `ToolRegistry`：集中管理工具宣告與查找
- `dispatch()` 或 `execute()`：根據工具名稱呼叫對應實作

這讓你在教學版裡仍然保留「能力宣告」與「能力執行」的分工，而不是把工具當成幾個裸露函式硬塞給 runtime。

> 💡 **生活化比喻**：`tools.py` 就像一本**工具型錄**加上**工具倉庫**。型錄（`ToolSpec`）告訴你有什麼工具、每個工具怎麼用、需要什麼等級的授權才能使用。倉庫管理員（`ToolRegistry`）負責查找和取出工具。而 `dispatch()` 就是真正拿起工具開始用的那個動作。

### `permissions.py`：治理邊界

`permissions.py` 對應第 8 章的 permission / guardrail layer。教學版不必完整重做 `PermissionEnforcer` 的所有 heuristics，但至少應該有：

- `PermissionMode`
- `PermissionPolicy`
- 一個 `authorize(tool_name, input)` 的最小授權流程

重點是讓 runtime 在每次工具執行前，真的會問 permission layer，而不是只在文字上說「理論上會檢查」。這個邏輯只要被拆到獨立檔案，學生就比較能真正理解「能力」與「治理」是兩個不同責任。

> 💡 **生活化比喻**：`permissions.py` 就像大樓的**門禁系統**。不管你手上有多少把鑰匙（工具），每次你要進某個房間之前，門禁系統都會先刷卡檢查你有沒有權限。如果你的卡片等級不夠（比如只有 `read-only` 權限），即使你知道門在哪裡，門禁也不會讓你進去。

> ⚠️ **初學者常見誤區**：有些人覺得「反正我的教學版只有兩三個工具，permissions 直接寫在 runtime 裡就好了」。這種想法非常危險！因為一旦權限邏輯散落在 runtime 各處，你很快就會分不清楚「什麼被允許、什麼被拒絕」。把 permissions 獨立出來，不是為了看起來比較厲害，而是為了**在系統成長時不失控**。

### `tests/`：從第一天就預期被驗證

最後是 `tests/`。很多人會覺得測試應該留到下一章再談，但在 project skeleton 階段先把 `test_runtime.py`、`test_tools.py`、`test_permissions.py` 放進樹裡，本身就有教學意義。它等於先宣告：這個專案一開始就預期自己會被驗證，而不是等功能都寫完才想到要補測。這種先把 testing 當正式模組的習慣，本身就是 harness thinking 的一部分。

若用「Part II 對照表」的方式看，每個 Python 檔案其實都能找到對應來源：

- `runtime.py` -> `claw-code/rust/crates/runtime/src/conversation.rs`
- `tools.py` -> `claw-code/rust/crates/tools/src/lib.rs`
- `permissions.py` -> `claw-code/rust/crates/runtime/src/permissions.rs` 與 `permission_enforcer.rs`
- `tests/test_runtime.py` -> runtime turn / tool-result roundtrip 的最小驗證
- `tests/test_tools.py` -> tool registry / dispatch / schema 的最小驗證
- `tests/test_permissions.py` -> read-only / workspace-write / denial path 的最小驗證

這種 mapping 很重要，因為它讓學生知道我們不是隨便取幾個 Python 檔案名，而是在有意識地把 Part II 拆解出的責任重新投影到 Part III 的教學版結構中。

## 本章任務

本章的實作任務可以被拆成四步：

1. 建立 `mini_harness/` package 與 `tests/` 目錄
2. 在 `runtime.py` 先定義最小回圈與 model / tool 邊界
3. 在 `tools.py` 建立最小 tool spec、registry 與 dispatch 流程
4. 在 `permissions.py` 定義 mode、policy 與授權判斷，並讓 runtime 在工具執行前使用它

這裡要注意一個順序原則：先把結構對，再把功能補進去。也就是說，先確立責任邊界，再逐步讓每個模組真的能工作。若一開始就把所有邏輯塞進 `runtime.py`，之後再拆開會比一開始就保留邊界更痛苦。

## 對照 `claw-code` 的設計差異

和 `claw-code` 相比，這個 Python 專案骨架做了三種刻意簡化。第一，crate-level 分層被壓縮成少量 Python 檔案。`claw-code` 把 runtime、tools、api、telemetry、plugins、commands 等責任分散到多個 crate；教學版則只保留最直接與最必要的三個核心模組。第二，成熟系統的周邊能力被暫時拿掉，例如 hooks、MCP、remote、prompt cache、session compaction。第三，CLI surface 與操作模式被刻意簡化，不在第一版就處理完整使用者入口。

但這些簡化不代表我們放棄系統思維。相反地，這樣的設計差異正是在保留 `claw-code` 的本質：runtime 仍然是流程控制核心，tools 仍然是正式能力層，permissions 仍然是治理層。真正被縮掉的，是那些對教學第一步來說尚非必要的規模化能力。

## 實作決策記錄

這一章先明確記下幾個 build 決策，讓後續實作不會漂移：

1. `runtime.py` 不直接持有工具細節
原因：要維持控制流程與能力宣告的分離，避免 runtime 變成萬能大檔案。

2. `tools.py` 保留 `ToolSpec`
原因：即使工具很少，也要讓 schema 與 required permission 跟著工具宣告走。

3. `permissions.py` 不只是常數設定
原因：它必須提供最小授權函式，真的參與執行流程，而不是只有裝飾性存在。

4. `tests/` 提前列入骨架
原因：testing 是系統設計的一部分，不應等到所有功能完成才被想到。

5. 第一版專案先不引入複雜 DI 或 plugin 機制
原因：對教學版而言，清楚邊界比高度抽象更重要。

## 本章小結

第 17 章把 `mini harness` 的概念範圍轉成具體 Python 專案骨架。`runtime.py` 對應流程控制，`tools.py` 對應能力宣告與 dispatch，`permissions.py` 對應治理邊界，`tests/` 則預告這是一個從一開始就要被驗證的系統。這個骨架的價值，不在於它已經完整，而在於它已經把最重要的系統責任放在對的位置上。

> **✅ 學習自我檢核**
>
> 讀完本章後，請確認你能做到以下每一項：
> - [ ] 我能畫出 `mini-harness/` 的檔案樹，並說出每個檔案的職責
> - [ ] 我能解釋為什麼 runtime、tools、permissions 不該合併成一個檔案
> - [ ] 我能說出 `ToolSpec` 至少包含哪四個欄位
> - [ ] 我知道 `permissions.py` 的 `authorize()` 函式會在什麼時候被呼叫
> - [ ] 我理解 `tests/` 為什麼要在第一天就放進專案骨架
> - [ ] 我能把教學版的每個檔案對應到 `claw-code` 的真實檔案

## 關鍵概念速查表

| 術語 | 說明 | 對應檔案 |
|---|---|---|
| Runtime Loop | 控制「接收輸入 → 呼叫模型 → 處理工具 → 回傳結果」的主迴圈 | `runtime.py` |
| Tool Dispatch | 根據工具名稱找到對應實作並執行 | `tools.py` |
| ToolSpec | 工具的正式宣告，包含名稱、描述、schema、所需權限 | `tools.py` |
| ToolRegistry | 集中管理所有工具宣告的註冊中心 | `tools.py` |
| PermissionMode | 目前系統允許的權限等級（如 read-only、workspace-write） | `permissions.py` |
| PermissionPolicy | 定義哪些權限等級可以做哪些事的規則集 | `permissions.py` |
| authorize() | 在工具執行前檢查權限是否足夠的函式 | `permissions.py` |
| Architectural Parity | 保留架構精神而非完整功能的設計策略 | 全專案 |
| Project Skeleton | 專案的初始檔案結構，定義責任邊界 | `mini-harness/` 整體 |

## 章末練習
1. 說明為什麼 `runtime.py`、`tools.py`、`permissions.py` 不應被合併成單一檔案。
2. 為 `mini harness` 設計兩個最小工具，並替它們各自指定 `required_permission`。
3. 如果你想再多拆一個檔案，你會拆哪一層？是 model client、session、還是 CLI？為什麼？

## 反思問題

- 你傾向於一開始就做較多模組拆分，還是先做一個大檔案再重構？對教學版來說，哪一種風險比較高？
- 如果一個學生把 `permissions.py` 視為可有可無的附加檔案，這透露了他在哪個概念上還沒真正理解？
- 你覺得 `tests/` 先出現在骨架裡，會改變學生對整個專案的心智模型嗎？怎麼改變？

> **📝 本章一句話總結**
>
> 好的 harness 骨架不在於功能多寡，而在於從第一天就把「流程控制」、「能力宣告」和「權限治理」放在各自該待的位置。

## 延伸閱讀 / 下一章預告

有了 project skeleton，下一章就會處理這個骨架中最容易被忽略、卻又最能區分 harness 與 demo script 的部分：`session persistence` 與 `basic testing`。也就是說，第 18 章會把狀態延續、resume flow、以及三類最低測試案例落實成教學版的可驗證設計。
