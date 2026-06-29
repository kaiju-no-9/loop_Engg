#!/usr/bin/env node
const { program } = require('commander');
const fs = require('fs-extra');
const path = require('path');
const yaml = require('js-yaml');
const { glob } = require('glob');

async function main() {
  const chalk = (await import('chalk')).default;

  program
    .description("Score your loop's readiness for production")
    .argument('<dir>', 'Directory containing .loops')
    .option('--suggest', 'Provide improvement suggestions')
    .action(async (targetDir, options) => {
      try {
        const loopsDir = path.resolve(targetDir, '.loops');
        if (!(await fs.pathExists(loopsDir))) {
            console.error(chalk.red(`No .loops directory found in ${targetDir}`));
            process.exit(1);
        }

        const loopPaths = await glob('*/', { cwd: loopsDir, absolute: true });
        
        if (loopPaths.length === 0) {
            console.log(chalk.yellow("No loops found to audit."));
            return;
        }

        for (const loopPath of loopPaths) {
            const loopName = path.basename(loopPath);
            console.log(chalk.blue(`\nAuditing loop: ${loopName}`));
            
            let score = 0;
            const suggestions = [];
            
            const hasState = await fs.pathExists(path.join(loopPath, 'STATE.md'));
            if (hasState) { score += 10; console.log(chalk.green('✅ State file present')); }
            else { suggestions.push('Missing STATE.md file'); console.log(chalk.red('❌ State file missing')); }

            const hasSkill = await fs.pathExists(path.join(loopPath, 'SKILL.md'));
            if (hasSkill) { score += 10; console.log(chalk.green('✅ Triage skill present')); }
            else { suggestions.push('Missing SKILL.md file (Triage skill)'); console.log(chalk.red('❌ Triage skill missing')); }

            const loopMdPath = path.join(loopPath, 'LOOP.md');
            const hasLoopMd = await fs.pathExists(loopMdPath);
            if (!hasLoopMd) {
                suggestions.push('Missing LOOP.md file'); 
                console.log(chalk.red('❌ LOOP.md missing'));
                console.log(chalk.yellow(`Score: ${score}/100`));
                continue;
            }
            score += 10; console.log(chalk.green('✅ LOOP.md exists'));
            
            const content = await fs.readFile(loopMdPath, 'utf8');
            const yamlMatch = content.match(/```yaml\n([\s\S]*?)\n```/);
            
            if (yamlMatch) {
                try {
                    const data = yaml.load(yamlMatch[1]);
                    
                    if (data.verifier && data.verifier.command) { score += 15; console.log(chalk.green('✅ Verifier defined (maker-checker)')); }
                    else { suggestions.push('Define a verifier command'); console.log(chalk.red('❌ Verifier missing')); }
                    
                    if (data.cadence) { score += 10; console.log(chalk.green('✅ LOOP.md has cadence and gates')); }
                    else { suggestions.push('Define a cadence'); console.log(chalk.red('❌ Cadence missing')); }
                    
                    if (data.budget && data.budget.max_cost_usd) { score += 10; console.log(chalk.green('✅ Budget cap set')); }
                    else { suggestions.push('Set a budget cap (max_cost_usd)'); console.log(chalk.red('❌ Budget cap missing')); }
                    
                    if (data.approval_required_for && data.approval_required_for.length > 0) { score += 10; console.log(chalk.green('✅ Approval gates on destructive actions')); }
                    else { suggestions.push('Add approval_required_for rules'); console.log(chalk.red('❌ Approval gates missing')); }
                    
                    if (data.file_scope) { score += 10; console.log(chalk.green('✅ File scope defined')); }
                    else { suggestions.push('Define file_scope'); console.log(chalk.red('❌ File scope missing')); }
                    
                    if (data.termination && data.termination.success && data.termination.failure) { score += 10; console.log(chalk.green('✅ Termination conditions defined')); }
                    else { suggestions.push('Add comprehensive termination conditions'); console.log(chalk.red('❌ Termination conditions incomplete')); }
                    
                    if (data.recovery) { score += 5; console.log(chalk.green('✅ Recovery strategy defined')); }
                    else { suggestions.push('Define recovery strategy'); console.log(chalk.red('❌ Recovery strategy missing')); }

                    const hasWorktree = data.worktree_isolation === true || data.worktree === true;
                    if (hasWorktree) {
                        console.log(chalk.green('✅ Worktree isolation enabled'));
                    } else {
                        console.log(chalk.yellow('⚠️ No worktree isolation — suggestion: add this before L3'));
                        suggestions.push('Enable worktree isolation (worktree_isolation: true) before moving to L3 of trust ramp');
                    }
                    
                } catch (e) {
                    console.log(chalk.red('❌ Could not parse LOOP.md YAML config'));
                    suggestions.push('Fix YAML syntax in LOOP.md');
                }
            } else {
                 console.log(chalk.red('❌ Could not find YAML config block in LOOP.md'));
                 suggestions.push('Add a YAML config block to LOOP.md');
            }
            
            console.log(chalk.bold(`Score: ${score}/100`));
            
            if (options.suggest && suggestions.length > 0) {
                console.log(chalk.yellow('\nSuggestions for improvement:'));
                suggestions.forEach(s => console.log(chalk.yellow(`- ${s}`)));
            }
        }
      } catch (err) {
        console.error(chalk.red(`Error: ${err.message}`));
        process.exit(1);
      }
    });

  program.parse();
}

main();
