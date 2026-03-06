#!/usr/bin/env node
/**
 * GitHub Issue Automator CLI
 */

const { GitHubIssueAutomator } = require('./index');

const automator = new GitHubIssueAutomator();

const command = process.argv[2];
const args = process.argv.slice(3);

async function main() {
    switch (command) {
        case 'check':
            const result = await automator.run();
            console.log(JSON.stringify(result, null, 2));
            break;
            
        case 'status':
            console.log(JSON.stringify(automator.getStatus(), null, 2));
            break;
            
        case 'set-workdir':
            if (!args[0]) {
                console.error('用法: qc-issues set-workdir <目录路径>');
                process.exit(1);
            }
            automator.setWorkDir(args[0]);
            console.log('工作目录已设置');
            break;
            
        case 'sync':
            const synced = await automator.syncRepo();
            console.log(synced ? '同步成功' : '同步失败');
            break;
            
        case 'list':
            const issues = await automator.getIssues();
            console.log('待处理 Issues:');
            issues.forEach(issue => {
                const analysis = automator.analyzeIssue(issue);
                console.log(`  #${issue.number} [${analysis.difficulty}] ${issue.title}`);
            });
            break;
            
        case 'work':
            if (!args[0]) {
                console.error('用法: qc-issues work <issue-number>');
                process.exit(1);
            }
            // 获取指定 issue
            const allIssues = await automator.getIssues();
            const targetIssue = allIssues.find(i => i.number === parseInt(args[0]));
            if (!targetIssue) {
                console.error('Issue 未找到');
                process.exit(1);
            }
            const work = await automator.processIssue(targetIssue);
            console.log(JSON.stringify(work, null, 2));
            break;
            
        default:
            console.log(`
GitHub Issue Automator

用法:
  qc-issues check              检查并处理 Issues
  qc-issues status             查看状态
  qc-issues set-workdir <dir>  设置工作目录
  qc-issues sync               同步本地仓库
  qc-issues list               列出待处理 Issues
  qc-issues work <number>      处理指定 Issue

注意:
  - 工作前会自动 git pull 同步代码
  - 使用 linxClawBot 账户提交 PR
  - PR 需要审查者批准
            `);
    }
}

main().catch(console.error);