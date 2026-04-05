# Harness Engineering Book

本 repo 是一份 **以開源專案 [claw-code](https://github.com/ultraworkers/claw-code) 為核心案例** 的 Harness Engineering 學習手冊：教學敘事、章節中的路徑與設計討論，皆對應到該專案在 GitHub 上的目錄與實作。請將 [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) 視為本教材的 **primary reference implementation**；閱讀時建議 clone 或線上對照原始碼，而非僅讀本書文字。

**案例來源（正式引用）**：[https://github.com/ultraworkers/claw-code](https://github.com/ultraworkers/claw-code)（授權與版本資訊以該 repo 為準。）

---

## 書籤導覽（Landing）

| 區塊 | 說明 |
|------|------|
| [這是什麼](#he-overview) | 教材定位與學習路線 |
| [案例 repo](#he-claw-code-ref) | **claw-code** 正式連結與引用方式 |
| [適合誰](#he-audience) | 先備能力 |
| [你會學到什麼](#he-outcomes) | 學習成果 |
| [閱讀方式：離線／Vercel](#he-readers) | `reader.html` 與動態 Web Reader |
| [先從哪裡開始](#he-start-here) | 檔案導覽 |
| [如何使用這本教材](#he-howto) | 自學／授課建議 |
| [全書結構](#he-structure) | Part I–IV 與附錄 |
| [主要案例來源（對照 claw-code）](#he-case-sources) | 建議閱讀的檔案路徑 |
| [what's next](#he-next) | 後續工作 |

---

<span id="he-overview"></span>

## 這是什麼

這是一套以 **claw-code**（[ultraworkers/claw-code](https://github.com/ultraworkers/claw-code)）為核心案例的 Harness Engineering 教材，兼具自學講義與正式課程教案兩種用途。整套教材採「先拆解、後實作」路線，先幫你看懂真實 agent harness，再帶你用 Python 重建一個可工作的 `mini harness`。

<span id="he-claw-code-ref"></span>

## 案例 repo（claw-code）

- **GitHub**：[https://github.com/ultraworkers/claw-code](https://github.com/ultraworkers/claw-code)
- **用途**：本書 Part II 與多處範例皆以該 repo 的目錄配置、模組邊界與設計取捨為準；若正文與上游版本不一致，請以上游 repo 為準並自行對照 commit／tag。

<span id="he-audience"></span>

## 適合誰

適合已具備基本程式能力、熟悉 Python、CLI、Git，但尚未系統性學過 agent harness / systems engineering 的學習者。若你已經會寫程式、也用過 AI coding 工具，但還沒有把 runtime、tools、permissions、session、testing 看成同一個系統，這套教材就是為你準備的。

<span id="he-outcomes"></span>

## 你會學到什麼

- 看懂 **claw-code** 的核心架構（對照 [GitHub 原始碼](https://github.com/ultraworkers/claw-code)）
- 能說明 runtime、tools、permissions、session、testing 的關係
- 能實作一個 `Python mini harness`
- 能區分哪些能力屬於 harness 本質，哪些屬於規模化後才長出的複雜度

<span id="he-readers"></span>

## 閱讀方式：離線／Vercel

| 方式 | 說明 |
|------|------|
| **離線單檔** | 開啟根目錄的 `reader.html`（由 `python3 tools/build_reader.py` 產生，內嵌已轉好的 HTML） |
| **Vercel 動態版** | 開啟 `/`（`public/index.html`）：前端以 `fetch` 載入 **`/md/…` 靜態檔**（由 `build_reader.py` 從教材根目錄複製到 `public/md/`），再以 Markdown 轉成 HTML；**不需把正文寫死在 HTML**，也不依賴 Serverless。請在**本機**執行 `python3 tools/build_reader.py`（先 `pip install -r tools/requirements.txt`）後 commit／推送 `public/md/`、`book-manifest.json`、`reader.html`。 |

部署提示：在 Vercel 將 **Root Directory** 設為本資料夾。若將 **Output Directory** 設成 `public`，仍可正常運作（靜態 `index.html` + `md/` + `book-manifest.json` 皆在 `public/` 內）。專案含 `package.json` 僅供建置指令；無需 `api/`。

<span id="he-start-here"></span>

## 先從哪裡開始

- **`reader.html`（離線瀏覽器版）**：單一 HTML、不需 npm／本機伺服器，用瀏覽器開啟即可側欄導覽、深淺色切換、章節篩選與書內連結跳轉；內文可離線閱讀（字型預設走 Google Fonts CDN，離線時會退回系統字型）。教材 Markdown 更新後，請執行 `pip install -r tools/requirements.txt`（首次或環境更換時）再執行 `python3 tools/build_reader.py`，以重新產生此檔與 `public/book-manifest.json`。
- **`public/index.html`（Vercel／本機動態版）**：執行時向 **`/md/<相對路徑>.md`** 取正文；章節列表來自 `book-manifest.json`（與 `public/md/` 由 `build_reader.py` 一併產生）。
- `index.md`：全書目錄與章節入口
- `roadmap.md`：自主學習路線圖
- `syllabus.md`：授課版本的課程視角
- `glossary.md`：關鍵術語表
- `references.md`：**claw-code** 核心來源檔閱讀清單
- `writing-progress.md`：目前撰寫進度與完成狀態

<span id="he-howto"></span>

## 如何使用這本教材

- **用瀏覽器讀（離線）**：開啟本目錄下的 `reader.html`；主欄會隨視窗寬度延伸（寬螢幕不會再卡在窄欄），窄螢幕可收合側欄並支援安全區與觸控友善按鈕高度。若你修改了任何章節 `.md`，請在專案內執行 `python3 tools/build_reader.py`（需已安裝 `tools/requirements.txt` 內的 `markdown`）以同步更新 `reader.html` 與動態讀者用的 manifest。
- **用瀏覽器讀（線上／Vercel）**：部署後使用站台首頁動態讀者；更新 `.md` 後重新部署即可，無須手動把 Markdown 貼進 HTML。
- 自主學習路線：依 `index.md` 與 `roadmap.md` 逐章前進，邊讀 [claw-code](https://github.com/ultraworkers/claw-code)、邊整理自己的設計筆記（亦可全程用 reader 對照）
- 授課使用路線：搭配 `syllabus.md` 依 Part I-IV 分段授課，將閱讀、實作與反思題組合成課程活動
- 快速導覽路線：若只想先看整體，先讀第 `1`、`2`、`4`、`15`、`16`、`19` 章，再回補細節章節

<span id="he-structure"></span>

## 全書結構

- Part I：概念地基
- Part II：**claw-code** 拆解
- Part III：`mini harness` 重建
- Part IV：整合與提升
- Appendices：閱讀地圖、專題指南、進修方向

<span id="he-case-sources"></span>

## 主要案例來源（對照 claw-code）

以下路徑相對於 [claw-code 專案根目錄](https://github.com/ultraworkers/claw-code)（請以該 repo 實際檔案為準）：

- `README.md`
- `USAGE.md`
- `PHILOSOPHY.md`
- `rust/README.md`
- `rust/crates/runtime/src/*`
- `rust/crates/tools/src/lib.rs`

<span id="he-next"></span>

## `what's next`

目前這套教材已經是可讀、可教、可自學的完整第一版，但還有幾個自然的下一步：

- 編輯型 QA：刪除重複句、壓縮冗長段落、統一章節語氣與密度
- **Web 讀者進階**（選做）：將字型改為 base64 內嵌以達成完全離線單檔、或加上列印樣式／閱讀進度匯出等
- 教學資產補件：補 `assets/diagrams/`、`assets/code-snippets/`、`assets/figures/`
- 專題驗證：依附錄 B 真的做一輪 `mini harness` 專題，檢查章節順序與作業設計是否順手
- 課程試教：用 `syllabus.md` 跑一輪課堂或自學 pilot，回收卡點與需要補強的章節
- 第二階段擴充：在教材之外，再補 `evaluation`、`MCP`、remote execution、deployment 等進階主題

如果你現在就要開始讀，最好的做法不是等它變成「完美版」，而是直接從 `reader.html`（離線）、`public/index.html`（線上部署後），或 `index.md`／`roadmap.md`（編輯器）進入，先走完一輪完整學習路徑。
