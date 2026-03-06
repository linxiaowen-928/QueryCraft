/**
 * GitHub Issue Automator
 * 
 * 自动处理 GitHub Issues 的协作 Skill
 * 
 * 功能：
 * 1. 定时检查指定仓库的 Issues
 * 2. 分析 Issue 可实现性
 * 3. 创建分支、修改代码、提交 PR
 * 
 * 使用 linxClawBot 账户操作
 */

const { execSync, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

// 配置
const CONFIG_PATH = path.join(__dirname, 'config.json');
const STATE_PATH = path.join(__dirname, 'state.json');

class GitHubIssueAutomator {
    constructor() {
        this.config = this.loadConfig();
        this.state = this.loadState();
    }

    /**
     * 加载配置
     */
    loadConfig() {
        try {
            return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
        } catch (e) {
            return {
                repository: "linxiaowen-928/QueryCraft",
                ssh_alias: "github-collab",
                github_user: "linxClawBot",
                check_interval_hours: 1,
                labels_to_process: ["help wanted", "good first issue", "enhancement", "bug"],
                max_issues_per_run: 3,
                work_dir: null,
                reviewer: "linxiaowen-928"
            };
        }
    }

    /**
     * 加载状态
     */
    loadState() {
        try {
            return JSON.parse(fs.readFileSync(STATE_PATH, 'utf8'));
        } catch (e) {
            return {
                last_check: null,
                processed_issues: [],
                current_work: null
            };
        }
    }

    /**
     * 保存状态
     */
    saveState() {
        fs.writeFileSync(STATE_PATH, JSON.stringify(this.state, null, 2));
    }

    /**
     * 设置工作目录
     */
    setWorkDir(dir) {
        this.config.work_dir = dir;
        fs.writeFileSync(CONFIG_PATH, JSON.stringify(this.config, null, 2));
        console.log(`[IssueAutomator] 工作目录设置为: ${dir}`);
    }

    /**
     * 检查是否需要工作
     */
    shouldWork() {
        if (!this.state.last_check) return true;
        
        const lastCheck = new Date(this.state.last_check);
        const now = new Date();
        const hoursSinceLastCheck = (now - lastCheck) / (1000 * 60 * 60);
        
        return hoursSinceLastCheck >= this.config.check_interval_hours;
    }

    /**
     * 验证 Git 身份
     */
    async verifyGitIdentity() {
        if (!this.config.work_dir) {
            console.error('[IssueAutomator] 工作目录未设置');
            return false;
        }

        try {
            // 检查 git user.name
            const userName = execSync('git config user.name', {
                cwd: this.config.work_dir,
                encoding: 'utf8'
            }).trim();

            // 检查 git user.email
            const userEmail = execSync('git config user.email', {
                cwd: this.config.work_dir,
                encoding: 'utf8'
            }).trim();

            if (userName !== this.config.github_user) {
                console.error(`[IssueAutomator] ❌ Git 身份错误! 当前: ${userName}, 应该是: ${this.config.github_user}`);
                console.log(`[IssueAutomator] 修复方法: git config user.name "${this.config.github_user}"`);
                return false;
            }

            if (this.config.git_email && userEmail !== this.config.git_email) {
                console.error(`[IssueAutomator] ❌ Git email 错误! 当前: ${userEmail}, 应该是: ${this.config.git_email}`);
                console.log(`[IssueAutomator] 修复方法: git config user.email "${this.config.git_email}"`);
                return false;
            }

            console.log(`[IssueAutomator] ✅ Git 身份正确: ${userName} <${userEmail}>`);
            return true;
        } catch (e) {
            console.error('[IssueAutomator] Git 身份验证失败:', e.message);
            return false;
        }
    }

    /**
     * 验证 SSH 连接
     */
    async verifySSH() {
        try {
            const result = execSync(`ssh -T git@${this.config.ssh_alias} 2>&1`, {
                encoding: 'utf8',
                timeout: 10000
            });

            if (result.includes(this.config.github_user)) {
                console.log(`[IssueAutomator] ✅ SSH 认证正确: ${this.config.github_user}`);
                return true;
            } else {
                console.error(`[IssueAutomator] ❌ SSH 认证错误! 应该是 ${this.config.github_user}`);
                console.log(`[IssueAutomator] SSH 输出: ${result}`);
                return false;
            }
        } catch (e) {
            // SSH 认证成功也会返回非零退出码
            if (e.stdout && e.stdout.includes(this.config.github_user)) {
                console.log(`[IssueAutomator] ✅ SSH 认证正确: ${this.config.github_user}`);
                return true;
            }
            console.error('[IssueAutomator] SSH 验证失败:', e.message);
            return false;
        }
    }

    /**
     * 设置正确的 Git 身份
     */
    async setGitIdentity() {
        if (!this.config.work_dir) {
            console.error('[IssueAutomator] 工作目录未设置');
            return false;
        }

        try {
            execSync(`git config user.name "${this.config.github_user}"`, {
                cwd: this.config.work_dir
            });
            execSync(`git config user.email "${this.config.git_email}"`, {
                cwd: this.config.work_dir
            });
            console.log(`[IssueAutomator] ✅ Git 身份已设置: ${this.config.github_user}`);
            return true;
        } catch (e) {
            console.error('[IssueAutomator] 设置 Git 身份失败:', e.message);
            return false;
        }
    }

    /**
     * 同步本地仓库
     */
    async syncRepo() {
        if (!this.config.work_dir) {
            throw new Error('工作目录未设置，请先设置 work_dir');
        }

        console.log('[IssueAutomator] 同步本地仓库...');
        
        try {
            // 切换到 main 分支
            execSync('git checkout main', { cwd: this.config.work_dir });
            
            // Pull 最新代码
            execSync(`git pull ${this.config.ssh_alias} main`, { 
                cwd: this.config.work_dir,
                encoding: 'utf8'
            });
            
            console.log('[IssueAutomator] 本地仓库已同步');
            return true;
        } catch (e) {
            console.error('[IssueAutomator] 同步失败:', e.message);
            return false;
        }
    }

    /**
     * 获取 Issues 列表
     */
    async getIssues() {
        console.log('[IssueAutomator] 获取 Issues...');
        
        try {
            const result = execSync(
                `gh issue list --repo ${this.config.repository} --state open --json number,title,labels,body --limit 20`,
                { encoding: 'utf8' }
            );
            
            const issues = JSON.parse(result);
            
            // 过滤已处理的
            const unprocessed = issues.filter(issue => 
                !this.state.processed_issues.includes(issue.number)
            );
            
            // 过滤标签
            const labeled = unprocessed.filter(issue => {
                if (!this.config.labels_to_process || this.config.labels_to_process.length === 0) {
                    return true;
                }
                return issue.labels.some(label => 
                    this.config.labels_to_process.includes(label.name)
                );
            });
            
            console.log(`[IssueAutomator] 发现 ${labeled.length} 个待处理 Issue`);
            return labeled.slice(0, this.config.max_issues_per_run);
            
        } catch (e) {
            console.error('[IssueAutomator] 获取 Issues 失败:', e.message);
            return [];
        }
    }

    /**
     * 分析 Issue 可实现性
     */
    analyzeIssue(issue) {
        const text = `${issue.title} ${issue.body || ''}`.toLowerCase();
        
        // 简单的可实现性分析
        const keywords = {
            easy: ['typo', 'fix', 'update', 'add', 'remove', '简单', '修复', '添加'],
            medium: ['implement', 'feature', 'enhance', '实现', '功能', '优化'],
            hard: ['refactor', 'architecture', 'redesign', '重构', '架构']
        };
        
        let difficulty = 'medium';
        let confidence = 50;
        
        if (keywords.easy.some(k => text.includes(k))) {
            difficulty = 'easy';
            confidence = 80;
        } else if (keywords.hard.some(k => text.includes(k))) {
            difficulty = 'hard';
            confidence = 30;
        }
        
        // 检查是否有明确的实现方向
        if (text.includes('how to') || text.includes('如何') || text.includes('建议')) {
            confidence += 20;
        }
        
        return {
            difficulty,
            confidence: Math.min(100, confidence),
            implementable: confidence >= 50
        };
    }

    /**
     * 处理 Issue
     */
    async processIssue(issue) {
        console.log(`[IssueAutomator] 处理 Issue #${issue.number}: ${issue.title}`);
        
        const analysis = this.analyzeIssue(issue);
        
        if (!analysis.implementable) {
            console.log(`[IssueAutomator] Issue #${issue.number} 可信度不足 (${analysis.confidence}%)，跳过`);
            return null;
        }
        
        console.log(`[IssueAutomator] Issue 难度: ${analysis.difficulty}, 可信度: ${analysis.confidence}%`);
        
        // 创建分支
        const branchName = `issue/${issue.number}-${issue.title.toLowerCase().replace(/[^a-z0-9]/g, '-').slice(0, 30)}`;
        
        try {
            execSync(`git checkout -b ${branchName}`, { 
                cwd: this.config.work_dir,
                encoding: 'utf8'
            });
            
            console.log(`[IssueAutomator] 创建分支: ${branchName}`);
            
            // 记录当前工作
            this.state.current_work = {
                issue_number: issue.number,
                branch: branchName,
                started_at: new Date().toISOString()
            };
            this.saveState();
            
            return {
                issue,
                branch: branchName,
                analysis
            };
            
        } catch (e) {
            console.error('[IssueAutomator] 创建分支失败:', e.message);
            return null;
        }
    }

    /**
     * 提交 PR
     */
    async createPR(issue, branch, description) {
        console.log(`[IssueAutomator] 提交 PR for Issue #${issue.number}`);
        
        try {
            // 推送分支
            execSync(`git push ${this.config.ssh_alias} ${branch}`, {
                cwd: this.config.work_dir,
                encoding: 'utf8'
            });
            
            // 创建 PR
            const prBody = `## 解决 Issue #${issue.number}

### 原始 Issue
${issue.title}

${issue.body || ''}

### 实现说明
${description}

---
*此 PR 由 linxClawBot 自动创建，请 @${this.config.reviewer} 审查*`;

            const result = execSync(
                `gh pr create --repo ${this.config.repository} --title "fix: ${issue.title}" --body "${prBody.replace(/"/g, '\\"').replace(/\n/g, '\\n')}" --base main --head ${branch}`,
                { encoding: 'utf8' }
            );
            
            console.log(`[IssueAutomator] PR 已创建: ${result.trim()}`);
            
            // 标记为已处理
            this.state.processed_issues.push(issue.number);
            this.state.current_work = null;
            this.saveState();
            
            return result.trim();
            
        } catch (e) {
            console.error('[IssueAutomator] 创建 PR 失败:', e.message);
            return null;
        }
    }

    /**
     * 运行检查周期
     */
    async run() {
        console.log('[IssueAutomator] 开始运行...');
        
        // 检查工作目录
        if (!this.config.work_dir) {
            console.log('[IssueAutomator] 等待工作目录设置...');
            return { status: 'waiting_for_workdir' };
        }

        // 验证 Git 身份
        const gitIdentityOk = await this.verifyGitIdentity();
        if (!gitIdentityOk) {
            console.log('[IssueAutomator] 尝试自动修复 Git 身份...');
            await this.setGitIdentity();
            const retryOk = await this.verifyGitIdentity();
            if (!retryOk) {
                return { status: 'git_identity_error' };
            }
        }

        // 验证 SSH 连接
        const sshOk = await this.verifySSH();
        if (!sshOk) {
            console.error('[IssueAutomator] SSH 认证失败，请检查 ~/.ssh/config');
            return { status: 'ssh_auth_error' };
        }
        
        // 检查是否需要工作
        if (!this.shouldWork()) {
            console.log('[IssueAutomator] 未到检查时间');
            return { status: 'not_yet' };
        }
        
        // 同步仓库
        const synced = await this.syncRepo();
        if (!synced) {
            return { status: 'sync_failed' };
        }
        
        // 获取 Issues
        const issues = await this.getIssues();
        
        if (issues.length === 0) {
            this.state.last_check = new Date().toISOString();
            this.saveState();
            return { status: 'no_issues', processed: 0 };
        }
        
        // 处理第一个 Issue
        const work = await this.processIssue(issues[0]);
        
        this.state.last_check = new Date().toISOString();
        this.saveState();
        
        return {
            status: 'working',
            issue: issues[0],
            work
        };
    }

    /**
     * 获取状态报告
     */
    getStatus() {
        return {
            config: this.config,
            state: this.state,
            next_check: this.state.last_check 
                ? new Date(new Date(this.state.last_check).getTime() + this.config.check_interval_hours * 60 * 60 * 1000)
                : 'now'
        };
    }
}

module.exports = { GitHubIssueAutomator };