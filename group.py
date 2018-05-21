#!/usr/bin/env python3

import sys

from inventory import mats_clipboard, needed_mats
from item import Item
from main import mod
from sql import items_in_group
from prices import get_prices

mats = mats_clipboard()

a = set()

for g in sys.argv[1:]:
    for i in items_in_group(g):
        if i.startswith("Medium ") or i.startswith("Small "):
            I = Item(i, 10, mats_mod=mod('.01, .0504'), top_level=True)
            if not needed_mats(I.get_components_flat(), [mats_clipboard]):
                p = get_prices(typeid=I.typeid, regionlimit='10000002')[0]
                a.add((I.get_profit_per_second(), (I.get_pretty_ppd(), p["sell"]["volume"], p["buy"]["volume"], i)))

for _, p in sorted(a, key=lambda x:x[0], reverse=True):
    print(*p, sep='\t')
