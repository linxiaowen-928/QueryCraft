# GitHub Issue Automator

自动处理 GitHub Issues 的协作 Skill。

## 语言偏好

**所有对话、日志、提交信息都使用中文。**

- 提交信息格式：`feat: 功能描述 (Issue #<number>)`
- PR 标题：`feat: 功能描述 (Issue #<number>)`
- PR 描述：使用中文说明
- 代码注释：使用中文
- 对话回复：使用中文

---

## 重要：同一机器多账户隔离

**OpenCode 和 OpenClaw 在同一台机器上，但使用不同的 GitHub 账户！**

| Agent | GitHub 账户 | SSH 远程 | 角色 |
|-------|------------|----------|------|
| OpenClaw (Xeon) | linxiaowen-928 | github | 审查者 |
| OpenCode | linxClawBot | github-collab | 开发者 |

## 前置条件（必须满足）

### 1. SSH 配置

确保 `~/.ssh/config` 包含：

```
# OpenClaw (Xeon) - 主账户
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519

# OpenCode - 协作者账户
Host github-collab
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_collab
```

### 2. 验证 SSH 连接

```bash
# OpenClaw 应该看到: Hi linxiaowen-928!
ssh -T git@github.com

# OpenCode 应该看到: Hi linxClawBot!
ssh -T git@github-collab
```

### 3. Git 配置隔离

**OpenCode 必须在项目目录设置正确的 git 身份：**

```bash
cd ~/code/QueryCraft

# 设置 OpenCode 的 git 身份
git config user.name "linxClawBot"
git config user.email "linxclawbot@users.noreply.github.com"

# 验证配置
git config user.name  # 应该输出: linxClawBot
```

### 4. 项目远程配置

```bash
cd ~/code/QueryCraft

# 添加 linxClawBot 专用远程
git remote add github-collab git@github-collab:linxiaowen-928/QueryCraft.git

# 验证远程
git remote -v | grep github-collab
```

### 5. gh CLI 认证

OpenCode 需要使用 linxClawBot 账户认证：

```bash
gh auth login -p ssh -h github.com
# 使用 linxClawBot 的 token
```

## 使用方法

### ⚠️ 重要：启动自动化的正确方式

**当收到 /ulw-loop、心跳或任何触发命令时，必须执行以下命令：**

```bash
cd ~/code/QueryCraft/.opencode/skills/github-issue-automator
node cli.js check
```

**可用的 CLI 命令：**

| 命令 | 说明 |
|------|------|
| `node cli.js check` | 检查并处理待处理的 Issues |
| `node cli.js status` | 查看 skill 状态 |
| `node cli.js list` | 列出待处理的 Issues |
| `node cli.js work <number>` | 处理指定的 Issue |

**❌ 不要自己用 `gh issue list --label ...` 查询！**

原因：`gh issue list --label "a,b,c"` 是 AND 逻辑，而 skill 需要的是 OR 逻辑。
skill 的 `node cli.js check` 会正确处理这个逻辑。

---

### 每次工作前必须验证身份

```bash
cd ~/code/QueryCraft

# 1. 验证 git 身份
git config user.name  # 必须是 linxClawBot

# 2. 验证 SSH
ssh -T git@github-collab  # 必须是 Hi linxClawBot!

# 3. 同步代码
git pull github-collab main
```

### Git 操作规范

```bash
# ✅ 正确 - 使用 linxClawBot 身份
git push github-collab <branch>

# ❌ 错误 - 这是主账户身份
git push github <branch>
git push origin <branch>
```

### 提交 PR

```bash
# 1. 创建分支
git checkout -b issue/<number>-<title>

# 2. 提交代码
git add .
git commit -m "feat: 功能描述 (Issue #<number>)"

# 3. 推送到正确的远程
git push github-collab issue/<number>-<title>

# 4. 创建 PR
gh pr create --repo linxiaowen-928/QueryCraft \
  --title "feat: 功能描述 (Issue #<number>)" \
  --body "解决 Issue #<number>" \
  --base main
```

## 常见错误

### 错误 1: 使用了错误的账户

```
git config user.name  # 输出 linxiaowen-928
```

**修复**：
```bash
git config user.name "linxClawBot"
git config user.email "linxclawbot@users.noreply.github.com"
```

### 错误 2: 推送到了错误的远程

```
git push github main  # ❌ 这是主账户的远程
```

**修复**：
```bash
git push github-collab <branch>  # ✅ 使用 linxClawBot 的远程
```

### 错误 3: SSH 认证错误

```
ssh -T git@github-collab
# Hi linxiaowen-928! You've successfully authenticated...
```

**原因**：SSH key 配置错误

