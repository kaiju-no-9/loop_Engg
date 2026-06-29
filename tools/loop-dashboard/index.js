#!/usr/bin/env node

'use strict';

(async () => {
  const { Command } = require('commander');
  const chalk = (await import('chalk')).default;
  const fs = require('fs-extra');
  const path = require('path');
  const { glob } = require('glob');
  const Table = require('cli-table3');
  const dayjs = require('dayjs');
  const relativeTime = require('dayjs/plugin/relativeTime');
  dayjs.extend(relativeTime);

  const program = new Command();

  program
    .name('loop-dashboard')
    .description('Aggregate state across all loops and render a health dashboard')
    .version('0.1.0')
    .argument('<dir>', 'Project directory containing .loops/')
    .action(async (dir) => {
      try {
        const absDir = path.resolve(dir);
        const loopsDir = path.join(absDir, '.loops');

        if (!await fs.pathExists(loopsDir)) {
          console.error(chalk.red(`\n✗ No .loops/ directory found in ${absDir}`));
          console.error(chalk.dim('  Run loop-init first to scaffold a loop into your project.\n'));
          process.exit(1);
        }

        // Find all state.json files
        const stateFiles = await glob('*/state.json', { cwd: loopsDir, absolute: false });

        if (stateFiles.length === 0) {
          console.log(chalk.yellow('\n📊 loop-dashboard'));
          console.log(chalk.dim(`   Scanning: ${loopsDir}\n`));
          console.log(chalk.yellow('   No state.json files found in .loops/*/'));
          console.log(chalk.dim('\n   state.json is auto-generated after each loop run.'));
          console.log(chalk.dim('   To see the dashboard, run your loops first:\n'));
          console.log(chalk.dim('     1. Scaffold a loop:  loop-init . --pattern ci-sweeper --tool claude-code'));
          console.log(chalk.dim('     2. Run the loop:     claude /loop ci-sweeper'));
          console.log(chalk.dim('     3. Check dashboard:  loop-dashboard .\n'));
          process.exit(0);
        }

        // Read all state.json files
        const states = [];
        for (const stateFile of stateFiles) {
          const fullPath = path.join(loopsDir, stateFile);
          try {
            const content = await fs.readFile(fullPath, 'utf8');
            const data = JSON.parse(content);
            states.push(data);
          } catch (e) {
            console.log(chalk.yellow(`   ⚠ Could not parse ${stateFile}: ${e.message}`));
          }
        }

        if (states.length === 0) {
          console.log(chalk.yellow('\n⚠ No valid state.json files found.\n'));
          process.exit(0);
        }

        // Render dashboard
        console.log(chalk.blue.bold('\n📊 loop-dashboard'));
        console.log(chalk.dim(`   Scanning: ${loopsDir}`));
        console.log(chalk.dim(`   Found:    ${states.length} loop(s)\n`));

        const table = new Table({
          head: [
            chalk.white.bold('Loop'),
            chalk.white.bold('Status'),
            chalk.white.bold('Last Run'),
            chalk.white.bold('Cost'),
            chalk.white.bold('Tokens'),
            chalk.white.bold('Commits'),
            chalk.white.bold('Human?'),
          ],
          colWidths: [22, 14, 18, 12, 12, 10, 10],
          style: { head: [], border: [] },
        });

        let totalCost = 0;
        let totalTokens = 0;
        let totalCommits = 0;
        let waitingCount = 0;

        for (const state of states) {
          const loopName = state.loop || 'unknown';
          const status = formatStatus(state.status, chalk);
          const lastRun = state.run_id
            ? chalk.dim(state.run_id)
            : chalk.dim('—');
          const cost = state.cost_usd !== undefined
            ? `$${state.cost_usd.toFixed(2)}`
            : '—';
          const tokens = state.tokens_used !== undefined
            ? state.tokens_used.toLocaleString()
            : '—';
          const commits = state.commits !== undefined
            ? state.commits.toString()
            : '—';
          const waitingForHuman = state.waiting_for_human;

          const humanCol = waitingForHuman
            ? chalk.yellow.bold('YES')
            : chalk.dim('no');

          // Apply yellow highlight for rows waiting for human action
          const row = waitingForHuman
            ? [
                chalk.yellow(loopName),
                status,
                lastRun,
                chalk.yellow(cost),
                chalk.yellow(tokens),
                chalk.yellow(commits),
                humanCol,
              ]
            : [loopName, status, lastRun, cost, tokens, commits, humanCol];

          table.push(row);

          totalCost += state.cost_usd || 0;
          totalTokens += state.tokens_used || 0;
          totalCommits += state.commits || 0;
          if (waitingForHuman) waitingCount++;
        }

        // Summary row
        table.push(
          [
            chalk.dim('─'.repeat(20)),
            chalk.dim('─'.repeat(12)),
            chalk.dim('─'.repeat(16)),
            chalk.dim('─'.repeat(10)),
            chalk.dim('─'.repeat(10)),
            chalk.dim('─'.repeat(8)),
            chalk.dim('─'.repeat(8)),
          ],
          [
            chalk.white.bold('TOTAL'),
            '',
            '',
            chalk.green.bold(`$${totalCost.toFixed(2)}`),
            chalk.cyan.bold(totalTokens.toLocaleString()),
            chalk.white.bold(totalCommits.toString()),
            waitingCount > 0 ? chalk.yellow.bold(waitingCount.toString()) : chalk.dim('0'),
          ]
        );

        console.log(table.toString());

        // Footer warnings
        if (waitingCount > 0) {
          console.log(chalk.yellow.bold(`\n⚠  ${waitingCount} loop(s) waiting for human action`));
          const waitingLoops = states.filter(s => s.waiting_for_human);
          for (const s of waitingLoops) {
            console.log(chalk.yellow(`   → ${s.loop}: review needed`));
          }
        }

        console.log();

      } catch (err) {
        console.error(chalk.red(`\n✗ Fatal error: ${err.message}`));
        if (process.env.DEBUG) console.error(err.stack);
        process.exit(1);
      }
    });

  program.parse(process.argv);

  /**
   * Format a status string with color coding.
   */
  function formatStatus(status, chalk) {
    if (!status) return chalk.dim('—');
    const upper = status.toUpperCase();
    switch (upper) {
      case 'COMPLETE':  return chalk.green.bold('COMPLETE');
      case 'SUCCESS':   return chalk.green.bold('SUCCESS');
      case 'RUNNING':   return chalk.blue.bold('RUNNING');
      case 'BLOCKED':   return chalk.yellow.bold('BLOCKED');
      case 'FAILED':    return chalk.red.bold('FAILED');
      case 'ERROR':     return chalk.red.bold('ERROR');
      default:          return chalk.white(status);
    }
  }
})();
