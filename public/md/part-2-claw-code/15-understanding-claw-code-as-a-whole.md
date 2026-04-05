# 第 15 章：把 `claw-code` 當成一個完整系統來理解

## 章節導言

前面的 Part II 其實做了一件有點反直覺的事：我們把一個真實 harness 拆得很開。你先看 runtime，再看 tool system，再看 permissions，再看 parity harness。這種拆法有助於學習，但也有一個風險，就是讀到後面時，腦中只剩下一堆局部模組，卻忘了它們原本是如何一起運作的。因此，第 15 章的任務不是再引入新名詞，而是把前面那些被拆開的元件重新接回整體流程。

真正成熟的系統理解，不只是知道有哪些 crate、有哪些型別、有哪些 policy，而是能用一條連續敘事說明：使用者如何從 CLI 進入系統、模型呼叫如何被組裝、工具如何被管理與執行、session 如何被持久化、permissions 如何在過程中持續發揮作用、以及 testing 為何能對這整條鏈做 end-to-end 驗證。只有當你能把這條敘事完整說出來，你才算真的看懂 `claw-code`。

這一章同時也是 Part II 的收束點。它要替你做兩件事：第一，把 `claw-code` 從「很多能力」重新還原成「一個整體系統」；第二，幫你分辨哪些東西屬於 harness 的本質，哪些是因為系統要支撐更真實、更大規模、更高可靠性而逐漸長出的能力。這個 distinction 會直接決定你在 Part III 要如何縮小系統、做出自己的 `mini harness`。

## 學習目標
- 能用 end-to-end 流程說明 `claw-code` 的整體運作
- 能解釋各 crate 與核心元件如何共同構成一個 agent harness
- 能區分 `claw-code` 中哪些能力屬於本質必要、哪些屬於規模化擴充

## 核心概念講解

把 `claw-code` 當成整體系統來看時，最有效的方法不是再按檔案順序走一遍，而是沿著一次真實使用流程來走。從 Rust README 提供的 crate responsibilities 出發，我們可以把整個系統濃縮成一條主流程。

第一步是 `CLI entry`。使用者透過 `rusty-claude-cli` 這個主二進位檔進入系統，可能是 interactive REPL，也可能是 one-shot prompt，也可能是 `--resume`、`status`、`system-prompt` 等模式。這一層的責任不是推理，而是把人的操作入口、旗標、slash commands、顯示格式與 session 互動方式整理成可啟動的工作表面。也就是說，它是 system surface。

第二步是 `request assembly`。CLI 收到任務後，真正進入 runtime 層。`runtime` crate 在 `lib.rs` 頂端就直白說明，它擁有 session persistence、permission evaluation、prompt assembly 等核心責任。這表示一旦進入執行核心，系統就不再只是把 prompt 往外送，而是會先決定：目前 session 狀態是什麼、system prompt 如何組裝、有哪些 project context、哪些 permission mode 生效、哪些工具被允許暴露給模型。

第三步是 `model call`。這時 `ConversationRuntime` 會把 system prompt 與 conversation messages 組成 `ApiRequest`，交給 `ApiClient`。這裡很重要的一點是：模型邊界被明確包成一個抽象接口，所以整個系統不是直接依賴某家 API，而是依賴「能回傳 `AssistantEvent` 流」的能力。這使得 runtime 真正掌控的是控制流程，而不是把控制權交給模型供應者。

第四步是 `event interpretation and tool execution`。模型回傳的不是單一答案，而是一串事件流。runtime 會從中辨識文字增量、usage、tool use、message stop 等訊號。如果 assistant message 內有 pending tool use，系統就不會把這視為整輪結束，而是透過 tool executor 與 tool registry 進入下一段資料流。這裡 `tools` crate 的角色就非常關鍵：它決定模型看得到哪些工具、這些工具的 schema 與 permission requirement 為何、使用者經由 `allowedTools` 限制後真正暴露出去的是哪個能力切片。

第五步是 `governance and boundaries`。工具不是拿到就執行。每一次工具呼叫，都可能經過 permission policy 的判斷，必要時再透過 enforcer 落到檔案寫入邊界、bash 判斷、或 approval flow。也就是說，能力鏈與治理鏈是同時運作的。runtime 不只是調度模型和工具，也負責把能力放在 guardrails 內。

第六步是 `state persistence`。每輪 assistant message、tool result、usage、可能的 compaction 都會回寫到 `Session`。這讓系統不只是「做完一輪就消失」，而是能被 resume、能保留 transcript、能在長對話中管理累積上下文。從系統角度看，session 並不是附屬 storage，而是把多輪 agent work 變成可持續流程的必要結構。

第七步是 `verification and feedback`。當這整條鏈完成後，系統還需要確保自己沒有悄悄退化。這就是 mock parity harness 的位置。它不是在某個孤立角落測單一函式，而是沿著 CLI entry、model interaction、tool use、permission branching、session behavior、usage output 這整條 end-to-end 路徑進行驗證。這也讓 `claw-code` 從「一個很多功能的 agent 工具」提升為「一個有自我驗證能力的 harness」。

