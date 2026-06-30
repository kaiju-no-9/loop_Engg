#!/usr/bin/env node
const { program } = require('commander');
const fs = require('fs-extra');
const path = require('path');
const yaml = require('js-yaml');

const RAW_REPO_URL = 'https://raw.githubusercontent.com/kaiju-no-9/loop_Engg/main';

async function main() {
  const chalk = (await import('chalk')).default;
  const inquirer = (await import('inquirer')).default;

  program
    .description('Scaffold a loop into your project')
    .argument('<target-dir>', 'Directory to initialize the loop in')
    .option('--pattern <name>', 'Name of the loop pattern to scaffold')
    .option('--tool <agent>', 'Agent tool to use (e.g., claude-code)')
    .action(async (targetDir, options) => {
      try {
        let patternName = options.pattern;
        let agentTool = options.tool;

        // Fetch patterns from remote registry
        console.log(chalk.blue('Fetching loop registry from remote repository...'));
        let patterns = [];
        try {
          const registryRes = await fetch(`${RAW_REPO_URL}/patterns/registry.yaml`);
          if (!registryRes.ok) {
            throw new Error(`HTTP ${registryRes.status}`);
          }
          const registryText = await registryRes.text();
          const registry = yaml.load(registryText);
          if (registry && Array.isArray(registry.loops)) {
            patterns = registry.loops.map(l => l.name);
          }
        } catch (e) {
          console.error(chalk.red(`Failed to fetch loop registry: ${e.message}`));
          process.exit(1);
        }

        if (patterns.length === 0) {
          console.error(chalk.red('Error: No patterns found in loop registry.'));
          process.exit(1);
        }

        if (!patternName) {
          const answers = await inquirer.prompt([
            {
              type: 'list',
              name: 'pattern',
              message: 'Select a loop pattern to scaffold:',
              choices: patterns
            }
          ]);
          patternName = answers.pattern;
        } else if (!patterns.includes(patternName)) {
          console.error(chalk.red(`Error: Pattern '${patternName}' is not a valid pattern in the registry.`));
          console.log(chalk.yellow(`Available patterns: ${patterns.join(', ')}`));
          process.exit(1);
        }

        if (!agentTool) {
          const answers = await inquirer.prompt([
            {
              type: 'list',
              name: 'tool',
              message: 'Select the agent tool to use:',
              choices: ['claude-code', 'gemini-cli', 'cursor', 'codex']
            }
          ]);
          agentTool = answers.tool;
        }

        const destDir = path.resolve(targetDir, '.loops', patternName);
        console.log(chalk.blue(`Scaffolding loop '${patternName}' into ${destDir}...`));
        await fs.ensureDir(destDir);

        const filesToFetch = ['LOOP.md', 'SKILL.md', 'STATE.md'];
        for (const file of filesToFetch) {
          const fileUrl = `${RAW_REPO_URL}/loops/${patternName}/${file}`;
          console.log(chalk.gray(`Fetching ${file}...`));
          const fileRes = await fetch(fileUrl);
          if (!fileRes.ok) {
            throw new Error(`Failed to fetch ${file} for pattern ${patternName} (HTTP ${fileRes.status})`);
          }
          const content = await fileRes.text();
          await fs.writeFile(path.join(destDir, file), content);
        }

        // Generate GitHub Actions workflow
        let loopMdContent = await fs.readFile(path.join(destDir, 'LOOP.md'), 'utf8');
        let cronSchedule = "0 2 * * *"; // default
        
        const yamlMatch = loopMdContent.match(/```yaml\n([\s\S]*?)\n```/);
        if (yamlMatch) {
            try {
                const loopData = yaml.load(yamlMatch[1]);
                if (loopData.cadence) cronSchedule = loopData.cadence;
            } catch (e) {
                console.warn(chalk.yellow('Warning: Could not parse LOOP.md to extract cadence. Using default.'));
            }
        }

        let envBlock = '';
        if (agentTool === 'claude-code') {
          envBlock = '          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}';
        } else if (agentTool === 'gemini-cli') {
          envBlock = '          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}';
        } else if (agentTool === 'codex') {
          envBlock = '          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}';
        } else if (agentTool === 'cursor') {
          envBlock = '          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}\n          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}';
        } else {
          envBlock = '          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}';
        }

        const workflowContent = `name: ${patternName} Loop\n\non:\n  schedule:\n    - cron: '${cronSchedule}'\n  workflow_dispatch:\n\njobs:\n  run-loop:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - name: Run Loop\n        run: ${agentTool} /loop ${patternName}\n        env:\n${envBlock}\n`;
        
        const workflowDir = path.resolve(targetDir, '.github/workflows');
        await fs.ensureDir(workflowDir);
        await fs.writeFile(path.join(workflowDir, `${patternName}.yml`), workflowContent);

        console.log(chalk.green(`Successfully initialized '${patternName}'.`));
      } catch (err) {
        console.error(chalk.red(`Error: ${err.message}`));
        process.exit(1);
      }
    });

  program.parse();
}

main();
