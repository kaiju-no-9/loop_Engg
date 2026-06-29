#!/usr/bin/env node

'use strict';

(async () => {
  const { Command } = require('commander');
  const chalk = (await import('chalk')).default;
  const fs = require('fs-extra');
  const path = require('path');
  const yaml = require('js-yaml');
  const { glob } = require('glob');

  const program = new Command();

  program
    .name('loop-audit')
    .description('Score your loop\'s production readiness (0–100)')
    .version('0.1.0')
    .argument('<dir>', 'Project directory containing .loops/')
    .option('--suggest', 'Print improvement suggestions for missing items')
    .action(async (dir, options) => {
      try {
        const absDir = path.resolve(dir);
        const loopsDir = path.join(absDir, '.loops');

        if (!await fs.pathExists(loopsDir)) {
          console.error(chalk.red(`\n✗ No .loops/ directory found in ${absDir}`));
          console.error(chalk.dim('  Run loop-init first to scaffold a loop into your project.\n'));
          process.exit(1);
        }

        // Discover loop directories
        const entries = await fs.readdir(loopsDir);
        const loopDirs = [];
        for (const entry of entries) {
          const full = path.join(loopsDir, entry);
          const stat = await fs.stat(full);
          if (stat.isDirectory()) loopDirs.push(entry);
        }

        if (loopDirs.length === 0) {
          console.error(chalk.yellow('\n⚠ No loop directories found in .loops/'));
          console.error(chalk.dim('  Expected directories like .loops/ci-sweeper/\n'));
          process.exit(1);
        }

        console.log(chalk.blue.bold('\n🔍 loop-audit'));
        console.log(chalk.dim(`   Scanning: ${loopsDir}\n`));

        let allPassed = true;

        for (const loopName of loopDirs) {
          const loopDir = path.join(loopsDir, loopName);
          const result = await auditLoop(loopName, loopDir, options.suggest);
          if (result.score < 80) allPassed = false;
        }

        if (allPassed) {
          console.log(chalk.green.bold('✅ All loops score 80+ — ready for production!\n'));
        } else {
          console.log(chalk.yellow.bold('⚠  Some loops score below 80 — review suggestions above.\n'));
        }

      } catch (err) {
        console.error(chalk.red(`\n✗ Fatal error: ${err.message}`));
        if (process.env.DEBUG) console.error(err.stack);
        process.exit(1);
      }
    });

  program.parse(process.argv);

  /**
   * Audit a single loop directory and return its score.
   */
  async function auditLoop(loopName, loopDir, showSuggestions) {
    const checks = [];
    const suggestions = [];
    let score = 0;

    // --- File existence checks ---

    // STATE.md (10 pts)
    const hasState = await fs.pathExists(path.join(loopDir, 'STATE.md'));
    checks.push({ name: 'STATE.md exists', points: 10, passed: hasState });
    if (hasState) score += 10;
    else suggestions.push('Create a STATE.md file to track loop execution state');

    // SKILL.md (10 pts)
    const hasSkill = await fs.pathExists(path.join(loopDir, 'SKILL.md'));
    checks.push({ name: 'SKILL.md exists', points: 10, passed: hasSkill });
    if (hasSkill) score += 10;
    else suggestions.push('Create a SKILL.md file to define the agent\'s triage skill');

    // LOOP.md (10 pts)
    const hasLoop = await fs.pathExists(path.join(loopDir, 'LOOP.md'));
    checks.push({ name: 'LOOP.md exists', points: 10, passed: hasLoop });
    if (hasLoop) score += 10;
    else suggestions.push('Create a LOOP.md file — this is the core loop definition');

    // --- LOOP.md content checks (only if LOOP.md exists) ---
    let loopConfig = null;
    if (hasLoop) {
      const content = await fs.readFile(path.join(loopDir, 'LOOP.md'), 'utf8');
      const yamlMatch = content.match(/```yaml\n([\s\S]*?)```/);
      if (yamlMatch) {
        try {
          loopConfig = yaml.load(yamlMatch[1]);
        } catch (e) {
          console.log(chalk.yellow(`   ⚠ Could not parse YAML block in ${loopName}/LOOP.md`));
        }
      }
    }

    // Verifier with command (15 pts)
    const hasVerifier = loopConfig &&
      loopConfig.verifier &&
      loopConfig.verifier.command;
    checks.push({ name: 'Verifier with command defined', points: 15, passed: !!hasVerifier });
    if (hasVerifier) score += 15;
    else suggestions.push('Add a verifier.command to LOOP.md (e.g., "npm test") — this is how the loop knows it succeeded');

    // Cadence (10 pts)
    const hasCadence = loopConfig && loopConfig.cadence;
    checks.push({ name: 'Cadence defined', points: 10, passed: !!hasCadence });
    if (hasCadence) score += 10;
    else suggestions.push('Add a cadence field to LOOP.md (cron expression, e.g., "0 2 * * *")');

    // Budget cap — max_cost_usd (10 pts)
    const hasBudget = loopConfig &&
      loopConfig.budget &&
      loopConfig.budget.max_cost_usd !== undefined;
    checks.push({ name: 'Budget cap (max_cost_usd) set', points: 10, passed: !!hasBudget });
    if (hasBudget) score += 10;
    else suggestions.push('Add budget.max_cost_usd to LOOP.md to prevent runaway costs');

    // Approval required for (10 pts)
    const hasApproval = loopConfig &&
      loopConfig.approval_required_for &&
      Array.isArray(loopConfig.approval_required_for) &&
      loopConfig.approval_required_for.length > 0;
    checks.push({ name: 'Approval gates defined', points: 10, passed: !!hasApproval });
    if (hasApproval) score += 10;
    else suggestions.push('Add approval_required_for to LOOP.md (e.g., push_to_main, delete_files)');

    // File scope (10 pts)
    const hasFileScope = loopConfig &&
      loopConfig.file_scope &&
      (loopConfig.file_scope.allow || loopConfig.file_scope.deny);
    checks.push({ name: 'File scope defined', points: 10, passed: !!hasFileScope });
    if (hasFileScope) score += 10;
    else suggestions.push('Add file_scope with allow/deny lists to LOOP.md to restrict file access');

    // Termination conditions beyond max_iterations (10 pts)
    const hasTermination = loopConfig &&
      loopConfig.termination;
    let hasExtraTermination = false;
    if (hasTermination) {
      const failConds = loopConfig.termination.failure || [];
      const successConds = loopConfig.termination.success || [];
      // Check if there are conditions beyond just max_iterations
      const allConds = [...failConds, ...successConds];
      const nonMaxIter = allConds.filter(c => {
        if (typeof c === 'string') return c !== 'max_iterations';
        if (typeof c === 'object') return !c.max_iterations;
        return true;
      });
      hasExtraTermination = nonMaxIter.length > 0;
    }
    checks.push({ name: 'Termination conditions beyond max_iterations', points: 10, passed: hasExtraTermination });
    if (hasExtraTermination) score += 10;
    else suggestions.push('Add termination conditions beyond max_iterations (e.g., no_progress_detected, budget_exhausted)');

    // Recovery strategy (5 pts)
    const hasRecovery = loopConfig &&
      loopConfig.recovery &&
      loopConfig.recovery.strategy;
    checks.push({ name: 'Recovery strategy defined', points: 5, passed: !!hasRecovery });
    if (hasRecovery) score += 5;
    else suggestions.push('Add a recovery strategy to LOOP.md (e.g., rollback_last_commit with escalation)');

    // --- Render results ---
    const scoreColor = score >= 80 ? chalk.green : score >= 50 ? chalk.yellow : chalk.red;
    const scoreIcon = score >= 80 ? '✅' : score >= 50 ? '⚠️' : '❌';

    console.log(chalk.white.bold(`   ┌─ ${loopName}`));

    for (const check of checks) {
      const icon = check.passed ? chalk.green('✓') : chalk.red('✗');
      const pts = check.passed
        ? chalk.green(`+${check.points}`)
        : chalk.dim(`+0/${check.points}`);
      console.log(`   │  ${icon} ${check.name} ${chalk.dim(`(${pts})`)}`);
    }

    console.log(`   │`);
    console.log(`   │  ${scoreIcon}  Loop Readiness Score: ${scoreColor.bold(score + '/100')}`);

    if (showSuggestions && suggestions.length > 0) {
      console.log(`   │`);
      console.log(`   │  ${chalk.yellow.bold('Suggestions:')}`);
      for (const s of suggestions) {
        console.log(`   │  ${chalk.yellow('→')} ${s}`);
      }
    }

    console.log(`   └${'─'.repeat(60)}\n`);

    return { score, checks, suggestions };
  }
})();
