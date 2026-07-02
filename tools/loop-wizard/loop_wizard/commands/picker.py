import sys

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.live import Live

console = Console()

def get_subsequence_score(query: str, target: str) -> float:
    """Returns a score > 0 if query is a subsequence of target, else 0.
    Substring matches score higher than scattered subsequences.
    """
    if not query:
        return 1.0
    
    q_len = len(query)
    t_len = len(target)
    
    # Exact match
    if query == target:
        return 20.0
        
    # Substring match
    idx = target.find(query)
    if idx != -1:
        coverage = q_len / t_len
        position_bonus = (t_len - idx) / t_len
        return 10.0 + coverage + position_bonus

    # Subsequence match (scattered)
    t_idx = 0
    matched_indices = []
    for char in query:
        while t_idx < t_len and target[t_idx] != char:
            t_idx += 1
        if t_idx == t_len:
            return 0.0
        matched_indices.append(t_idx)
        t_idx += 1
        
    span = matched_indices[-1] - matched_indices[0] + 1
    span_score = q_len / span
    coverage = q_len / t_len
    return span_score + coverage

def match_pattern(pattern: dict, query: str, known_domains: list[str]) -> float:
    """Matches a pattern against a query, returning a score.
    Supports domain filtering (e.g., 'frontend/') and prioritizes name over description.
    """
    search_str = query.lower()
    
    # Extract domain prefix if present and valid
    if '/' in search_str:
        prefix, rest = search_str.split('/', 1)
        if prefix in [d.lower() for d in known_domains]:
            if pattern.get('domain', '').lower() != prefix:
                return 0.0
            search_str = rest

    if not search_str:
        return 1.0

    name_lower = pattern.get('name', '').lower()
    desc_lower = pattern.get('description', '').lower()

    name_score = get_subsequence_score(search_str, name_lower)
    if name_score > 0:
        return name_score * 100.0  # Name matches rank much higher
        
    desc_score = get_subsequence_score(search_str, desc_lower)
    if desc_score > 0:
        return desc_score
        
    return 0.0

def get_filtered_patterns(patterns: list[dict], query: str, known_domains: list[str]) -> list[tuple[dict, float]]:
    """Returns a list of matching patterns and their scores."""
    filtered = []
    for p in patterns:
        score = match_pattern(p, query, known_domains)
        if score > 0:
            filtered.append((p, score))
            
    # If the search query part is empty (or just a domain prefix), preserve original order
    search_str = query.lower()
    if '/' in search_str:
        prefix, rest = search_str.split('/', 1)
        if prefix in [d.lower() for d in known_domains]:
            search_str = rest
            
    if not search_str:
        return filtered
        
    # Otherwise sort by score descending
    filtered.sort(key=lambda x: x[1], reverse=True)
    return filtered

import click

def read_key() -> str:
    """Reads a single keypress robustly using click."""
    try:
        ch = click.getchar()
        if ch in ('\x1b[A', '\x1bOA'):
            return 'up'
        if ch in ('\x1b[B', '\x1bOB'):
            return 'down'
        if ch in ('\x1b[C', '\x1bOC'):
            return 'right'
        if ch in ('\x1b[D', '\x1bOD'):
            return 'left'
        if ch in ('\r', '\n'):
            return 'enter'
        if ch in ('\x7f', '\x08'):
            return 'backspace'
        if ch == '\x1b':
            return 'esc'
        if ch == '\x03':
            raise KeyboardInterrupt()
        return ch
    except Exception:
        # Fallback if any I/O error occurs
        raise KeyboardInterrupt()

