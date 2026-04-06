# 第 11 章：Config、Modes 與執行環境

## 章節導言

前一章談的是系統如何把世界描述給模型，而這一章要問的是：這些世界設定本身從哪裡來？對真實 harness 而言，很多關鍵行為都不是寫死在原始碼裡，而是受到 `config hierarchy`、permission modes、sandbox 與 remote / local 環境條件影響。也就是說，系統的表現不只由 code 決定，也由設定層與執行環境決定。

`claw-code` 在這一層做得相當成熟。`config.rs` 不只是讀一個 JSON，而是有來源層級、合併 precedence、feature-specific parsing，以及針對 model、permissions、hooks、plugins、MCP、sandbox 等能力的結構化解析。另一方面，`remote.rs` 又提醒我們：environment-sensitive behavior 不只是 config file 的問題，還可能來自環境變數、proxy 狀態、remote session token 與 base URL。這些一起構成了系統的 operational environment。

本章會先釐清 `config hierarchy`，再討論 permission modes 如何由設定層進入 runtime，最後看 environment-sensitive behavior 為什麼是 agent harness 需要面對的真實邊界。你會看到，成熟系統之所以可用，不只是因為它功能多，而是因為它知道如何讓相同核心在不同 scope 與環境下表現出不同但可預期的行為。

> **📋 本章速覽**
>
> 讀完本章後，你將能夠：
> - 理解設定不是一個檔案，而是多層設定依優先順序合併的結果
> - 知道 permission modes（權限模式）如何從設定檔進入 runtime
> - 理解為什麼 local 和 remote 執行環境根本是不同的問題
> - 看懂 `ConfigLoader` 如何把多來源設定轉成 runtime 可用的結構
> - 判斷 mini harness 的設定系統該保留哪些最小層級

## 學習目標
- 能說明 `config hierarchy` 如何決定最終有效設定
- 能解釋 permission modes 與 permission rules 如何從設定層流入 runtime
- 能理解 local / remote / proxy 這類 environment-sensitive behavior 為什麼屬於 harness 問題

### 先備知識檢查

開始本章前，請確認你已經了解以下內容：

- [ ] 知道什麼是 JSON 格式（設定檔通常是 JSON）
- [ ] 理解「覆寫」的概念：後來的值蓋掉先前的值
- [ ] 讀過第 8 章，對 permission policy 有基本認識
- [ ] 知道什麼是環境變數（如 `HOME`、`PATH` 這類系統設定）

## 核心概念講解
### config hierarchy

`USAGE.md` 已先把 `config file resolution order` 寫得很清楚，`config.rs` 則把它落實成 `ConfigLoader::discover()` 的搜尋順序。它至少會依序看：

1. `~/.claw.json`
2. `~/.config/claw/settings.json`
3. `<repo>/.claw.json`
4. `<repo>/.claw/settings.json`
5. `<repo>/.claw/settings.local.json`

這就是典型的 `config hierarchy`。重點不是檔案多，而是 scope 清楚：user scope、project scope、local override scope 會逐層疊加。這種設計使得同一套核心系統可以有全域預設、專案規則、以及本機覆寫，而不必把所有差異都硬寫進原始碼。

> 💡 **生活化比喻**：Config hierarchy 就像穿衣服的層次。你有一套「基本穿搭」（全域預設），上班時會套上「公司制服」（專案規則），而到了特別冷的日子你還會加一件「自己的外套」（本機覆寫）。最終你身上穿的，是這三層疊在一起的結果。外層會蓋住內層的部分——如果公司規定穿白襯衫，你就不會看到裡面的花 T-shirt。

> ⚠️ **初學者常見誤區**
>
> - **誤區一**：以為改了全域設定就一定會生效——如果專案層或本機層有覆寫，全域設定會被蓋掉。搞不清楚「到底哪個設定在生效」是初學者最常遇到的困擾。
> - **誤區二**：以為所有設定都寫在同一個檔案裡——成熟系統的設定通常分散在多個檔案中，依層級合併。

### permission modes

前面第 8 章談的是 permission policy 的運作，這裡則要補上「這些 modes 從哪裡來」。在 `config.rs` 裡，`RuntimeFeatureConfig` 會解析出 `permission_mode` 與 `permission_rules`；`parse_optional_permission_mode()` 也支援從 `permissionMode` 或 `permissions.defaultMode` 這類欄位讀取設定。這意味著 permission 並不只是 CLI 當下傳入的旗標，它也可以是一個由設定層提供的預設。

這個設計很重要，因為它讓安全邊界不只是一個臨時命令列選項，而能成為專案層規則的一部分。同時，allow / deny / ask 規則也能透過 config 載入，讓 permission system 真正成為可設定、可版本化的治理機制，而不是零散寫在程式裡的特殊判斷。

> 💡 **生活化比喻**：Permission modes 就像大樓的門禁系統。你可以在保全室統一設定「所有訪客都需要登記」（全域預設），也可以針對某層樓設定「研發部門需要刷卡才能進」（專案層規則），甚至某個人可以有特別的通行權限（本機覆寫）。重點是這些規則是寫在系統裡的，而不是每次都靠保全臨時決定。

### environment-sensitive behavior

