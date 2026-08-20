#!/usr/bin/env python3
"""
gea2archappl.py - convert GEA ChannelArchiver .cnfg files into EPICS Archiver
Appliance archivePV JSON.

GEA line format:   <pvname> <period_seconds> [Monitor|Scan]
  - lines starting with '!' are engine globals, '#' are comments
  - a missing third field means Scan (ChannelArchiver's default)

Parent records
--------------
The appliance's mgmt console resolves "record.FIELD" by stripping the field and
reporting the *parent* record's status. GEA configs frequently archive only
output fields (ao:aoZernikes.VALF) and never the bare record, so those PVs show
as "Not being archived" even though the engine is archiving them fine.

Adding the bare record fixes the display and makes the singular
/retrieval/data/getData.json endpoint (used by the Quick chart and the Grafana
ArchiverAppliance datasource) work for the field. Verified: with the parent
archived, the field still returns its own data, not the parent's.

Use --parents none for a strict like-for-like migration.

Examples
--------
  ./gea2archappl.py altair                     # one system -> altair-pvs.json
  ./gea2archappl.py --all --combined all.json  # every system, single file
  ./gea2archappl.py --all --check-tree         # also cross-check TED pv_tree
"""
import argparse, json, os, re, sys
from pathlib import Path

# This lives in <repo>/admin/scripts/gea-migration/, so the repo root is three up.
REPO = Path(__file__).resolve().parents[3]

# Site configs (gnconfig / cpconfig) are normally checked out alongside the TED repo.
# Override with $GEA_CONFIG or --gea-config.
SITE = os.environ.get("TED_SITE", "MK")
SITE_CONFIG = {"MK": "gnconfig", "CP": "cpconfig"}
GEA_CONFIG = Path(os.environ.get(
    "GEA_CONFIG", REPO.parent / SITE_CONFIG.get(SITE, "gnconfig") / "gea" / "config"))
TED_TREE = Path(os.environ.get(
    "TED_TREE", REPO / "ted-api" / "pv_tree" / "channels" / SITE))
APPLIANCE = os.environ.get("TED_APPLIANCE", "http://mkoteddev-lv1:17665")

FIELD_RE = re.compile(r"^(.*)\.([A-Za-z0-9]+)$")


def parse_cnfg(path):
    """-> {pv: {'period': str, 'method': 'MONITOR'|'SCAN'}}, [warnings]"""
    pvs, warn = {}, []
    for n, raw in enumerate(path.read_text(errors="replace").splitlines(), 1):
        line = raw.strip()
        if not line or line[0] in "#!":
            continue
        parts = line.split()
        pv = parts[0]
        period = parts[1] if len(parts) > 1 else "1"
        try:
            float(period)
        except ValueError:
            warn.append(f"{path.name}:{n}: unparseable period {period!r}, using 1")
            period = "1"
        # ChannelArchiver defaults to Scan when the method is omitted.
        method = parts[2].upper() if len(parts) > 2 else "SCAN"
        if method not in ("MONITOR", "SCAN"):
            warn.append(f"{path.name}:{n}: unknown method {parts[2]!r}, using SCAN")
            method = "SCAN"
        if pv in pvs:
            warn.append(f"{path.name}:{n}: duplicate {pv}, keeping first")
            continue
        pvs[pv] = {"period": period, "method": method}
    return pvs, warn


def add_parents(pvs, mode):
    """Insert bare parent records. mode: 'valx' | 'all' | 'none'. -> list of added pvs."""
    if mode == "none":
        return []
    added = {}
    for pv, cfg in pvs.items():
        m = FIELD_RE.match(pv)
        if not m:
            continue
        rec, field = m.groups()
        if field == "VAL":
            continue  # the appliance already treats record.VAL as the record
        if mode == "valx" and not re.fullmatch(r"VAL[A-Z]", field):
            continue
        if rec in pvs or f"{rec}.VAL" in pvs:
            continue  # parent already covered
        per = float(cfg["period"])
        if rec not in added or per < float(added[rec]["period"]):
            added[rec] = {"period": cfg["period"], "method": "MONITOR"}
    pvs.update(added)
    return sorted(added)


def to_json(pvs):
    return [
        {"pv": pv, "samplingperiod": c["period"], "samplingmethod": c["method"]}
        for pv, c in pvs.items()
    ]


