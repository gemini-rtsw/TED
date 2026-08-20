# GEA -> Archiver Appliance migration

Tools for moving PVs from the old GEA ChannelArchiver configs into the EPICS
Archiver Appliance.

## Layout assumed

    <parent>/TED/           this repo
    <parent>/gnconfig/      GN site config (gea/config/<system>/<system>.cnfg)
    <parent>/cpconfig/      GS site config

Paths are derived from the repo location. Override with `--gea-config`,
`--ted-tree`, `--appliance`, or the env vars `GEA_CONFIG`, `TED_TREE`,
`TED_APPLIANCE`, `TED_SITE` (MK|CP, default MK).

## gea2archappl.py

Converts `.cnfg` files into `archivePV` JSON.

    ./gea2archappl.py gcal --out .                     # one system
    ./gea2archappl.py --all --out ./out                # every system
    ./gea2archappl.py --all --combined all-pvs.json    # plus one merged file
    ./gea2archappl.py --all --check-tree               # cross-check the TED pv_tree
    ./gea2archappl.py gcal --parents none              # strict like-for-like

GEA line format is `<pv> <period_seconds> [Monitor|Scan]`; `!` lines are engine
globals and `#` lines are comments. A missing third field means **Scan**, which
is ChannelArchiver's default - not Monitor.

It prints the `curl` command to load the result, and reports duplicate PV lines
rather than silently dropping them (GEA's configs contain 33 of them).

### Parent records

The appliance's mgmt console resolves `record.FIELD` by stripping the field and
reporting the **parent** record's status. GEA often archives only output fields
(`ao:aoZernikes.VALF`) and never the bare record, so those PVs display as
"Not being archived" even though the engine is archiving them correctly.

By default (`--parents valx`) the bare record is added for `.VAL<letter>`
fields when neither `record` nor `record.VAL` is already present. This fixes the
display and makes the singular `/retrieval/data/getData.json` endpoint work for
the field - that endpoint 404s otherwise, which affects the Quick chart and the
Grafana ArchiverAppliance datasource. Verified: with the parent archived, the
field still returns its own data, not the parent's.

`record.VAL` is the record itself, so it never needs a parent added.

## verify_pvs.py

    ./verify_pvs.py gcal-pvs.json

Reports which PVs are genuinely archiving. Uses `getPVDetails` (engine truth)
rather than `getPVStatus`, which misreports `.VAL<letter>` fields for the reason
above.

## Typical run

    ./gea2archappl.py gcal --out .
    curl -X POST -H 'Content-Type: application/json' \
      --data @gcal-pvs.json \
      http://mkoteddev-lv1:17665/mgmt/bpl/archivePV
    # wait 5-10 min; PVs sit in METAINFO_GATHERING before they start archiving
    ./verify_pvs.py gcal-pvs.json

Adding a PV to the appliance does **not** put it in Grafana's PV browser - that
tree is `ted-api/pv_tree/channels/<SITE>/**/*.yaml` and must be edited
separately. Use `--check-tree` to find mismatches in both directions.
