"""Shared constants and configuration for loop-wizard."""

# Remote repository URL for fetching loop patterns and registry
RAW_REPO_URL = "https://raw.githubusercontent.com/kaiju-no-9/loop_Engg/main"

# Model pricing: cost per 1M tokens (USD)
MODELS = {
    # Anthropic
    "claude-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-opus": {"input": 15.00, "output": 75.00},
    "claude-3-opus": {"input": 15.00, "output": 75.00},
    "claude-haiku": {"input": 0.25, "output": 1.25},
    "claude-3-5-haiku": {"input": 0.25, "output": 1.25},
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    # Google
    "gemini-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    # Google DeepMind — Antigravity
    "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
    # OpenCode (model-agnostic — use the underlying provider's pricing)
    "opencode-default": {"input": 1.25, "output": 5.00},
}

# Cadence label -> estimated runs per month
CADENCE_MULTIPLIERS = {
    "nightly": 30,
    "daily": 30,
    "weekly": 4,
    "hourly": 720,
    "on-pr": 20,
    "on-release": 4,
    "on-merge": 20,
    "on-schema-change": 4,
    "on-file-change": 10,
    "on-test-failure": 10,
    "on-commit": 30,
}

# Cadence presets for the wizard's select question
CADENCE_PRESETS = [
    {
        "label": "Every night at 2am",
        "value": "0 2 * * *",
        "description": "Recommended — runs while you sleep",
    },
    {
        "label": "Every hour",
        "value": "0 * * * *",
        "description": "For active CI environments",
    },
    {
        "label": "On every push",
        "value": "__trigger__",
        "description": "Triggered by GitHub event",
    },
    {
        "label": "Manually only",
        "value": "__manual__",
        "description": "You run it yourself each time",
    },
]

# Supported agent tools (display order in the interactive picker)
AGENT_TOOLS = [
    "claude-code",
    "claude",
    "gemini-cli",
    "antigravity",
    "cursor",
    "opencode",
    "codex",
]

# Agent tool -> environment variable for GitHub Actions
AGENT_ENV_VARS = {
    "claude-code": {
        "ANTHROPIC_API_KEY": "${{ secrets.ANTHROPIC_API_KEY }}",
    },
    "claude": {
        "ANTHROPIC_API_KEY": "${{ secrets.ANTHROPIC_API_KEY }}",
    },
    "gemini-cli": {
        "GEMINI_API_KEY": "${{ secrets.GEMINI_API_KEY }}",
    },
    "antigravity": {
        # Antigravity is powered by Google DeepMind's Gemini models
        "GOOGLE_API_KEY": "${{ secrets.GOOGLE_API_KEY }}",
        "GEMINI_API_KEY": "${{ secrets.GEMINI_API_KEY }}",
    },
    "cursor": {
        "OPENAI_API_KEY": "${{ secrets.OPENAI_API_KEY }}",
        "ANTHROPIC_API_KEY": "${{ secrets.ANTHROPIC_API_KEY }}",
    },
    "opencode": {
        # OpenCode is model-agnostic — set the key for your chosen provider
        "OPENCODE_API_KEY": "${{ secrets.OPENCODE_API_KEY }}",
        "ANTHROPIC_API_KEY": "${{ secrets.ANTHROPIC_API_KEY }}",
        "OPENAI_API_KEY": "${{ secrets.OPENAI_API_KEY }}",
    },
    "codex": {
        "OPENAI_API_KEY": "${{ secrets.OPENAI_API_KEY }}",
    },
}

# Rich metadata for each agent tool: shown in the interactive wizard picker
AGENT_METADATA = {
    "claude-code": {
        "icon": "🤖",
        "provider": "Anthropic",
        "description": "Terminal-native agentic coding tool by Anthropic",
        "run_cmd": "claude /loop {pattern}",
    },
    "claude": {
        "icon": "⚡",
        "provider": "Anthropic",
        "description": "Claude CLI — lightweight Anthropic agent",
        "run_cmd": "claude /loop {pattern}",
    },
    "gemini-cli": {
        "icon": "♊",
        "provider": "Google",
        "description": "Gemini CLI by Google — open-source, 1M token context",
        "run_cmd": "gemini /loop {pattern}",
    },
    "antigravity": {
        "icon": "🪐",
        "provider": "Google DeepMind",
        "description": "Antigravity — advanced agentic AI coding assistant by Google DeepMind",
        "run_cmd": "antigravity /loop {pattern}",
    },
    "cursor": {
        "icon": "🖱️",
        "provider": "Cursor / Anysphere",
        "description": "AI-powered editor with agent mode",
        "run_cmd": "cursor /loop {pattern}",
    },
    "opencode": {
        "icon": "🔓",
        "provider": "SST / Open-source",
        "description": "OpenCode — model-agnostic open-source terminal coding agent (75+ providers)",
        "run_cmd": "opencode run /loop {pattern}",
    },
    "codex": {
        "icon": "🧮",
        "provider": "OpenAI",
        "description": "OpenAI Codex CLI agent",
        "run_cmd": "codex /loop {pattern}",
    },
}

# Stack auto-detection: file -> (stack name, default test command, default test dir)
STACK_SIGNATURES = [
    ("package.json", "Node.js", "npm test", "test/"),
    ("pytest.ini", "Python (pytest)", "pytest", "tests/"),
    ("pyproject.toml", "Python", "pytest", "tests/"),
    ("setup.py", "Python", "python -m unittest", "tests/"),
    ("Cargo.toml", "Rust", "cargo test", "tests/"),
    ("go.mod", "Go", "go test ./...", "."),
    ("pom.xml", "Java (Maven)", "mvn test", "src/test/"),
    ("build.gradle", "Java (Gradle)", "./gradlew test", "src/test/"),
    ("Gemfile", "Ruby", "bundle exec rspec", "spec/"),
    ("composer.json", "PHP", "./vendor/bin/phpunit", "tests/"),
]

# Default values when nothing is detected or specified
DEFAULTS = {
    "test_command": "npm test",
    "test_dir": "test/",
    "budget": 2.00,
    "cadence": "0 2 * * *",
    "merge_strategy": "pr",
}
