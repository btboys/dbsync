# 备份任务取消功能设计

## 背景
当前备份任务一旦启动无法手动取消，任务可能长时间卡在 running 状态（如 495 分钟）。

## 需求
- 用户可以取消正在执行的备份任务
- 取消后任务标记为"已取消"状态
- 取消时删除已生成的备份文件（如果有）
- Worker 完成 dump 后若发现已取消，则丢弃结果

## 方案

### 1. 数据库变更
在 `record_status` enum 中新增 `cancelled` 状态。

### 2. 后端 API
新增 `POST /api/v1/backup-records/{record_id}/cancel`：
- 验证记录存在且状态为 running
- 更新状态为 cancelled，设置 finished_at
- 删除已生成的文件（如果有）
- 记录取消日志

### 3. Worker 变更
在 dump 完成后、更新 success 前检查数据库状态：
- 若已取消，删除文件并记录日志后返回
- 不更新 success 状态

### 4. 前端变更
- BackupDetail.vue：添加"取消任务"按钮，仅对 running 记录显示
- TaskStatusTag.vue：新增 cancelled 标签样式（灰色）
- api/client.ts：新增 cancelBackupRecord 方法

## 文件改动
- `backend/app/models/__init__.py`
- `backend/app/api/backup.py`
- `backend/app/worker/backup.py`
- `frontend/src/api/client.ts`
- `frontend/src/views/BackupDetail.vue`
- `frontend/src/components/TaskStatusTag.vue`
