#!/usr/bin/env node

'use strict';

(async () => {
  const { Command } = require('commander');
  const chalk = (await import('chalk')).default;
  const fs = require('fs-extra');
  const path = require('path');
  const yaml = require('js-yaml');

  const program = new Command();

  program
    .name('loop-init')
    .description('Scaffold a loop pattern into your project')
    .version('0.1.0')
    .argument('<target-dir>', 'Target project directory to scaffold the loop into')
    .option('--pattern <loop-name>', 'Name of the loop pattern to scaffold (e.g., ci-sweeper)')
    .option('--tool <agent-name>', 'AI agent tool to use in the workflow', 'claude-code')
    .action(async (targetDir, options) => {
      try {
        const { pattern, tool } = options;

        if (!pattern) {
          console.error(chalk.red('✗ Error: --pattern is required'));
          console.error(chalk.dim('  Usage: loop-init <target-dir> --pattern <loop-name> --tool <agent-name>'));
          process.exit(1);
        }

        const validTools = ['claude-code', 'codex', 'cursor', 'gemini-cli'];
        if (!validTools.includes(tool)) {
          console.error(chalk.red(`✗ Error: --tool must be one of: ${validTools.join(', ')}`));
          process.exit(1);
        }

        // Resolve the loop source directory from the repo's loops/ folder
        const loopsRoot = path.resolve(__dirname, '../../loops/');
        const loopSrcDir = path.join(loopsRoot, pattern);

        if (!await fs.pathExists(loopSrcDir)) {
          console.error(chalk.red(`✗ Error: Loop pattern "${pattern}" not found in ${loopsRoot}`));
          const available = await fs.readdir(loopsRoot);
          const dirs = [];
          for (const entry of available) {
            const stat = await fs.stat(path.join(loopsRoot, entry));
            if (stat.isDirectory()) dirs.push(entry);
          }
          if (dirs.length > 0) {
            console.error(chalk.yellow('\n  Available patterns:'));
            dirs.forEach(d => console.error(chalk.dim(`    - ${d}`)));
          }
          process.exit(1);
        }

        // Resolve absolute target directory
        const absTarget = path.resolve(targetDir);
        const loopDestDir = path.join(absTarget, '.loops', pattern);

        console.log(chalk.blue.bold('\n🔄 loop-init'));
        console.log(chalk.dim(`   Pattern: ${pattern}`));
        console.log(chalk.dim(`   Tool:    ${tool}`));
        console.log(chalk.dim(`   Target:  ${absTarget}\n`));

        // Copy LOOP.md, SKILL.md, STATE.md
        await fs.ensureDir(loopDestDir);

        const filesToCopy = ['LOOP.md', 'SKILL.md', 'STATE.md'];
        for (const file of filesToCopy) {
          const src = path.join(loopSrcDir, file);
          const dest = path.join(loopDestDir, file);
          if (await fs.pathExists(src)) {
            await fs.copy(src, dest);
            console.log(chalk.green(`   ✓ Copied ${file}`));
          } else {
            console.log(chalk.yellow(`   ⚠ ${file} not found in pattern — skipped`));
          }
        }

        // Parse LOOP.md for cadence
        const loopMdPath = path.join(loopSrcDir, 'LOOP.md');
        const loopMdContent = await fs.readFile(loopMdPath, 'utf8');
        let cadence = '0 2 * * *'; // default: nightly at 2am

        // Extract the YAML block from LOOP.md
        const yamlMatch = loopMdContent.match(/```yaml\n([\s\S]*?)```/);
        if (yamlMatch) {
          try {
            const loopConfig = yaml.load(yamlMatch[1]);
            if (loopConfig.cadence) {
              // Extract just the cron expression (remove inline comments)
              cadence = loopConfig.cadence.replace(/#.*$/, '').trim().replace(/^["']|["']$/g, '');
            }
          } catch (e) {
            console.log(chalk.yellow(`   ⚠ Could not parse YAML in LOOP.md — using default cadence`));
          }
        }

        // Generate GitHub Actions workflow
        const workflowDir = path.join(absTarget, '.github', 'workflows');
        await fs.ensureDir(workflowDir);

        const workflowContent = generateWorkflow(pattern, cadence, tool);
        const workflowPath = path.join(workflowDir, `${pattern}.yml`);
        await fs.writeFile(workflowPath, workflowContent, 'utf8');
        console.log(chalk.green(`   ✓ Generated workflow: .github/workflows/${pattern}.yml`));

        console.log(chalk.green.bold(`\n✅ Loop "${pattern}" scaffolded successfully!\n`));
        console.log(chalk.dim('   Next steps:'));
        console.log(chalk.dim(`   1. Review .loops/${pattern}/LOOP.md and customize for your project`));
        console.log(chalk.dim(`   2. Run ${chalk.white(`loop-audit ${targetDir}`)} to check readiness`));
        console.log(chalk.dim(`   3. Run ${chalk.white(`loop-cost --pattern ${pattern}`)} to estimate costs`));
        console.log(chalk.dim(`   4. Commit and push to enable the scheduled workflow\n`));

      } catch (err) {
        console.error(chalk.red(`\n✗ Fatal error: ${err.message}`));
        if (process.env.DEBUG) console.error(err.stack);
        process.exit(1);
      }
    });

  program.parse(process.argv);

  /**
   * Generate a GitHub Actions workflow YAML for the given loop pattern.
   */
  function generateWorkflow(pattern, cadence, tool) {
    const toolCommands = {
      'claude-code': {
        setup: `      - name: Install Claude Code\n        run: npm install -g @anthropic-ai/claude-code`,
        run: `      - name: Run Loop\n        run: claude /loop ${pattern}\n        env:\n          ANTHROPIC_API_KEY: \${{ secrets.ANTHROPIC_API_KEY }}`,
      },
      'codex': {
        setup: `      - name: Install Codex\n        run: npm install -g @openai/codex`,
        run: `      - name: Run Loop\n        run: codex --approval-mode full-auto "Run the ${pattern} loop as defined in .loops/${pattern}/LOOP.md"\n        env:\n          OPENAI_API_KEY: \${{ secrets.OPENAI_API_KEY }}`,
      },
      'cursor': {
        setup: `      - name: Setup Cursor\n        run: echo "Cursor requires desktop environment — see docs for headless setup"`,
        run: `      - name: Run Loop\n        run: cursor --loop ${pattern}\n        env:\n          CURSOR_API_KEY: \${{ secrets.CURSOR_API_KEY }}`,
      },
      'gemini-cli': {
        setup: `      - name: Install Gemini CLI\n        run: npm install -g @anthropic-ai/gemini-cli || npm install -g gemini-cli`,
        run: `      - name: Run Loop\n        run: gemini /loop ${pattern}\n        env:\n          GOOGLE_API_KEY: \${{ secrets.GOOGLE_API_KEY }}`,
      },
    };

    const toolConfig = toolCommands[tool] || toolCommands['claude-code'];

    return `# Auto-generated by loop-init — ${pattern}
# Edit this file to customize the workflow for your project.

name: "Loop: ${pattern}"

on:
  schedule:
    - cron: "${cadence}"
  workflow_dispatch:
    inputs:
      dry_run:
        description: "Run in dry-run mode (plan only, no changes)"
        required: false
        default: "false"
        type: boolean

permissions:
  contents: write
  pull-requests: write
  issues: write

jobs:
  run-loop:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

${toolConfig.setup}

${toolConfig.run}

      - name: Upload State
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: loop-state-${pattern}
          path: .loops/${pattern}/
`;
  }
})();
