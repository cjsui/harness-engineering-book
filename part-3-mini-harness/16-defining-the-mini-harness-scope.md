# 第 16 章：定義 Mini Harness 的最小範圍

## 章節導言

現在我們終於要從「看懂真實 harness」跨到「自己做一個縮小版 harness」。但在真正開始寫 Python 之前，有一件事比寫程式更重要：先把範圍定義對。很多教學專案失敗，不是因為學生不會寫，而是因為一開始沒有把最小可行範圍切清楚，結果不是一路膨脹成重做整個真實系統，就是反過來縮得太小，最後只剩一個包了 prompt 的小腳本，完全失去 harness 的本質。

因此，第 16 章的任務不是進入實作細節，而是做一個有意識的減法。我們要從前面學到的 `claw-code` 整體圖中，挑出最值得保留的核心，再明確列出這一版 `mini harness` 不做什麼。這種範圍切割不是偷懶，而是教學設計本身。因為本書的目標從來不是複製 `claw-code`，而是讓你在理解真實系統之後，能獨立做出一個「保留本質、但規模適中」的 agent harness。

這一章會先界定 v1 的 included 與 excluded 清單，再說明為什麼這樣的減法仍然保留了 Harness Engineering 的核心。接著，我們會把這些決策轉成下一章可以直接動手的任務說明。換句話說，這一章就是 Part III 的 scope contract。

## 學習目標
- 能清楚定義 `mini harness` v1 應包含與不應包含的能力
- 能把前面學到的 `claw-code` 本質能力轉譯成可教學、可實作的 Python 範圍
- 能說明「做得更小」與「做得太薄」之間的差別

## 核心概念講解

定義 `mini harness` 範圍時，最重要的原則不是功能數量，而是是否保留了 agent harness 的本質。從前面 Part II 的分析來看，最小可行版本至少要讓我們看見：模型不是直接裸跑，而是被放進一個有回圈、有工具、有權限、有狀態、有測試的工作系統。若這幾個本質不見了，就算程式跑得起來，也比較像聊天包裝器，而不是 harness。

基於這個原則，本書將 `mini harness` v1 定義為以下範圍：

### Included:
- message loop
- tool dispatch
- permission policy
- session persistence
- basic tests

這五項其實正對應前面一路建立起來的核心地圖。`message loop` 讓系統不是單次輸入輸出，而是真正有 assistant turn、tool result、再回圈的概念；`tool dispatch` 讓模型有手腳；`permission policy` 讓手腳不會無限制亂動；`session persistence` 讓狀態能跨回合延續；`basic tests` 則保證這些行為不只是「看起來可以」，而是可被驗證。

接著，我們也要明確定義這一版不做什麼：

### Excluded for v1:
- full MCP support
- remote execution
- plugin lifecycle
- full parity harness

這四項被排除，不是因為它們不重要，而是因為它們都屬於較高階、較規模化、或較整合性的能力。`full MCP support` 與 `plugin lifecycle` 牽涉擴充協定與生命週期管理，適合在理解核心 loop 後再加；`remote execution` 代表另一層環境邊界問題，不應和本地最小系統綁在同一個起點；`full parity harness` 則是成熟驗證架構，不是教學版第一步的必要門檻。

更精確地說，v1 的問題不是「能不能做很多」，而是「能不能把最關鍵的系統骨架做對」。如果 v1 能清楚展現 turn loop、tool call、permission denial、session roundtrip 與幾個代表性測試，那它就已經達成了本書的建構目標。

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