一個成熟 harness 通常不能假設自己永遠在同一種環境裡執行。`remote.rs` 很明確地展示了這點：`RemoteSessionContext` 會從環境變數讀取 remote enabled 狀態、session id 與 base URL；`UpstreamProxyBootstrap` 會根據 token path、CA bundle、proxy 狀態與 session token 決定是否啟用 upstream proxy。這些都屬於 environment-sensitive behavior。

這裡值得特別注意的是：環境行為不是附屬邊角，而是系統執行條件的一部分。對本地單機教學版來說，這些看起來也許太重；但對真實 harness 而言，local 與 remote 根本不是同一個問題。執行位置不同，能見資源不同，proxy 與證書路徑不同，甚至安全假設也不同。把這些差異顯性化，正是成熟 harness 的一部分。

> 💡 **生活化比喻**：這就像同一個 App，在你家 Wi-Fi 和在公司 VPN 下的行為可能完全不同。在家可以直接連網，在公司要走代理伺服器（proxy）；在家用個人帳號，在公司用企業帳號。App 如果不處理這些環境差異，到了公司就會莫名其妙連不上。Harness 面對的 local / remote 差異也是同樣的道理。

### config 與 runtime 的關係

`config.rs` 的真正價值，不是儲存設定，而是把設定轉成 runtime 可直接消費的 feature config。`RuntimeConfig` 不只保留 merged settings 與 loaded entries，還解析出 hooks、plugins、MCP、oauth、model、permission mode、permission rules、sandbox 等結構化子配置。這使得 runtime 並不需要自己去碰原始 JSON，而能直接拿到較乾淨的 typed configuration。

這種分層能避免一個很常見的壞味道：每個子系統自己去讀 JSON、自己解字串、自己決定 precedence。當系統規模變大時，那會讓 config behavior 非常難以推理。`claw-code` 用 `ConfigLoader` 把這一層集中處理，換來的是較高的一致性與可測試性。

> 💡 **生活化比喻**：想像你開一家餐廳。如果每個廚師自己去倉庫翻找食材、自己決定今天的菜單，廚房一定亂成一團。好的做法是有一個「備料組」（ConfigLoader）統一處理：把食材洗好切好、依照今天的菜單分配到各個工作站。廚師只需要拿到已經整理好的食材（typed configuration）就可以開始煮菜，不需要自己去倉庫翻箱倒櫃。

> ⚠️ **初學者常見誤區**
>
> - **誤區**：以為設定就是「讀一個 JSON 檔」這麼簡單——成熟系統的設定涉及多來源合併、優先順序、型別解析、預設值處理等。如果每個模組自己去讀原始設定檔，很容易出現「A 模組讀到的值和 B 模組不一樣」的 bug。

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

### 學習自我檢核

讀完本章後，請確認以下每一項你都能做到：

- [ ] 我能說出 config hierarchy 的至少三個層級（user / project / local）
- [ ] 我能解釋為什麼後面的設定會「覆寫」前面的設定
- [ ] 我知道 permission modes 可以從設定檔載入，而不只是靠 CLI 參數
- [ ] 我理解 local 和 remote 執行環境為什麼不能當成同一回事
- [ ] 我能說明 `ConfigLoader` 集中處理設定的好處（一致性、可測試性）
- [ ] 我能判斷 mini harness 的設定系統該保留哪些層級

### 關鍵概念速查表

| 術語 | 英文 | 簡要說明 |
|------|------|----------|
| 設定階層 | Config Hierarchy | 多層設定檔依優先順序合併，決定最終有效值 |
| 權限模式 | Permission Modes | 控制 agent 能做什麼的安全設定（allow / deny / ask） |
| 設定載入器 | ConfigLoader | 負責搜尋、讀取、合併多來源設定的集中模組 |
| 執行時設定 | RuntimeConfig | 已合併並解析成結構化型別的設定，供 runtime 直接使用 |
| 環境敏感行為 | Environment-Sensitive Behavior | 系統行為因 local / remote / proxy 等環境差異而改變 |
| 使用者範圍 | User Scope | `~/.claw.json` 等全域設定，適用於所有專案 |
| 專案範圍 | Project Scope | `<repo>/.claw.json` 等設定，只對特定專案生效 |
| 本機覆寫 | Local Override | `settings.local.json` 等個人設定，優先級最高且不入版控 |

## 章末練習
1. 說明 `config hierarchy` 對真實 harness 有什麼好處，也有什麼代價。
2. 解釋為什麼 permission mode 應該可以來自 config，而不只是 CLI 旗標。
3. 如果你要為 `mini harness` 設計最小設定系統，你會支援哪些層級？哪些先不支援？

## 反思問題

- 你是否曾經在大型系統中搞不清楚某個設定到底從哪裡生效？這和本章的 precedence 問題有何相似？
- 若一個系統完全不顯性處理 remote / proxy 環境差異，最可能在哪些情境出問題？
- 對教學版來說，你覺得應先教 config 還是先教 runtime？為什麼？

> **📝 本章一句話總結**
>
> 成熟的 harness 不是只寫好核心邏輯，還要讓同一套核心能透過分層設定與環境感知，在不同 scope 和不同環境下可預期地運作。

## 延伸閱讀 / 下一章預告

到這裡，Part II 的中層系統面已經更完整了：你看過 CLI、session、Prompt Assembly、config 與 environment。接下來若往 extension 與 remote 繼續走，就會自然接到第 12、13 章的 MCP / plugin 邊界與 remote execution 問題。
