#!/usr/bin/env python3
"""
Walk the PV tree for a site, ask the Archiver Appliance about every PV,
and list the ones that are NOT being archived (missing, paused, or
disconnected). Read-only — it changes nothing.

Run inside the ted-api container (has PyYAML + host networking):
    docker exec ted-api python3 /ted-api/check_archiving.py
Env overrides: SITE (default from container), ARCHIVER, CHANNELS_DIR.
"""
import os
import sys
import json
import urllib.parse
import urllib.request

import yaml

SITE = os.environ.get("SITE", "MK")
CHANNELS_DIR = os.environ.get("CHANNELS_DIR", f"/ted-api/pv_tree/channels/{SITE}")
ARCHIVER = os.environ.get("ARCHIVER", "http://127.0.0.1:17665")
CHUNK = 100  # PVs per archiver request


def collect_pvs(node, out):
    """Recursively gather leaf strings that look like EPICS PV names."""
    if isinstance(node, dict):
        for v in node.values():
            collect_pvs(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_pvs(v, out)
    elif isinstance(node, str):
        s = node.strip()
        if ":" in s and " " not in s:   # PV names have a colon, no spaces
            out.add(s)


def load_tree_pvs():
    pvs = set()
    for root, _dirs, files in os.walk(CHANNELS_DIR):
        for name in files:
            if not (name.endswith(".yaml") or name.endswith(".yml")):
                continue
            with open(os.path.join(root, name)) as f:
                data = yaml.safe_load(f)
            if data:
                collect_pvs(data, pvs)
    return sorted(pvs)


def archiver_status(pvs):
    status = {}
    for i in range(0, len(pvs), CHUNK):
        chunk = pvs[i:i + CHUNK]
        url = f"{ARCHIVER}/mgmt/bpl/getPVStatus?pv=" + urllib.parse.quote(",".join(chunk))
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                for item in json.load(r):
                    status[item.get("pvName")] = item
        except Exception as e:
            print(f"  ! archiver query failed for chunk {i}-{i+len(chunk)}: {e}",
                  file=sys.stderr)
    return status


def main():
    pvs = load_tree_pvs()
    print(f"Found {len(pvs)} PVs in the {SITE} tree ({CHANNELS_DIR})")
    if not pvs:
        return

    status = archiver_status(pvs)

    bad = []
    for pv in pvs:
        item = status.get(pv)
        if item is None:
            bad.append((pv, "no status returned"))
            continue
        st = item.get("status", "unknown")
        conn = str(item.get("connectionState", "")).lower()
        if st != "Being archived":
            bad.append((pv, st))
        elif conn == "false":
            bad.append((pv, "Being archived / DISCONNECTED"))

    print(f"\n{len(bad)} of {len(pvs)} PVs are NOT archiving:\n")
    for pv, why in bad:
        print(f"  {pv:45s} {why}")


if __name__ == "__main__":
    main()
