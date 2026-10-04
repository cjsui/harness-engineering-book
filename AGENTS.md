

## 2026-10-04 Vercel 封存與重建

Ron 已指定刪除 Vercel 專案 `harness-engineering-book`（原 ID `prj_jMZdNy4ED1MLJaSpRjdT90AbplYJ`），不得由例行維護、push 或掃描自行重新部署。實際刪除結果以中央服務封存紀錄為準。GitHub repository 與程式碼保留，不刪除。

### 還原流程

1. 取得 Ron 明確重新啟用指令。先讀備份 `/Users/cjsui/service-archives/20261004-140645/vercel/harness-engineering-book` 的 project.json、domains.json、git-version.json（若有）與 environment.json；機密不可寫入 Git 或報告。
2. 在 Vercel scope `cjsuis-projects` 建立同名專案，依原 project.json 還原 framework、rootDirectory、build/install/output 設定，重新連結本 repo。舊 project ID 不可再使用。
3. 恢復環境變數的 target 與 branch 範圍，再部署 preview 驗證。Sensitive 無法讀回而需重新設定的 keys：無已知缺項。資料庫或外部 GAS 資源未刪除，需另驗證連線與資料是否仍在。
4. 取得正式環境恢復指令後部署 production，依 domains.json 核對網域。DNS 不可自行改指向；若需更改先列計畫。完成後更新中央 my-online-service 報告。

備份位置含私密設定，檔案權限必須維持私有。本文件不是自動重建指令。


### 刪除後查證與環境變數限制

已於 2026-10-04 刪除並以原專案 ID 查證不存在。environment.json 保留的是 Vercel 加密 metadata 或空 Sensitive 值，**不可直接匯入當明文值**；重建時需要從原憑證來源或外部資料庫管理頁重建下列環境變數：無。GitHub 原始碼已保留；myfirstweb 無部署與可回收原始碼，僅設定紀錄。