**修复**：检查 `~/.ssh/config` 中的 IdentityFile 路径

## 工作流程

```
1. 验证身份 (git config user.name == linxClawBot)
2. 验证 SSH (ssh -T git@github-collab)
3. git pull github-collab main (同步本地)
4. gh issue list (获取 Issues)
5. 分析 Issue 可实现性
6. 创建分支: issue/<number>-<title>
7. 实现修改
8. git push github-collab <branch> (推送分支)
9. gh pr create (创建 PR)
10. 继续处理下一个 Issue
11. 定期检查 PR 状态，响应审查意见
```

## PR 状态监控（重要）

提交 PR 后，需要定期检查 PR 状态并响应审查意见。

### 检查频率
- 每 30 分钟检查一次已提交的 PR 状态
- 或在空闲时间主动检查

### 检查命令

```bash
# 列出自己提交的 PR
gh pr list --repo linxiaowen-928/QueryCraft --author @me --state open

# 查看 PR 详情和评论
gh pr view <pr-number> --repo linxiaowen-928/QueryCraft

# 查看 PR 的审查评论
gh api repos/linxiaowen-928/QueryCraft/pulls/<pr-number>/comments
```

### PR 审查结果处理

| 状态 | 操作 |
|------|------|
| **APPROVED** ✅ | 等待合并，无需操作 |
| **CHANGES_REQUESTED** ❌ | 根据审查意见修改代码，重新提交 |
| **COMMENTED** 💬 | 回复评论或说明情况 |

### CR 未通过时的操作流程（重要）

**关键原则：不要创建新 PR，在同一 PR 上提交修改！**

当 PR 收到审查意见需要修改时，直接在原分支上提交新的 commit，推送到同一分支即可。GitHub 会自动更新 PR 内容。

#### 步骤详解

**1. 读取审查评论**
```bash
# 查看 PR 详情
gh pr view <pr-number> --repo linxiaowen-928/QueryCraft

# 查看审查评论
gh api repos/linxiaowen-928/QueryCraft/pulls/<pr-number>/comments
```

**2. 切换到 PR 对应的分支**
```bash
cd ~/code/QueryCraft

# 方法 1: 根据分支名切换（如果本地有）
git checkout issue/<number>-<title>

# 方法 2: 从远程拉取分支（如果本地没有）
git fetch github-collab
git checkout -b issue/<number>-<title> github-collab/issue/<number>-<title>

# 同步最新代码
git pull github-collab issue/<number>-<title>
```

**3. 根据审查意见修改代码**
- 逐条阅读审查意见
- 修改对应文件
- 本地测试确认修改正确

**4. 提交修改并推送（自动更新同一 PR）**
```bash
# 提交修改
git add .
git commit -m "fix: 根据审查意见修改 <具体问题描述>"

# 推送到同一分支（这会自动更新 PR）
git push github-collab issue/<number>-<title>
```

**推送后，GitHub 会自动更新 PR 内容，无需创建新 PR！**

**5. 回复审查评论（可选）**
```bash
# 回复说明已修复
gh pr comment <pr-number> --repo linxiaowen-928/QueryCraft --body "已修复审查意见，请重新审查"
```

#### 示例场景

**审查意见**：
> ❌ 问题: Dockerfile 健康检查使用 curl，但 python:3.11-slim 没有 curl

**修复流程**：
```bash
# 1. 切换到 PR 分支
cd ~/code/QueryCraft
git checkout issue/13-docker-deployment

# 2. 修改 Dockerfile
# 将 CMD curl 改为 CMD python -c

# 3. 提交修改
git add backend/Dockerfile
git commit -m "fix: 使用 Python 替代 curl 进行健康检查"

# 4. 推送到同一分支
git push github-collab issue/13-docker-deployment

# PR #13 会自动更新，无需创建新 PR！
```

#### 常见错误

| 错误做法 | 正确做法 |
|----------|----------|
| ❌ 创建新 PR | ✅ 在原 PR 上继续提交 |
| ❌ 删除分支重新开始 | ✅ 在同一分支上修改 |
| ❌ 新开 issue-xxx-v2 分支 | ✅ 推送到原分支 |
| ❌ git push github-collab main | ✅ git push github-collab issue/xxx |

### 重要提示

- **不要等待 PR 合并**：提交 PR 后继续处理其他 Issue
- **及时响应审查**：发现审查意见后尽快处理
- **保持分支整洁**：一个 PR 对应一个 Issue，不要混合多个功能

## 配置文件

- `config.json` - Skill 配置
- `state.json` - 运行状态（自动生成）

---
*OpenClaw Skill - GitHub Issue Automator*
*版本: 1.1.0*