def tree_codes(site_dir):
    """-> {pv: [label paths]} across every yaml under the site dir."""
    try:
        import yaml
    except ImportError:
        sys.exit("--check-tree needs pyyaml:  pip install pyyaml")
    codes = {}

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "codes":
                    for pv in v or []:
                        codes.setdefault(pv, []).append(" > ".join(path))
                else:
                    walk(v, path + [str(k)])

    for f in sorted(site_dir.rglob("*.yaml")):
        walk(yaml.safe_load(f.read_text()) or {}, [])
    return codes


def norm(pv):
    """EPICS treats pv and pv.VAL as the same field."""
    return pv[:-4] if pv.endswith(".VAL") else pv


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("systems", nargs="*", help="system names (default: --all)")
    ap.add_argument("--all", action="store_true", help="every system under the gea config dir")
    ap.add_argument("--gea-config", type=Path, default=GEA_CONFIG)
    ap.add_argument("--out", type=Path, default=Path("."), help="output directory")
    ap.add_argument("--combined", type=Path, help="also write one merged json")
    ap.add_argument("--parents", choices=["valx", "all", "none"], default="valx",
                    help="add bare parent records (default: valx = only for .VALA-style fields)")
    ap.add_argument("--appliance", default=APPLIANCE, help=f"appliance base url (default {APPLIANCE})")
    ap.add_argument("--check-tree", action="store_true", help="cross-check against the TED pv_tree")
    ap.add_argument("--ted-tree", type=Path, default=TED_TREE)
    args = ap.parse_args()

    if args.all or not args.systems:
        files = sorted(p for d in sorted(args.gea_config.iterdir()) if d.is_dir()
                       for p in sorted(d.glob("*.cnfg")))
    else:
        files = []
        for s in args.systems:
            found = sorted((args.gea_config / s).glob("*.cnfg"))
            if not found:
                sys.exit(f"no .cnfg under {args.gea_config / s}")
            files += found

    args.out.mkdir(parents=True, exist_ok=True)
    merged, all_warn, rows = {}, [], []

    for f in files:
        pvs, warn = parse_cnfg(f)
        base = len(pvs)
        added = add_parents(pvs, args.parents)
        all_warn += warn
        name = f.parent.name
        out = args.out / f"{name}-pvs.json"
        out.write_text(json.dumps(to_json(pvs), indent=2) + "\n")
        rows.append((name, base, len(added), len(pvs), out.name))
        for pv, c in pvs.items():
            merged.setdefault(pv, c)

    w = max(len(r[0]) for r in rows)
    print(f"{'system'.ljust(w)}  {'gea':>5} {'+par':>5} {'total':>6}  file")
    for name, base, added, total, fn in rows:
        print(f"{name.ljust(w)}  {base:5} {added:5} {total:6}  {fn}")
    print(f"{'TOTAL'.ljust(w)}  {sum(r[1] for r in rows):5} {sum(r[2] for r in rows):5} "
          f"{sum(r[3] for r in rows):6}   unique across systems: {len(merged)}")

    if args.combined:
        args.combined.write_text(json.dumps(to_json(merged), indent=2) + "\n")
        print(f"\ncombined -> {args.combined} ({len(merged)} PVs)")

    if all_warn:
        print(f"\nwarnings ({len(all_warn)}):")
        for x in all_warn[:40]:
            print("  ", x)
        if len(all_warn) > 40:
            print(f"   ... and {len(all_warn) - 40} more")

    print("\nto load, run:")
    targets = [args.combined] if args.combined else [args.out / fn for *_, fn in rows]
    for t in targets:
        print(f"\n  curl -X POST -H 'Content-Type: application/json' \\\n"
              f"    --data @{t} \\\n"
              f"    {args.appliance}/mgmt/bpl/archivePV")
    print("\nthen verify (a few minutes later):")
    print(f"\n  curl -s {args.appliance}/mgmt/bpl/getNeverConnectedPVs | python3 -m json.tool")

    if args.check_tree:
        codes = tree_codes(args.ted_tree)
        gea_n = {norm(p) for p in merged}
        ted_n = {norm(p) for p in codes}
        no_chan = sorted(p for p in codes if norm(p) not in gea_n)
        no_label = sorted(p for p in merged if norm(p) not in ted_n)
        print(f"\nTED labels with no GEA channel : {len(no_chan)}")
        for p in no_chan:
            print(f"   {p}")
            for path in sorted(set(codes[p])):
                print(f"       {path}")
        print(f"\nGEA channels with no TED label : {len(no_label)}")
        for p in no_label:
            print(f"   {p}")


if __name__ == "__main__":
    main()
