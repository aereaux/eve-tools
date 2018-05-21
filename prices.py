import requests

cached_prices = {}


def _get_single_element(l):
    assert len(l) == 1
    return l[0]


def _make_list(i):
    try:
        return list(i)
    except TypeError:
        return [i]


def get_prices(**kwargs):
    """Retrieves price info from eve-central.com.

    Takes arguments in the same form that eve-central's api takes them.  The
    most important is typeid, which controls with type is searched for.
    """
    kwargs['typeid'] = _make_list(kwargs['typeid'])
    cached = set(kwargs['typeid']).intersection(set(cached_prices.keys()))
    kwargs['typeid'] = set(kwargs['typeid']) - set(cached_prices.keys())
    if kwargs['typeid']:
        j = requests.get("https://api.evemarketer.com/ec/marketstat/json", params=kwargs).json()
        cached_prices.update({_get_single_element(i['buy']['forQuery']['types']): i for i in j})
    else:
        j = []
    j.extend(cached_prices[i] for i in cached)
    return j
