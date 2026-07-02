# Feature: Interactive Loop Pattern Picker

## Problem

`loopwiz` currently prints a static numbered table of all loop patterns and asks the user to type a number. This breaks down as the registry grows:

- Numbered lists stop being scannable past ~20 items
- No way to find a pattern by keyword without reading every row
- Non-interactive contexts (CI, cron, scripts) can't use a printed table at all

## Goal

Replace the static table + number prompt with a live, searchable, keyboard-navigable picker for interactive (TTY) sessions, while adding direct flags for non-interactive use. This is the primary UX; flags are the escape hatch.

## Scope

- In scope: picker UI, fuzzy search, domain grouping/filtering, non-TTY fallback via flags
- Out of scope: changing the registry data source, adding new loop patterns, remote/hosted registry sync

## User-facing behavior

### Interactive mode (TTY attached)

Running `loopwiz` with no arguments launches the picker:

- A search input is shown with placeholder text explaining fuzzy search and domain shorthand
- Below it, a live list of patterns renders, grouped by `domain` when the search box is empty
- Typing filters the list in place using fuzzy matching against `name` and `description` (name weighted higher)
- Typing `domain/` as a prefix (e.g. `frontend/`) scopes results to that domain before fuzzy-matching the rest of the query
- `↑` / `↓` moves the active selection; hovering with a mouse also updates it in graphical terminals that support it
- `Enter` confirms the active selection and proceeds to run that pattern
- `Esc` clears the current search and resets to the full grouped list
- An empty result set shows guidance text (e.g. suggesting a domain filter) rather than a blank screen

### Non-interactive mode (no TTY, e.g. CI/cron/pipes)

The picker never renders. Instead:

- `loopwiz run <pattern-name>` runs a pattern directly by exact name
- `loopwiz --pattern=<pattern-name>` is equivalent, for scripts that prefer flags
- `loopwiz --list` prints the full registry as plain text (one pattern per line: `name<TAB>domain<TAB>description`) for piping into other tools
- `loopwiz --domain=<domain>` filters `--list` output to one domain
- If no pattern is resolvable in a non-TTY context (bad name, missing flag), exit non-zero with a clear error naming the closest valid pattern names

### Detection

- Check `isatty(stdin)` (or platform equivalent) at startup
- If false, skip the picker entirely — never attempt to draw an interactive UI a script can't respond to

## Data model

No changes to the existing registry shape. Each entry needs (already present):

```
{ id: string, name: string, description: string, domain: string }
```

## Matching logic

- Fuzzy match: subsequence match against `name` first; if no match, fall back to `description` at a lower weight so name matches always rank above description-only matches
- Case-insensitive
- Substring matches score higher than scattered-subsequence matches (prefer `security-scan` matching `scan` closely over a loose subsequence hit elsewhere)
- Domain prefix (`domain/query`) is parsed before fuzzy matching and only applied if the token exactly matches a known domain

## UI reference

See attached mockup: `loopwiz-picker.html` (interactive HTML prototype demonstrating search, grouping, keyboard nav, and empty state). Use it as the interaction spec — arrow-key behavior, grouping-when-idle, and the non-interactive hint in the footer should all carry over into the real implementation.

## Acceptance criteria

- [ ] Running `loopwiz` in a TTY shows the grouped list with no query typed
- [ ] Typing any substring of a pattern name filters to matches within one frame/render cycle (no visible lag at current registry size)
- [ ] Typing `<domain>/` scopes the list to that domain only
- [ ] Arrow keys move selection without scrolling the whole terminal
- [ ] Enter on a selection runs that pattern; Esc clears search
- [ ] Empty results show a helpful message, not a blank list
- [ ] `loopwiz run <name>`, `--pattern=<name>`, `--list`, and `--domain=<domain>` all work with no TTY attached and never attempt to draw the picker
- [ ] Invalid pattern name in non-interactive mode exits non-zero with a specific, actionable error
- [ ] Works correctly at current registry size (16) and remains responsive at 10x that size (simulate with generated fixture data)

## Implementation notes (pick based on stack)

| Language | Library |
|---|---|
| Node/TS | `@clack/prompts` (+ custom filter) or `inquirer` with `inquirer-autocomplete-prompt` |
| Python | `questionary` or `InquirerPy` |
| Go | `charmbracelet/bubbletea` + `bubbles/list` |
| Rust | `inquire` or `dialoguer` |

Keep the matching/filtering logic in a pure, testable function separate from the rendering library, so it can be unit tested without a terminal and swapped if the picker library changes later.

## Open questions

- Should recently-run patterns be pinned to the top of the idle (no-query) view?
- Should `--list` output support `--json` for tooling that wants structured output instead of TSV?
