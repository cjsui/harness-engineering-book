# 第 13 章：Remote 與多執行環境能力

## 章節導言

很多人在第一次看 agent harness 時，會把 remote execution 想成「只是把同樣的東西搬去另一台機器跑」。但真正的系統設計一旦走到這裡，就會發現事情完全不是這麼簡單。當執行位置不同，session token、proxy、CA bundle、可見檔案系統、環境變數、網路邊界、甚至信任假設都會跟著改變。也就是說，local 與 remote 並不是同一套 runtime 的單純部署差異，而是不同 execution boundary。

`claw-code` 的 `remote.rs` 很有代表性，因為它沒有把 remote support 寫成一個模糊 flag，而是明確拆出 `RemoteSessionContext`、`UpstreamProxyBootstrap`、`UpstreamProxyState`、`DEFAULT_REMOTE_BASE_URL`、proxy env propagation、CA bundle 路徑與 session token 讀取。這些設計都在傳達同一件事: remote execution 的困難，不在於把 prompt 送到遠端，而在於讓整個 runtime 能在不同環境條件下安全、一致、可診斷地工作。

本章也要先做成熟度聲明：這裡教的是 execution environment architecture 與目前已存在的 remote code paths，不是在宣稱 repo 已經提供完整 shipped 的 plugin system 或 skills registry API。凡是牽涉後續擴充面的討論，都必須明確標示為 planned，而不是被描述成現在已完成的產品能力。

本章的核心任務，就是把這些 environment boundaries 講清楚。你要理解的不是某個單一 API，而是為什麼 local 與 remote 是兩類不同問題；以及真實 harness 如何把這些差異顯性放進環境偵測、proxy bootstrap 與 subprocess env construction 中。

## 學習目標
- 能說明 local 與 remote execution 為什麼不是同一個問題
- 能解釋 `RemoteSessionContext`、`UpstreamProxyBootstrap` 與 proxy env state 的角色
- 能理解 execution environment boundary 為什麼是成熟 harness 必須正式處理的主題

## 核心概念講解
### remote execution

`remote.rs` 一開始就用環境變數把 remote context 做成顯性結構。`RemoteSessionContext` 會從環境中讀出：

- remote 是否啟用
- `session_id`
- `base_url`

這表示 remote execution 在 `claw-code` 裡不是一段隱藏邏輯，而是一個明確的 session context。系統需要知道自己是不是處於 remote 模式、連的是哪個遠端 session、對應哪個 base URL，才能進一步決定後面如何建立代理與子程序環境。這也說明，remote support 的本質不是多一條網路請求，而是多一層執行上下文。

### environment boundaries

真正的難點在 execution environment boundary。`UpstreamProxyBootstrap` 會根據 remote context、是否啟用 upstream proxy、session token path、CA bundle path、system CA path 與讀出的 token 來判斷 `should_enable()`。也就是說，系統不是看到 `CLAUDE_CODE_REMOTE=true` 就直接啟動 remote 模式，而是要確認多個條件一起滿足。

這反映出一個很重要的設計原則: 環境切換不是布林值，而是一組邊界條件。檔案路徑、證書、token、proxy、session id、網路例外名單，都屬於 execution environment 的一部分。若不顯性處理這些條件，系統在 local 看起來能跑，到了 remote 或 proxy 受限環境就可能立即失效。

### why local and remote are not the same problem

本章最核心的一句話就是：`local and remote are not the same problem`。在 local 模式下，工具與 runtime 多半假設自己直接面對本地工作區、本地檔案、本地 shell、本地憑證與直接網路；在 remote 模式下，則可能需要透過 upstream proxy、遠端 session token、特定 CA bundle 與轉譯後的 subprocess env 才能工作。這些差異不是表面部署位置不同，而是整條 operational chain 不同。

`remote.rs` 的 `subprocess_env()` 很值得注意，因為它會在啟用狀態下建出 `HTTPS_PROXY`、`NO_PROXY`、`SSL_CERT_FILE`、`NODE_EXTRA_CA_CERTS`、`REQUESTS_CA_BUNDLE`、`CURL_CA_BUNDLE` 等環境變數。這說明 remote execution 問題往往不是 agent loop 本身，而是整個執行環境如何被重新包裝給下游程序。換句話說，remote 不是「再多一個 transport」而已，而是系統外殼本身也要跟著改變。

### boundary-aware design

