import sys
from cvxopt.glpk import ilp
from cvxopt import matrix as m
import numpy as np
from subprocess import Popen, PIPE
from collections import Counter
from prices import get_prices

from common import ores, minerals, eff, m3pm, per, get_sqlite_cur

def wrap_ilp(c, G, h):
    status, x = ilp(m(c), m(G), m(h), I=set(range(len(c))))

    x = np.array(x).T
    assert x.shape[0] == 1
    return status, x[0]


def print_nicely(arg):
    for args in arg:
        row_format = "{:<12}" + "{:>24}" * (len(args)-1)
        print(row_format.format(*args))


def report_ores(amts, done_funcs=[]):
    c = get_sqlite_cur()

    if done_funcs is None:
        done_funcs = []

    sizes = np.zeros(len(ores))
    prices = np.zeros(len(ores))
    matrix = np.zeros((len(minerals), len(ores)))
    for i, ore in enumerate(ores):
        cmd = "SELECT typeName, typeID, volume FROM invTypes WHERE typeName = ?;"
        c.execute(cmd, (ore,))
        for o, id, volume in c:
            sizes[ores.index(o)] = volume
            prices[ores.index(o)] = get_prices(typeid=id, regionlimit='10000002')[0]['sell']['fivePercent'] 

        cmd = ("SELECT iT2.typeName, quantity AS materialName "
               "FROM invTypeMaterials AS iTM "
               "JOIN invTypes AS iT1 ON iTM.typeID = iT1.typeID "
               "JOIN invTypes AS iT2 ON iTM.materialTypeID = iT2.typeID "
               "WHERE iT1.typeName = ?;")
        c.execute(cmd, (ore,))
        for mineral, value in c:
            matrix[minerals.index(mineral), i] = value

    matrix *= eff

    vector = np.zeros(len(minerals))
    leftovers = Counter()
    for mineral, value in amts.items():
        try:
            vector[minerals.index(mineral)] += value
        except ValueError:
            leftovers[mineral] += value

    done_ores = np.zeros(len(ores))
    done_minerals = np.zeros(len(minerals))
    for i in done_funcs:
        for thing, amount in i().items():
            if thing.startswith("Compressed "):
                thing = thing[11:]
                amount *= per
            try:
                ore = ores.index(thing)
                done_ores[ore] += amount/per
            except ValueError:
                try:
                    mineral = minerals.index(thing)
                    done_minerals[mineral] += amount
                except ValueError:
                    print("Not an ore or mineral: {}".format(thing),
                          file=sys.stderr)

    done_uncomp_ores, done_comp_ores = np.modf(done_ores)

    needed = np.clip(vector - (matrix @ done_comp_ores + done_minerals),
                     0, None)

    print("Needed minerals:")
    print_nicely(zip(minerals, np.ceil(needed).astype(int)))

    status, x = wrap_ilp(sizes, np.vstack([-matrix, -np.eye(len(sizes))]),
                         np.hstack([-needed, np.zeros(len(sizes))]))
    x_uncompressed = np.clip(x - done_uncomp_ores, 0, None) * per
    print("Ores to mine with lowest total volume:")
    print_nicely(zip(ores, x_uncompressed.astype(int), x_uncompressed * sizes))
    vol = x_uncompressed @ sizes
    print("Total volume: {} m^3, {} hours".format(vol, vol/m3pm/60))

    status, x = wrap_ilp(prices, np.vstack([-matrix, -np.eye(len(prices))]),
                         np.hstack([-needed, np.zeros(len(prices))]))
    x_uncompressed = np.clip(x - done_uncomp_ores, 0, None) * per
    print("Ores to mine with lowest total prices:")
    print_nicely(zip(ores, x_uncompressed.astype(int), x_uncompressed * prices))
    pric = x_uncompressed @ prices
    print("Total price: {} isk".format(pric))

    return leftovers


if __name__ == "__main__":
    from item import Item
    import sys
    item = Item(sys.argv[1])
    report_ores(item.get_components_flat())
