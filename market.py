#!/usr/bin/env python

import sys, sched, datetime, time, functools, webbrowser, pickle, os.path
from sched import scheduler
from ezcurses import Cursed
from curses import beep

from api import get_api

def get_expires(r):
    try:
        try:
            return datetime.datetime.strptime(r.header['Expires'][0], "%d %b %Y %H:%M:%S %Z").replace(tzinfo=datetime.timezone.utc).timestamp()
        except ValueError:
            return datetime.datetime.strptime(r.header['Expires'][0], "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=datetime.timezone.utc).timestamp()
    except KeyError:
        return (datetime.datetime.now() + datetime.timedelta(minutes=5)).timestamp()

def get_orders():
    op = esi_app.op['get_characters_character_id_orders'](character_id=api_info['CharacterID'])
    #op = esi_app.op['get_corporations_corporation_id_orders'](corporation_id=corp)
    orders = esi_client.request(op)
    if not 200 <= orders.status < 300:
        raise Exception(f'HTTP Error {orders.status}: {orders.raw}')
    redraw(orders.header['Expires'][0])
    od = {o['order_id']: o for o in orders.data}
    for order in set(od) - set(sched_tasks):
        line = od[order]
        sched_tasks[order] = ['', None, 0, False]
        print_order(line['order_id'], line['region_id'], line['type_id'], line['location_id'], line['is_buy_order'] if "is_buy_order" in line else False)
    for order in set(sched_tasks) - set(od):
        s.cancel(sched_tasks[order][1])
        del sched_tasks[order]
    redraw(orders.header['Expires'][0])
    expires = get_expires(orders)
    s.enterabs(expires + 10, 0, get_orders)

functools.lru_cache()
def typeid_to_name(typeid):
    r = esi_client.request(esi_app.op['get_universe_types_type_id'](type_id=typeid))
    return r.data.name

def higher_orders(mine, orders, buy):
    compare = lambda p, m: p > m if buy else p < m
    return [order for order in orders if compare(order.price, mine)]

def redraw(newtime = None):
    if newtime is not None:
        redraw.time = newtime
    pad.write(redraw.time)
    for i, (c, _, _, h) in enumerate(sorted(sched_tasks.values(), key=lambda x: x[2]), 1):
        pad.write(c, (0, i), 'red' if h else None)
    pad.refresh(clear=True)
        
def print_order(order_id, region, type_id, structure_id, is_buy, last=None):
    r1 = esi_client.request(esi_app.op['get_markets_region_id_orders'](region_id=region,type_id=type_id,order_type='buy' if is_buy else 'sell',))
    #r2 = esi_client.request(esi_app.op['get_markets_structures_structure_id'](structure_id=structure_id))
    #expires = min(get_expires(r1), get_expires(r2))
    expires = get_expires(r1)
    #if 200 <= r1.status < 300 and 200 <= r2.status < 300:
    if 200 <= r1.status < 300:
        #proc = {dat.order_id: dat for dat in r1.data + [l for l in r2.data if l.type_id==type_id and l.is_buy_order==is_buy]}
        proc = {dat.order_id: dat for dat in r1.data}
        try:
            my_order = proc[order_id]
            higher = len(higher_orders(my_order.price, proc.values(), my_order.is_buy_order))
            newlast = (higher, my_order.price)
            do_beep = higher and newlast != last
            if do_beep:
                beep()
            sched_tasks[order_id][0] = '\t'.join(map(str, [my_order.volume_remain, my_order.volume_total, higher, typeid_to_name(my_order.type_id)]))
            sched_tasks[order_id][2] = expires
            sched_tasks[order_id][3] = do_beep
        except KeyError:
            try:
                sched_tasks[order_id][0] = '\t'.join(map(str, ['NA', 'NA', 'NA', typeid_to_name(type_id)]))
                sched_tasks[order_id][2] = 0
                sched_tasks[order_id][3] = False
                newlast = last
            except KeyError:
                return
    else:
        #raise Exception(r1.raw+r2.raw)
        raise Exception(r1.raw)
        #print(r1.raw, r2.raw, '\a', file=sys.stderr)
        print(r1.raw, '\a', file=sys.stderr)
        newlast = last
    redraw()
    sched_tasks[order_id][1] = s.enterabs(expires + 10, 0, print_order, (order_id, region, type_id, structure_id, is_buy, newlast))

api_info, esi_app, esi_client = get_api(sys.argv[1], ["esi-markets.read_character_orders.v1", "esi-markets.structure_markets.v1", "esi-markets.read_corporation_orders.v1"])
op = esi_app.op['get_characters_character_id'](character_id=api_info['CharacterID'])
char = esi_client.request(op)
corp = char.data["corporation_id"]

sched_tasks = {}

s = sched.scheduler(time.time)

with Cursed() as scr:
    pad = scr.new_pad()
    get_orders()
    s.run()
