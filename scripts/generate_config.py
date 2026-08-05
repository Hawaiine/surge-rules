#!/usr/bin/env python3
"""
generate_config.py — 生成 Surge 配置文件（Surge.conf / Surge.min.conf）
从 ruleset/ 扫描品牌，生成完整 Surge 配置。
输出：
- configs/Surge.conf       # 完整版（含注释、段间空行）
- configs/Surge.min.conf   # 精简版（无注释、紧凑）
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

ROOT = Path(__file__).resolve().parent.parent
_MIHOMO_SCRIPTS = ROOT.parent / 'mihomo-rules' / 'scripts'
if str(_MIHOMO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_MIHOMO_SCRIPTS))

try:
    from commit_writer import STRATEGY_GROUP_MAP  # type: ignore
except Exception:
    STRATEGY_GROUP_MAP = {}

# 直接加载 lib/icons_map.py，避免包名冲突
import importlib.util
_ICONS_MAP_PATH = _SCRIPTS_DIR / "lib" / "icons_map.py"
_icons_spec = importlib.util.spec_from_file_location("icons_map", _ICONS_MAP_PATH)
_icons_mod = importlib.util.module_from_spec(_icons_spec)
_icons_spec.loader.exec_module(_icons_mod)
IconsMap = _icons_mod.IconsMap

# 基础策略组定义（不含品牌组）
SYSTEM_GROUPS_ORDER = [
    '🛑 全球拦截',
    '🎯 全球直连',
    '🔧 手动切换',
    '🐟 漏网之鱼',
]

# 节点组占位（Surge 示例节点，用户需替换）
NODE_GROUPS = [
    '🇭🇰 香港节点',
    '🇯🇵 日本节点',
    '🇺🇸 美国节点',
    '🇸🇬 新加坡节点',
    '🇹🇼 台湾节点',
    '🇰🇷 韩国节点',
    '🇬🇧 英国节点',
    '🇩🇪 德国节点',
    '🇫🇷 法国节点',
    '🇨🇦 加拿大节点',
    '🇦🇺 澳大利亚节点',
    '🇮🇳 印度节点',
    '🇹🇷 土耳其节点',
    '🇦🇷 阿根廷节点',
    '🇧🇷 巴西节点',
    '🇷🇺 俄罗斯节点',
    '🇲🇾 马来西亚节点',
    '🇹🇭 泰国节点',
    '🇻🇳 越南节点',
    '🇵🇭 菲律宾节点',
    '🇮🇩 印尼节点',
]

# 全量品牌（用于生成 Surge 配置，避免遗漏）
COMMON_BRANDS = [
    'AWS',
    'AbemaTV',
    'Amazon',
    'Anthropic',
    'Apple',
    'AppleTV',
    'Applications',
    'Bahamut',
    'Bangumi',
    'Bank',
    'Bilibili',
    'Bluesky',
    'CATCHPLAY',
    'CNCIDR',
    'Cloudflare',
    'Cursor',
    'DAZN',
    'DAnimeStore',
    'DMMTV',
    'Deezer',
    'Direct',
    'Discord',
    'Disney',
    'Docker',
    'F1TV',
    'Facebook',
    'FujiTV',
    'GameJapan',
    'GeneralAI',
    'GitHub',
    'Google',
    'GoogleAI',
    'HBO',
    'HOYTV',
    'HamiVideo',
    'Hotstar',
    'Hulu',
    'Instagram',
    'KKTV',
    'LINETV',
    'LanCIDR',
    'Lemino',
    'LiTV',
    'Manus',
    'Messenger',
    'MetaBrainz',
    'Microsoft',
    'Mora',
    'MusicJapan',
    'Musixmatch',
    'MyVideo',
    'NHK',
    'Netflix',
    'Niconico',
    'Nintendo',
    'NowE',
    'OasisicSelf',
    'OneDrive',
    'OpenAI',
    'PT',
    'PTChina',
    'PayPal',
    'Perplexity',
    'Pinterest',
    'Pixiv',
    'Podcast',
    'Poe',
    'Porn',
    'PornChina',
    'PrimeVideo',
    'Private',
    'Proxy',
    'Qobuz',
    'Radiko',
    'RakutenTV',
    'ReadsJapan',
    'Reddit',
    'Reject',
    'SiriAI',
    'Spotify',
    'Steam',
    'Synology',
    'TMDB',
    'TVer',
    'Telasa',
    'Telegram',
    'Threads',
    'Tidal',
    'TikTok',
    'Tubi',
    'Twitch',
    'UNext',
    'VideoMarket',
    'Viu',
    'WOWOW',
    'WSJ',
    'Wallpaper',
    'WhatsApp',
    'X',
    'YouTube',
    'YouTubeMusic',
    'ZLibrary',
    'friDayvideo',
    'iCloud',
    'iCloudPrivateRelay',
    'karaokeDAM',
    'myTVSuper',
]


def load_brand_info(ruleset_dir: Path) -> List[dict]:
    brand_info = []
    if not ruleset_dir.exists():
        return brand_info
    for d in sorted(ruleset_dir.iterdir()):
        if not d.is_dir():
            continue
        list_path = d / f'{d.name}.list'
        if not list_path.exists():
            continue
        brand_info.append({
            'key': d.name,
            'sg': STRATEGY_GROUP_MAP.get(d.name, d.name),
            'behavior': 'classical',
        })
    return brand_info


def filter_brand_info(brand_info: List[dict]) -> List[dict]:
    """仅保留常用品牌，避免配置膨胀。"""
    common_keys = set(COMMON_BRANDS)
    result = []
    for bi in brand_info:
        if bi['key'] in common_keys:
            result.append(bi)
    return result


def write_if_changed(path: Path, content: str) -> bool:
    if path.exists():
        existing = path.read_text()
        if existing == content:
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True


def gen_general() -> str:
    now = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    return f"""[General]