成熟 harness 面對 remote 問題時，最值得學的不是每個 env var 名稱，而是 boundary-aware design。`RemoteSessionContext`、`UpstreamProxyBootstrap`、`UpstreamProxyState` 分別負責不同層次的問題：目前是否處於 remote session、是否應該啟動 upstream proxy、若啟動後應該如何把環境傳給子程序。這種分層讓 remote 支援不是一個到處散落的 if/else，而是一組可推理、可測試、可逐步擴充的環境模型。

也正因如此，本章雖然和第 12 章一樣涉及較高階能力，但它們不是同一類主題。第 12 章處理的是 extension boundary；第 13 章處理的是 execution environment boundary。前者關心外部能力如何被系統吸納，後者關心系統自己在哪裡、如何、在什麼條件下執行。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/rust/crates/runtime/src/remote.rs`
- `claw-code/rust/README.md`

### 閱讀順序
1. 先讀 `remote.rs` 的 `RemoteSessionContext`
2. 再讀 `UpstreamProxyBootstrap` 與 `UpstreamProxyState`
3. 最後回頭看 `rust/README.md`，把 remote 能力放回整體 runtime 責任圖中理解

### 閱讀重點
- `RemoteSessionContext` 如何從 env 建立 remote execution 上下文
- `UpstreamProxyBootstrap` 為什麼要同時看 token、session id、CA bundle、base URL
- `subprocess_env()` 如何把 remote/proxy 邏輯轉成下游程序可用的環境
- 為什麼 local / remote 是不同 execution boundary，而不是同一套 loop 的小變形

## 設計取捨分析

remote support 的最大取捨，是把環境差異顯性化，還是把它藏在隱形部署細節裡。顯性化的好處是結構清楚、可測試、出問題時容易診斷；代價則是模組數變多、學習門檻上升。`claw-code` 顯然選擇前者，因為它承認 remote execution 本來就不是小事，若不提早做成模組，之後很容易在 proxy、token、憑證與子程序邊界上積出難以理解的技術債。

另一個取捨則是 remote 能力是否該在教學版過早引入。本書的答案是否定的。不是因為 remote 不重要，而是因為它牽涉的 execution boundary 遠比本地最小 harness 複雜。若學生還沒掌握本地 loop、tooling、permissions、session，就先被丟進 proxy 與 CA bundle 問題，學習重點很容易失焦。

## Mini Harness 連結點

`mini harness` 第一版明確排除 `remote execution`，理由在本章已經很清楚了：它不是一個小附加功能，而是另一層 execution environment 問題。教學版最值得先帶走的，不是 remote support 本身，而是這個觀念: 一旦系統跨出本地執行環境，你就必須重新思考 session context、proxy、憑證、子程序環境與信任邊界。完整 `claw-code` 已經替你示範這些責任該如何被模組化；教學版則先把它保留成未來擴充方向。

## 本章小結

第 13 章要你學到的，不是如何立刻做出 remote harness，而是為什麼 remote execution 是一類獨立的架構問題。`RemoteSessionContext`、`UpstreamProxyBootstrap`、`UpstreamProxyState` 共同說明，當執行位置改變時，環境、token、proxy、CA bundle 與 subprocess behavior 都會跟著改變。這使得 local 與 remote 不是同一套系統的小差異，而是不同 execution boundary 的設計問題。

## 章末練習
1. 解釋為什麼 remote execution 不應被理解成「同一套東西搬到別台機器跑」。
2. 說明 `UpstreamProxyBootstrap::should_enable()` 背後反映了哪些環境邊界條件。
3. 如果未來要把 `mini harness` 擴充成支援 remote，你認為最先需要補的三個模組責任是什麼？

## 反思問題

- 你是否曾在系統設計中低估過「環境差異」本身的複雜度？後來通常是在哪裡出問題？
- 對 agent harness 來說，remote support 最難的是 transport、security、還是 operational debugging？為什麼？
- 如果一個系統只在 local 測得很好，但完全沒有 boundary-aware 的 remote 設計，你會信任它被拿去做真實跨環境工作嗎？

## 延伸閱讀 / 下一章預告

第 12、13 章一起補完後，Part II 對 `claw-code` 的整體拆解就更接近完整版本了。接下來若回到 Part III 與 Part IV，你會更清楚看到：哪些能力值得在 `mini harness` 裡保留，哪些則應該留在真實系統的後續擴充與規模化階段。
