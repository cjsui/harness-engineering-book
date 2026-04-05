# 第 4 章：如何閱讀一個真實的 Agent Harness

## 章節導言

很多人第一次打開大型 agent repo，第一個反應是直接從某個看起來最核心的原始碼檔案開始往下讀。結果常常是十五分鐘後就迷路：型別很多、模組很多、crate 很多、功能交錯得很快，越讀越不知道自己到底在找什麼。這不是你不夠聰明，而是因為大型 harness 本來就不適合用「從第一行看到最後一行」的方式閱讀。

閱讀真實 harness，比閱讀一般教學專案更像在做系統考古。你要先找到入口，再辨識核心 loop，再看能力邊界，最後才進入實作細節。若順序反了，就很容易把大量局部細節誤認成全貌。也正因如此，本章要教你的不是某個單一檔案，而是一套閱讀策略。這套策略會陪你讀完整個 `claw-code`，也會影響你未來看任何 agent framework 的方式。

對本書而言，這一章尤其重要，因為 `claw-code` 有一個容易造成混淆的特徵：根目錄 `README.md` 同時談 Python-first porting workspace 與 Rust workspace。若你沒有先建立閱讀順序與範圍界線，很容易一開始就卡在「到底該先看哪裡」。所以這一章的目標很實際：讓你知道如何不迷路，並且知道何時應該停下來回到高階地圖，而不是被局部細節拖走。

## 學習目標
- 能建立閱讀大型 agent harness 的基本路線圖
- 能先找入口與邊界，再逐步深入核心 loop 與細部模組
- 能避免把大型 repo 的局部細節誤當成整體設計

## 核心概念講解
### 從 README 與 usage 進入

閱讀真實 harness 的第一步，不是打開最深的原始碼，而是讀作者怎麼描述系統。`README.md` 與 `USAGE.md` 通常提供三種非常重要的資訊：系統定位、主要工作入口、以及目前實作成熟度。以 `claw-code` 為例，根目錄 `README.md` 一方面說 active Rust workspace lives in `rust/`，另一方面又說 main source tree is now Python-first。這種資訊如果不先消化，後面所有 code reading 都可能建立在錯誤假設上。

`USAGE.md` 的價值則在於它把系統當成一個可操作工具來介紹。你會看到 interactive REPL、one-shot prompt、permission mode、allowed tools、session resume、config resolution、mock parity harness 等用法。這些不是只有「怎麼用」的資訊，它們同時也是「系統有哪些核心功能」的證據。對初學者而言，usage guide 往往比原始碼更適合作為系統地圖的第一張草圖。

### 先找入口，再找核心 loop

當你從 README 與 usage 建立初步地圖之後，下一步不是隨便挑一個模組深入，而是先找「從哪裡進來」。對 CLI harness 而言，入口通常是二進位檔或主命令程式，例如 `rusty-claude-cli` 這一層。入口層會告訴你有哪些 subcommands、哪些模式是 one-shot、哪些模式是 REPL、哪些流程需要 `--resume` 或特定 flag。這些都是系統 surface。

確認入口後，才去找核心 loop。對 `claw-code` 來說，這個 loop 的代表是 `ConversationRuntime` 所在的 runtime 層。你不必一開始就理解所有細節，但你要知道：真正把使用者輸入、模型回應、工具呼叫、權限檢查、session 更新串起來的，是這個層，而不是 CLI 表面本身。這樣你才不會把指令介面誤當成系統核心。

### 先看邊界，再讀實作細節

大型 harness 最難讀的地方之一，是很多能力同時存在：API client、streaming、tools、permissions、session、prompt assembly、config、remote、MCP、telemetry。若你直接埋進某個函式，通常會在還沒搞清楚邊界前，就看到一大堆跨模組呼叫。比較好的方式，是先畫邊界。

所謂邊界，就是先問每個層負責什麼、不負責什麼。例如：CLI 層負責使用者入口與顯示；runtime 層負責 agent loop 與狀態協調；tools 層負責能力宣告與執行；permissions 層負責決定這些能力何時能動；session 層負責持久化與恢復。當你先用責任分工來看 repo，再回頭看函式與型別，就比較不會陷入「每個名稱都看得懂，但還是不知道整體在幹嘛」的困境。

### 如何避免迷失在大型 repo

