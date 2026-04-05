# 第 8 章：Permissions and Guardrails：讓模型不會亂來

## 章節導言

一旦模型有了工具，問題就不再只是「它能做什麼」，而是「它可以被允許做什麼」。這是 agent harness 與一般聊天系統最鮮明的分界點之一。工具讓模型有能力改變世界；permissions 則決定這個改變世界的能力是否被限制在合理邊界內。沒有這一層，agent 很快就會從「很方便」變成「很危險」。

`claw-code` 對 guardrails 的處理值得細讀，因為它不是只做一個粗略的 yes/no 開關，而是把 permission mode、規則匹配、hook override、interactive approval、file-write boundary、bash 檢查等機制拆開來處理。這透露出一個很重要的設計觀念：安全不是事後補上的外掛，而是 runtime 內部正式承認並治理的一條控制流程。

本章會先把 `PermissionMode` 的分層說清楚，再討論 allow / deny / ask 三種規則如何互動，接著說明 `PermissionPolicy` 與 `PermissionEnforcer` 為什麼是兩種不同責任。最後，我們要回到最根本的問題：為什麼不能只靠模型自律？如果你能回答這個問題，你就真正理解了 guardrails 的必要性。

## 學習目標
- 能比較不同 `permission mode` 的意義與風險差異
- 能說明 allow / deny / ask 與 policy / enforcement 的分工
- 能為 `mini harness` 設計一套最小但合理的 permission model

## 核心概念講解
### permission mode

`permissions.rs` 一開始就定義了 `PermissionMode`：

- `ReadOnly`
- `WorkspaceWrite`
- `DangerFullAccess`
- `Prompt`
- `Allow`

從使用者操作角度，最常見的是前三種：`read-only`、`workspace-write`、`danger-full-access`，這也和 `USAGE.md` 的 CLI flags 對應。它們代表的是整個 session 的基本操作邊界：只能讀、可在 workspace 內寫、或幾乎完全放開。這些 mode 的意義不只是 convenience，而是系統對風險承受度的明確宣告。

另外兩個 mode 則更像系統內部治理語意。`Prompt` 代表某些行為需要走 interactive approval flow；`Allow` 則代表更寬鬆的全開狀態。也就是說，`PermissionMode` 不是單純的使用者 UI 文案，而是一套用來比較當前權限與工具需求的正式階層。

### allow / deny / ask

`PermissionPolicy` 真正精彩的地方，在於它不是只看「目前 mode 是否高於工具需求」，而是再疊加三種規則集合：`allow_rules`、`deny_rules`、`ask_rules`。從 `authorize_with_context()` 的流程可以看出，deny rule 會先被檢查；ask rule 會要求進一步 approval；allow rule 則能在相符情況下直接放行，但 ask rule 仍可能優先要求確認。

這裡反映出一個重要原則：permission 不是單一層級比較，而是靜態 mode、細粒度規則、以及互動式確認三者共同形成的結果。舉例來說，就算當前 mode 理論上足夠，ask rule 仍然可以要求額外確認；反過來說，hook 也可能透過 `PermissionOverride` 臨時把某個決策改成 Allow、Deny、或 Ask。這使得權限系統不只可分層，也可被更高層 orchestration 或 hooks 介入。

### policy 與 enforcement 的差異

這是很多人第一次讀權限系統時最容易混淆的地方。`PermissionPolicy` 的工作是做授權判斷，回答「依照目前模式、工具需求、規則與上下文，這次操作應該被允許還是拒絕？」它產出的是 `PermissionOutcome`，也就是 Allow 或 Deny，以及被拒絕時的原因。

`PermissionEnforcer` 則是另一層責任。它把 policy 帶到實際執行邊界上，回傳較具結構的 `EnforcementResult`。像 `check_file_write()` 會額外考慮 workspace boundary，`check_bash()` 則會用保守 heuristic 判斷某個 command 是否只讀。也就是說，policy 比較像抽象授權邏輯；enforcement 則是把這個邏輯落在具體操作面，補上路徑、命令性質與執行上下文。

這個分層很值得學。若 policy 和 enforcement 全混在一起，系統很快就會變成難以測試的 if/else 叢林；若只有 policy 沒有 enforcement，則很多真實邊界條件無法被良好表示，例如「workspace-write 可以寫工作區內，但不能寫工作區外」這類規則。

### 為什麼不能只靠模型自律

