# 第 18 章：加入 Session Persistence 與基本測試

## 章節導言

如果第 17 章讓 `mini harness` 長出了最小的骨架，那麼第 18 章要讓它真正成為「可持續工作的系統」。一個只有 runtime、tools、permissions 的第一版程式，雖然已經比聊天腳本更接近 harness，但如果它無法保存狀態、無法 resume、也沒有最低測試，整體仍然非常脆弱。你很難長對話工作，也很難知道之後修改時是不是把系統默默改壞了。

因此，本章處理的是兩個最能提升系統穩定度、卻又不需要過度膨脹範圍的能力：`session persistence` 與 `basic testing`。前者讓多輪互動不再每次都從零開始；後者讓 runtime、permissions、session 這幾個核心責任至少有最小而有代表性的驗證方式。這兩者一加進來，`mini harness` 就會從一個概念原型，變成一個真正可迭代的教學系統。

和 `claw-code` 相比，我們在這裡依然採取有意識的簡化。重點不是複製完整 session rotation、compaction metadata、usage accounting 或 full parity harness，而是學會：在縮小版系統裡，哪些 session 與 testing 能力最值得先做，才能最大化學習價值與系統穩定度。

> **📋 本章速覽**
>
> 讀完本章，你將會：
> - 選定 `jsonl` 作為 session 持久化格式，並理解為什麼這是好選擇
> - 實作一個最小的 resume flow（啟動時讀檔 → 重建記憶 → 持續追加）
> - 設計三類最重要的測試案例：runtime turn、permission denial、session roundtrip
> - 理解「狀態持久化」和「自動測試」為什麼是 harness 的核心能力，不是附加功能
> - 把你的 mini harness 從「能跑一次」升級成「能反覆修改、反覆驗證」

## 學習目標
- 能為 `mini harness` 選擇合理的 session 檔案格式並設計最小 resume flow
- 能定義三類最小但有代表性的測試案例
- 能說明為什麼 session persistence 與 testing 應被視為核心功能，而非事後補件

> **🔍 先備知識檢查**
>
> 開始本章之前，請確認你已經：
> - [ ] 完成第 17 章的專案骨架建立（`runtime.py`、`tools.py`、`permissions.py` 都已存在）
> - [ ] 理解 JSON 和 JSONL 的差異（JSONL = 每行一個獨立 JSON 物件）
> - [ ] 知道什麼是 message role（user、assistant、tool_result 等）
> - [ ] 讀過第 9 章關於 session 的概念，知道 session 不只是「聊天記錄」
> - [ ] 有基本的 Python 單元測試概念（知道 `pytest` 或 `unittest` 是什麼）
>
> 如果 JSONL 格式不太熟悉，可以先想像一個 `.txt` 檔案，每一行都是一筆完整的 JSON 資料。

## 核心概念講解

### Session 檔案格式：為什麼選 JSONL

本章先做一個非常務實的決策：`mini harness` 的 session file format 採用 `jsonl`。選擇它的原因不是因為它最炫，而是因為它很適合教學版系統。每一行可以代表一筆 message record，追加寫入容易、閱讀與除錯也直觀，未來若要加入 compaction 或 metadata，也比單一巨大 JSON 物件更容易漸進擴充。更重要的是，這個選擇和 `claw-code` 的 session persistence 脈絡是相通的，因此學生能把教學版與真實系統做有意義對照。

> 💡 **生活化比喻**：把 JSONL 想像成一本**活頁筆記本**。每一頁（每一行）都是一筆完整的記錄，你可以隨時在最後面加新頁，也可以打開任何一頁單獨看。相比之下，單一 JSON 物件就像把所有筆記寫在同一張大紙上——改一個地方就得重寫整張紙，非常不方便。

### 最小 Session Record

一個最小 session record 至少應該保留幾件事：message role、content、必要時的 tool result 資訊、以及可辨識當前 session 的 metadata。教學版不一定要從一開始就保存所有 usage breakdown 或 compaction 狀態，但至少要能做到兩件事：把新訊息 append 到 session 檔中，以及在啟動時把既有 session replay 回記憶體。只要這兩件事成立，resume flow 就有了最小可用版本。

> ⚠️ **初學者常見誤區**：很多人在設計 session 格式時，會想一步到位，把所有可能用到的欄位（token 計數、時間戳記、模型版本、壓縮狀態...）全部加進去。結果第一版還沒跑起來，格式就已經複雜到難以除錯。**先只保留 role 和 content，等系統真正需要時再擴充。**

### Minimal Resume Flow

