#!/usr/bin/env python3
"""
update_readmes.py — 为每个 ruleset/<Brand>/ 生成 README.md
对齐上游：标题=策略组名，统计=实际规则计数。
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

ROOT = _SCRIPTS_DIR.parent

try:
    from mihomo_rules.commit_writer import STRATEGY_GROUP_MAP  # type: ignore
except Exception:
    try:
        sys.path.insert(0, str(ROOT.parent / 'mihomo-rules' / 'scripts'))
        from commit_writer import STRATEGY_GROUP_MAP  # type: ignore
    except Exception:
        STRATEGY_GROUP_MAP = {}

from lib.canonical import count_by_type, parse_rule_line, TYPES_ORDER


def read_list_counts(list_path: Path) -> dict[str, int]:
    counts = {t: 0 for t in TYPES_ORDER}
    with open(list_path) as f:
        for line in f:
            s = line.rstrip('\n')
            if not s or s.startswith('#'):
                continue
            if ',' in s:
                rtype = s.split(',', 1)[0].strip()
            else:
                continue
            if rtype in counts:
                counts[rtype] += 1
    return counts


def render_table(counts: dict[str, int]) -> str:
    lines = ['| 类型 | 数量 |', '|------|------|']
    for t in TYPES_ORDER:
        if counts.get(t, 0):
            lines.append(f'| {t} | {counts[t]} |')
    return '\n'.join(lines)


def make_readme(brand: str, display: str, counts: dict[str, int], total: int) -> str:
    lines = [
        f'# 📦 {display} 规则集',
        '',
        '## 📊 统计',
        render_table(counts),
        '',
        f'- **behavior**: classical',
        f'- **策略组**: {display}',
        '',
    ]
    return '\n'.join(lines) + '\n'


def main() -> int:
    ruleset_dir = ROOT / 'ruleset'
    updated = 0
    for brand_dir in sorted(ruleset_dir.iterdir()):
        if not brand_dir.is_dir():
            continue
        list_path = brand_dir / f'{brand_dir.name}.list'
        if not list_path.exists():
            continue
        counts = read_list_counts(list_path)
        total = sum(counts.values())
        display = STRATEGY_GROUP_MAP.get(brand_dir.name, brand_dir.name)
        readme_path = brand_dir / 'README.md'
        content = make_readme(brand_dir.name, display, counts, total)
        changed = True
        if readme_path.exists():
            if readme_path.read_text() == content:
                changed = False
        if changed:
            readme_path.write_text(content)
            updated += 1
    print(f'[+] 生成 README: {updated} 个')
    return 0


if __name__ == '__main__':
    sys.exit(main())
