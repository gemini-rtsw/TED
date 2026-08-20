#!/usr/bin/env python3
"""Verify PVs are really archiving. Uses getPVDetails (engine truth), not getPVStatus."""
import json, os, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

HOST = os.environ.get("TED_APPLIANCE", "http://mkoteddev-lv1:17665")

def truth(pv):
    url = f"{HOST}/mgmt/bpl/getPVDetails?pv=" + urllib.parse.quote(pv)
    try:
        d = json.load(urllib.request.urlopen(url, timeout=30))
    except Exception as e:
        return pv, "ERROR", str(e)
    kv = {r["name"]: r["value"] for r in d}
    arch = kv.get("Is engine currently archiving this?", "no")
    conn = kv.get("Is this PV currently connected?", "?")
    evts = kv.get("How many events so far?", "0")
    return pv, ("OK" if arch == "yes" and conn == "yes" else "FAIL"), f"events={evts}"

if len(sys.argv) < 2:
    sys.exit(f"usage: {sys.argv[0]} <pvs.json>   (appliance: $TED_APPLIANCE, default {HOST})")
pvs = [x["pv"] if isinstance(x, dict) else x for x in json.load(open(sys.argv[1]))]
with ThreadPoolExecutor(max_workers=8) as ex:
    rows = list(ex.map(truth, pvs))
ok  = [r for r in rows if r[1] == "OK"]
bad = [r for r in rows if r[1] != "OK"]
print(f"archiving OK : {len(ok)}/{len(rows)}")
print(f"problems     : {len(bad)}")
for pv, st, info in bad:
    print(f"   {st:5} {pv}  {info}")
