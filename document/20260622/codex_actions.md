# Codex GitHub Actions 配置

本仓库新增 `.github/workflows/codex.yml`，用于让维护者在 issue、PR 评论、PR review 或 review thread 中通过 `@codex`、`@Codex`、`/codex` 触发 Codex。

## 触发与权限

- workflow 会先用 GitHub API 校验评论者对仓库拥有 `write`、`maintain` 或 `admin` 权限。
- 普通用户、历史贡献者、只读成员的触发会被跳过。
- PR 场景不会 checkout PR head/merge ref。workflow 始终 checkout 可信 `master`，再通过 GitHub API 把 PR files 与 diff 作为文本数据传给 Codex，避免在带 secret 的 privileged comment workflow 中执行未信任 PR 代码。
- Codex 的本地改动不会自动 push；如果产生 diff，会上传为 `codex-patch-<run_id>` artifact，并在回复中提示。

## Secret 配置

参考的认证模型是不使用 `openai/codex-action@v1` 的 `OPENAI_API_KEY`，而是在 CI 中直接安装 Codex CLI，并恢复 ChatGPT 登录态。

需要在 GitHub repository secrets 中配置：

- `CODEX_AUTH_JSON`：本地 `~/.codex/auth.json` 的完整内容。

生成方式：

```bash
codex login
cat ~/.codex/auth.json
```

如果本地 Codex 使用系统 keychain 而不是文件保存登录态，先在 `~/.codex/config.toml` 中配置：

```toml
cli_auth_credentials_store = "file"
```

然后重新执行 `codex login`，再复制 `~/.codex/auth.json` 到 GitHub Secret。

## 安全边界

- `CODEX_AUTH_JSON` 会写入 `$RUNNER_TEMP/codex-home/auth.json`，权限为 `600`，不在仓库工作区内。
- Codex CLI 会先安装，再恢复 `CODEX_AUTH_JSON`，避免依赖安装步骤接触登录态。
- Codex 运行时使用 `workspace-write` sandbox，且关闭 agent 阶段网络访问。
- workflow 不给 checkout 写 token，默认只允许读代码、写 issue/PR 评论。
- shell 环境会排除常见 token、secret、key 变量，避免被 Codex 子进程继承。

如果后续要让 Codex 直接向 PR 分支 push commit，应另行增加细粒度 `CODEX_GITHUB_TOKEN`，并把推送逻辑放到独立 job 中处理。
