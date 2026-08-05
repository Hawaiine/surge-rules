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

try:
    from lib.ownership_map import SUB_PARENT  # type: ignore
except Exception:
    SUB_PARENT = {}

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

# 节点组占位（地区策略组，通过正则从订阅中自动筛选节点）
NODE_GROUPS = [
    ('🇭🇰 香港节点', r'(?=.*(港|HK|(?i)Hong))^((?!(台|日|韩|新|美|Game|游戏|打機|解锁)).)*$', 'Country/Hongkong-2.png'),
    ('🇯🇵 日本节点', r'(?=.*(日|JP|(?i)Japan))^((?!(港|台|韩|新|美|Game|游戏)).)*$', 'Country/Japan-1.png'),
    ('🇺🇸 美国节点', r'(?=.*(美|US|(?i)States|American))^((?!(港|台|日|韩|新|Game|游戏|Test|专线|解锁|CN|BGP|free)).)*$', 'Country/US-1.png'),
    ('🇸🇬 新加坡节点', r'(?=.*(新|狮|獅|SG|(?i)Singapore))^((?!(港|台|日|韩|美|Game|游戏)).)*$', 'Country/Singapore-2.png'),
    ('🇹🇼 台湾节点', r'(?=.*(台|TW|(?i)Taiwan))^((?!(港|日|韩|新|美|Game|游戏|Test)).)*$', 'Country/CN-Taiwan-2.png'),
    ('🇰🇷 韩国节点', r'(?=.*(韩国|Korea|KR))^((?!(港|台|日|新|美|Game|游戏)).)*$', 'Country/Korea-1.png'),
    ('🇬🇧 英国节点', r'(?=.*(英国|United.Kingdom|UK))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/UK-2.png'),
    ('🇩🇪 德国节点', r'(?=.*(德国|Germany|DE))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/Germany-1.png'),
    ('🇫🇷 法国节点', r'(?=.*(法国|France|FR))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/France-1.png'),
    ('🇨🇦 加拿大节点', r'(?=.*(加拿大|Canada|CA))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/Canada-1.png'),
    ('🇦🇺 澳大利亚节点', r'(?=.*(澳大利亚|Australia|AU))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/Australia-1.png'),
    ('🇮🇳 印度节点', r'(?=.*(印度|India|IN))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/India-1.png'),
    ('🇹🇷 土耳其节点', r'(?=.*(土耳其|Turkey|TR))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/Turkey-1.png'),
    ('🇦🇷 阿根廷节点', r'(?=.*(阿根廷|Argentina|AR))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/Argentina-1.png'),
    ('🇧🇷 巴西节点', r'(?=.*(巴西|Brazil|BR))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/Brazil-1.png'),
    ('🇷🇺 俄罗斯节点', r'(?=.*(俄罗斯|Russia|RU))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/Russia-1.png'),
    ('🇲🇾 马来西亚节点', r'(?=.*(马来西亚|Malaysia|MY))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/Malaysia-1.png'),
    ('🇹🇭 泰国节点', r'(?=.*(泰国|Thailand|TH))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/Thailand-1.png'),
    ('🇻🇳 越南节点', r'(?=.*(越南|Vietnam|VN))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/Vietnam-1.png'),
    ('🇵🇭 菲律宾节点', r'(?=.*(菲律宾|Philippines|PH))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/Philippines-1.png'),
    ('🇮🇩 印尼节点', r'(?=.*(印尼|Indonesia|ID))^((?!(港|台|日|韩|新|美|Game|游戏)).)*$', 'Country/Indonesia-1.png'),
]

ICON_BASE = 'https://raw.githubusercontent.com/Hawaiine/Oasisic-Icons/main/icons'

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