`minimal resume flow` 可以設計得很簡單。例如：

1. 啟動時檢查是否提供 `session_path`
2. 若存在，從 `jsonl` 檔 replay message records，重建 in-memory session
3. 若不存在，建立新 session
4. 每次 user / assistant / tool result 新增後，立即 append 一筆新 record

這種流程的教學價值很高，因為它把「session 是一個真正的狀態容器」這件事具體化了。學生會很清楚看到：resume 並不是 magical feature，而是因為系統一直有在持久化自己。

> 💡 **生活化比喻**：Resume flow 就像你玩遊戲時的**自動存檔**功能。每完成一個動作，遊戲就自動存一次進度（append）。下次打開遊戲時，它會讀取存檔把你送回上次的位置（replay）。如果沒有存檔機制，每次開遊戲都得從第一關重來——這就是沒有 session persistence 的 harness 的處境。

### 三類基本測試

接著是 testing。本章要求至少涵蓋三類測試：

- runtime turn
- permission denial
- session persistence roundtrip

**`runtime turn` 測試**要回答的問題是：一個最小 assistant turn 是否真的能完成模型回應、工具呼叫、工具結果回寫、以及最終收斂？它對應的是第 6 章的核心 loop。教學版不需要模擬所有 `AssistantEvent` 類型，但至少應該有一個 scripted model stub，讓 runtime 能完成一輪「要求工具 -> 收到結果 -> 輸出最終回答」的往返。

> 💡 **生活化比喻**：Runtime turn 測試就像在餐廳開幕前做的**試營運**。你找一組假客人（stub），走完點餐、做菜、上菜、結帳的完整流程，確認每一步都能順利銜接。

**`permission denial` 測試**則對應第 8 章。它應該檢查：當某個工具需求高於當前 `PermissionMode` 時，系統是否真的拒絕執行，而不是只是理論上有這個 policy。這類測試很重要，因為它直接驗證「治理層真的有參與流程」，而不是停留在設定檔或文件上。

> 💡 **生活化比喻**：Permission denial 測試就像測試大樓門禁是否**真的鎖著**。你不能只檢查門上有沒有鎖，你得實際用一張權限不夠的卡去刷，確認門確實打不開。

**`session persistence roundtrip` 測試**則對應第 9 章即將補寫的 session 主題，也和本章的核心功能直接相關。它要回答的是：一個 session 寫出後，是否能被正確讀回，且至少保留 message 順序、role、基本內容與必要 metadata。只要這個 roundtrip 不穩，resume flow 就沒有可信基礎。

> 💡 **生活化比喻**：Session roundtrip 測試就像你寫一封信寄出去，再請收件人把信寄回來，然後檢查**內容有沒有在路上被改掉或弄丟**。如果寄出去的和收回來的不一樣，整個通信系統就不可靠。

> ⚠️ **初學者常見誤區**：有些人會寫很多「看起來有測」但其實沒有測到重點的測試，例如只檢查「session 檔案存在」但不檢查「讀回來的內容是否正確」，或者只檢查「runtime 不報錯」但不檢查「工具結果是否真的被送回下一輪」。**好的測試要驗證行為，不只是驗證不出錯。**

從測試哲學看，這三類案例的價值不在於數量，而在於剛好分別覆蓋了 `執行`、`治理`、`狀態` 三個最核心面向。這比寫很多零散、只檢查 getter/setter 的測試更接近 harness engineering 的需求。

## 本章任務

本章的具體任務可以整理成四步：

1. 為 `mini harness` 選定 `jsonl` 作為 session 檔案格式
2. 在 runtime 或 session helper 中加入最小 `resume` 流程
3. 實作三類基本測試：runtime turn、permission denial、session persistence roundtrip
4. 確保測試名稱與檔案分工反映前一章 project skeleton，而不是把所有驗證塞進單一測試檔

執行順序上，建議先做 session roundtrip，再做 runtime turn，最後做 permission denial。原因是 session persistence 一旦穩定，runtime 測試與後續 debug 都更容易追蹤；而 permission denial 則依賴前面已有清楚的 mode / policy 介面。

## 對照 `claw-code` 的設計差異

`claw-code` 的 session 系統比教學版成熟得多。從 `session.rs` 可以看到它支援 JSON 與 JSONL 載入、append 寫入、rotation、compaction metadata、fork provenance、usage metadata 等能力。教學版顯然不需要一次做到這麼完整。對 `mini harness` 而言，真正值得先保留的是：`Session` 作為持久化狀態容器、append-friendly 格式、以及最小 resume 能力。

