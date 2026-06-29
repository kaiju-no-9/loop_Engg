#!/usr/bin/env node
const { program } = require('commander');
const fs = require('fs-extra');
const path = require('path');
const { glob } = require('glob');
const Table = require('cli-table3');
const dayjs = require('dayjs');

async function main() {
  const chalk = (await import('chalk')).default;

  program
    .description('Aggregate state across all loops and render a health report')
    .argument('<dir>', 'Directory containing .loops')
    .action(async (targetDir) => {
      try {
        const loopsDir = path.resolve(targetDir, '.loops');
        if (!(await fs.pathExists(loopsDir))) {
            console.error(chalk.red(`No .loops directory found in ${targetDir}`));
            process.exit(1);
        }

        const stateFiles = await glob('*/state.json', { cwd: loopsDir, absolute: true });
        
        if (stateFiles.length === 0) {
            console.log(chalk.yellow("No state.json files found. Run some loops first!"));
            return;
        }

        const table = new Table({
            head: ['Loop', 'Status', 'Last Run', 'Cost ($)', 'Tokens', 'Commits', 'Human Wait?'],
            style: { head: ['cyan'] }
        });

        let totalCost = 0;
        let totalTokens = 0;
        let totalCommits = 0;

        let highestCostVal = -1;
        let highestCostLoop = 'None';
        let mostCommitsVal = -1;
        let mostCommitsLoop = 'None';
        const waitingLoops = [];

        for (const file of stateFiles) {
            try {
                const data = await fs.readJson(file);
                const loopName = data.loop || path.basename(path.dirname(file));
                const cost = data.cost_usd || 0;
                const tokens = data.tokens_used || 0;
                const commits = data.commits || 0;

                totalCost += cost;
                totalTokens += tokens;
                totalCommits += commits;

                if (cost > highestCostVal) {
                    highestCostVal = cost;
                    highestCostLoop = loopName;
                }
                if (commits > mostCommitsVal) {
                    mostCommitsVal = commits;
                    mostCommitsLoop = loopName;
                }
                if (data.waiting_for_human) {
                    waitingLoops.push(loopName);
                }
                
                const needsHuman = data.waiting_for_human ? chalk.bgYellow.black(' YES ') : 'NO';
                
                let lastRunDate = 'Unknown';
                if (data.run_id) {
                    const match = data.run_id.match(/^(\d{4}-\d{2}-\d{2})/);
                    if (match) {
                        lastRunDate = dayjs(match[1]).format('YYYY-MM-DD');
                    } else {
                        lastRunDate = dayjs(data.run_id).isValid() ? dayjs(data.run_id).format('YYYY-MM-DD') : data.run_id;
                    }
                }

                table.push([
                    loopName,
                    data.status === 'COMPLETE' ? chalk.green(data.status) : (data.status === 'FAILED' ? chalk.red(data.status) : data.status),
                    lastRunDate,
                    `$${cost.toFixed(2)}`,
                    tokens.toLocaleString(),
                    commits,
                    needsHuman
                ]);
            } catch (e) {
                console.warn(chalk.yellow(`Could not read ${file}`));
            }
        }
        
        console.log(chalk.blue(`\nLoop Dashboard Overview`));
        console.log(table.toString());
        
        console.log(chalk.cyan(`\nTotal Metrics:`));
        console.log(`- Cost: $${totalCost.toFixed(2)}`);
        console.log(`- Tokens: ${totalTokens.toLocaleString()}`);
        console.log(`- Commits: ${totalCommits}`);

        console.log(chalk.cyan(`\nAggregate Insights:`));
        console.log(`- Highest Cost Loop: ${highestCostLoop} ($${highestCostVal >= 0 ? highestCostVal.toFixed(2) : '0.00'})`);
        console.log(`- Most Commits Loop: ${mostCommitsLoop} (${mostCommitsVal >= 0 ? mostCommitsVal : 0} commits)`);
        if (waitingLoops.length > 0) {
            console.log(`- Loops Waiting for Human Action: ${chalk.yellow(waitingLoops.join(', '))}`);
        } else {
            console.log(`- Loops Waiting for Human Action: ${chalk.green('None')}`);
        }
        console.log();

      } catch (err) {
        console.error(chalk.red(`Error: ${err.message}`));
        process.exit(1);
      }
    });

  program.parse();
}

main();
