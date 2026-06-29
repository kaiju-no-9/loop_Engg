#!/usr/bin/env node
const { program } = require('commander');
const fs = require('fs-extra');
const path = require('path');
const yaml = require('js-yaml');
const Table = require('cli-table3');

async function main() {
  const chalk = (await import('chalk')).default;

  const MODELS = {
      'claude-sonnet': { input: 3.00, output: 15.00 },
      'claude-3.5-sonnet': { input: 3.00, output: 15.00 },
      'claude-3-5-sonnet': { input: 3.00, output: 15.00 },
      'claude-opus': { input: 15.00, output: 75.00 },
      'claude-3-opus': { input: 15.00, output: 75.00 },
      'claude-haiku': { input: 0.25, output: 1.25 },
      'claude-3-5-haiku': { input: 0.25, output: 1.25 },
      'gpt-4o': { input: 2.50, output: 10.00 },
      'gpt-4o-mini': { input: 0.15, output: 0.60 },
      'gemini-pro': { input: 1.25, output: 5.00 },
      'gemini-1.5-pro': { input: 1.25, output: 5.00 }
  };
  
  const CADENCE_MULTIPLIERS = {
      'nightly': 30, 'daily': 30, 'weekly': 4, 'hourly': 720,
      'on-pr': 20, 'on-release': 4, 'on-merge': 20,
      'on-schema-change': 4, 'on-file-change': 10, 'on-test-failure': 10,
      'on-commit': 30
  };

  program
    .description('Estimate token and dollar cost before running a loop')
    .requiredOption('--pattern <name>', 'Loop pattern name')
    .option('--cadence <freq>', 'Frequency (e.g., nightly, weekly)')
    .option('--model <model>', 'Model name', 'claude-sonnet')
    .action(async (options) => {
      try {
        const loopPath = path.resolve(__dirname, '../../loops', options.pattern);
        const loopMdPath = path.join(loopPath, 'LOOP.md');
        
        if (!(await fs.pathExists(loopMdPath))) {
            console.error(chalk.red(`Error: LOOP.md not found for pattern '${options.pattern}'`));
            process.exit(1);
        }

        const content = await fs.readFile(loopMdPath, 'utf8');
        const yamlMatch = content.match(/```yaml\n([\s\S]*?)\n```/);
        
        let maxTokens = 50000;
        let maxCost = 2.0;
        let loopCadence = options.cadence || 'nightly';
        
        if (yamlMatch) {
            try {
                const data = yaml.load(yamlMatch[1]);
                if (data.budget) {
                    if (data.budget.max_tokens) maxTokens = data.budget.max_tokens;
                    if (data.budget.max_cost_usd) maxCost = data.budget.max_cost_usd;
                }
                if (!options.cadence && data.cadence) {
                    const c = data.cadence.trim().toLowerCase();
                    if (c === 'hourly' || c.startsWith('0 * * * *')) {
                        loopCadence = 'hourly';
                    } else if (c === 'daily' || c === 'nightly' || c.startsWith('0 2 * * *') || c.startsWith('0 3 * * *') || c.startsWith('0 8 * * *') || c.startsWith('0 9 * * *')) {
                        loopCadence = 'nightly';
                    } else if (c === 'weekly' || c.match(/^0 \d+ \* \* [0-7]$/)) {
                        loopCadence = 'weekly';
                    } else if (c.includes('pr')) {
                        loopCadence = 'on-pr';
                    } else if (c.includes('release')) {
                        loopCadence = 'on-release';
                    } else if (c.includes('merge')) {
                        loopCadence = 'on-merge';
                    } else if (c.includes('schema') || c.includes('migration')) {
                        loopCadence = 'on-schema-change';
                    } else if (c.includes('file') || c.includes('contract')) {
                        loopCadence = 'on-file-change';
                    } else if (c.includes('fail') || c.includes('repair') || c.includes('test')) {
                        loopCadence = 'on-test-failure';
                    } else if (c.includes('commit') || c.includes('push') || c === 'event-driven') {
                        loopCadence = 'on-commit';
                    } else {
                        loopCadence = 'nightly';
                    }
                }
            } catch (e) {}
        }
        
        const modelRates = MODELS[options.model.toLowerCase()] || MODELS['claude-sonnet'];
        const estCostPerRun = (maxTokens * 0.8 / 1000000 * modelRates.input) + (maxTokens * 0.2 / 1000000 * modelRates.output);
        const runsPerMonth = CADENCE_MULTIPLIERS[loopCadence] || 30;
        const estCostPerMonth = estCostPerRun * runsPerMonth;
        
        console.log(chalk.blue(`Cost Estimate for ${options.pattern} using ${options.model}`));
        
        const table = new Table({
            head: ['Metric', 'Value'],
            style: { head: ['cyan'] }
        });
        
        table.push(
            ['Max Tokens/Run (Budget)', maxTokens.toLocaleString()],
            ['Max Cost/Run (Budget)', `$${maxCost.toFixed(2)}`],
            ['Est. Cost/Run', `$${Math.min(estCostPerRun, maxCost).toFixed(2)}`],
            ['Cadence', `${loopCadence} (~${runsPerMonth} runs/mo)`],
            ['Est. Cost/Month', `$${Math.min(estCostPerMonth, maxCost * runsPerMonth).toFixed(2)}`]
        );
        
        console.log(table.toString());

      } catch (err) {
        console.error(chalk.red(`Error: ${err.message}`));
        process.exit(1);
      }
    });

  program.parse();
}

main();
