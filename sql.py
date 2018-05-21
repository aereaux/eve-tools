from common import get_sqlite_cur
from functools import lru_cache


def items_in_group(group):
    c = get_sqlite_cur()

    cmd = ("SELECT typeName FROM invTypes WHERE groupID = ? AND published = 1;")
    c.execute(cmd, (group,))
    return (i[0] for i in c)


@lru_cache()
def get_item_details(item):
    c = get_sqlite_cur()

    cmd = ("SELECT ap.typeID, ap.activityID "
           "FROM industryActivityProducts ap "
           "JOIN invTypes p ON ap.productTypeID = p.typeID "
           "WHERE p.typeName = ?;")
    c.execute(cmd, (item,))
    act = c.fetchone()

    if act:
        cmd = ("SELECT ap.quantity, a.time, p.volume, p.typeID, iG.groupName, iC.categoryName "
               "FROM industryActivity a "
               "LEFT OUTER JOIN industryActivityProducts ap ON a.typeID = ap.typeID AND a.activityID = ap.activityID "
               "LEFT OUTER JOIN invTypes p ON ap.productTypeID = p.typeID "
               "LEFT OUTER JOIN invGroups iG on p.groupID = iG.groupID "
               "LEFT OUTER JOIN invCategories iC on iG.categoryID = iC.categoryID "
               "WHERE a.typeID = ? and a.activityID = ?;")
        c.execute(cmd, act)
        details = c.fetchone()

        cmd = ("SELECT m.typeName, am.quantity, m.volume, m.groupID "
               "FROM invTypes m "
               "JOIN industryActivityMaterials am ON m.typeID=am.materialTypeID "
               "WHERE am.typeID= ? and am.activityID = ?")
        c.execute(cmd, act)
        components = c.fetchall()
    else:
        cmd = ("SELECT 1, 0, p.volume, p.typeID, iG.groupName, iC.categoryName "
               "FROM invTypes p "
               "LEFT OUTER JOIN invGroups iG on p.groupID = iG.groupID "
               "LEFT OUTER JOIN invCategories iC on iG.categoryID = iC.categoryID "
               "WHERE p.typeName = ?;")
        c.execute(cmd, (item,))
        details = c.fetchone()

        components = None

    cmd = ("SELECT iT2.typeName, quantity "
           "FROM invTypeMaterials iTM "
           "JOIN invTypes iT1 ON iTM.typeID = iT1.typeID "
           "JOIN invTypes iT2 ON iTM.materialTypeID = iT2.typeID "
           "WHERE iT1.typeName = ?;")
    c.execute(cmd, (item,))
    reproc = c.fetchall()

    return details, reproc, components