def render_picker(query: str, patterns: list[dict], known_domains: list[str], selected_idx: int, viewport_start: int) -> tuple[Group, int, int]:
    """Builds the rich Group for the picker interface and calculates viewport state."""
    filtered_pairs = get_filtered_patterns(patterns, query, known_domains)
    selectable_patterns = [p[0] for p in filtered_pairs]
    
    if not selectable_patterns:
        selected_idx = 0
    else:
        selected_idx = max(0, min(selected_idx, len(selectable_patterns) - 1))
        
    # Build search line
    search_text = Text("  Search: ", style="bold white")
    if not query:
        search_text.append("Type to fuzzy search... Use domain/ prefix (e.g., backend/)", style="dim italic")
    else:
        has_prefix = False
        if '/' in query:
            parts = query.split('/', 1)
            prefix = parts[0]
            if prefix.lower() in [d.lower() for d in known_domains]:
                has_prefix = True
                search_text.append(prefix + "/", style="bold magenta")
                search_text.append(parts[1], style="bold white")
        if not has_prefix:
            search_text.append(query, style="bold white")
            
    # Determine if we group by domain
    search_str = query.lower()
    if '/' in search_str:
        prefix, rest = search_str.split('/', 1)
        if prefix in [d.lower() for d in known_domains]:
            search_str = rest
            
    is_grouped = not bool(search_str)
    
    all_render_lines = []
    selected_line_idx = 0
    
    if not selectable_patterns:
        empty_text = Text("\n  No matching patterns found.\n", style="yellow")
        empty_text.append("  Try searching for a different keyword or check your spelling.\n", style="white")
        empty_text.append("  You can also scope search to a domain using: ", style="white")
        empty_text.append("domain/", style="magenta")
        all_render_lines.append(empty_text)
    else:
        if is_grouped:
            # Group by domain
            patterns_by_domain = {d: [] for d in known_domains}
            for p in selectable_patterns:
                dom = p.get('domain', '')
                if dom in patterns_by_domain:
                    patterns_by_domain[dom].append(p)
                else:
                    if 'Other' not in patterns_by_domain:
                        patterns_by_domain['Other'] = []
                    patterns_by_domain['Other'].append(p)
                    
            for dom in sorted(patterns_by_domain.keys()):
                dom_patterns = patterns_by_domain[dom]
                if dom_patterns:
                    all_render_lines.append(Text(f"\n[ {dom} ]", style="bold cyan"))
                    for p in dom_patterns:
                        is_selected = (selectable_patterns[selected_idx] == p)
                        name = p.get('name', '')
                        desc = p.get('description', '')
                        line = Text()
                        if is_selected:
                            selected_line_idx = len(all_render_lines)
                            line.append("  ▸ ", style="bold green")
                            line.append(f"{name:<25}", style="bold green")
                            line.append(desc, style="white")
                        else:
                            line.append("    ", style="white")
                            line.append(f"{name:<25}", style="bold cyan")
                            line.append(desc, style="dim")
                        all_render_lines.append(line)
        else:
            # Flat list
            all_render_lines.append(Text("")) # padding
            for i, p in enumerate(selectable_patterns):
                is_selected = (i == selected_idx)
                name = p.get('name', '')
                dom = p.get('domain', '')
                desc = p.get('description', '')
                line = Text()
                if is_selected:
                    selected_line_idx = len(all_render_lines)
                    line.append("  ▸ ", style="bold green")
                    line.append(f"{name:<25}", style="bold green")
                    line.append(f"[{dom}] ", style="bold magenta")
                    line.append(desc, style="white")
                else:
                    line.append("    ", style="white")
                    line.append(f"{name:<25}", style="bold cyan")
                    line.append(f"[{dom}] ", style="dim")
                    line.append(desc, style="dim")
                all_render_lines.append(line)
                
    # Viewport logic
    max_lines = 12
    if selected_line_idx < viewport_start:
        viewport_start = selected_line_idx
    elif selected_line_idx >= viewport_start + max_lines:
        viewport_start = selected_line_idx - max_lines + 1
        
    viewport_start = max(0, min(viewport_start, len(all_render_lines) - max_lines))
    
    visible_lines = all_render_lines[viewport_start:viewport_start + max_lines]
    
    # Add scroll indicators if needed
    list_group = []
    if viewport_start > 0:
        list_group.append(Text("    ↑ (more patterns above)", style="dim italic"))
    else:
        list_group.append(Text("")) # padding
        
    list_group.extend(visible_lines)
    
    if viewport_start + max_lines < len(all_render_lines):
        list_group.append(Text("    ↓ (more patterns below)", style="dim italic"))
    else:
        list_group.append(Text("")) # padding
        
    footer = Text("\n  [Up/Down]", style="bold blue")
    footer.append(" Navigate  ", style="dim")
    footer.append("[Enter]", style="bold blue")
    footer.append(" Select  ", style="dim")
    footer.append("[Esc]", style="bold blue")
    footer.append(" Clear/Exit\n", style="dim")
    footer.append("  Non-interactive? Run: ", style="dim italic")
    footer.append("loopwiz run <pattern-name>", style="white italic")
    
    panel = Panel(
        Group(
            search_text,
            Text("─────────────────────────────────────────────────────────────────", style="dim"),
            *list_group,
            footer
        ),
        title="[bold magenta]⚡ SELECT LOOP PATTERN ⚡[/bold magenta]",
        title_align="left",
        border_style="magenta",
        padding=(1, 2),
        expand=False
    )
    
    return panel, selected_idx, viewport_start, selectable_patterns

def run_picker(patterns: list[dict]) -> str | None:
    """Runs the interactive pattern picker. Returns selected pattern name or None."""
    known_domains = sorted(list(set(p.get('domain', 'Other') for p in patterns)))
    
    query = ""
    selected_idx = 0
    viewport_start = 0
    selectable_patterns = []
    
    console.print()
    
    with Live(auto_refresh=False, console=console) as live:
        while True:
            panel, selected_idx, viewport_start, selectable_patterns = render_picker(
                query, patterns, known_domains, selected_idx, viewport_start
            )
            live.update(panel, refresh=True)
            
            try:
                ch = read_key()
            except KeyboardInterrupt:
                return None
                
            if ch == 'enter':
                if selectable_patterns:
                    return selectable_patterns[selected_idx].get('name')
            elif ch == 'esc':
                if query:
                    query = ""
                    selected_idx = 0
                    viewport_start = 0
                else:
                    return None
            elif ch == 'backspace':
                if query:
                    query = query[:-1]
                    selected_idx = 0
            elif ch == 'up':
                if selectable_patterns:
                    selected_idx = (selected_idx - 1) % len(selectable_patterns)
            elif ch == 'down':
                if selectable_patterns:
                    selected_idx = (selected_idx + 1) % len(selectable_patterns)
            elif len(ch) == 1 and ch.isprintable():
                query += ch
                selected_idx = 0
