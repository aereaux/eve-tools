import sqlite3
import collections


# Taken from https://gist.github.com/thatalextaylor/7408395
def pretty_time_delta(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%dd%dh%dm%ds' % (days, hours, minutes, seconds)
    elif hours > 0:
        return '%dh%dm%ds' % (hours, minutes, seconds)
    elif minutes > 0:
        return '%dm%ds' % (minutes, seconds)
    else:
        return '%ds' % (seconds,)


def get_sqlite_cur():
    conn = sqlite3.connect('sqlite-latest.sqlite')
    return conn.cursor()


def split_dict(d):
    c = get_sqlite_cur()

    cats = collections.defaultdict(lambda: {})

    cmd = ("SELECT typeName, groupName, categoryName "
           "FROM invTypes AS t "
           "JOIN invGroups AS g ON t.groupID=g.groupID "
           "JOIN invCategories AS c ON g.categoryID=c.categoryID "
           "WHERE typeName in ({0})".format(', '.join('?' for _ in d)))
    c.execute(cmd, tuple(d.keys()))
    things = {x: (y, z) for x, y, z in c.fetchall()}
    for i, j in d.items():
        cats[things[i]].update({i: j})

    return cats


def multiply_counter(c, s):
    r = collections.Counter()
    for k in c.keys():
        r[k] = c[k] * s
    return r


def typeid_to_name(tid):
    c = get_sqlite_cur()

    cmd = ("SELECT typeName "
           "FROM invTypes AS t "
           "WHERE typeID = ?")
    c.execute(cmd, (tid,))
    return c.fetchone()[0]


minerals = ["Tritanium", "Pyerite", "Mexallon", "Nocxium", "Isogen", "Zydrine", "Megacyte", "Morphite"]
mineral_ids = [34, 35, 36, 38, 37, 39, 40, 11399]

ores = ["Veldspar", "Scordite", "Pyroxeres", "Plagioclase", "Omber", "Kernite", "Jaspet", "Hemorphite", "Hedbergite", "Gneiss", "Dark Ochre", "Crokite", "Spodumain", "Bistot", "Arkonor", "Mercoxit"]
ore_ids = [1230, 1228, 1224, 18, 1227, 20, 1226, 1231, 21, 1229, 1232, 1225, 19, 1223, 22, 11395]

eff = 0.86
m3pm = 1027 / 169.2 * 60 * 2 + 26.25 * 5
per = 100