def sort_brands(brand_info: List[dict]) -> List[dict]:
    """子品牌排在父品牌前，避免宽泛规则截胡。"""
    if not SUB_PARENT:
        return brand_info

    sub_parents = set(SUB_PARENT.keys())
    parent_brands = set(SUB_PARENT.values())
    # 品牌 key -> 完整信息
    info_map = {bi['key']: bi for bi in brand_info}

    # 递归收集所有子品牌（含嵌套）
    def collect_children(parent: str, seen: set) -> list:
        kids = []
        for child in sorted(SUB_PARENT.keys()):
            if SUB_PARENT[child] == parent and child not in seen:
                seen.add(child)
                grandkids = collect_children(child, seen)
                kids.append(child)
                kids.extend(grandkids)
        return kids

    result = []
    done = set()
    # 先处理有父品牌的子品牌
    for parent in sorted(parent_brands):
        children = collect_children(parent, done)
        for c in children:
            if c in info_map:
                result.append(info_map[c])
                done.add(c)
        if parent in info_map and parent not in done:
            result.append(info_map[parent])
            done.add(parent)

    # 剩余品牌按字母序
    for bi in brand_info:
        if bi['key'] not in done:
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
    return f"""# ===========================================
# Surge Configuration
# Surge 官方网站 - https://nssurge.com/
# Surge 官方手册 - https://manual.nssurge.com/
# Surge 中文指引 - https://manual.nssurge.com/book/understanding-surge/cn/
# Surge 官方社区 - https://community.nssurge.com/
# Updated: {now} (UTC+8)
# ===========================================

[General]
# 日志等级
loglevel = notify

# WiFi 助手（自动切换蜂窝网络）
wifi-assist = true

# 允许局域网其它设备访问代理服务
allow-wifi-access = true
wifi-access-http-port = 6152
wifi-access-socks5-port = 6153

# 允许接入热点中的其它设备访问代理服务
allow-hotspot-access = true

# 国内测速地址
internet-test-url = http://www.apple.com/library/test/success.html

# 国外测速地址
proxy-test-url = http://cp.cloudflare.com/generate_204

# 测速超时（秒）
test-timeout = 2

# 跳过代理（局域网/本地地址直连）
skip-proxy = 127.0.0.1, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 100.64.0.0/10, localhost, *.local

# 跳过 TUN 模式（局域网地址）
bypass-tun = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12

# IPv6 支持
ipv6 = true

# IPv6 VIF 工作模式
ipv6-vif = auto

# DNS 服务器
dns-server = 119.29.29.29, 1.0.0.1, 8.8.4.4

# 加密 DNS
encrypted-dns-server = https://doh.pub/dns-query

# 劫持 DNS（拦截发往指定地址的 DNS 查询）
hijack-dns = 8.8.8.8:53, 8.8.4.4:53

# 强制保留真实 IP 的域名（用于 NAT 检测、游戏联机）
always-real-ip = *.srv.nintendo.net, *.stun.playstation.net

# 自定义 GeoIP 数据库
geoip-maxmind-url = https://raw.githubusercontent.com/Loyalsoldier/geoip/release/Country.mmdb

# 当遇到 reject 策略时返回错误页
show-error-page-for-reject = true

# 游戏优化（UDP 优先）
udp-priority = true

"""


def gen_proxy_placeholder() -> str:
    return """[Proxy]
# ===========================================
# 代理节点配置
# 方式一：使用外部配置文件（推荐）
#   将代理节点写入 configs/Proxy.dconf，格式参考该文件内的注释
#   取消注释下面这行即可加载：
#   #!include configs/Proxy.dconf
#
# 方式二：直接在此处添加节点
#   支持类型：http, https, socks5, socks5-tls, ss, vmess, trojan, snell, wireguard
#   参考：https://manual.nssurge.com/proxy/proxy.html
# ===========================================
#!include configs/Proxy.dconf

"""


def gen_proxy_groups_full(icons: Dict[str, str], brand_info: List[dict]) -> str:
    lines: List[str] = ['[Proxy Group]']
    # 系统组
    lines.append('🛑 全球拦截 = select, 🇨🇳国内直连, 🚫REJECT, no-alert=0, hidden=0, include-all-proxies=0, icon-url=https://raw.githubusercontent.com/Hawaiine/Oasisic-Icons/main/icons/General/Reject.png')
    lines.append('🎯 全球直连 = select, 🇨🇳国内直连, no-alert=0, hidden=0, include-all-proxies=0, icon-url=https://raw.githubusercontent.com/Hawaiine/Oasisic-Icons/main/icons/General/Direct.png')
    lines.append('🔧 手动切换 = select, 🇨🇳国内直连, 🇺🇸美国节点, 🇭🇰香港节点, 🇸🇬新加坡节点, 🇯🇵日本节点, 🇹🇼台湾节点, 🇰🇷韩国节点, 🚀节点选择, no-alert=0, hidden=0, include-all-proxies=0, icon-url=https://raw.githubusercontent.com/Hawaiine/Oasisic-Icons/main/icons/General/Auto.png')
    lines.append('')
    # 订阅节点列表
    lines.append('# 订阅节点列表（将下方 policy-path 替换为你的订阅地址）')
    lines.append('🌱节点列表 = select, no-alert=0, hidden=1, include-all-proxies=0, update-interval=43200, policy-path=此处填入订阅地址, icon-url=https://raw.githubusercontent.com/Hawaiine/Oasisic-Icons/main/icons/General/Area.png')
    lines.append('')
    # 地区节点组（通过正则从订阅中自动筛选）
    for ng, regex, icon_path in NODE_GROUPS:
        lines.append(f'{ng} = select, no-alert=0, hidden=0, include-all-proxies=0, update-interval=0, policy-regex-filter={regex}, include-other-group=🌱节点列表, icon-url={ICON_BASE}/{icon_path}')
    lines.append('')
    # 全局代理
    lines.append('🚀节点选择 = smart, no-alert=1, hidden=1, update-interval=0, interval=600, tolerance=50, include-other-group="🇺🇸美国节点, 🇭🇰香港节点, 🇸🇬新加坡节点, 🇯🇵日本节点, 🇹🇼台湾节点, 🇰🇷韩国节点, 🇬🇧英国节点"')
    lines.append('')
    # 品牌策略组
    for i, bi in enumerate(brand_info):
        if i > 0:
            lines.append('')
        icon_url = f', icon-url={icons[bi["sg"]]}' if bi['sg'] in icons else ''
        lines.append(f'{bi["sg"]} = select, 🇨🇳国内直连, 🇺🇸美国节点, 🇭🇰香港节点, 🇸🇬新加坡节点, 🇯🇵日本节点, 🇹🇼台湾节点, 🇰🇷韩国节点, 🇬🇧英国节点, 🚀节点选择, no-alert=0, hidden=0, include-all-proxies=0{icon_url}, include-other-group=🌱节点列表')
    lines.append('')
    # 兜底
    lines.append('🐟 漏网之鱼 = select, 🇨🇳国内直连, 🇺🇸美国节点, 🇭🇰香港节点, 🇸🇬新加坡节点, 🇯🇵日本节点, 🇹🇼台湾节点, 🇰🇷韩国节点, 🇬🇧英国节点, 🚀节点选择, no-alert=0, hidden=0, include-all-proxies=0, icon-url=https://raw.githubusercontent.com/Hawaiine/Oasisic-Icons/main/icons/General/Global-4.png, include-other-group=🌱节点列表')
    return '\n'.join(lines) + '\n\n'


