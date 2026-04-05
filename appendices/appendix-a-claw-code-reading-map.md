# 附錄 A：`claw-code` 閱讀地圖

## 這份附錄要解決什麼問題

`claw-code` 不是一個適合從頭到尾線性讀完的 repo。對初學者來說，真正困難的通常不是看不懂單一函式，而是不知道「先讀哪裡、後讀哪裡」，也不知道哪些檔案是核心，哪些暫時可以略過。因此，這份附錄的目的不是列出所有檔案，而是替你建立一條和本書章節對齊的閱讀地圖。

最重要的原則只有一句話：`先用問題帶路，不要用目錄帶路`。你應該先問自己現在想理解的是入口、runtime、tools、permissions、session、prompt、config、extension、remote，還是 testing，再去追對應檔案。

## 建議的總閱讀順序

若你要完整走一次 `claw-code`，建議使用以下順序：

1. `claw-code/README.md`
2. `claw-code/USAGE.md`
3. `claw-code/PHILOSOPHY.md`
4. `claw-code/rust/README.md`
5. `claw-code/rust/crates/runtime/src/lib.rs`
6. `claw-code/rust/crates/runtime/src/conversation.rs`
7. `claw-code/rust/crates/tools/src/lib.rs`
8. `claw-code/rust/crates/runtime/src/permissions.rs`
9. `claw-code/rust/crates/runtime/src/session.rs`
10. `claw-code/rust/crates/runtime/src/prompt.rs`
11. `claw-code/rust/crates/rusty-claude-cli/tests/mock_parity_harness.rs`

這條順序的目的，是先建立入口與哲學，再進核心 runtime，最後才處理 verification 與較高階邊界。

## 章節對照表

| 本書章節 | 你要回答的問題 | 優先閱讀檔案 | 第一輪先看什麼 |
|---|---|---|---|
| 第 1 章 | 為什麼這不是單純 prompt 工具？ | `README.md`, `PHILOSOPHY.md` | 產品定位、agent 工作方式、設計哲學 |
| 第 4 章 | 如何建立 reading strategy？ | `README.md`, `USAGE.md`, `rust/README.md` | 入口文件、workspace layout、crate responsibilities |
| 第 5 章 | 系統從哪裡進來？ | `USAGE.md`, `rusty-claude-cli` 相關檔案 | subcommands、modes、system surface |
| 第 6 章 | runtime loop 怎麼運作？ | `runtime/src/lib.rs`, `runtime/src/conversation.rs` | `ApiRequest`、`AssistantEvent`、turn loop |
| 第 7 章 | tools 怎麼被定義與暴露？ | `tools/src/lib.rs` | `ToolSpec`、registry、`definitions()` |
| 第 8 章 | guardrails 在哪裡真的生效？ | `runtime/src/permissions.rs` 及相關 enforcer 檔案 | `PermissionMode`、policy、授權判斷 |
| 第 9 章 | session 與 transcript 如何持久化？ | `runtime/src/session.rs` | append、resume、transcript 結構 |
| 第 10 章 | system prompt 怎麼被組起來？ | `runtime/src/prompt.rs` | project context、instruction files、prompt assembly |
| 第 11 章 | config 與 modes 怎麼影響行為？ | `runtime/src/lib.rs` 與 config 相關檔案 | hierarchy、settings、環境敏感行為 |
| 第 12 章 | MCP / plugins 到底做到哪裡？ | extension / bridge / registry 相關檔案 | implemented path 與 planned surface 的邊界 |
| 第 13 章 | remote 為什麼是另一種問題？ | remote / proxy / execution context 相關檔案 | local vs remote boundary |
| 第 14 章 | 系統怎麼驗證自己沒退化？ | `tests/mock_parity_harness.rs`, `mock_parity_scenarios.json` | scenario-based verification |
| 第 15 章 | 如何把整體重新接回來？ | `rust/README.md`, `runtime/src/lib.rs`, `tools/src/lib.rs` | end-to-end 系統鏈 |

## 按主題閱讀，而不是按資料夾閱讀

### Route 1：如果你想先看懂整體系統

1. `claw-code/README.md`
2. `claw-code/USAGE.md`
3. `claw-code/rust/README.md`
4. `claw-code/rust/crates/runtime/src/lib.rs`

這條路線適合第一次進 repo 時使用。目標不是理解所有型別，而是先知道「有哪些主要層次」。

### Route 2：如果你最關心 runtime loop

1. `claw-code/rust/crates/runtime/src/lib.rs`
2. `claw-code/rust/crates/runtime/src/conversation.rs`
3. 回看第 6 章與第 15 章

重點是沿著一次 assistant turn 去看，而不是從每個 helper module 細節開始。

### Route 3：如果你最關心 tools 與 permissions

1. `claw-code/rust/crates/tools/src/lib.rs`
2. `claw-code/rust/crates/runtime/src/permissions.rs`
3. 對照第 7、8 章

這條路線最適合想理解「能力」與「治理」如何耦合的人。

### Route 4：如果你最關心 session / prompt / config

1. `claw-code/rust/crates/runtime/src/session.rs`
2. `claw-code/rust/crates/runtime/src/prompt.rs`
3. config 與相關 settings 檔案
4. 對照第 9、10、11 章

這條路線可以幫你理解系統為什麼不是把 prompt 直接送出去，而是先把上下文與設定組成工作環境。

### Route 5：如果你最關心 extension、remote 與 testing

1. extension / bridge / registry 相關檔案
2. remote / execution context / proxy 相關檔案
3. `claw-code/rust/crates/rusty-claude-cli/tests/mock_parity_harness.rs`
4. `claw-code/rust/mock_parity_scenarios.json`

這條路線建議放在較後面，因為它比較容易把初學者帶進規模化複雜度，而忽略核心 loop。

## 第一輪閱讀時可以暫時略過什麼

第一次讀 `claw-code`，你不需要同時追所有 helper、所有旗標、所有實驗性邊界。更好的做法是先刻意略過：

- 還看不出責任邊界的細碎 utility 檔案
- 你暫時不打算實作的規模化能力
- 所有你一追就會忘記原本問題的支線

這不是偷懶，而是為了保留閱讀主軸。對初學者來說，最大的風險通常不是讀太少，而是讀太散。

## 三個常見閱讀錯誤

1. 一開始就去追 Python port，結果錯過 `rust/` 主實作的責任分層。
2. 看到 `MCP`、plugins、remote 就立刻深挖，結果核心 runtime 還沒建立穩定心智模型。
3. 把 mock parity harness 當成附屬測試，不把它當成理解整個 harness 的入口之一。

## 最後的使用建議

如果你是第一次學 Harness Engineering，請把這份 reading map 和本書章節一起使用，而不是獨立使用。最有效的方式，是先用章節建立問題意識，再用這份 reading map 對照 `claw-code` 的具體檔案。這樣你讀到的就不只是原始碼，而是一條有教學節奏的理解路線。
