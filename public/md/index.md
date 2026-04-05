# Harness Engineering 教材索引

## 閱讀方式

本書採「先拆解、後實作」的學習順序。建議先完成 Part I 與 Part II，建立閱讀大型 harness 的能力，再進入 Part III 的 `mini harness` 重建，最後用 Part IV 做整體回看。

## 全書目錄

### Part I：Harness Engineering 的基礎觀念
1. [第 1 章：從 Prompt Engineering 到 Harness Engineering](part-1-foundations/01-from-prompt-to-harness-engineering.md)
2. [第 2 章：AI Agent 系統的基本構成](part-1-foundations/02-agent-system-components.md)
3. [第 3 章：Harness 的核心設計原則](part-1-foundations/03-harness-design-principles.md)
4. [第 4 章：如何閱讀一個真實的 Agent Harness](part-1-foundations/04-how-to-read-a-real-agent-harness.md)

### Part II：以 `claw-code` 拆解真實 Harness
5. [第 5 章：從 CLI 入口看整個系統](part-2-claw-code/05-cli-entry-and-system-surface.md)
6. [第 6 章：Conversation Runtime：Agent Loop 的心臟](part-2-claw-code/06-conversation-runtime.md)
7. [第 7 章：Tool System：讓模型有手腳](part-2-claw-code/07-tool-system.md)
8. [第 8 章：Permissions and Guardrails：讓模型不會亂來](part-2-claw-code/08-permissions-and-guardrails.md)
9. [第 9 章：Session、Transcript、Memory](part-2-claw-code/09-session-transcript-memory.md)
10. [第 10 章：Prompt Assembly 與 Project Context](part-2-claw-code/10-prompt-assembly-and-project-context.md)
11. [第 11 章：Config、Modes 與執行環境](part-2-claw-code/11-config-modes-and-environment.md)
12. [第 12 章：MCP、Plugins 與能力擴充](part-2-claw-code/12-mcp-and-plugins.md)
13. [第 13 章：Remote 與多執行環境能力](part-2-claw-code/13-remote-and-execution-environments.md)
14. [第 14 章：Parity Harness 與測試哲學](part-2-claw-code/14-parity-harness-and-testing.md)
15. [第 15 章：把 `claw-code` 當成一個完整系統來理解](part-2-claw-code/15-understanding-claw-code-as-a-whole.md)

### Part III：用 Python 重建一個 Mini Harness
16. [第 16 章：定義 Mini Harness 的最小範圍](part-3-mini-harness/16-defining-the-mini-harness-scope.md)
17. [第 17 章：實作最小 Runtime、Tools 與 Permissions](part-3-mini-harness/17-building-runtime-tools-permissions.md)
18. [第 18 章：加入 Session Persistence 與基本測試](part-3-mini-harness/18-session-persistence-and-basic-testing.md)

### Part IV：整合與提升
19. [第 19 章：從 Mini Harness 回看真實 Harness](part-4-integration/19-from-mini-harness-back-to-real-harness.md)

### Appendices
A. [附錄 A：`claw-code` 閱讀地圖](appendices/appendix-a-claw-code-reading-map.md)
B. [附錄 B：`mini harness` 專題製作指南](appendices/appendix-b-mini-harness-project-guide.md)
D. [附錄 D：後續進修方向](appendices/appendix-d-further-study.md)