def gen_proxy_groups_min(icons: Dict[str, str], brand_info: List[dict]) -> str:
    lines: List[str] = ['[Proxy Group]']
    # 系统组
    lines.append('🛑 全球拦截 = select, 🇨🇳国内直连, 🚫REJECT, no-alert=0, hidden=0, include-all-proxies=0')
    lines.append('🎯 全球直连 = select, 🇨🇳国内直连, no-alert=0, hidden=0, include-all-proxies=0')
    lines.append('🔧 手动切换 = select, 🇨🇳国内直连, 🇺🇸美国节点, 🇭🇰香港节点, 🇸🇬新加坡节点, 🇯🇵日本节点, 🇹🇼台湾节点, 🇰🇷韩国节点, 🚀节点选择, no-alert=0, hidden=0, include-all-proxies=0')
    # 订阅节点列表
    lines.append('🌱节点列表 = select, no-alert=0, hidden=1, include-all-proxies=0, update-interval=43200, policy-path=此处填入订阅地址')
    # 地区节点组
    for ng, regex, icon_path in NODE_GROUPS:
        lines.append(f'{ng} = select, no-alert=0, hidden=0, include-all-proxies=0, update-interval=0, policy-regex-filter={regex}, include-other-group=🌱节点列表')
    # 全局代理
    lines.append('🚀节点选择 = smart, no-alert=1, hidden=1, update-interval=0, interval=600, tolerance=50, include-other-group="🇺🇸美国节点, 🇭🇰香港节点, 🇸🇬新加坡节点, 🇯🇵日本节点, 🇹🇼台湾节点, 🇰🇷韩国节点, 🇬🇧英国节点"')
    # 品牌策略组
    for bi in brand_info:
        icon_url = f', icon-url={icons[bi["sg"]]}' if bi['sg'] in icons else ''
        lines.append(f'{bi["sg"]} = select, 🇨🇳国内直连, 🇺🇸美国节点, 🇭🇰香港节点, 🇸🇬新加坡节点, 🇯🇵日本节点, 🇹🇼台湾节点, 🇰🇷韩国节点, 🇬🇧英国节点, 🚀节点选择, no-alert=0, hidden=0, include-all-proxies=0{icon_url}, include-other-group=🌱节点列表')
    # 兜底
    lines.append('🐟 漏网之鱼 = select, 🇨🇳国内直连, 🇺🇸美国节点, 🇭🇰香港节点, 🇸🇬新加坡节点, 🇯🇵日本节点, 🇹🇼台湾节点, 🇰🇷韩国节点, 🇬🇧英国节点, 🚀节点选择, no-alert=0, hidden=0, include-all-proxies=0, include-other-group=🌱节点列表')
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
    brand_info = sort_brands(brand_info)

    icons = IconsMap()
    icons.build()

    general = gen_general()
    proxies = gen_proxy_placeholder()
    common_brand_info = filter_brand_info(brand_info)
    common_brand_info = sort_brands(common_brand_info)
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
