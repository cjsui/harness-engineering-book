# 第 11 章：Config、Modes 與執行環境

## 章節導言

前一章談的是系統如何把世界描述給模型，而這一章要問的是：這些世界設定本身從哪裡來？對真實 harness 而言，很多關鍵行為都不是寫死在原始碼裡，而是受到 `config hierarchy`、permission modes、sandbox 與 remote / local 環境條件影響。也就是說，系統的表現不只由 code 決定，也由設定層與執行環境決定。

`claw-code` 在這一層做得相當成熟。`config.rs` 不只是讀一個 JSON，而是有來源層級、合併 precedence、feature-specific parsing，以及針對 model、permissions、hooks、plugins、MCP、sandbox 等能力的結構化解析。另一方面，`remote.rs` 又提醒我們：environment-sensitive behavior 不只是 config file 的問題，還可能來自環境變數、proxy 狀態、remote session token 與 base URL。這些一起構成了系統的 operational environment。

本章會先釐清 `config hierarchy`，再討論 permission modes 如何由設定層進入 runtime，最後看 environment-sensitive behavior 為什麼是 agent harness 需要面對的真實邊界。你會看到，成熟系統之所以可用，不只是因為它功能多，而是因為它知道如何讓相同核心在不同 scope 與環境下表現出不同但可預期的行為。

## 學習目標
- 能說明 `config hierarchy` 如何決定最終有效設定
- 能解釋 permission modes 與 permission rules 如何從設定層流入 runtime
- 能理解 local / remote / proxy 這類 environment-sensitive behavior 為什麼屬於 harness 問題

## 核心概念講解
### config hierarchy

`USAGE.md` 已先把 `config file resolution order` 寫得很清楚，`config.rs` 則把它落實成 `ConfigLoader::discover()` 的搜尋順序。它至少會依序看：

1. `~/.claw.json`
2. `~/.config/claw/settings.json`
3. `<repo>/.claw.json`
4. `<repo>/.claw/settings.json`
5. `<repo>/.claw/settings.local.json`

這就是典型的 `config hierarchy`。重點不是檔案多，而是 scope 清楚：user scope、project scope、local override scope 會逐層疊加。這種設計使得同一套核心系統可以有全域預設、專案規則、以及本機覆寫，而不必把所有差異都硬寫進原始碼。

### permission modes

前面第 8 章談的是 permission policy 的運作，這裡則要補上「這些 modes 從哪裡來」。在 `config.rs` 裡，`RuntimeFeatureConfig` 會解析出 `permission_mode` 與 `permission_rules`；`parse_optional_permission_mode()` 也支援從 `permissionMode` 或 `permissions.defaultMode` 這類欄位讀取設定。這意味著 permission 並不只是 CLI 當下傳入的旗標，它也可以是一個由設定層提供的預設。

這個設計很重要，因為它讓安全邊界不只是一個臨時命令列選項，而能成為專案層規則的一部分。同時，allow / deny / ask 規則也能透過 config 載入，讓 permission system 真正成為可設定、可版本化的治理機制，而不是零散寫在程式裡的特殊判斷。

### environment-sensitive behavior

一個成熟 harness 通常不能假設自己永遠在同一種環境裡執行。`remote.rs` 很明確地展示了這點：`RemoteSessionContext` 會從環境變數讀取 remote enabled 狀態、session id 與 base URL；`UpstreamProxyBootstrap` 會根據 token path、CA bundle、proxy 狀態與 session token 決定是否啟用 upstream proxy。這些都屬於 environment-sensitive behavior。

這裡值得特別注意的是：環境行為不是附屬邊角，而是系統執行條件的一部分。對本地單機教學版來說，這些看起來也許太重；但對真實 harness 而言，local 與 remote 根本不是同一個問題。執行位置不同，能見資源不同，proxy 與證書路徑不同，甚至安全假設也不同。把這些差異顯性化，正是成熟 harness 的一部分。

### config 與 runtime 的關係

