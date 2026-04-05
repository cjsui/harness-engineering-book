# 第 7 章：Tool System：讓模型有手腳

## 章節導言

一個沒有工具的模型，最多只能當顧問；一個有工具的模型，才可能成為 agent。但真正困難的地方從來不是「把工具接上去」，而是「如何把工具接成一個可控、可理解、可限制的能力層」。如果工具只是零散函式的集合，模型可能勉強能呼叫幾個能力，卻很難在大型系統中穩定使用。`claw-code` 的 `tools` crate 值得學，不是因為它工具很多，而是因為它把工具表面做成一個有宣告、有治理、有過濾機制的 registry system。

本章的核心問題有五個：單一工具應該如何被宣告？所有工具如何被統一管理？模型真正看到的是哪一層工具定義？使用者透過 `--allowedTools` 限制能力時，系統如何把別名與 canonical name 處理乾淨？以及 built-in、runtime、plugin tools 這三種來源為什麼需要被一起考慮？這些問題如果沒有被設計清楚，工具系統很快就會變成一堆難以治理的 capability leak。

換句話說，tool system 的任務不只是讓模型「有手腳」，而是讓這雙手腳能被清楚說明、被安全開放、被合理限制，並且能在未來擴充時不把整個系統變成混亂的能力黑箱。

## 學習目標
- 能說明 `ToolSpec`、`GlobalToolRegistry` 與 `definitions()` 各自的角色
- 能解釋 `allowed tools` 與 permission 要如何共同治理工具表面
- 能指出哪些 tool-system 能力是 `mini harness` 必須保留、哪些可以先省略

## 核心概念講解
### tool schema

`ToolSpec` 是理解整個 tool system 的第一個關鍵。它把四個東西綁在一起：

- `name`
- `description`
- `input_schema`
- `required_permission`

這個設計非常重要，因為它表示工具不是只有「可做的事」，還同時帶著「怎麼被描述」與「需要什麼權限」一起被宣告。也就是說，一個工具一旦進入 registry，就不只是程式碼能力，而是成為一個可被模型理解、可被 runtime 傳遞、也可被 permissions 系統治理的正式介面。

如果拿掉 schema 層，工具很快就會退化成零散本地函式：模型不知道輸入格式、系統很難統一暴露能力、權限資訊也無法穩定附著。這也是為什麼 `ToolSpec` 看似簡單，卻是整個 tool system 的語義基礎。

### tool registry

單一工具的宣告只是第一步，真正重要的是所有工具如何被集中管理。`GlobalToolRegistry` 的欄位很直接：`plugin_tools`、`runtime_tools`、`enforcer`。這表示它不是只收 built-in tools，而是預期系統中的工具可能來自多個來源，而且這些來源最終都要被統一管理。

從實作可看出，registry 並不是單純的容器。`with_plugin_tools()` 會檢查 plugin tool 名稱是否和 built-in 衝突，也會擋下重複名稱；`with_runtime_tools()` 則會再和 built-in 與 plugin 工具一起做名稱衝突檢查。這說明 registry 的責任不只是「裝東西」，還包括維持能力空間的整體一致性。若沒有這層檢查，大型系統很快就會出現名稱碰撞、描述混亂、權限不一致等問題。

### tool dispatch

很多初學者會把 registry 和 dispatch 混在一起，但兩者其實不同。registry 的工作是維護「有哪些工具」以及「這些工具的定義是什麼」；dispatch 的工作則是當模型真的發出 tool use 時，系統如何把那個名稱導向正確執行器並回收結果。也就是說，registry 比較像能力目錄，dispatch 比較像行動路由。

在 `claw-code` 的整體架構中，這兩層是分開的。`tools` crate 管的是宣告與整理，而實際執行是在 runtime / tool executor 的流程裡發生。這種分工很值得學，因為它讓「模型看到什麼工具」與「系統怎麼執行工具」可以被分別推理與測試。如果把兩者混成一團，你很難單獨驗證工具表面是否合理，也很難清楚限制哪些工具能被暴露給模型。

### allowed tools

`normalize_allowed_tools()` 是一個很容易被忽略、但其實很實用的函式。它處理的問題是：當使用者透過 `--allowedTools` 輸入工具限制時，系統如何把這些值正規化成 canonical name 集合。這裡不只支援直接輸入正式工具名，也支援一些常用 alias，例如：

- `read` -> `read_file`
- `write` -> `write_file`
- `edit` -> `edit_file`
- `glob` -> `glob_search`
- `grep` -> `grep_search`

這個函式的重要性在於，它把 CLI surface 的使用便利性與內部工具命名一致性橋接起來。使用者可以用較自然的縮寫，但系統內部仍維持穩定 canonical name。若沒有這層正規化，`--allowedTools` 會變得脆弱且難用；如果把 alias 邏輯散落在各處，則整個工具治理也會變得難維護。

