# 附錄 D：後續進修方向

## 為什麼還需要這份附錄

完成本書後，你已經有能力看懂 `claw-code` 的核心架構，也能自己做出一個 `mini harness`。但 Harness Engineering 的學習不會停在這裡。真正往實務走時，系統常常會碰到更長的生命週期、更多工具來源、更多使用情境，以及更高的可靠性需求。這些問題，未必適合放進第一輪教材，但很適合作為第二階段進修方向。

這份附錄的目的是幫你辨識下一步可能的路線，而不是要你一次全做完。你應該根據自己的目標，選擇最需要的一條往下挖。

## 方向 1：`MCP` 與能力擴充介面

如果你想讓 harness 能接更多外部能力來源，而不是只靠內建工具，下一步很自然會走到 `MCP`。這條路線的核心問題包括：

- 工具 schema 如何跨邊界對齊？
- 外部能力如何被安全地註冊到系統？
- permission policy 要怎麼延伸到外部工具？
- lifecycle 與 error handling 該放在哪一層？

這個方向適合想研究 extension architecture、tool bridge 與能力治理的人。

## 方向 2：Multi-Agent Orchestration

當一個 agent 不夠用，或者你想把任務拆成 planner、executor、reviewer 等多角色時，就會進入 multi-agent orchestration。這條路線最重要的不是讓 agent 數量變多，而是處理：

- 任務如何切分
- 中介狀態如何共享
- 角色邊界如何定義
- 錯誤與衝突如何回收

如果沒有清楚 orchestration 設計，多代理只會把單代理的混亂放大。

## 方向 3：UI 與 Human Oversight

本書主要用 CLI 與教材式視角理解 harness，但真實系統常常還需要更好的操作介面。你可以研究：

- approval flow 如何在 UI 中被清楚呈現
- transcript、tool logs、permission decision 如何可視化
- 人類如何中途介入、修正、批准或中止 agent 行為
- 長任務如何讓使用者維持可理解感

這個方向特別適合想把 harness 變成真正可被一般使用者操作的產品介面的人。

## 方向 4：Deployment 與運維

當 harness 從個人專案變成團隊工具，deployment 問題就會浮現。這不只是把程式放到雲端而已，而是要考慮：

- 執行環境如何隔離
- secrets 與 credentials 如何管理
- remote workers 如何被啟動與監控
- 版本更新如何避免破壞既有 workflow
- 成本、資源與失敗重試如何被追蹤

這條路線會讓你看到，為什麼很多看似「只是工程雜事」的能力，其實會反過來改寫 harness 的核心設計。

## 方向 5：Evaluation、Telemetry 與 Cost Awareness

只要系統開始長期使用，`evaluation` 就不再是可有可無的補充件。你會需要思考：

- 什麼叫做一輪任務成功？
- 哪些 scenario 應該被固定回歸測試？
- usage、latency、tool failure rate、approval rate 應該如何觀測？
- 哪些指標能提醒你系統正在退化？

如果沒有 evaluation 與 telemetry，系統就算看起來能跑，也很難知道它是不是在悄悄變差。

## 方向 6：Security、Sandbox 與 Policy Engineering

當 agent 擁有更多手腳，安全邊界就會成為真正的設計核心。後續可深入的問題包括：

- shell、file system、network 的能力該如何分層授權？
- sandbox 與 approval 機制如何彼此搭配？
- 哪些政策應由 prompt 處理，哪些應由外部系統強制？
- 如何避免模型在錯誤環境假設下做出高風險操作？

這條方向特別適合想從 Guardrails 進一步走向更嚴格 policy engineering 的人。

## 一條實際可行的進修順序

如果你不確定從哪裡開始，以下是一條很穩健的順序：

1. 先補 local reliability：CLI、config、prompt assembly、更多 tests
2. 再補 evaluation / telemetry，建立可觀測性
3. 接著才處理 `MCP` 或其他 extension boundary
4. 最後再考慮 remote、deployment、multi-agent orchestration

這個順序的好處是：你會先把系統做得穩、看得清，再去碰會大量放大複雜度的議題。

## 可作為第二階段專題的題目

若你想延伸本書內容，可以考慮以下題目：

- 為 `mini harness` 加上一個簡化版 CLI 與 config 機制
- 為 `mini harness` 增加 scenario-based evaluation
- 設計一個最小 `MCP` bridge 實驗
- 把 permission decision 與 tool logs 做成簡單 UI
- 實作一個可被部署到遠端 worker 的執行模型

## 最後建議

後續進修最重要的不是一次學最多，而是每次只擴充一條責任鏈。當你加入 `MCP`、deployment、evaluation 或 multi-agent 時，都應該反問自己：這一層新能力是否仍然能被既有 runtime、permissions、session、testing 框架穩定承接？如果答案是否定的，代表你需要的可能不是更多功能，而是先把骨架補強。