`config.rs` 的真正價值，不是儲存設定，而是把設定轉成 runtime 可直接消費的 feature config。`RuntimeConfig` 不只保留 merged settings 與 loaded entries，還解析出 hooks、plugins、MCP、oauth、model、permission mode、permission rules、sandbox 等結構化子配置。這使得 runtime 並不需要自己去碰原始 JSON，而能直接拿到較乾淨的 typed configuration。

這種分層能避免一個很常見的壞味道：每個子系統自己去讀 JSON、自己解字串、自己決定 precedence。當系統規模變大時，那會讓 config behavior 非常難以推理。`claw-code` 用 `ConfigLoader` 把這一層集中處理，換來的是較高的一致性與可測試性。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/USAGE.md`
- `claw-code/rust/crates/runtime/src/config.rs`
- `claw-code/rust/crates/runtime/src/remote.rs`

### 閱讀順序
1. 先讀 `USAGE.md` 的 config file resolution order
2. 再讀 `config.rs` 的 `ConfigLoader`、`RuntimeConfig`、permission / sandbox parsing
3. 最後讀 `remote.rs` 的 `RemoteSessionContext` 與 `UpstreamProxyBootstrap`

### 閱讀重點
- `config hierarchy` 如何決定設定覆寫順序
- permission modes 與 permission rules 如何從 config 流入 runtime
- local / remote / proxy 這些環境條件如何改變系統行為
- 為什麼成熟 harness 需要把 environment-sensitive behavior 顯性做成模組

## 設計取捨分析

設定層最大的取捨，是彈性與可理解性之間的平衡。層級越多、可覆寫點越多，系統越靈活，但也越難判斷某個最終行為到底來自哪裡。`claw-code` 選擇接受這種複雜度，因為它需要同時支援 user defaults、project rules、local overrides、remote context、sandbox 與 plugin / MCP 等多種面向。這對真實系統很合理，但教學上就需要特別強調 precedence 與 scope，否則學生很容易迷失。

另一個取捨則是 remote / environment 行為要不要早期納入。若完全不處理，系統看起來更純粹；但真實部署時，很多 operational 問題就會突然變成例外情況。`claw-code` 選擇把這些問題提前顯性化，雖然增加模組數與概念負擔，卻也讓 local 與 remote 邊界比較不會藏在隱晦副作用中。

## Mini Harness 連結點

`mini harness` 在這一層最值得保留的，是簡化版 `config hierarchy` 與最基本的 permission mode 設定。例如教學版可以只支援 project-level 與 local-level 設定，先不處理完整 user scope、MCP、plugin、remote proxy 等能力。但即使縮小，也應該讓學生看到：設定不是散落常數，而是會影響 runtime mode、工具限制與基本環境行為的正式層。完整 `claw-code` 增加的，則是更成熟的 scope 合併與環境分流能力。

## 本章小結

`claw-code` 的 `config hierarchy`、permission modes 與 environment-sensitive behavior 共同說明了一件事：真實 harness 不只是寫好核心 loop，還要讓這個 loop 能在不同 scope、不同專案、不同環境條件下以可預期方式運作。`ConfigLoader` 把設定 precedence 變得可推理，`RuntimeConfig` 把設定轉成 runtime 可用結構，而 `remote.rs` 則提醒我們 local 與 remote 邊界本來就是系統設計問題。

## 章末練習
1. 說明 `config hierarchy` 對真實 harness 有什麼好處，也有什麼代價。
2. 解釋為什麼 permission mode 應該可以來自 config，而不只是 CLI 旗標。
3. 如果你要為 `mini harness` 設計最小設定系統，你會支援哪些層級？哪些先不支援？

## 反思問題

- 你是否曾經在大型系統中搞不清楚某個設定到底從哪裡生效？這和本章的 precedence 問題有何相似？
- 若一個系統完全不顯性處理 remote / proxy 環境差異，最可能在哪些情境出問題？
- 對教學版來說，你覺得應先教 config 還是先教 runtime？為什麼？

## 延伸閱讀 / 下一章預告

到這裡，Part II 的中層系統面已經更完整了：你看過 CLI、session、Prompt Assembly、config 與 environment。接下來若往 extension 與 remote 繼續走，就會自然接到第 12、13 章的 MCP / plugin 邊界與 remote execution 問題。
