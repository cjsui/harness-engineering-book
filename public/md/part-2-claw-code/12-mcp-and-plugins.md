# 第 12 章：MCP、Plugins 與能力擴充

## 章節導言

到這裡為止，我們看的大多是 `claw-code` 內建就有的核心能力：runtime、tools、permissions、session、prompt、config。第 12 章開始，焦點轉到另一個很容易讓人誤解的主題: 系統如何被擴充。這裡最需要小心的，不是技術細節，而是成熟度判斷。因為在真實 repo 裡，常常會同時存在「已實作的架構骨架」與「尚未完全 shipped 的產品介面」。若沒有把兩者分清楚，學生很容易把 extension boundary 誤讀成完整 plugin 平台。

`claw-code` 正是一個典型例子。從 `rust/README.md` 的 features table 可看到，`MCP server lifecycle` 標為已存在，但 `Plugin system` 與 `Skills registry` 則仍標示為 planned。另一方面，`mcp_tool_bridge.rs`、`mcp.rs`、`plugin_lifecycle.rs` 又確實已經提供了不少可讀程式碼：MCP tool naming、server registry、resource/tool metadata、plugin healthcheck、degraded mode、lifecycle trait 等。這代表我們不是在看空白規劃，而是在看一組可閱讀的 extension architecture 片段。

本章必須先做一個成熟度聲明：這裡教的是 extension architecture 與目前已存在的 code paths，不是在介紹一套 fully shipped 的 plugin system，也不是在介紹已完成的 skills registry API。凡是涉及尚未成熟的 plugin / skills 產品面，都必須被標示為 planned，而不能當作現況來教。

因此，本章的核心任務不是教你「如何使用一個已完成的 plugin 平台」，而是教你如何讀懂 `claw-code` 當前已存在的擴充邊界。你要分清楚哪些東西今天已經在程式碼中成立，哪些仍然只是 planned direction。這種區分，本身就是閱讀真實 agent harness 的重要能力。

## 學習目標
- 能說明 `MCP`、plugin tools、plugin lifecycle 在 `claw-code` 中目前處於什麼成熟度
- 能解釋 extension architecture 與完整 plugin product surface 之間的差異
- 能避免把尚未 shipped 的 plugin / skills registry 能力誤讀成已完成系統

## 核心概念講解
### MCP

在 `claw-code` 裡，`MCP` 並不是只是一個抽象名詞，而是已經有具體工具橋接與命名邏輯。`mcp.rs` 會把 server name 與 tool name 正規化成像 `mcp__server__tool` 的形式，也會根據 `McpServerConfig` 計算 signature 與 config hash。這代表系統已經明確處理「外部 server 上的工具要如何被表示成 runtime 可辨識的工具名」這個問題。

而 `mcp_tool_bridge.rs` 更進一步展示了橋接層的存在。它定義了 `McpToolRegistry`、`McpServerState`、`McpToolInfo`、`McpResourceInfo`、connection status、resource/tool listing 與 `call_tool()` 的流程。從這裡可以看出，`MCP` 在 `claw-code` 裡不是紙上談兵，而是已有 stateful registry 與 server-manager bridge 的架構雛形。

### plugin tools

從工具系統角度看，plugin tools 的關鍵不是「plugin」這個字本身，而是外部能力如何進入既有工具表面。前面第 7 章已看過 `GlobalToolRegistry` 可以同時處理 built-in、runtime、plugin tools；這一章再從 `mcp_tool_bridge.rs` 補上一層，就更清楚了: plugin-like capability 其實需要被轉譯成工具資訊、註冊狀態、server health 與呼叫路徑，才能真正進入 runtime。

也就是說，plugin tools 在這裡更接近「被橋接進現有 tool system 的外部能力」，而不是一個你今天就能穩定安裝、瀏覽、升級、卸載的完整市集型體驗。這個 distinction 非常重要，因為它決定我們該把本章教成架構閱讀，而不是產品操作手冊。

### extensibility boundaries

`claw-code` 目前最有價值的地方，是它已經讓 extensibility boundaries 相當清楚。`mcp_tool_bridge.rs` 處理 server state 與外部能力橋接，`mcp.rs` 處理 naming、signature 與 config identity，`plugin_lifecycle.rs` 則處理 plugin health、degraded mode、discovery 與 shutdown 的生命週期抽象。這些模組共同回答了一個問題: 如果系統要納入外部能力，哪些責任必須被顯性化？

答案至少包括: 名稱轉換、狀態追蹤、發現能力、健康檢查、降級模式、關閉流程。這些都是 extension boundary 的核心責任。即使今天還沒有完整 shipped 的 plugin product，這條責任鏈本身已經很值得學。因為它告訴你，擴充不是「把新工具接進來」那麼簡單，而是要處理跨進程、跨 server、跨可用性狀態的治理問題。

