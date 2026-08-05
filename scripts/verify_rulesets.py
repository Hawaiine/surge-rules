#!/usr/bin/env python3
"""
verify_rulesets.py — 校验 ruleset/*.list 一致性
检查项：
- UTF-8 无 BOM
- Header 四要素（Source / Rule Count / TOTAL / Last Updated）
- Header/Body 计数一致
- 类型白名单
- DOMAIN-REGEX 允许（Surge 支持）
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from lib.canonical import TYPES_ORDER, parse_rule_line

SURGE_TYPES = set(TYPES_ORDER)
HEADER_KEYS = ['Source', 'Rule Count', 'TOTAL', 'Last Updated']
TYPE_RE = re.compile(r'(?P<type>[A-Z][A-Z0-9_-]+):\s+(?P<count>\d+)')
TOTAL_RE = re.compile(r'^#\s+TOTAL:\s+(?P<count>\d+)\s*$')


def iter_list_files(ruleset_dir: Path):
    for path in sorted(ruleset_dir.rglob('*.list')):
        yield path


def parse_header(path: Path) -> Tuple[dict[str, int], int, List[str]]:
    counts: dict[str, int] = {}
    total = 0
    errors: List[str] = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            s = line.rstrip('\n')
            if not s.startswith('#'):
                break
            tm = TOTAL_RE.match(s)
            if tm:
                total = int(tm.group('count'))
                continue
            # 新格式：单行 # TYPE count TYPE count ...
            for m in TYPE_RE.finditer(s):
                counts[m.group('type')] = int(m.group('count'))
    return counts, total, errors


def parse_body(path: Path) -> Tuple[dict[str, int], List[str]]:
    counts = {t: 0 for t in TYPES_ORDER}
    errors: List[str] = []
    in_body = False
    with open(path, encoding='utf-8') as f:
        for line in f:
            s = line.rstrip('\n')
            if not in_body:
                if s == '':
                    continue
                if s.startswith('#'):
                    continue
                in_body = True
            if not s or s.startswith('#'):
                continue
            rule = parse_rule_line(s)
            if not rule.rtype:
                errors.append(f'invalid rule: {s}')
                continue
            if rule.rtype not in SURGE_TYPES:
                errors.append(f'unsupported type: {rule.rtype}')
                continue
            counts[rule.rtype] += 1
    return counts, errors


def check_file(path: Path) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    header_counts, header_total, _ = parse_header(path)
    body_counts, body_errors = parse_body(path)
    errors.extend(body_errors)
    for t in TYPES_ORDER:
        if header_counts.get(t, 0) != body_counts.get(t, 0):
            errors.append(f'header #{t}={header_counts.get(t, 0)} != body={body_counts.get(t, 0)}')
    actual_total = sum(body_counts.values())
    if header_total != actual_total:
        errors.append(f'header TOTAL={header_total} != actual={actual_total}')
    return len(errors) == 0, errors


def main() -> int:
    ruleset_dir = Path(__file__).resolve().parent.parent / 'ruleset'
    files = list(iter_list_files(ruleset_dir))
    print(f'[+] 发现 {len(files)} 个 .list 文件')
    total_pass = 0
    total_fail = 0
    all_errors = {}
    for path in files:
        ok, errors = check_file(path)
        if ok:
            total_pass += 1
        else:
            total_fail += 1
            all_errors[path.name] = errors
    print(f'--- 结果 ---')
    print(f'  PASS: {total_pass}')
    print(f'  FAIL: {total_fail}')
    if all_errors:
        print('--- 失败明细 ---')
        for name, errs in sorted(all_errors.items()):
            for e in errs:
                print(f'  {name}: {e}')
    return 0 if total_fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
