#!/usr/bin/env python

import argparse
import re
from operator import mul
from functools import reduce

from item import Item, DummyItem
from needed_ore import report_ores, print_nicely
from inventory import needed_mats, mats_clipboard
from api import mats_api, bps_api
from collections import Counter


mod_dict = {}

def parse_bp_api(arg):
    return [Item(i['typeName'][:-10], runs=int(i['runs']), mats_mod=0.99, top_level=True) for i in bps_api() if i['typeName'].endswith("Blueprint") and re.search(arg, i['typeName'][:-10])]

def parse_bp(bp):
    """Parse an Item from the specified blueprint format string."""
    b = bp.split(':')
    if len(b) == 1:
        return Item(b[0], top_level=True)
    elif len(b) == 2:
        return Item(b[1], runs=int(b[0]), top_level=True)
    elif len(b) == 3:
        return Item(b[0], mats_mod=parse_mod_spec(b[1]), time_mod=parse_mod_spec(b[2]), top_level=True)
    elif len(b) == 4:
        return Item(b[1], runs=int(b[0]), mats_mod=parse_mod_spec(b[2]), time_mod=parse_mod_spec(b[3]), top_level=True)
    else:
        raise ValueError("Invalid blueprint specifier: {}".format(bp))


def mod(text):
    mods = text.split(',')
    return reduce(mul, (1-float(m) for m in mods), 1)


def parse_mod_option(modi):
    name, value = modi.split('=')
    mod_dict[name] = mod(value)


def parse_mod_spec(spec):
    try:
        return mod(spec)
    except ValueError:
        return mod_dict[spec]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description='Display profit stats for a specified item.')
    ap.add_argument('-b', '--blueprint', action='append', help='Specify a blueprint as [Quantity:]<Item Name>[:ME:TE]')
    ap.add_argument('-p', '--component', action='append', default=[],
            help='Specify a component blueprint as [Quantity:]<Item Name>[:ME:TE]')
    ap.add_argument('--api-blueprints', action='append', help='Get blueprints from the API')
    ap.add_argument('-f', '--profit', action='store_true', help='Print profit information')
    ap.add_argument('-o', '--ore', action='store_true', help='Print ore information.')
    ap.add_argument('-n', '--need', action='store_true', help='Print needed mats information.')
    ap.add_argument('-c', '--clipboard', dest='mat_funcs', action='append_const', const=mats_clipboard, help='Look for information in the clipboard.')
    ap.add_argument('-a', '--api', dest='mat_funcs', action='append_const', const=mats_api, help='Look for information in the api.')
    ap.add_argument('-m', '--modifier', action='append', help='Set a modifier value to be reused.', default=[])
    ap.add_argument('-e', '--exit', action='store_true', help='Indicate needed items with exit value')
    args = ap.parse_args()

    for i in args.modifier:
        parse_mod_option(i)

    bps = list(map(parse_bp, args.blueprint or []))
    for bp in args.api_blueprints or []:
        bps.extend(parse_bp_api(bp))
    comps = list(map(parse_bp, args.component))
    mats = Counter()
    total_profit = 0
    products = []
    for bp in bps:
        bp.rec_eval_group(536, parse_mod_spec('.01,.0504,.1')) # Station Components
        bp.rec_eval_group(873, parse_mod_spec('.01,.042,.1')) # Capital Construction Components
        bp.rec_eval_group(334, parse_mod_spec('.01,.0504,.1')) # Construction Components
        bp.rec_eval_group(913, parse_mod_spec('.01,.0504,.1')) # Advanced Capital Construction Components
        for comp in comps:
            try:
                bp.rec_eval_component(comp)
            except KeyError:
                pass
        if args.profit:
            print(bp)
            total_profit += bp.get_profit()
        mats += bp.get_components_flat()
        products.append(bp)
    if args.profit:
        print(total_profit)
    if args.ore:
        left = report_ores(mats, args.mat_funcs)
    if args.need or args.exit:
        left = needed_mats(mats, args.mat_funcs)
        if args.need:
            print_nicely(left.items())
        if args.exit and left:
            exit(1)