### what exists today vs what is still planned

這裡必須非常明確。根據 `rust/README.md`：

- `MCP server lifecycle`：已存在
- `Plugin system`：planned
- `Skills registry`：planned

再對照原始碼，我們可以更精準地說：`MCP` 相關 naming、bridge、registry、server state 與 plugin lifecycle trait 等「架構片段」已存在並可閱讀；但這不等於 repo 已經提供一個 fully shipped 的 plugin system，也不等於 skills registry API 已經是完成產品。`plugin_lifecycle.rs` 提供的是 lifecycle abstraction、healthcheck 與 discovery model，並非完整外掛發佈、安裝、治理與使用者操作層。

因此，本章需要明講三件事。第一，這些章節教的是 extension architecture 與現有程式碼。第二，它們**不**是在教一個完整 shipped plugin system。第三，凡是談到 plugin system / skills registry 的完整產品面，都必須被標示為 planned，而不能當成現況來教。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/rust/crates/runtime/src/mcp_tool_bridge.rs`
- `claw-code/rust/crates/runtime/src/mcp.rs`
- `claw-code/rust/crates/runtime/src/plugin_lifecycle.rs`

### 閱讀順序
1. 先讀 `mcp.rs`，理解 naming、signature、config hash
2. 再讀 `mcp_tool_bridge.rs`，看 server/tool/resource state 如何被註冊與呼叫
3. 最後讀 `plugin_lifecycle.rs`，看 healthcheck、degraded mode、discovery 與 shutdown 抽象

### 閱讀重點
- `MCP` tool naming 為何要做成 `mcp__server__tool` 形式
- `McpToolRegistry` 如何承接外部 server 狀態與工具/資源資訊
- `PluginLifecycle` trait 暗示了哪些現有 lifecycle 責任
- 哪些程式碼是 today’s implemented architecture，哪些產品層能力仍屬 planned

## 設計取捨分析

extension architecture 最大的取捨，是提早設計清楚邊界，還是等產品成熟後再補抽象。`claw-code` 明顯偏向前者：即使 plugin system 還沒完整 shipped，也先把 naming、bridge、healthcheck、degraded mode、shutdown 等責任做成顯性模組。這樣做的好處是系統將來較容易擴充，風險也比較不會被埋在臨時 glue code 裡；代價則是學生若只看檔名，很容易誤以為整套產品已成熟。

也因此，教材需要主動補上成熟度框架。否則讀者可能把「已有 lifecycle trait」誤解成「已有完整 plugin 平台」，把「已有 skills command」誤解成「已有完整 skills registry」。本章最大的教學責任，就是避免這種過度推論。

## Mini Harness 連結點

`mini harness` 在第一版明確不納入 full MCP support 與 plugin lifecycle，這不是退步，而是有意識的範圍控制。教學版最值得帶走的，不是外部擴充功能本身，而是 extension boundary 的觀念: 若未來真的要接外部 server 或外掛，你至少要處理 naming、state、discovery、health 與 degradation。完整 `claw-code` 已經替你示範這些責任如何被拆出來；教學版則先把這些觀念保留在腦中，而不急著實作。

## 本章小結

第 12 章真正教的，不是一個已完成的 plugin 平台，而是 `claw-code` 當前已存在的 extension architecture。`MCP` tool naming、server registry、bridge、plugin lifecycle、healthcheck、degraded mode 這些都已經有可讀程式碼；但 `Plugin system` 與 `Skills registry` 仍屬 planned。能把「已實作的架構邊界」與「尚未 shipped 的產品表面」分清楚，就是讀懂真實 harness 成熟度的關鍵能力。

## 章末練習
1. 解釋為什麼 `MCP server lifecycle` 已存在，不代表完整 `Plugin system` 已完成。
2. 說明 `mcp__server__tool` 這類命名形式解決了什麼問題。
3. 如果未來要把 `mini harness` 擴充成支援外部能力，你認為最先必須補的三個責任是什麼？

## 反思問題

- 你是否常把 repo 中「已有某個抽象或 trait」誤認成「已有完整產品能力」？這個習慣會怎麼影響系統判讀？
- 對 extension architecture 來說，你覺得 healthcheck 與 degraded mode 為什麼值得這麼早被考慮？
- 若一個系統完全不顯性處理 extension boundary，你覺得它最終會在什麼地方失控？

## 延伸閱讀 / 下一章預告

第 12 章處理的是外部能力如何被橋接進系統；第 13 章則會處理另一種更根本的邊界: 執行環境本身。也就是說，我們將從 extension boundary 轉到 environment boundary，討論為什麼 local 與 remote execution 根本不是同一類問題。