如果把這整張圖再壓縮一點，你可以把 `claw-code` 想成四層：

1. `入口層`：CLI、slash commands、resume、status、輸出格式
2. `執行層`：`ConversationRuntime`、prompt assembly、session、usage
3. `能力層`：tool specs、registry、runtime tools、plugin tools
4. `治理與驗證層`：permissions、enforcer、mock parity harness、telemetry

這四層並不是彼此分離，而是沿著一次工作流相互穿透。使用者從入口層進來，執行層驅動模型回圈，能力層提供手腳，治理與驗證層確保這一切可控且可回歸。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/rust/README.md`
- `claw-code/rust/crates/runtime/src/lib.rs`
- `claw-code/rust/crates/tools/src/lib.rs`

### 閱讀順序
1. 先讀 `rust/README.md` 的 workspace layout 與 crate responsibilities
2. 再讀 `runtime/src/lib.rs`，看 runtime 真正收斂了哪些責任
3. 最後讀 `tools/src/lib.rs`，確認能力層如何被宣告與輸出

### 閱讀重點
- `rusty-claude-cli`、`runtime`、`tools`、`api`、`telemetry` 各自負責什麼
- `runtime` 為何同時重新匯出 conversation、permissions、prompt、session、remote、usage 等模組
- `tools` 如何把 built-in、runtime、plugin 能力統一成模型可見工具表面

## 設計取捨分析

把 `claw-code` 當成整體來看時，一個最重要的分析框架是：`什麼是 essential，什麼是 scale-induced`。所謂 essential，是指就算你要做一個教學版或最小版系統，也幾乎不能拿掉的東西，例如：模型邊界、runtime loop、tool dispatch、permission gating、session persistence、基本測試。這些能力一旦拿掉，系統會從 harness 退化成比較脆弱的聊天包裝器。

而 scale-induced 能力，則是那些因為真實使用情境、可靠性要求與擴充需求而長出的部分，例如：hooks、session tracer、prompt cache telemetry、完整 plugin 路徑、remote execution、MCP lifecycle、豐富的 CLI surface、較完整的 parity scenario 組合。這些能力不是不重要，而是它們的重要性來自系統規模與成熟度，而不是作為 harness 的最小本質。

這個區分很關鍵，因為如果你看不出兩者差異，就會在學習時被規模嚇到，或在重建時不是做得過大，就是削得過頭。`claw-code` 真正教你的，不只是「真實系統很複雜」，而是「要能在複雜度裡辨認本質」。

## Mini Harness 連結點

這一章最直接的任務，就是替 Part III 做減法。現在你應該可以回答：如果不追求完整複製 `claw-code`，我最少要帶走什麼？答案會很接近這樣一張縮圖：一個 CLI 或簡單入口、一個最小 runtime loop、一組明確的工具、一層最小 permission policy、一個可 resume 的 session 檔，以及幾個能覆蓋核心行為的測試。這些就是 `mini harness` 的骨架。

也因此，第 16 章不會問「如何重做整個 `claw-code`」，而會問「在理解整個真實系統之後，哪個縮小版本最有教學價值、也最能保留本質」。這正是從分析走向建構的轉折點。

## 本章小結

把 `claw-code` 當成整體系統來理解時，你看到的不再是分散的 crate，而是一條從 CLI entry、到 request assembly、到 model event stream、到 tool execution、到 permission gating、到 session persistence、再到 parity verification 的連續工作流。真正重要的，不只是這條鏈很完整，而是你已經能分辨其中哪些是 harness 的本質，哪些是成熟系統因規模而長出的能力。這個區分，正是 Part III 能成立的基礎。

## 章末練習
1. 用一段文字描述 `claw-code` 從使用者輸入到工具執行再到 session 更新的 end-to-end 流程。
2. 各列出三項你認為屬於 `essential` 與 `scale-induced` 的能力，並解釋理由。
3. 說明為什麼 mock parity harness 應被視為整體系統理解的一部分，而不是附錄工具。

## 反思問題

- 你過去在讀大型系統時，是否習慣把所有能力都視為同等重要？這樣的閱讀習慣會帶來什麼問題？
- 如果現在要把 `claw-code` 拿去教學，你最怕學生把哪個規模化能力誤認成「一定要先做」？為什麼？
- 你會如何向一位沒看過原始碼的人解釋：為什麼 `claw-code` 不只是很多功能的 CLI，而是一個 harness？

## 延伸閱讀 / 下一章預告

從下一章開始，我們就正式進入 Part III。也就是說，不再只是分析別人的系統，而是要根據你剛剛整理出的本質清單，定義一個可由自己實作的 Python `mini harness` 範圍。第 16 章的核心任務，就是做對這個縮減。
