# 第 19 章：從 Mini Harness 回看真實 Harness

## 章節導言

到第 18 章為止，你已經不是只會「看懂別人的 agent 系統」而已，你也真的做出了一個可工作的 `mini harness`。這一步非常重要，因為它會徹底改變你再回頭看 `claw-code` 的方式。前面在 Part II 讀 `claw-code` 時，你很可能一邊佩服、一邊覺得系統很大；但現在你已經親手處理過 runtime loop、tool dispatch、permission gating、session persistence 與 basic tests，再回看真實 harness 時，你會開始有能力分辨：哪些複雜度是本質，哪些複雜度是規模化之後才不得不長出來的。

因此，本章不是要你把 `mini harness` 當成最終答案，也不是要你把 `claw-code` 當成不可企及的巨大系統。本章真正的任務，是把兩者接起來，建立一種成熟的比較視角。你要學會用自己做過的縮小版系統，反過來理解真實 harness 的設計取捨；同時也要能為自己的下一步升級路線做出判斷。

換句話說，第 19 章是全書的整合章。它要回答的問題不是「我們還能再加什麼功能」，而是「在真的做過之後，我們到底學到了什麼」，以及「如果要從教學版走向更真實的 harness，應該先長出哪些能力，為什麼」。

> **📋 本章速覽**
>
> 讀完本章，你將會：
> - 用「已掌握 / 需補強 / 規模化」三類框架重新分類所有 harness 能力
> - 理解 `mini harness` 和 `claw-code` 之間的差異不是功能多寡，而是成熟度
> - 學會判斷下一步該優先補什麼，而不是盲目加功能
> - 建立一種「回看能力」——用自己的實作經驗解讀大型系統的設計決策
> - 擬定屬於你自己的 v2 升級路線圖

## 學習目標
- 能用 `mini harness` 的實作經驗重新解讀 `claw-code` 的複雜度來源
- 能區分 local teaching harness 與規模化 real harness 之間的能力落差
- 能替自己的下一版 harness 擬定有順序的升級路線，而不是無限制加功能

> **🔍 先備知識檢查**
>
> 開始本章之前，請確認你已經：
> - [ ] 完成第 17 章（建立了 mini harness 的專案骨架）
> - [ ] 完成第 18 章（加入了 session persistence 和三類基本測試）
> - [ ] 對 Part II（第 6-15 章）有整體印象，至少知道每章在講什麼
> - [ ] 能說出 `claw-code` 至少有哪五個主要的責任層
> - [ ] 心裡已經有「我的 mini harness 還缺什麼」的初步想法
>
> 本章是整合章，需要你對全書有一定程度的整體理解。如果前面的章節還很模糊，建議先快速回顧。

## 核心概念講解

### 建立「回看能力」

完成 `mini harness` 之後，最值得建立的新能力，是一種「回看能力」。很多學習者在做完教學版系統後，會掉進兩個相反的誤區。第一個誤區是過度自滿，覺得自己已經做出一個 harness，因此真實系統只是不必要地把東西做複雜。第二個誤區則是過度挫折，覺得自己做出來的只是玩具，和 `claw-code` 之間還有不可跨越的鴻溝。這兩種看法都不夠成熟。

> 💡 **生活化比喻**：就像你學開車一樣。在駕訓班的練習場（mini harness）上學會了基本操控、轉彎、停車。這時候你不會說「F1 賽車（claw-code）不過是把車開快一點」（過度自滿），也不會說「我只會在練習場開，上路根本不可能」（過度挫折）。正確的態度是：你已經掌握了駕駛的本質，接下來要根據實際路況一步步升級能力。

> ⚠️ **初學者常見誤區**：最危險的心態是「我的 mini harness 能跑了，接下來直接加 MCP 和 multi-agent 吧！」這就像剛拿到駕照就要去跑山路——你跳過了太多中間步驟。正確的做法是先把基礎做穩，再逐步擴展。

### 三類能力框架

比較好的框架是把 `mini harness` 視為一個 `concept lens`。它不是 `claw-code` 的縮小 copy，也不是純 demo。它的價值在於讓你把真實系統拆成三種類型的能力：

1. `已掌握的本質能力`
2. `需要補強的本地能力`
3. `屬於規模化與產品化的能力`

**第一類：已掌握的本質能力**

通常包括：

- runtime loop
- tool dispatch
- permission gating
- session persistence
- basic testing

這些能力之所以重要，是因為只要拿掉其中幾項，系統就很容易退化成一個包裝模型 API 的腳本，而不是一個真正的 harness。你在 Part III 做的事，就是把這些骨架真正裝到手上。

> 💡 **生活化比喻**：這五項本質能力就像蓋房子的**地基、承重牆、屋頂、門窗、電力系統**。少了任何一個，房子都不能住人。你在 Part III 完成的，就是把一棟最小但能住人的房子蓋出來了。

