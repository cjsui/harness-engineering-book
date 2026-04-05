# 第 1 章：從 Prompt Engineering 到 Harness Engineering

## 章節導言

很多人第一次接觸 AI coding，直覺上會把它理解成「把問題問好一點，模型就會回答好一點」。這個理解在早期並不算錯，因為當時多數工作流確實以單輪問答為主：人把程式碼、錯誤訊息、需求描述貼進對話框，模型回傳一段文字或一段程式碼，再由人自己去執行、測試、修正。這種工作方式的重點，自然會落在 prompt wording、上下文安排、few-shot example、Chain-of-Thought 之類的技巧上。

但今天的 AI coding 工具已經不是單純的聊天視窗。像 `claw-code` 這種系統，真正重要的不是模型會不會「講得漂亮」，而是它能不能在一個可操作、可限制、可測試的環境裡穩定工作。模型要能讀檔、搜尋、執行工具、被限制權限、保存 session、接受測試、在失敗後重試。到了這個階段，工程焦點就從「如何對模型說話」轉向「如何為模型搭建工作系統」。

這一章的任務，是把這個典範轉移講清楚。你不只要知道 `Harness Engineering` 是什麼，還要知道它為什麼會取代純粹的 prompt 技巧，成為現代 agent tooling 的主軸。更重要的是，你要開始建立本書的第一個核心視角：學 `claw-code`，不是為了背一個 repo，而是為了理解一種把 LLM 變成可運作系統元件的方法。

## 學習目標
- 能區分 prompt engineering 與 harness engineering
- 能說明為什麼現代 AI coding 的瓶頸已轉向系統設計
- 能解釋 tools、permissions、session、testing 為何成為主軸

## 核心概念講解
### Prompt engineering 在早期工作流中的角色

早期的 LLM 使用方式，本質上比較接近「高能力但無手腳的顧問」。你可以向它提問、要求它產生程式碼、請它解釋錯誤，但模型本身無法直接進入你的工作區，也不能自己跑測試、讀 log、呼叫 shell、操作版本控制。換句話說，模型只能靠你餵給它的文字來理解世界。

在這種條件下，`Prompt Engineering` 之所以重要，是因為它是在資訊受限、互動受限的情況下，盡可能提高輸出品質的方法。你要決定哪些背景資訊先給、哪些 code snippet 要貼、問題要分成幾步、要不要先給範例、要不要要求模型先思考再回答。這些技巧並不虛假，它們曾經真的是有效的工程能力。

但它有兩個明顯限制。第一，很多資訊整理工作其實是由人手動代勞，例如複製錯誤訊息、刪掉不相關內容、重述需求。第二，輸出品質常常高度依賴單次 prompt 的文字工藝，結果容易脆弱，也不容易在團隊中重現。只要換一個人提問、少貼一段背景、或多貼了一段噪音，模型的回答品質就可能明顯波動。

### 為什麼「環境感知 + 工具使用 + 護欄」改變了問題本質

當模型開始被放進 CLI、IDE、agent runtime 裡，問題的性質就變了。現在它不再只是根據一段輸入文字回答，而是可以透過工具看到工作區、讀取檔案、搜尋程式碼、執行測試、回收錯誤、再進行下一輪判斷。這時候，模型不再只是「回答器」，而是被放進一個會持續運轉的行動回圈中。

這裡有三個關鍵變化。第一，`環境感知` 讓模型不必完全依賴人手動貼上下文；它可以自己讀 repo、查檔案、觀察目前狀態。第二，`工具使用` 讓模型從生成文字變成能採取行動的 agent。第三，`護欄` 讓這些行動不至於無限制擴張，避免模型因判斷失誤而誤寫檔案、亂跑指令、或做出高風險操作。

這也就是為什麼現代 AI coding 的難點不再只是 prompt。真正難的是：你要給模型哪些能力？哪些能力要先 ask 再做？哪些狀態要保存？怎麼讓它知道專案規則？怎麼測試它的行為是否符合預期？這些都不是單句 prompt 能解決的，它們是 system design 問題。

### Oracle 心智模型與 Reasoning Engine 心智模型的差異

如果把 LLM 想成 `Oracle`，你的工作重點就會是「問得更準」。Oracle 心智模型假設模型本身像一個幾乎完整的智慧來源，而人類的主要任務是用夠好的話術把答案問出來。這會自然導向 prompt trick、措辭技巧、以及一次性輸出的優化。

但在 `Harness Engineering` 裡，更有用的心智模型是把 LLM 看成 `Reasoning Engine`。也就是說，模型是系統中的推理元件，不是整個系統本身。它負責理解目標、規劃下一步、解讀工具結果、產生行動建議；但它是否可靠，取決於外層是否替它準備了好的 runtime、好的工具界面、好的權限政策、好的記憶方式，以及好的驗證機制。

這個差異很重要。當你把模型當成 Oracle 時，失敗往往被理解成「我 prompt 下得不夠好」；當你把模型當成 Reasoning Engine 時，失敗會被拆成更可工程化的問題：是不是上下文組裝錯了？是不是工具集合太少？是不是 permission mode 不合理？是不是 session 沒保存導致前文遺失？是不是缺少 deterministic test 去重現 bug？後者才是可以穩定改進的工程路徑。

### Harness engineering 的工作邊界

`Harness Engineering` 不等於模型訓練，也不等於單純寫一個聊天 UI。它關注的是：如何把一個已存在的模型，包裝成一個可操作、可限制、可測試、可維護的工作系統。這通常包含幾個核心面向。