測試面也是同樣邏輯。`claw-code` 透過 mock parity harness 驗證 streaming、tool roundtrip、permission branching、plugin path、auto compaction、token cost reporting 等多種 scenario；教學版則只需要抓住能代表本質的三類案例。這不是降低標準，而是把 testing 的哲學先留住，再把規模控制在可教、可做、可完成的範圍。

## 實作決策記錄

本章先把幾個 persistence / testing 決策明確記錄下來：

1. session 格式選擇 `jsonl`
原因：append 寫入直觀、除錯友善、也較容易和真實 harness 的 session 心智模型對齊。

2. resume flow 採「讀檔 replay」而非複雜 checkpoint
原因：教學版先聚焦可理解性與可驗證性，不先引入過多狀態同步機制。

3. 測試先覆蓋三類核心行為，不追求大量案例
原因：高價值 scenario 比大量低價值測試更符合 harness engineering 的需求。

4. 測試允許使用簡化 stub / fake model client
原因：重點是驗證 runtime 行為與邊界，不是接上真實模型供應者。

## 本章小結

第 18 章替 `mini harness` 補上了最關鍵的穩定度能力：以 `jsonl` 持久化 session、透過最小 resume flow 重建上下文、並用 runtime turn、permission denial、session persistence roundtrip 三類測試覆蓋執行、治理與狀態三個核心面向。到這一步，教學版系統才真正從概念骨架變成一個可反覆修改、可驗證、可持續工作的 harness。

> **✅ 學習自我檢核**
>
> 讀完本章後，請確認你能做到以下每一項：
> - [ ] 我能解釋 JSONL 和單一 JSON 物件作為 session 格式的優劣差異
> - [ ] 我能畫出 minimal resume flow 的四個步驟
> - [ ] 我能說出三類基本測試各自在驗證什麼核心面向
> - [ ] 我理解為什麼 session roundtrip 測試建議最先做
> - [ ] 我知道 scripted model stub 是什麼，以及為什麼測試不需要接真實模型
> - [ ] 我能解釋「好的測試驗證行為，不只驗證不出錯」這句話的意思

## 關鍵概念速查表

| 術語 | 說明 | 所屬面向 |
|---|---|---|
| JSONL | 每行一個 JSON 物件的文字格式，適合追加寫入 | 狀態持久化 |
| Session Record | 一筆包含 role、content 的對話記錄 | 狀態持久化 |
| Resume Flow | 啟動時從檔案重建 session 的流程 | 狀態持久化 |
| Append 寫入 | 只在檔案末尾新增，不改動已有內容 | 狀態持久化 |
| Runtime Turn 測試 | 驗證一輪完整「模型回應 → 工具呼叫 → 結果回寫」是否正常 | 執行驗證 |
| Permission Denial 測試 | 驗證權限不足時工具是否被正確拒絕 | 治理驗證 |
| Session Roundtrip 測試 | 驗證 session 寫出後能被正確讀回 | 狀態驗證 |
| Scripted Model Stub | 回傳固定腳本的假模型，用於測試 runtime 行為 | 測試工具 |
| Scenario-based Testing | 以完整使用情境（而非零碎函式）為單位的測試策略 | 測試哲學 |

## 章末練習
1. 說明為什麼本章選擇 `jsonl` 而不是單一 JSON 物件作為第一版 session 格式。
2. 為 `runtime turn` 測試設計一個最小 scripted model stub，描述它應回傳哪些步驟。
3. 如果你只能保留一個測試類別，你會保留 `runtime turn`、`permission denial`、還是 `session persistence roundtrip`？為什麼？

## 反思問題

- 你覺得很多初學者為什麼會低估 session persistence 的價值？
- 如果系統只有 session persistence、沒有測試，和只有測試、沒有 persistence，各自會在什麼地方變得脆弱？
- 當教學版 `mini harness` 將來想升級時，你會先擴充更多 session 能力，還是先擴充更多 parity-style 測試？理由是什麼？

> **📝 本章一句話總結**
>
> Session persistence 讓系統有記憶，basic testing 讓系統有信心——兩者加起來，才能把教學骨架變成真正可迭代的 harness。

## 延伸閱讀 / 下一章預告

完成第 18 章後，Part III 的核心建構就已經成形。接下來若回看 `claw-code`，你會更清楚哪些能力是教學版已經掌握的本質，哪些則是成熟系統因規模而長出的複雜度。這也會為最後的整合章鋪路，讓你能真正回答：從 `mini harness` 回看真實 harness，我們到底學到了什麼。