避免迷失的關鍵，不是一次讀更多，而是一次只讀對的東西。實務上可以採用三個策略。第一，`分層閱讀`：先文件、再入口、再核心 loop、再相鄰邊界、最後才是局部實作。第二，`帶問題閱讀`：每次進檔案前先問自己要回答什麼問題，例如「runtime 和 tools 怎麼分工？」、「permission mode 在哪裡決定？」。第三，`建立自己的對照筆記`：把檔案、責任、核心型別、與本書章節對應起來。

還有一個常見誤區值得提醒：不要急著把每個檔案都讀完。大型 harness 往往不是靠「通讀」理解，而是靠「反覆定向抽讀」理解。你先建立粗地圖，遇到某章主題再回來抽讀相關檔案，這樣反而更接近工程上真正有效的閱讀方式。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/README.md`
- `claw-code/USAGE.md`
- `claw-code/rust/README.md`
- `claw-code/rust/crates/runtime/src/lib.rs`

### 閱讀順序
1. 先讀 `claw-code/README.md`，確認 Rust / Python 兩條路線的關係
2. 再讀 `claw-code/USAGE.md`，把 CLI 功能面與操作面建立起來
3. 接著讀 `claw-code/rust/README.md`，理解 crate responsibilities
4. 最後回到 `runtime/src/lib.rs`，確認核心責任如何在 runtime 層收束

### 閱讀重點
- `README.md` 要先幫你釐清「教材主讀 Rust，但 repo 又有 Python port」這個範圍問題
- `USAGE.md` 讓你先從使用者角度看到 REPL、one-shot、permission modes、session resume、config hierarchy、parity harness 等能力
- `rust/README.md` 的 crate responsibilities 是理解整體系統分工的捷徑
- `runtime/src/lib.rs` 頂端說明「This crate owns session persistence, permission evaluation, prompt assembly...」，可作為核心 loop 周邊責任的濃縮摘要

## 設計取捨分析

閱讀大型 harness 有一個核心取捨：你要先求全貌，還是先求細節？如果一開始就鑽細節，你很快會得到局部理解，但常常失去方向；如果只看文件與表層，又可能產生過度簡化的印象。比較好的做法其實是往返式閱讀：先靠 README / usage / crate responsibilities 拿到系統地圖，再帶著具體問題回到原始碼找證據。

這種方法的代價是速度看起來比較慢，因為你會重讀同一份文件、反覆回到同一個檔案。但它的好處是理解比較穩，而且更接近真實工程工作。因為在大型系統裡，真正稀缺的不是「把檔案讀完」，而是「知道自己為什麼在讀這個檔案，以及讀完後能回答什麼設計問題」。

## Mini Harness 連結點

這一章雖然看起來像是在教你「怎麼讀別人的 repo」，其實也在替 Part III 做準備。因為當你開始做 `mini harness` 時，也必須用同樣的方法對待自己的系統：先定義入口、再定義核心 loop、再界定工具與權限邊界、最後才補細節。會讀真實 harness 的人，通常也更會設計自己的 harness，因為他知道哪一層應該先被釐清，哪一層不該太早展開。

## 本章小結

閱讀真實 agent harness 的正確順序，通常是先讀 README / usage 釐清定位與功能面，再找 CLI 入口與核心 loop，接著以邊界分工理解各層責任，最後才進入局部實作。對 `claw-code` 這種同時存在 Rust workspace 與 Python porting 脈絡的 repo 而言，閱讀策略尤其重要。它能避免你在大量細節中迷失，也能讓每次抽讀原始碼都更有方向。

## 章末練習
1. 用自己的話寫出你閱讀 `claw-code` 的第一輪路線圖。
2. 解釋為什麼讀 `USAGE.md` 不是「只看操作文件」，而是理解系統功能面的重要步驟。
3. 如果一個 repo 同時有多條實作路線，你會用哪些標準決定教材應該主讀哪一條？

## 反思問題

- 你過去讀大型 repo 時，最常犯的是「太早鑽細節」還是「只停留在文件表面」？為什麼？
- 如果現在要你帶另一位同學讀 `claw-code`，你會要求他先回答哪三個問題，才准他進入原始碼？
- 你是否曾經因為沒有先釐清 system surface，而把某個模組的重要性高估或低估？

## 延伸閱讀 / 下一章預告

到這裡，Part I 的基礎已經完成：你知道為什麼要學 Harness Engineering、知道 agent system 的元件地圖、知道好的 harness 應遵守哪些原則，也知道面對真實 repo 時該如何閱讀。下一章開始，我們就正式進入 Part II，從 CLI 入口把 `claw-code` 當成一個真實系統來拆解。