第一是 `runtime`，也就是 turn loop 與控制流程的核心。第二是 `tooling`，包括工具 schema、registry、dispatch 與工具結果回收。第三是 `permissions / guardrails`，決定哪些工具在什麼條件下能執行。第四是 `session / memory`，讓多輪互動與中斷恢復成為可能。第五是 `prompt assembly / project context`，把系統規則、專案脈絡與工作指令組裝成模型真正看到的上下文。第六是 `testing / verification`，用 scenario 或 mock harness 去驗證整體行為。

這裡還有一個常被忽略的邊界：人類的角色沒有消失，只是位置變了。`PHILOSOPHY.md` 一再強調，真正稀缺的不是打字速度，而是 direction、judgment、taste 與 system design。也就是說，Harness Engineering 並不是要把人移除，而是要把人從微操 prompt 的位置，移到設計系統、設定邊界、判斷取捨的位置。

### 為什麼本課程主讀 Rust 而不是 Python port

這是學習 `claw-code` 時最容易混亂的地方。根目錄 `README.md` 明確寫著「The main source tree is now Python-first」，而且 `src/` 被描述為 active Python porting workspace。只看這段，初學者很容易直覺認為本課程應該直接主讀 Python。

但同一份 `README.md` 也在最前面標示：active Rust workspace lives in `rust/`，並且明確建議先從 `USAGE.md` 與 `rust/README.md` 進入。再往下看，根目錄 `README.md` 其實也承認目前 Python workspace 還不是 complete one-to-one replacement。換句話說，`src/` 比較像平行中的 porting effort，而 `rust/` 才是目前較完整、較可操作、具備 session、permission、tooling、MCP、parity harness 等系統面能力的主教學案例。

因此，本教材主讀 `rust/`，不是因為 Python 不重要，而是因為我們想教的是 harness，而不是只找一個語法較親切的檔案樹。對初學者來說，這確實增加了語言門檻；但它換來的是更完整的系統視野。至於 Python，會在 Part III 變成重建 `mini harness` 的教學語言，讓你把在 Rust 系統中學到的概念轉譯成較易上手的實作。

## `claw-code` 對照閱讀
### 建議閱讀檔案
- `claw-code/README.md`
- `claw-code/PHILOSOPHY.md`
- `claw-code/rust/README.md`

### 閱讀順序
1. 先看 `README.md`
2. 再看 `PHILOSOPHY.md`
3. 最後看 `rust/README.md`

### 閱讀重點
- repo 不只是 code，而是 coordination system 的產物；`README.md` 與 `PHILOSOPHY.md` 都在提醒你，真正值得學的層不是單一語言重寫本身，而是後面的 agent workflow
- 真正值得學的是 harness 與 workflow layer；也就是 runtime、tools、permissions、sessions、testing 這些把模型變成工作系統的結構
- `README.md` 中的 Python-first 敘述指向另一條 porting effort；本教材的 study scope 仍以 `rust/` workspace 為準，因為它目前更完整地承載了 harness 能力

## 設計取捨分析

從教材設計的角度看，這一章其實在處理兩個取捨。第一個取捨，是要不要把學習重心放在 prompt 技巧。若這樣做，進入門檻看似低，學生很快就能獲得「好像變強了」的回饋；但這種能力往往不穩，也難以解釋大型 agent 工具為什麼能運作。相反地，從 harness 角度切入，前期比較抽象，卻能讓學生真正理解系統是怎麼把模型能力轉化成可操作能力。

第二個取捨，是要不要一開始就選擇較容易讀的 Python。若只求語法友善，Python 確實較適合入門；但如果教材的核心任務是「看懂一個真實、完整、具備 guardrails 的 agent harness」，那麼主讀 `rust/` 會更誠實。這是本書刻意採取的教學策略：先忍受一點語言難度，換取對完整系統的正確認知；之後再用 Python 把核心概念重建成自己的版本。

## Mini Harness 連結點

到了 Part III，我們不會重做整個 `claw-code`，而是會問一個更有教學價值的問題：如果你只能保留最重要的本質，要留下什麼？從本章角度看，答案已經開始浮現了。`mini harness` 至少要有能執行回圈的 runtime、能採取行動的工具、能限制行動的 permissions、能延續脈絡的 session，以及能驗證行為的基本測試。這五者正是 Harness Engineering 與單純 prompt 工作流的分水嶺。

## 本章小結

`Prompt Engineering` 著重於如何讓模型在一次互動中回答得更好；`Harness Engineering` 則著重於如何把模型包進一個可觀測、可操作、可限制、可測試的系統。當模型從 Oracle 變成 Reasoning Engine，工程的重點就不再只是說話技巧，而是 runtime、tools、permissions、session、testing 與整體工作流設計。理解這個轉向，是讀懂 `claw-code` 與後續自己做出 `mini harness` 的起點。

## 章末練習
1. 用自己的話定義 harness engineering。
2. 說明 prompt engineering 與 harness engineering 的差異。
3. 列出三個你認為不能只交給模型自律處理的問題。

## 反思問題

- 如果一個 AI coding 工具完全不提供 permission layer，你會信任它替你直接操作真實專案嗎？為什麼？
- 在你過去使用聊天式 AI 的經驗裡，有哪些挫折其實不是模型「不聰明」，而是工作流本身設計得不夠好？
- 如果今天讓你做一個最小 agent 工具，你會優先投資在 prompt wording、tooling、還是 testing？你的理由是什麼？

## 延伸閱讀 / 下一章預告

讀完這一章後，下一步不是立刻鑽進某個函式，而是先建立系統地圖。第 2 章會把 model、runtime、tools、permissions、session、config、testing 這些元件放進同一張架構圖裡，讓你知道一個 agent harness 到底由哪些部分組成，以及為什麼它們不能被混為一談。
