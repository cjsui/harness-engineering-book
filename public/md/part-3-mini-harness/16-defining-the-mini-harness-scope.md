# 第 16 章：定義 Mini Harness 的最小範圍

## 章節導言

現在我們終於要從「看懂真實 harness」跨到「自己做一個縮小版 harness」。但在真正開始寫 Python 之前，有一件事比寫程式更重要：先把範圍定義對。很多教學專案失敗，不是因為學生不會寫，而是因為一開始沒有把最小可行範圍切清楚，結果不是一路膨脹成重做整個真實系統，就是反過來縮得太小，最後只剩一個包了 prompt 的小腳本，完全失去 harness 的本質。

因此，第 16 章的任務不是進入實作細節，而是做一個有意識的減法。我們要從前面學到的 `claw-code` 整體圖中，挑出最值得保留的核心，再明確列出這一版 `mini harness` 不做什麼。這種範圍切割不是偷懶，而是教學設計本身。因為本書的目標從來不是複製 `claw-code`，而是讓你在理解真實系統之後，能獨立做出一個「保留本質、但規模適中」的 agent harness。

這一章會先界定 v1 的 included 與 excluded 清單，再說明為什麼這樣的減法仍然保留了 Harness Engineering 的核心。接著，我們會把這些決策轉成下一章可以直接動手的任務說明。換句話說，這一章就是 Part III 的 scope contract。

> **📋 本章速覽**
> - 學會如何對專案做「有意識的減法」——定義 v1 該做什麼、不該做什麼
> - 認識 mini harness v1 的五大核心能力：message loop、tool dispatch、permission policy、session persistence、basic tests
> - 了解四項被刻意排除的能力及其排除理由
> - 理解「做得更小」和「做得太薄」之間的關鍵差異
> - 為下一章的 Python 實作建立清楚的範圍邊界

## 學習目標
- 能清楚定義 `mini harness` v1 應包含與不應包含的能力
- 能把前面學到的 `claw-code` 本質能力轉譯成可教學、可實作的 Python 範圍
- 能說明「做得更小」與「做得太薄」之間的差別

### 先備知識檢查

開始本章前，請確認你已經理解以下概念：

- [ ] 已讀完第 15 章，能區分 essential（本質必要）和 scale-induced（規模驅動）的能力
- [ ] 理解 agent harness 的四層架構：入口層、執行層、能力層、治理與驗證層
- [ ] 知道什麼是 message loop——模型回應 → 工具執行 → 再次送給模型的循環
- [ ] 能用自己的話解釋 tool dispatch、permission policy 和 session persistence 分別做什麼

## 核心概念講解

定義 `mini harness` 範圍時，最重要的原則不是功能數量，而是是否保留了 agent harness 的本質。從前面 Part II 的分析來看，最小可行版本至少要讓我們看見：模型不是直接裸跑，而是被放進一個有回圈、有工具、有權限、有狀態、有測試的工作系統。若這幾個本質不見了，就算程式跑得起來，也比較像聊天包裝器，而不是 harness。

> 💡 **生活化比喻**：這就像開一家最小的餐廳。你不需要米其林級的裝潢和二十道菜的菜單，但你至少需要：一個能做菜的廚房（runtime loop）、幾道招牌菜（tools）、基本的食安衛生規範（permissions）、一本記帳本（session persistence）、以及每天打烊前確認明天食材到位的流程（tests）。少了任何一個，你頂多算是在路邊擺攤，不算開餐廳。

基於這個原則，本書將 `mini harness` v1 定義為以下範圍：

### Included:
- message loop
- tool dispatch
- permission policy
- session persistence
- basic tests

這五項其實正對應前面一路建立起來的核心地圖。`message loop` 讓系統不是單次輸入輸出，而是真正有 assistant turn、tool result、再回圈的概念；`tool dispatch` 讓模型有手腳；`permission policy` 讓手腳不會無限制亂動；`session persistence` 讓狀態能跨回合延續；`basic tests` 則保證這些行為不只是「看起來可以」，而是可被驗證。