**第二類：需要補強的本地能力**

這類能力還沒有完全跳到 `remote`、`MCP`、`plugins` 或 deployment 等高階場景，但一旦你想讓 `mini harness` 更穩、更可用，就很容易遇到它們。例如：

- 較清楚的 CLI entry 與 mode routing
- 更完整的 prompt assembly
- config hierarchy 與 settings override
- 更細緻的 transcript 結構
- 更有代表性的 scenario tests 與 evaluation

這些能力比 Part III 更進一步，但仍然可以在單機、本地、教學可控的範圍內成長。它們通常是最值得優先做的 `v2 local upgrades`。

> 💡 **生活化比喻**：這就像你的房子已經能住了，但還可以加上**更好的門鎖、窗簾、收納系統、對講機**。這些升級不需要整棟重蓋，但會讓住起來舒服很多。

**第三類：屬於規模化與產品化的能力**

當你從單一學習者工具，走向多種環境、多種工具來源、較長生命週期與較高可靠性需求時，才會真的碰到它們。例如：

- `MCP` 與外部能力橋接
- plugin lifecycle 與 extension boundary
- remote execution 與多執行環境治理
- hooks、telemetry、usage accounting
- 更完整的 regression coverage、cost tracking、deployment concerns

這些能力不是多餘裝飾，而是規模化系統的真問題。但它們的重要性，來自使用情境與運維現實，而不是來自「harness 這個概念本身」。

> 💡 **生活化比喻**：這就像從一棟住家升級成**公寓大樓**——需要電梯、消防系統、物業管理、停車場。這些不是因為「蓋房子的概念變了」，而是因為**規模變了、住的人多了、需要管理的東西多了**。

### 升級順序的重要性

如果把這三類能力轉成升級順序，一條很合理的路線通常會是：

1. `先把本地 teaching harness 做穩`
2. `再補 local reliability 與 operator usability`
3. `最後才處理擴充邊界與跨環境邊界`

這個順序非常重要。很多人一做完教學版，就急著加 `MCP`、remote 或 multi-agent orchestration，結果反而把原本已經理解的核心 loop 攪亂。更穩健的做法，是先補那些能直接提升可理解性與可驗證性的能力，例如更好的 CLI、config、prompt assembly、scenario tests 與 evaluation 策略。因為這些能力會讓你後續面對規模化問題時，仍然看得見系統的骨架。

### 如何成熟地回看 `claw-code`

另一個值得建立的觀念是：`claw-code` 並不是「mini harness 加很多功能」而已。真正的差異不只是功能數量，而是多條責任鏈的成熟度同時提高了。它的 system surface 更完整、governance 更細緻、session 更成熟、extension boundary 更清楚、verification 也更有系統。這表示從 `mini harness` 走向真實 harness，不是做一個大規模功能加法，而是同時升級多個系統面向。

所以，回看 `claw-code` 時，最成熟的問題不再是「它有什麼我沒有」，而是：

- 它多出來的每一層複雜度，是為了解哪一種真實問題？
- 這個問題在我的系統裡是否已經出現？
- 如果還沒出現，我現在是不是其實不該先做？

當你能這樣問，代表你已經開始具備 Harness Engineering 的設計判斷，而不只是閱讀能力。

## 本章任務

本章的整合任務有四步：

1. 用 `已掌握 / 需補強 / 規模化` 三類框架，重新盤點你的 `mini harness`
2. 對照 `claw-code`，寫出三項你最想優先補的 `v2 local upgrades`
3. 為其中一項升級寫一段簡短設計說明，說明它要解決什麼真實痛點
4. 刻意列出三項你現在暫時不做的能力，並說明為什麼它們屬於後期議題

若你是自學者，本章最有價值的產出，通常不是新程式碼，而是一份 `upgrade roadmap`。這份 roadmap 應該能回答：你的下一版要先補 CLI、config、prompt assembly、testing，還是 transcript / evaluation？順序為何？每一步預計降低哪一種風險？

若你是授課者，則可以把本章任務設計成總結型作業：要求學生提交一份比較報告，說明自己的 `mini harness` 與 `claw-code` 的差異，並提出一條合理的 v2 演化路線。

## 對照 `claw-code` 的設計差異

最容易誤解的一點，是把 `claw-code` 和 `mini harness` 的差異理解成「前者功能比較多」。其實更準確的說法是：`claw-code` 的多數能力都不是孤立存在，而是彼此互相支撐。舉例來說，較豐富的 CLI surface 會影響 session 操作與 modes；較成熟的 prompt assembly 會影響 project context 與 config；`MCP` 和 plugin path 會影響 tool registry 與 permission evaluation；remote execution 又會改寫整個執行環境邊界。這種互相牽動，正是規模化 harness 和教學版 harness 最大的差異。

