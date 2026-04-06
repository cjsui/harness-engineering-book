# References

> **閱讀優先度說明**：
> - ⭐ **必讀**：理解本書核心概念的關鍵檔案
> - 📖 **建議**：能加深理解的重要參考
> - 📄 **進階**：適合想深入特定主題時再看

## Primary Source Repository

- ⭐ `claw-code/README.md`
  — 整個專案的入口文件，幫你快速理解 claw-code 是什麼、為什麼存在。**這是第一個該讀的檔案。**

- ⭐ `claw-code/USAGE.md`
  — 說明系統怎麼被使用，包括指令、模式、操作方式。幫你從「使用者視角」理解系統的外部行為。

- 📖 `claw-code/rust/README.md`
  — Rust 實作的總覽，說明 crate 之間的分工。幫你建立「系統有哪些主要模組」的全景圖。

## Core Runtime Files

- ⭐ `claw-code/rust/crates/runtime/src/lib.rs`
  — Runtime 模組的入口，定義核心型別與公開介面。是理解整個 runtime 分層的起點。

- ⭐ `claw-code/rust/crates/runtime/src/conversation.rs`
  — 實作 turn loop 的核心邏輯。**這是全書最重要的對照檔案**——第 6 章的所有概念都來自這裡。

- ⭐ `claw-code/rust/crates/runtime/src/permissions.rs`
  — Permission policy 的實作。幫你看到「治理層」不只是概念，而是真的參與每次工具執行。

- 📖 `claw-code/rust/crates/runtime/src/session.rs`
  — Session 持久化的實作。幫你理解 session 如何被保存、載入、resume，以及為什麼不是簡單的 JSON dump。

- 📖 `claw-code/rust/crates/runtime/src/prompt.rs`
  — Prompt assembly 的實作。展示 system prompt 不是一段固定文字，而是被動態組裝的工作環境。

## Tooling Files

- ⭐ `claw-code/rust/crates/tools/src/lib.rs`
  — 工具系統的核心。定義 ToolSpec、registry、dispatch 機制。是理解「能力宣告與能力執行分離」的關鍵檔案。

## Verification Files

- 📖 `claw-code/rust/crates/rusty-claude-cli/tests/mock_parity_harness.rs`
  — Mock parity harness 的測試實作。展示如何用 scenario-based 方式驗證系統行為一致性。

- 📄 `claw-code/rust/mock_parity_scenarios.json`
  — Parity 測試的 scenario 定義檔。讓你看到測試場景是怎麼被結構化的。

## Reading Strategy

建議依照以下順序閱讀，逐步加深理解：

1. ⭐ 先看 README / USAGE 建立入口（搞清楚這個系統是什麼、怎麼用）
2. ⭐ 再看 runtime 核心（理解一輪對話是怎麼跑完的）
3. ⭐ 再看 tools / permissions（理解能力和治理怎麼分工）
4. 📖 再看 session / prompt（理解狀態和上下文怎麼被管理）
5. 📖 最後看 testing（理解系統怎麼驗證自己沒退化）
