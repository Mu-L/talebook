# 书架功能说明

## 背景

PR#837 将原有“待读”入口调整为“我的书架”。本次实现按纯改名处理，不新增独立数据模型。

## 实现

- 前端新增 `/user/shelf` 页面，并在登录用户导航中展示“我的书架”入口。
- 对外接口统一为 `/api/shelf` 与 `/api/book/:id/shelf`。
- 后端继续复用 `ReadingState.wants`、`set_wants()` 与 `wants_date` 存储书架状态。
- 旧的 `/api/wants`、`/api/book/:id/wants`、`/api/case`、`/api/book/:id/case` 不再注册。

## 后续

如果产品确认“书架”和“待读”需要同时存在，应新增独立字段或模型，并迁移当前复用 `wants` 的接口实现。
