from collections import Counter
from subprocess import Popen, PIPE

def needed_mats(need, done_funcs):
    have = Counter()
    for i in done_funcs or []:
        have += i()
    return need - have

def mats_clipboard():
    r = Counter()
    for raw in Popen(["xclip", "-out", "-selection", "clipboard"],
                     stdout=PIPE, universal_newlines=True).stdout:
        try:
            thing, amount = raw.split('\t')[:2]
            amount = int(amount.replace(',', ''))
        except ValueError:
            continue
        r[thing] += amount
    return r