loglevel = notify
skip-proxy = 127.0.0.1, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 100.64.0.0/10, localhost, *.local
dns-server = system, https://doh.pub/dns-query, https://dns.alidns.com/dns-query
external-controller-access = surgerules@127.0.0.1:6170
# iOS
bypass-system = true
bypass-tun = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12
# macOS
interface = 0.0.0.0
port = 6152
socks-port = 6153

"""


def gen_proxy_placeholder() -> str:
    return """[Proxy]
# ===========================================
# Proxy 节点（示例占位，请替换为实际节点）
# ===========================================
ProxyA = http, 1.2.3.4, 443
ProxyB = socks5, 5.6.7.8, 1080
Direct = direct

"""


def gen_proxy_groups_full(icons: Dict[str, str], brand_info: List[dict]) -> str:
    lines: List[str] = ['[Proxy Group]']
    for ng in NODE_GROUPS:
        lines.append(f'{ng} = url-test, ProxyA, ProxyB, Direct, interval=600, timeout=5, tolerance=50')
    for sg in SYSTEM_GROUPS_ORDER:
        lines.append(f'{sg} = select, ProxyA, ProxyB, Direct')
    for i, bi in enumerate(brand_info):
        if i > 0:
            lines.append('')
        lines.append(f'{bi["sg"]} = select, Direct, 🇭🇰 香港节点, 🇯🇵 日本节点, 🇺🇸 美国节点, 🇸🇬 新加坡节点')
        if bi['sg'] in icons:
            lines.append(f'    # icon: {icons[bi["sg"]]}')
    return '\n'.join(lines) + '\n\n'


def gen_proxy_groups_min(icons: Dict[str, str], brand_info: List[dict]) -> str:
    lines: List[str] = ['[Proxy Group]']
    for ng in NODE_GROUPS:
        lines.append(f'{ng} = url-test, ProxyA, ProxyB, Direct, interval=600, timeout=5, tolerance=50')
    for sg in SYSTEM_GROUPS_ORDER:
        lines.append(f'{sg} = select, ProxyA, ProxyB, Direct')
    for bi in brand_info:
        lines.append(f'{bi["sg"]} = select, Direct, 🇭🇰 香港节点, 🇯🇵 日本节点, 🇺🇸 美国节点, 🇸🇬 新加坡节点')
    return '\n'.join(lines) + '\n\n'


def gen_rule_set_line(brand_key: str, brand_sg: str, no_resolve: bool = False, extended: bool = False, use_proxy: bool = True) -> str:
    url = f'https://raw.githubusercontent.com/Hawaiine/surge-rules/main/ruleset/{brand_key}.list'
    if brand_key == 'Reject':
        target = '🛑 全球拦截'
    elif brand_key in {'Direct', 'Private', 'LanCIDR'}:
        target = '🎯 全球直连'
    elif brand_key == 'CNCIDR':
        target = '🎯 全球直连'
    elif brand_key == 'Proxy':
        target = '🔧 手动切换'
    else:
        target = brand_sg if use_proxy else '🎯 全球直连'
    parts = [f'RULE-SET,{url},{target}']
    if no_resolve:
        parts.append('no-resolve')
    if extended:
        parts.append('extended-matching')
    return ','.join(parts)


def gen_rules_full(brand_info: List[dict]) -> str:
    lines = ['[Rule]']
    lines.append('# ----- 1. 拦截 (最高优先级) -----')
    lines.append(gen_rule_set_line('Reject', '🛑 全球拦截', use_proxy=False))
    lines.append('')
    lines.append('# ----- 2. 品牌分流 (按需取消注释, 放在国内规则前) -----')
    lines.append('# 顺序说明: 子品牌/重叠品牌排父品牌前, 避免被宽泛规则截胡')
    lines.append('# 例: AppleTV/SiriAI/iCloud 在 Apple 前')
    common_keys = {bi['key'] for bi in filter_brand_info(brand_info)}
    for bi in brand_info:
        rule_line = gen_rule_set_line(bi['key'], bi['sg'], no_resolve=False, extended=False, use_proxy=True)
        if bi['key'] in common_keys:
            lines.append(rule_line)
        else:
            lines.append(f'# {rule_line}')
    lines.append('')
    lines.append('# ----- 3. 局域网 & 直连 -----')
    lines.append(gen_rule_set_line('Direct', '🎯 全球直连', use_proxy=False))
    lines.append(gen_rule_set_line('Private', '🎯 全球直连', use_proxy=False))
    lines.append(gen_rule_set_line('LanCIDR', '🎯 全球直连', use_proxy=False))
    lines.append('')
    lines.append('# ----- 4. 国内 IP (GeoIP 放最后, 兜底国内流量) -----')
    lines.append(gen_rule_set_line('CNCIDR', '🎯 全球直连', no_resolve=True, use_proxy=False))
    lines.append('GEOIP,CN,🎯 全球直连,no-resolve')
    lines.append('')
    lines.append('# ----- 5. 代理 (国际流量) -----')
    lines.append(gen_rule_set_line('Proxy', '🔧 手动切换', use_proxy=True))
    lines.append('')
    lines.append('# ----- 6. 兜底 (必须最后) -----')
    lines.append('MATCH,🐟 漏网之鱼')
    lines.append('')
    return '\n'.join(lines) + '\n'


def gen_rules_min(brand_info: List[dict]) -> str:
    lines = ['[Rule]']
    common_keys = {bi['key'] for bi in filter_brand_info(brand_info)}
    for bi in brand_info:
        if bi['key'] not in common_keys:
            continue
        lines.append(gen_rule_set_line(bi['key'], bi['sg'], no_resolve=False, extended=False, use_proxy=True))
    lines.append(gen_rule_set_line('Reject', '🛑 全球拦截', use_proxy=False))
    lines.append(gen_rule_set_line('Direct', '🎯 全球直连', use_proxy=False))
    lines.append(gen_rule_set_line('Private', '🎯 全球直连', use_proxy=False))
    lines.append(gen_rule_set_line('LanCIDR', '🎯 全球直连', use_proxy=False))
    lines.append(gen_rule_set_line('CNCIDR', '🎯 全球直连', no_resolve=True, use_proxy=False))
    lines.append('GEOIP,CN,🎯 全球直连,no-resolve')
    lines.append(gen_rule_set_line('Proxy', '🔧 手动切换', use_proxy=True))
    lines.append('MATCH,🐟 漏网之鱼')
    return '\n'.join(lines) + '\n'


def assemble_full(general: str, proxies: str, proxy_groups: str, rules: str) -> str:
    return f"""{general}{proxies}{proxy_groups}{rules}[Host]