> 💡 **生活化比喻**：這五項就像人體的基本系統。**message loop** 是心臟（持續跳動、推動循環）；**tool dispatch** 是手腳（實際做事）；**permission policy** 是免疫系統（阻止有害動作）；**session persistence** 是記憶（記得之前做過什麼）；**basic tests** 是健康檢查（定期確認身體正常運作）。少了任何一個，人（系統）都無法正常生活（運作）。

接著，我們也要明確定義這一版不做什麼：

### Excluded for v1:
- full MCP support
- remote execution
- plugin lifecycle
- full parity harness

這四項被排除，不是因為它們不重要，而是因為它們都屬於較高階、較規模化、或較整合性的能力。`full MCP support` 與 `plugin lifecycle` 牽涉擴充協定與生命週期管理，適合在理解核心 loop 後再加；`remote execution` 代表另一層環境邊界問題，不應和本地最小系統綁在同一個起點；`full parity harness` 則是成熟驗證架構，不是教學版第一步的必要門檻。

> ⚠️ **初學者常見誤區**：很多初學者在看到 Excluded 清單時會焦慮：「少了這些，我的系統是不是不完整？」答案是：v1 本來就不追求完整，它追求的是**本質完整**。就像學開車，你不需要第一天就學會手排、賽道駕駛、雪地操控。先把自排車在一般道路上開好，基本功扎實了，進階技能隨時都能補上。

更精確地說，v1 的問題不是「能不能做很多」，而是「能不能把最關鍵的系統骨架做對」。如果 v1 能清楚展現 turn loop、tool call、permission denial、session roundtrip 與幾個代表性測試，那它就已經達成了本書的建構目標。

> ⚠️ **初學者常見誤區**：另一個常見錯誤是「既然簡單就好，那我用 20 行 Python 寫一個 while loop 加 API call 就算 harness 了吧？」——這就是「做得太薄」。真正的差別在於：harness 有**結構**。loop 不只是 while True，而是有明確的 turn 概念；工具不是寫死在 if/else 裡，而是透過 dispatch 機制管理；權限不是沒有，而是有一層 policy。20 行腳本可能「能跑」，但它不是 harness。

## 本章任務

本章的具體任務有四個：

1. 把 `mini harness` 的核心需求寫成明確 scope，而不是模糊願望清單
2. 為下一章的 Python 檔案分工預留清楚邊界
3. 為第 18 章的 session / testing 設定最低完成標準
4. 防止範圍膨脹，避免學生在第一版系統裡過早引入 MCP、remote、plugins 等高階能力

完成這一章後，你應該能回答三個非常實際的問題：第一，v1 一定要有哪些能力才配叫做 harness？第二，哪些能力明明重要，但現在故意不做？第三，下一章開始寫 Python 時，哪些檔案與模組責任已經可以先決定？

## 對照 `claw-code` 的設計差異

`claw-code` 是一個成熟、真實、面向較完整使用情境的 harness，因此它的責任範圍遠大於 `mini harness`。它有更完整的 CLI surface、有較多工具來源、有 permission policy 與 enforcer 的多層治理、有 session compaction、有 parity harness、有 remote 與 MCP 路徑，也有較多與觀測、追蹤、hook 相關的能力。這些能力對真實系統很有價值，但若一開始就全部搬進教學版，學生很可能還沒真正掌握核心 loop，就先被周邊複雜度淹沒。

因此，`mini harness` 的差異不是「比較差的 `claw-code`」，而是「刻意保留本質的教學版縮圖」。它不追求 feature parity，而追求 concept parity。也就是說，雖然能力範圍大幅縮小，但它仍然應該在架構上保留 `claw-code` 的幾個關鍵精神：模型透過 runtime 被協調、工具透過宣告與 dispatch 被管理、權限作為外部治理層存在、session 是可持久化狀態，而 testing 是必要條件。

> 💡 **生活化比喻**：`claw-code` 是一架波音 747（商用客機），`mini harness` 是一架塞斯納 172（小型教練機）。教練機不是「爛掉的 747」，而是刻意設計來學飛行的。它保留了飛行的本質——引擎、機翼、操縱桿、儀表板，但拿掉了 747 才需要的東西——三百個座位、商務艙、自動駕駛、跨洋油箱。你在教練機上學會的飛行原理，在 747 上同樣適用。

## 實作決策記錄

本章先記下幾個對後續實作會有直接影響的決策：

