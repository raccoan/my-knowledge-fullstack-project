# AI 接口用户级限流

## 行为与边界

使用 `limits` 的 MovingWindowRateLimiter 和 Redis Lua 脚本实现滑动窗口准入，按已认证用户 ID 隔离额度。多个 FastAPI worker / 实例连接同一 Redis、使用相同 namespace 时共享额度，无需进程内字典或自写 Lua。

| 业务范围 | 共享配额的接口 | 默认额度 |
| --- | --- | --- |
| chat | POST /chat、POST /chat/stream | 每用户滚动 60 秒内 10 次 |
| interview | POST /interviews、POST /interviews/{id}/answer | 每用户滚动 60 秒内 10 次 |

依赖在 JWT 认证之后、路由数据库操作和模型调用之前执行。未认证请求不扣额度；已准入后业务校验失败、模型失败或用户停止生成仍占用一次额度，不退款。每次面试作答可能调用多个模型，计量单位是接口请求，不是模型调用次数或 Token。此功能不限制同时生成数量，也不构成全站费用上限；上传/解析等接口不在本次范围内。

超额返回 HTTP 429；Redis 超时/不可用时返回 HTTP 503，不降级为进程内计数。两者均带 `Retry-After` 秒数，CORS 暴露该响应头。错误体示例：

```json
{"detail":{"code":"rate_limit_exceeded","message":"请求过于频繁，请稍后再试","retry_after":12,"scope":"chat"}}
```

Redis 不可用的 code 为 `rate_limit_unavailable`。前端 Axios 与 SSE fetch 共用错误解析，VueUse 管理冷却计时和卸载清理。倒计时期间禁止提交；结束后由用户手动重试，不自动重复付费调用。聊天撤回本次临时消息并恢复输入；重新生成被拒绝时保留原回答；面试保留回答并提供创建失败后的重试入口。没有在服务端确认准入前删除旧回答。

## 启动与配置

在仓库根目录启动本地 Redis（需要 Docker）：

```sh
docker compose -f compose.redis.yaml up -d
```

Redis 只映射本机 6379 端口。远程部署请通过私有网络连接 Redis，并配置认证/TLS URL。不要将带密码的 URL 提交到 Git。

更新依赖（requirements.txt 已由 UTF-16 统一为 UTF-8）：

```sh
python -m pip install -r backend/requirements.txt
cd frontend
npm ci
```

将以下设置加入 `backend/.env`，其余应用配置沿用原有配置：

```dotenv
REDIS_URL=redis://127.0.0.1:6379/0
RATE_LIMIT_ENABLED=true
RATE_LIMIT_NAMESPACE=knowledge-ai
RATE_LIMIT_CHAT_REQUESTS=10
RATE_LIMIT_INTERVIEW_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_REDIS_TIMEOUT_SECONDS=1
RATE_LIMIT_UNAVAILABLE_RETRY_SECONDS=5
```

默认开启，无 Redis 时 AI 接口返回 503；仅本地不测试此功能时可显式设置 `RATE_LIMIT_ENABLED=false`。不同部署环境应使用不同 namespace。配置在进程启动时读取，修改后需重启。超时限制每次 Redis 操作，关闭 redis-py 默认重试以避免长时间等待。连接按应用生命周期释放；Redis 不存储问题或回答正文，键包含范围和用户 ID，窗口数据由库管理过期。

## 验证

```sh
python -m pip install -r backend/requirements-dev.txt
python -m pytest -q
cd frontend
npm test
npm run build
npm run test:e2e
```

浏览器测试默认使用本机 Chrome，可按环境修改 Playwright channel。后端测试使用 fakeredis + Lua 引擎执行 limits 脚本，覆盖多连接池并发、用户/范围隔离、窗口恢复、故障及实际路由准入顺序；数据库与模型由替身隔离。浏览器测试模拟 HTTP 响应，覆盖聊天 429/503、原回答保留、面试回答保留和创建重试。本次不依赖真实 Redis、数据库或付费模型，测试结果不代表生产压测或真实服务联调。