# 本地 DNS 映射（按需添加）
# 127.0.0.1 localhost

"""


def assemble_min(general: str, proxies: str, proxy_groups: str, rules: str) -> str:
    return f"""{general}{proxies}{proxy_groups}{rules}[Host]
# 本地 DNS 映射（按需添加）
# 127.0.0.1 localhost

"""


def main() -> None:
    ruleset_dir = ROOT / 'ruleset'
    brand_info = load_brand_info(ruleset_dir)

    icons = IconsMap()
    icons.build()

    general = gen_general()
    proxies = gen_proxy_placeholder()
    common_brand_info = filter_brand_info(brand_info)
    proxy_groups_full = gen_proxy_groups_full(icons.all_icons(), common_brand_info)
    proxy_groups_min = gen_proxy_groups_min(icons.all_icons(), common_brand_info)
    rules_full = gen_rules_full(brand_info)
    rules_min = gen_rules_min(brand_info)

    full = assemble_full(general, proxies, proxy_groups_full, rules_full)
    min_conf = assemble_min(general, proxies, proxy_groups_min, rules_min)

    out_dir = ROOT / 'configs'
    changed_full = write_if_changed(out_dir / 'Surge.conf', full)
    changed_min = write_if_changed(out_dir / 'Surge.min.conf', min_conf)

    print(f'[+] Surge.conf: {"updated" if changed_full else "unchanged"}')
    print(f'[+] Surge.min.conf: {"updated" if changed_min else "unchanged"}')


if __name__ == '__main__':
    main()