這是 permission 系統存在的根本理由。有人可能會說：模型已經很聰明了，只要在 system prompt 裡提醒它不要做危險事，不就夠了嗎？答案通常是不夠。因為 prompt 指令只能提供行為傾向，不能提供真正可執行、可驗證、可拒絕的邊界控制。當模型判斷錯誤、上下文不足、或任務壓力過高時，它仍可能選擇高風險操作。

`claw-code` 的 mock parity scenarios 很直接地證明了這件事。像 `write_file_denied`、`bash_permission_prompt_approved`、`bash_permission_prompt_denied` 這些場景之所以重要，就是因為系統必須在外部明確決定：什麼行為會被拒絕、什麼行為必須 ask、什麼情況下 approval 才能放行。若這些判斷完全交給模型自己決定，整個 guardrail 就等於不存在。

換句話說，好的 agent 不是「會自我克制的模型」，而是「被放進良好制度中的模型」。自律可以是加分項，但不能是唯一防線。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/rust/crates/runtime/src/permissions.rs`
- `claw-code/rust/crates/runtime/src/permission_enforcer.rs`

### 閱讀順序
1. 先讀 `PermissionMode`、`PermissionOutcome`、`PermissionPolicy`
2. 再看 `authorize_with_context()` 如何依序處理 deny / ask / allow / override
3. 最後讀 `PermissionEnforcer` 的 `check()`、`check_file_write()`、`check_bash()`

### 閱讀重點
- `PermissionMode` 如何表達不同風險層級
- `PermissionPolicy` 如何把 active mode、tool requirement、rule matching、interactive prompt 串起來
- `PermissionEnforcer` 如何把抽象政策落到具體工具執行邊界上
- `read-only`、`workspace-write`、`danger-full-access` 在真實檔案寫入與 bash 執行上的差異

## 設計取捨分析

permission system 的核心取捨，是安全性與摩擦成本之間的平衡。`read-only` 最安全，但也最限制 agent 能力；`danger-full-access` 最順手，但把大量風險暴露給模型；`workspace-write` 則試圖在生產力與邊界控制之間找折衷。再加上 ask rules 後，系統可以針對特定高風險行為保留人類批准流程，但同時也增加了互動中斷與心智負擔。

另一個取捨是 policy 與 enforcement 要不要分開。分開的好處是抽象清楚、可測試性好、理由可追溯；壞處則是你得維護兩層概念，不像一個巨大的條件判斷那麼「看起來直接」。`claw-code` 選擇承擔這個複雜度，因為它換來的是更可靠的治理結構。對真實 harness 來說，這筆成本通常值得。

## Mini Harness 連結點

在 `mini harness` 裡，我們不一定需要完整複製 `claw-code` 的所有 permission 細節，但至少要保留三件事：第一，有明確的 mode 分層，例如 `read-only`、`workspace-write`、`danger-full-access`；第二，工具宣告要帶著所需權限；第三，要有一個最小授權函式在工具執行前被呼叫。若教學版還能再進一步保留 ask / deny 規則，那會更接近真實系統；但就算先簡化，也不能把所有保護都塞回 prompt 文字裡。

## 本章小結

`claw-code` 的 permission system 展示了 guardrails 的真正樣子：不是一句「請小心操作」，而是一套由 `PermissionMode`、`PermissionPolicy`、`PermissionEnforcer`、rules、prompts 與執行邊界共同構成的治理流程。能力越強，越需要這種制度化控制。理解它，才能明白 agent harness 的安全性不是附屬品，而是核心架構的一部分。

## 章末練習
1. 比較 `read-only`、`workspace-write`、`danger-full-access`
2. 說明 `ask` 規則何時有必要
3. 設計一條適合 `mini harness` 的最小 permission policy

## 反思問題

- 如果讓你在「較安全但常打斷工作流」與「較順手但風險較高」之間二選一，你會如何為不同任務設計不同 permission mode？
- 你是否認為某些工具應該永遠不允許在 fully automatic 模式下執行？為什麼？
- 若一個系統只有 mode 分層，沒有 allow / deny / ask 規則，它最可能在哪些邊界案例出現漏洞？

## 延伸閱讀 / 下一章預告

讀完 guardrails 後，接下來要問的是：你怎麼知道這些權限、工具與 runtime 真的按預期運作？這個問題會在第 14 章得到回答。我們會從 `mock parity harness` 出發，看看真實 agent harness 為什麼需要 deterministic、scenario-based 的驗證方法。