也因此，`mini harness` 的設計差異應該被理解為一種刻意壓縮。它保留的是 `architectural parity`，不是 `feature parity`。你已經實作到的，是 harness 最核心的幾條骨架；而 `claw-code` 額外擁有的，則是讓這些骨架能在更真實、更長期、更高風險的情境下工作所需要的成熟層。

這個差異並不意味著 `mini harness` 不夠真實，而是說它的真實性來自「讓你親手做出本質」，`claw-code` 的真實性則來自「讓這些本質在規模化世界裡仍然成立」。兩者合起來，才構成這門課真正想教的 Harness Engineering 全貌。

## 實作決策記錄

本章不新增大量功能，但會替後續升級留下一組決策原則：

1. `v1` 的成功標準是 concept parity，不是 feature parity
原因：本書的核心目標是讓學習者掌握 harness 的骨架，而不是重做整個 `claw-code`。

2. `v2` 優先補 local reliability，不先追規模化功能
原因：CLI、config、prompt assembly、testing 與 evaluation 會先提升可理解性與可驗證性。

3. 每加一項能力，都要先說清楚它解的是哪種真實問題
原因：避免為了模仿大型系統而盲目加功能，導致結構重新失焦。

4. 規模化能力必須和治理、測試、觀測一起成長
原因：`MCP`、remote、deployment 或多代理協作若沒有對應 guardrails 與 verification，只會放大風險。

## 本章小結

第 19 章的重點，不是再替 `mini harness` 疊更多功能，而是建立一種成熟的回看能力。現在你應該能用 `已掌握的本質能力`、`需要補強的本地能力`、以及 `屬於規模化與產品化的能力` 三類框架，重新理解 `claw-code` 與自己做出的系統差異。這種判斷力，才是從教材走向真實設計工作的真正門檻。

> **✅ 學習自我檢核**
>
> 讀完本章後，請確認你能做到以下每一項：
> - [ ] 我能用三類框架（已掌握 / 需補強 / 規模化）分類任何一個 harness 能力
> - [ ] 我能說出至少三個「已掌握的本質能力」和三個「需要補強的本地能力」
> - [ ] 我能解釋為什麼「先補 local reliability」比「直接加 MCP」更好
> - [ ] 我能說出 `claw-code` 和 `mini harness` 的差異不只是功能數量，而是成熟度
> - [ ] 我能為自己的 mini harness 擬定一條有順序的 v2 升級路線
> - [ ] 回看 `claw-code` 時，我能問出「這層複雜度在解什麼真實問題」

## 關鍵概念速查表

| 術語 | 說明 | 出處 |
|---|---|---|
| Concept Lens | 把 mini harness 當作理解真實系統的「透鏡」，而非縮小複製品 | 本章核心概念 |
| Architectural Parity | 保留架構精神但不追求完整功能 | 第 17-19 章 |
| Feature Parity | 完整複製所有功能（本書刻意不追求） | 對照概念 |
| 已掌握的本質能力 | runtime loop、tool dispatch、permission gating、session、testing | 三類框架 |
| 需要補強的本地能力 | CLI、config、prompt assembly、scenario tests | 三類框架 |
| 規模化能力 | MCP、remote、plugins、telemetry、deployment | 三類框架 |
| v2 Local Upgrades | 不需跳到規模化就能提升系統穩定度的下一步改進 | 升級路線 |
| Upgrade Roadmap | 有順序、有理由的系統升級計畫 | 本章產出 |
| 回看能力 | 用自己的實作經驗重新解讀大型系統設計決策的能力 | 本章核心 |

## 章末練習
1. 請把你的 `mini harness` 現況分成 `已掌握 / 需補強 / 規模化` 三類，每類至少列三項。
2. 在 CLI、config、prompt assembly、evaluation、scenario testing 中，選兩項作為 `v2` 優先升級，並說明排序理由。
3. 說明為什麼 `MCP`、remote execution 或 deployment 不一定適合成為教學版下一步的第一優先。

## 反思問題

- 你過去是否有過「一看到大型系統就想全部複製」的衝動？這種衝動對學習與設計有什麼風險？
- 如果你真的要把 `mini harness` 變成日常可用工具，你最先感受到的痛點會是什麼：入口、設定、上下文、工具治理、還是測試？
- 當一個系統開始規模化時，你覺得最容易被低估的是哪一層：permissions、session、evaluation、還是環境邊界？

> **📝 本章一句話總結**
>
> Harness Engineering 的真正門檻不是「能做出多少功能」，而是「能判斷下一步該先做什麼、為什麼」。

## 延伸閱讀 / 下一章預告

本書主體到這裡完成，但學習其實才剛進入第二階段。接下來建議你使用附錄作為行動指南：附錄 A 幫你建立 `claw-code` 的重點閱讀地圖，附錄 B 幫你把 `mini harness` 變成可交付的專題作品，附錄 D 則整理 `MCP`、multi-agent、UI、deployment、evaluation 等後續延伸方向。
