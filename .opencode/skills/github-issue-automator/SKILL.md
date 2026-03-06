# GitHub Issue Automator

自动处理 GitHub Issues 的协作 Skill。

## 前置条件（必须满足）

### 1. SSH 配置

确保 `~/.ssh/config` 包含：

```
Host github-collab
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_collab
```

### 2. SSH Key 文件

- `~/.ssh/id_ed25519_collab` - 私钥
- `~/.ssh/id_ed25519_collab.pub` - 公钥

公钥已添加到 GitHub 账户 `linxClawBot`。

### 3. 验证 SSH 连接

```bash
ssh -T git@github-collab
# 应该显示: Hi linxClawBot! You've successfully authenticated...
```

### 4. Git 远程配置

在 QueryCraft 项目目录执行：

```bash
git remote add github-collab git@github-collab:linxiaowen-928/QueryCraft.git
```

### 5. gh CLI 认证

使用 linxClawBot 账户登录：

```bash
gh auth login -p ssh -h github.com
```

## 使用方法

### 工作前必须执行

```bash
# 每次工作前同步本地代码
cd ~/code/QueryCraft
git pull github-collab main
```

### 命令

```bash
cd ~/.openclaw/workspace/skills/github-issue-automator

# 查看状态
node cli.js status

# 同步仓库
node cli.js sync

# 列出待处理 Issues
node cli.js list

# 检查并处理 Issues
node cli.js check

# 处理特定 Issue
node cli.js work <issue-number>
```

## 工作流程

```
1. git pull github-collab main (同步本地)
2. gh issue list (获取 Issues)
3. 分析 Issue 可实现性
4. 创建分支: issue/<number>-<title>
5. 实现修改
6. git push github-collab <branch> (推送分支)
7. gh pr create (创建 PR)
8. 等待 @linxiaowen-928 审查
```

## 账户说明

| 账户 | 角色 | SSH 别名 | 用途 |
|------|------|----------|------|
| linxClawBot | 开发者 | github-collab | 提交 PR |
| linxiaowen-928 | 审查者 | github | 审查批准 |

## Git 操作规范

```bash
# 正确 - 使用 linxClawBot 身份
git push github-collab <branch>

# 错误 - 这是主账户身份
git push github <branch>
git push origin <branch>
```

## 配置文件

- `config.json` - Skill 配置
- `state.json` - 运行状态（自动生成）

---
*OpenClaw Skill - GitHub Issue Automator*
*版本: 1.0.0*