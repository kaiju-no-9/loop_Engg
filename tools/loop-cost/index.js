#!/usr/bin/env node

'use strict';

(async () => {
  const { Command } = require('commander');
  const chalk = (await import('chalk')).default;
  const fs = require('fs-extra');
  const path = require('path');
  const yaml = require('js-yaml');
  const Table = require('cli-table3');

  // Model pricing: cost per 1M tokens
  const MODEL_PRICING = {
    'claude-sonnet': { input: 3.00, output: 15.00 },
    'claude-opus':   { input: 15.00, output: 75.00 },
    'gpt-4o':        { input: 2.50, output: 10.00 },
    'gpt-4o-mini':   { input: 0.15, output: 0.60 },
    'gemini-pro':    { input: 1.25, output: 5.00 },
  };

  // Cadence to runs-per-month multiplier
  const CADENCE_MULTIPLIERS = {
    'nightly':  30,
    'daily':    30,
    'weekly':   4,
    'hourly':   720,
    'on-pr':    20,
  };

  const program = new Command();

  program
    .name('loop-cost')
    .description('Estimate token and dollar cost before running a loop')
    .version('0.1.0')
    .requiredOption('--pattern <name>', 'Name of the loop pattern to estimate costs for')
    .option('--cadence <freq>', 'Override cadence (nightly, daily, weekly, hourly, on-pr)')
    .option('--model <model>', 'Model to use for pricing', 'claude-sonnet')
    .action(async (options) => {
      try {
        const { pattern, model } = options;

        // Validate model
        if (!MODEL_PRICING[model]) {
          console.error(chalk.red(`\n✗ Unknown model: "${model}"`));
          console.error(chalk.dim(`  Available models: ${Object.keys(MODEL_PRICING).join(', ')}\n`));
          process.exit(1);
        }

        // Resolve the loop directory
        const loopsRoot = path.resolve(__dirname, '../../loops/');
        const loopDir = path.join(loopsRoot, pattern);

        if (!await fs.pathExists(loopDir)) {
          console.error(chalk.red(`\n✗ Loop pattern "${pattern}" not found in ${loopsRoot}`));
          process.exit(1);
        }

        const loopMdPath = path.join(loopDir, 'LOOP.md');
        if (!await fs.pathExists(loopMdPath)) {
          console.error(chalk.red(`\n✗ LOOP.md not found in ${loopDir}`));
          process.exit(1);
        }

        // Parse LOOP.md
        const content = await fs.readFile(loopMdPath, 'utf8');
        const yamlMatch = content.match(/```yaml\n([\s\S]*?)```/);
        let loopConfig = {};
        if (yamlMatch) {
          try {
            loopConfig = yaml.load(yamlMatch[1]);
          } catch (e) {
            console.error(chalk.yellow('⚠ Could not parse YAML block in LOOP.md — using defaults'));
          }
        }

        // Extract budget info
        const maxTokens = (loopConfig.budget && loopConfig.budget.max_tokens) || 50000;
        const maxCostUsd = (loopConfig.budget && loopConfig.budget.max_cost_usd) || 2.00;

        // Determine cadence
        let cadenceLabel = options.cadence;
        if (!cadenceLabel && loopConfig.cadence) {
          // Infer cadence label from cron expression
          cadenceLabel = inferCadenceLabel(loopConfig.cadence);
        }
        if (!cadenceLabel) cadenceLabel = 'nightly';

        if (!CADENCE_MULTIPLIERS[cadenceLabel]) {
          console.error(chalk.red(`\n✗ Unknown cadence: "${cadenceLabel}"`));
          console.error(chalk.dim(`  Available: ${Object.keys(CADENCE_MULTIPLIERS).join(', ')}\n`));
          process.exit(1);
        }

        const runsPerMonth = CADENCE_MULTIPLIERS[cadenceLabel];
        const pricing = MODEL_PRICING[model];

        // Estimate: assume 70% input tokens, 30% output tokens per run
        const inputTokens = Math.round(maxTokens * 0.7);
        const outputTokens = Math.round(maxTokens * 0.3);

        const inputCost = (inputTokens / 1_000_000) * pricing.input;
        const outputCost = (outputTokens / 1_000_000) * pricing.output;
        const costPerRun = inputCost + outputCost;
        const costPerMonth = costPerRun * runsPerMonth;

        // Render output
        console.log(chalk.blue.bold('\n💰 loop-cost'));
        console.log(chalk.dim(`   Pattern:  ${pattern}`));
        console.log(chalk.dim(`   Model:    ${model}`));
        console.log(chalk.dim(`   Cadence:  ${cadenceLabel} (${runsPerMonth} runs/month)`));
        console.log(chalk.dim(`   Budget:   $${maxCostUsd.toFixed(2)}/run cap, ${maxTokens.toLocaleString()} tokens/run cap`));
        console.log();

        const table = new Table({
          head: [
            chalk.white.bold('Metric'),
            chalk.white.bold('Value'),
          ],
          colWidths: [35, 25],
          style: { head: [], border: [] },
        });

        table.push(
          ['Estimated input tokens/run', chalk.cyan(inputTokens.toLocaleString())],
          ['Estimated output tokens/run', chalk.cyan(outputTokens.toLocaleString())],
          ['Total tokens/run', chalk.cyan(maxTokens.toLocaleString())],
          [chalk.dim('─'.repeat(33)), chalk.dim('─'.repeat(23))],
          ['Input cost/run', chalk.green(`$${inputCost.toFixed(4)}`)],
          ['Output cost/run', chalk.green(`$${outputCost.toFixed(4)}`)],
          ['Total cost/run', chalk.green.bold(`$${costPerRun.toFixed(4)}`)],
          [chalk.dim('─'.repeat(33)), chalk.dim('─'.repeat(23))],
          ['Runs/month', chalk.yellow(runsPerMonth.toString())],
          ['Estimated cost/month', chalk.green.bold(`$${costPerMonth.toFixed(2)}`)],
          ['Budget cap/run', chalk.red(`$${maxCostUsd.toFixed(2)}`)],
        );

        console.log(table.toString());

        // Warning if estimated cost exceeds budget
        if (costPerRun > maxCostUsd) {
          console.log(chalk.red.bold(`\n⚠  Estimated cost/run ($${costPerRun.toFixed(4)}) exceeds budget cap ($${maxCostUsd.toFixed(2)})!`));
          console.log(chalk.dim('   The loop will terminate early due to budget_exhausted.\n'));
        } else {
          const utilization = ((costPerRun / maxCostUsd) * 100).toFixed(1);
          console.log(chalk.dim(`\n   Budget utilization: ${utilization}% of $${maxCostUsd.toFixed(2)} cap per run`));
          console.log();
        }

      } catch (err) {
        console.error(chalk.red(`\n✗ Fatal error: ${err.message}`));
        if (process.env.DEBUG) console.error(err.stack);
        process.exit(1);
      }
    });

  program.parse(process.argv);

  /**
   * Infer a human-readable cadence label from a cron expression.
   */
  function inferCadenceLabel(cronExpr) {
    // Clean inline comments
    const cron = cronExpr.replace(/#.*$/, '').trim().replace(/^["']|["']$/g, '');
    const parts = cron.split(/\s+/);
    if (parts.length < 5) return 'nightly';

    const [minute, hour, dom, month, dow] = parts;

    // Hourly: minute is fixed, hour is *
    if (hour === '*' && dom === '*' && month === '*' && dow === '*') return 'hourly';
    // Daily/nightly: specific hour, * for the rest
    if (hour !== '*' && dom === '*' && month === '*' && dow === '*') return 'nightly';
    // Weekly: specific dow
    if (dom === '*' && month === '*' && dow !== '*') return 'weekly';

    return 'nightly';
  }
})();