1. 實作語言選擇 `Python`
原因：教學與自學門檻較低，能把注意力放在系統概念，而不是 Rust 語法細節。

2. 先做本地單機版本，不做 remote execution
原因：先把最小本地回圈做穩，比同時處理跨環境邊界更有教學價值。

3. 先做少量工具，不追求完整工具表面
原因：tooling 的重點是 schema、dispatch、permission coupling，不是工具數量。

4. 先做基本 scenario / unit tests，不做 full parity harness
原因：保留 testing 哲學，但避免第一版就承擔完整 mock service 與大量場景維護成本。

這些決策不是臨時方便，而是刻意為「把本質學到手」服務。

## 本章小結

第 16 章的核心工作，是替 `mini harness` v1 畫出清楚邊界：要包含 message loop、tool dispatch、permission policy、session persistence、basic tests；暫不包含 full MCP support、remote execution、plugin lifecycle、full parity harness。這種範圍定義的目的，不是做得保守，而是讓教學版能保留 harness 的本質，同時維持可實作性與可完成性。

### 學習自我檢核

讀完本章後，請確認你能做到以下每一項：

- [ ] 我能列出 mini harness v1 的五項 included 能力，並解釋為什麼每一項都不能省
- [ ] 我能列出四項 excluded 能力，並解釋為什麼現在不做不等於不重要
- [ ] 我能區分「做得更小」（保留本質的精簡）和「做得太薄」（失去 harness 結構的簡化）
- [ ] 我理解 mini harness 追求的是 concept parity（概念對等）而非 feature parity（功能對等）
- [ ] 我能回答：v1 要有哪些能力才配叫 harness？哪些能力故意不做？下一章要做哪些模組？
- [ ] 我不會因為 v1 範圍小就覺得「不完整」——我知道這是有意識的教學設計

### 關鍵概念速查表

| 術語 | 說明 |
|------|------|
| **Mini Harness** | 本書設計的教學版 agent harness，保留核心本質但大幅縮減規模 |
| **Scope Contract** | 明確定義 v1 要做什麼、不做什麼的範圍約定，防止膨脹或過度簡化 |
| **Message Loop** | 模型回應 → 解析事件 → 工具執行 → 結果回傳 → 再次呼叫模型的循環機制 |
| **Tool Dispatch** | 根據模型的 tool use 請求，找到對應工具並執行的分派機制 |
| **Permission Policy** | 定義哪些工具操作被允許、哪些被拒絕的治理規則層 |
| **Session Persistence** | 將對話狀態、工具結果等寫入持久化儲存，讓工作可中斷、可恢復 |
| **Feature Parity** | 功能對等——兩個系統擁有相同的功能集合（mini harness 不追求這個） |
| **Concept Parity** | 概念對等——兩個系統在架構精神上一致，即使功能範圍不同（mini harness 追求這個） |
| **Included（v1 包含）** | message loop、tool dispatch、permission policy、session persistence、basic tests |
| **Excluded（v1 排除）** | full MCP support、remote execution、plugin lifecycle、full parity harness |

### 本章一句話總結

> **Mini harness v1 的設計哲學不是「做最少的功能」，而是「用最小的規模保留 harness 的完整本質」——有回圈、有工具、有權限、有狀態、有測試，五個缺一不可。**

## 章末練習
1. 解釋為什麼 `session persistence` 應被納入 v1，而 `remote execution` 不應該。
2. 如果把 `basic tests` 從 v1 移除，這個系統還算不算一個合格的教學版 harness？為什麼？
3. 請你重新設計一版 `mini harness` scope，並說明你和本章版本最大的差異。

## 反思問題

- 你在自己的專案裡，是否有過「第一版做太大」導致難以完成的經驗？如果有，和本章的範圍控制有什麼共通點？
- 你認為 `mini harness` 最容易失去本質的地方是什麼：loop、tools、permissions、session，還是 testing？
- 若只能再多加入一項現在被排除的能力，你最想加哪一項？為什麼？

## 延伸閱讀 / 下一章預告

有了清楚範圍後，下一章就可以真正動手。第 17 章會把這份 scope 轉成具體的 Python project skeleton，開始實作最小 runtime、tools 與 permissions，讓 `mini harness` 從概念藍圖走向可執行程式。
