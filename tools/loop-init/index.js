#!/usr/bin/env node
const { program } = require('commander');
const fs = require('fs-extra');
const path = require('path');
const yaml = require('js-yaml');

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

        const loopsBaseDir = path.resolve(__dirname, '../../loops');
        if (!patternName) {
          if (!(await fs.pathExists(loopsBaseDir))) {
            console.error(chalk.red('Error: loops/ directory not found in the project.'));
            process.exit(1);
          }
          const folders = await fs.readdir(loopsBaseDir);
          const patterns = [];
          for (const file of folders) {
            const fullPath = path.join(loopsBaseDir, file);
            if ((await fs.stat(fullPath)).isDirectory()) {
              patterns.push(file);
            }
          }

          if (patterns.length === 0) {
            console.error(chalk.red('Error: No patterns found in loops/ directory.'));
            process.exit(1);
          }

          const answers = await inquirer.prompt([
            {
              type: 'list',
              name: 'pattern',
              message: 'Select a loop pattern to scaffold:',
              choices: patterns
            }
          ]);
          patternName = answers.pattern;
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

        const sourceDir = path.resolve(loopsBaseDir, patternName);
        const destDir = path.resolve(targetDir, '.loops', patternName);

        if (!(await fs.pathExists(sourceDir))) {
          console.error(chalk.red(`Error: Pattern '${patternName}' not found.`));
          process.exit(1);
        }

        console.log(chalk.blue(`Scaffolding loop '${patternName}' into ${destDir}...`));
        
        await fs.ensureDir(destDir);
        await fs.copy(path.join(sourceDir, 'LOOP.md'), path.join(destDir, 'LOOP.md'));
        await fs.copy(path.join(sourceDir, 'SKILL.md'), path.join(destDir, 'SKILL.md'));
        await fs.copy(path.join(sourceDir, 'STATE.md'), path.join(destDir, 'STATE.md'));

        // Generate GitHub Actions workflow
        let loopMdContent = await fs.readFile(path.join(sourceDir, 'LOOP.md'), 'utf8');
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

        const workflowContent = `name: ${patternName} Loop\n\non:\n  schedule:\n    - cron: '${cronSchedule}'\n  workflow_dispatch:\n\njobs:\n  run-loop:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - name: Run Loop\n        run: ${agentTool} /loop ${patternName}\n        env:\n          ANTHROPIC_API_KEY: \${{ secrets.ANTHROPIC_API_KEY }}\n`;
        
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