### built-in tools、runtime tools、plugin tools

`GlobalToolRegistry` 最值得學的一點，是它沒有假設所有工具都來自同一種來源。內建工具來自 `mvp_tool_specs()`；runtime tools 可在執行期被加入；plugin tools 則代表外部擴充來源。接著，`definitions()` 會把這三種來源統一轉成模型可見的 `ToolDefinition` 列表。

這裡其實有一條很漂亮的資料流：使用者先透過 config 或 CLI 決定可見工具範圍，registry 透過 `normalize_allowed_tools()` 取得 canonical allowed set，再用 `definitions()` 只把允許暴露的 built-in、runtime、plugin 工具轉成最終提供給模型的工具表面。換句話說，模型看到的不是整個本地宇宙，而是經過 registry 篩選後的能力切片。

這也是本章必須強調的「如果拿掉它會壞什麼」分析之一。若拿掉 `definitions()` 這種統一輸出層，工具來源再多也只是零散集合，模型端很難拿到一致的工具清單；若拿掉 `required_permission` 與 `permission_specs()` 的關聯，權限系統就無法穩定知道每個工具需要哪種 permission mode。tool system 因此不是一個獨立小模組，而是整個 governance chain 的一環。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/rust/crates/tools/src/lib.rs`
- `claw-code/rust/crates/runtime/src/permissions.rs`

### 閱讀順序
1. 先讀 `ToolSpec`、`GlobalToolRegistry`、`RuntimeToolDefinition`
2. 再讀 `normalize_allowed_tools()`
3. 最後讀 `definitions()` 與 `permission_specs()`

### 閱讀重點
- `ToolSpec`：單一工具如何把 schema 與 required permission 綁在一起
- `GlobalToolRegistry`：如何合併 built-in、runtime、plugin 三種工具來源
- `normalize_allowed_tools`：如何把 alias 與 canonical name 統一
- `definitions()` method：如何把 registry 中可見的工具轉成模型真正可用的 `ToolDefinition`

## 設計取捨分析

tool system 最根本的取捨，是能力廣度與治理清晰度之間的平衡。工具越多，模型能做的事越多；但工具越多，也越需要統一 naming、schema、permission mapping、allowed-tools filtering、以及衝突檢查。`claw-code` 選擇把這些治理工作做得相對完整，因此工具層不是一份簡單清單，而是一個正式 registry。

這種設計的代價，是閱讀上會多一層抽象。初學者可能會想：「為什麼不直接寫一個 map，tool name 對 function 就好了？」答案是那樣做雖然快，但很難支援工具來源擴充、很難把 permission 綁進宣告、也很難穩定控制模型可見表面。當系統規模一大，這些省略掉的抽象反而會變成技術債。因此 `claw-code` 的做法雖然較重，卻更接近真實 harness 面對的問題。

## Mini Harness 連結點

在 `mini harness` 裡，我們會保留 tool system 的骨架，但把它縮小。教學版依然應該有明確的 tool spec，至少包含名稱、描述、輸入格式與權限需求；也應該有一個很小的 registry，能決定哪些工具暴露給模型。但我們大概不會一開始就做 plugin tools、複雜搜尋、完整 alias 集合或大量 runtime tool definitions。對 `mini harness` 來說，真正不能拿掉的是「能力宣告與治理綁在一起」這個原則，而不是所有成熟系統才需要的周邊功能。

## 本章小結

`claw-code` 的 tool system 告訴我們：讓模型有手腳，不是把幾個 function 接上去就算完成。真正的重點是把工具做成有 schema、有 permission、有 registry、有 filtering、有統一輸出層的能力系統。`ToolSpec`、`GlobalToolRegistry`、`normalize_allowed_tools()`、`definitions()` 正是這條能力鏈上的幾個關鍵節點。理解它們，你才會知道工具層為何既是 capability layer，也是 governance layer。

## 章末練習
1. 說明為什麼 `ToolSpec` 必須同時包含 `input_schema` 與 `required_permission`。
2. 解釋 `normalize_allowed_tools()` 在 CLI 使用體驗與內部一致性之間扮演的角色。
3. 如果要為 `mini harness` 設計最小版 tool registry，你會保留哪些欄位與函式？

## 反思問題

- 你覺得在真實 agent 系統中，工具數量增加時最先壞掉的會是 schema、命名、還是 permission 治理？為什麼？
- 如果只做 dispatch、不做 registry，短期看起來省事；那長期會在哪些地方付出代價？
- 你是否能接受模型看到的工具清單和系統實際存在的工具清單不同？在什麼條件下這是合理的？

## 延伸閱讀 / 下一章預告

有了 runtime 的 heart 與 tools 的 hands，下一個問題自然是：這雙手到底能動到什麼程度，誰來說了算？接下來的第 8 章會進入 `Permissions and Guardrails`，把 capability 與 governance 如何真正扣合起來講清楚。
