from copy import deepcopy
import math
import datetime
import collections

from common import multiply_counter, pretty_time_delta
from sql import get_item_details
from prices import get_prices


def mult_comps(comp, runs, mult):
    if comp < 2:
        return comp * runs
    else:
        return math.ceil(comp * runs * mult)


class Item:
    """Class to represent items."""
    def __init__(self, item, runs=None, quantity=None, mats_mod=1.0, time_mod=1.0, top_level=False):
        """Constructor for an Item object.  Takes an item name."""
        self.name = item

        if mats_mod == None:
            mats_mod = 1.0

        if time_mod == None:
            time_mod = 1.0

        details, reproc, components = get_item_details(item)

        self.quantity, self.time, self.volume, self.typeid, self.group, self.category = details

        self.reprocessing = dict()
        if reproc:
            for i, q in reproc:
                self.reprocessing[i] = {"quantity": q}

        self.components = {}
        if components:
            for i, q, v, g in components:
                self.components[i] = {"quantity": q, "volume": v, "group": g}

        self.mats_mod = mats_mod
        self.time_mod = time_mod
        if self.quantity is None:
            self.quantity = 1
        if runs is None:
            if quantity is None:
                self.runs = 1
            else:
                self.runs = math.ceil(quantity / self.quantity)
        else:
            if quantity is None:
                self.runs = runs
            else:
                raise ValueError("Only runs OR quantity can be set")

        self.top_level = top_level
        self.volume = self.volume * self.runs * self.quantity

    def get_components_tree(self):
        """Returns the components needed in a tree dict form with the specified me."""
        c = deepcopy(self.components)
        for i in c:
            try:
                c[i]["item"] = c[i]["item"].get_components_tree()
            except KeyError:
                c[i]["quantity"] = mult_comps(c[i]["quantity"], self.runs, self.mats_mod)
        return c

    def get_components_flat(self):
        """Returns the components needed in a flat list form with the specified me."""
        c = deepcopy(self.components)
        total = collections.Counter()
        for i in c:
            try:
                total += c[i]["item"].get_components_flat()
            except KeyError:
                total[i] += mult_comps(c[i]["quantity"], self.runs, self.mats_mod)
        return total

    def get_time(self):
        """Returns the time the blueprint takes with specified te."""
        return datetime.timedelta(seconds=self.time * self.time_mod * self.runs)

    def rec_eval_group(self, group, mats_mod=None, time_mod=None):
        """Marks a specific component to be recursively evaluated."""
        for name, comp in self.components.items():
            if comp["group"] == group:
                self.rec_eval_component(name, mats_mod, time_mod)

    def rec_eval_component(self, component, mats_mod=None, time_mod=None):
        """Marks a specific component to be recursively evaluated."""
        if not isinstance(component, self.__class__):
            component = Item(component, quantity=mult_comps(self.components[component]["quantity"], self.runs, self.mats_mod), mats_mod=mats_mod, time_mod=time_mod)
        else:
            component = Item(component.name, quantity=mult_comps(self.components[component.name]["quantity"], self.runs, self.mats_mod), mats_mod=component.mats_mod, time_mod=component.time_mod)
        self.components[component.name]["item"] = component

    def rec_uneval_component(self, component):
        """Unmarks a specific component for recursive evaluation."""
        del self.components[component]["item"]

    def _get_prices(self, asb='all', avg='fivePercent'):
        return get_prices(typeid=self.typeid, regionlimit='10000002')[0][asb][avg]

    def price(self):
        if self.top_level:
            return self._get_prices('sell') * self.runs * self.quantity
        else:
            return self._get_prices('buy') * self.runs * self.quantity

    def _get_cost(self, ret_list=False):
        l = (Item(i, quantity=j).price() for i, j in self.get_components_flat().items())
        if not ret_list: return sum(l)
        else: return list(l)

    def _get_volume(self, ret_list=False):
        l = (Item(i, quantity=j).volume for i, j in self.get_components_flat().items())
        if not ret_list: return sum(l)
        else: return list(l)

    def get_profit(self):
        """Returns the potential profit of buying the components and then manufacturing them."""
        return self.price() - self._get_cost()

    def get_profit_per_second(self):
        """Returns the potential profit per second."""
        return self.get_profit()/self.get_time().total_seconds()

    def get_pretty_ppd(self):
        return "{:,.2f} isk/day".format(self.get_profit_per_second()*60*60*24)

    def _get_parts_str(self):
        comps = [("Component", "Quantity")] + list(self.get_components_flat().items())
        costs = ["Cost"] + ['{:,.2f}'.format(i) for i in self._get_cost(True)]
        volumes = ["Volume"] + ['{:,.1f}'.format(i) for i in self._get_volume(True)]
        groups = ["Group"] + [Item(i).group for i, _ in comps[1:]]
        categories = ["Category"] + [Item(i).category for i, _ in comps[1:]]
        li = max(len(i) for i, _ in comps)
        ln = max(len(str(n)) for _, n in comps)
        lp = max(len(p) for p in costs)
        lv = max(len(v) for v in volumes)
        lg = max(len(g) for g in groups)
        lc = max(len(c) for c in categories)
        parts = '\n'.join("{:<{}}  {:>{}}  {:>{}}  {:>{}}  {:>{}}  {:>{}}".format(
            i, li, num, ln, p, lp, v, lv, g, lg, c, lc) for (i, num), p, v, g, c in zip(comps, costs, volumes, groups, categories))
        return parts

    def __str__(self):
        """Return a pretty description of the object."""
        pps = self.get_profit_per_second()
        time = pretty_time_delta(self.get_time().total_seconds())
        parts = self._get_parts_str()
        return ("\033[1m{}:\033[0m Material Mod {}, Time Mod {}, {} run(s)\n\n"
                "{}\n\n"
                "\033[1mOutput Units:\033[0m {}, \033[1mInput Volume:\033[0m {} m3, \033[1mOutput Volume:\033[0m {} m3\n"
                "\033[1mTotal:\033[0m {:,.2f} isk, \033[1mPrice:\033[0m {:,.2f} isk, \033[1mProfit:\033[0m {:,.2f} isk\n"
                "\033[1mTime:\033[0m {}, \033[1mIncome:\033[0m {:,.2f} isk/s, {}\n").format(
                        self.name, self.mats_mod, self.time_mod, self.runs, parts, self.runs * self.quantity, self._get_volume(),
                        self.volume, self._get_cost(), self.price(), self.get_profit(), time, pps, self.get_pretty_ppd())


class DummyItem(Item):
    def __init__(self, components):
        self.components = components
