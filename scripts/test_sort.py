#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts').resolve()))
sys.path.insert(0, str(Path('../mihomo-rules/scripts').resolve()))

from lib.ownership_map import SUB_PARENT
print('SUB_PARENT loaded:', len(SUB_PARENT))

# Import from the local surge-rules generate_config
import importlib.util
spec = importlib.util.spec_from_file_location('surge_gen', str(Path('scripts/generate_config.py').resolve()))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sort_brands = mod.sort_brands
load_brand_info = mod.load_brand_info

brand_info = load_brand_info(Path('ruleset'))
print(f'brand_info count: {len(brand_info)}')
print('Before sort, first 5:')
for bi in brand_info[:5]:
    print(f'  {bi["key"]}')

sorted_info = sort_brands(brand_info)
print('After sort, first 15:')
for bi in sorted_info[:15]:
    print(f'  {bi["key"]}')

# Check sub-brand ordering
apple_idx = next(i for i, bi in enumerate(sorted_info) if bi['key'] == 'Apple')
appletv_idx = next(i for i, bi in enumerate(sorted_info) if bi['key'] == 'AppleTV')
siriai_idx = next(i for i, bi in enumerate(sorted_info) if bi['key'] == 'SiriAI')
icloud_idx = next(i for i, bi in enumerate(sorted_info) if bi['key'] == 'iCloud')
icloudpr_idx = next(i for i, bi in enumerate(sorted_info) if bi['key'] == 'iCloudPrivateRelay')
google_idx = next(i for i, bi in enumerate(sorted_info) if bi['key'] == 'Google')
googleai_idx = next(i for i, bi in enumerate(sorted_info) if bi['key'] == 'GoogleAI')
aws_idx = next(i for i, bi in enumerate(sorted_info) if bi['key'] == 'AWS')
amazon_idx = next(i for i, bi in enumerate(sorted_info) if bi['key'] == 'Amazon')

print(f'\n--- Sub/Parent ordering ---')
print(f'AppleTV({appletv_idx}) < Apple({apple_idx}): {appletv_idx < apple_idx}')
print(f'SiriAI({siriai_idx}) < Apple({apple_idx}): {siriai_idx < apple_idx}')
print(f'iCloud({icloud_idx}) < Apple({apple_idx}): {icloud_idx < apple_idx}')
print(f'iCloudPrRelay({icloudpr_idx}) < iCloud({icloud_idx}): {icloudpr_idx < icloud_idx}')
print(f'GoogleAI({googleai_idx}) < Google({google_idx}): {googleai_idx < google_idx}')
print(f'AWS({aws_idx}) < Amazon({amazon_idx}): {aws_idx < amazon_idx}')