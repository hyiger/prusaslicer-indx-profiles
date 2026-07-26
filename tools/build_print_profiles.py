#!/usr/bin/env python3
"""
Build a PrusaSlicer system vendor bundle of print profiles for the Prusa
CORE One INDX, for any nozzle size Prusa has defined a common for.

Prusa ships INDX profiles for 0.4 mm only - `variants = HF0.4` is the whole
list for both INDX models. But PrusaResearch.ini already contains per-nozzle
commons for 0.25 / 0.3 / 0.5 / 0.6 / 0.8, complete with widths, solid-layer
counts, support parameters and infill anchors. They are unreleased scaffolding:
nothing inherits from them and no variant declares them.

This resolves the requested commons and emits them as usable profiles.

Geometry is sourced verbatim. Speeds are only derived where Prusa has not done
a speed pass on the size-specific common - see tools/nozzles.py. Inheritance
cannot cross bundle files, so values are embedded rather than referenced. Keys
the chain does not set are left to PrusaSlicer's defaults, as upstream does.

    python3 build_print_profiles.py PrusaResearch.ini out.ini --nozzle 0.6
    python3 build_print_profiles.py PrusaResearch.ini out.ini -n 0.6 -n 0.8
"""
import argparse
import collections
import io
import re
import sys

from nozzles import NOZZLES, TIERS, COMMON_EDITS, speed_for

BUNDLE_NAME = 'hyiger INDX'
BUNDLE_VERSION = '0.3.0'


def load(path):
    sections, cur = collections.OrderedDict(), None
    with open(path, encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            m = re.match(r'^\[(.+)\]$', s)
            if m:
                cur = m.group(1)
                sections.setdefault(cur, collections.OrderedDict())
                continue
            if not s or s.startswith('#') or s.startswith(';'):
                continue
            if cur is not None and '=' in line:
                k, v = line.split('=', 1)
                sections[cur][k.strip()] = v.strip()
    return sections


def resolve(sections, name, seen=None):
    seen = set() if seen is None else seen
    if name in seen:
        raise RuntimeError('inheritance cycle at ' + name)
    seen.add(name)
    if name not in sections:
        raise KeyError(name)
    kind = name.split(':', 1)[0]
    raw = sections[name]
    out = collections.OrderedDict()
    for parent in [p.strip() for p in raw.get('inherits', '').split(';') if p.strip()]:
        out.update(resolve(sections, kind + ':' + parent, set(seen)))
    for k, v in raw.items():
        if k != 'inherits':
            out[k] = v
    return out


SPEED_KEYS = [('perimeter_speed', 'perim', 'perimeter_extrusion_width'),
              ('external_perimeter_speed', 'ext', 'external_perimeter_extrusion_width'),
              ('small_perimeter_speed', 'small', 'external_perimeter_extrusion_width'),
              ('infill_speed', 'infill', 'infill_extrusion_width'),
              ('solid_infill_speed', 'solid', 'solid_infill_extrusion_width'),
              ('top_solid_infill_speed', 'top', 'top_infill_extrusion_width')]


def build_nozzle(vendor, noz, report):
    common = collections.OrderedDict(resolve(vendor, 'print:' + noz.common))

    for key, (val, _why) in COMMON_EDITS.items():
        if key == 'interlocking_beam_width':
            val = '%g' % (float(noz.dia) * 2)
        common[key] = val

    variants = collections.OrderedDict()
    for tier_key, tier_label, idx in TIERS:
        h = noz.layers[idx]
        o = collections.OrderedDict()
        o['layer_height'] = '%g' % h
        if noz.flow:
            for key, qk, wk in SPEED_KEYS:
                o[key] = str(speed_for(noz.flow[qk], float(common[wk]), h))
        o.update(noz.extra.get(tier_key, {}))
        # Prusa writes layer heights to two decimals: 0.20mm, 0.32mm.
        variants['%.2fmm %s @COREONEINDX %s' % (h, tier_label, noz.tag)] = o

    always = set.intersection(*(set(d) for d in variants.values()))
    for k in always:
        common.pop(k, None)
    missing = set().union(*(set(d) for d in variants.values())) - always - set(common)
    if missing:
        raise RuntimeError('%s: keys overridden by some tiers but absent from '
                           'the common: %s' % (noz.dia, sorted(missing)))

    report.append((noz, list(variants), common))
    return common, variants


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('vendor', help='path to PrusaResearch.ini')
    ap.add_argument('out', help='output vendor bundle .ini')
    ap.add_argument('-n', '--nozzle', action='append', dest='nozzles',
                    metavar='DIA', help='nozzle size; repeatable (default: 0.6)')
    ap.add_argument('--list', action='store_true', help='list known sizes and exit')
    args = ap.parse_args()

    if args.list:
        print('%-6s %-22s %-22s %s' % ('dia', 'upstream common', 'layers', 'status'))
        for d, n in sorted(NOZZLES.items(), key=lambda kv: float(kv[0])):
            status = 'validated' if n.validated else 'UNVALIDATED'
            if n.flow is None and not n.validated:
                status = 'NO TARGETS - speeds untouched'
            print('%-6s %-22s %-22s %s' % (
                d, n.common, '/'.join('%.2f' % x for x in n.layers), status))
            print('%-6s %s' % ('', '  ' + n.note))
        return 0

    wanted = args.nozzles or ['0.6']
    unknown = [d for d in wanted if d not in NOZZLES]
    if unknown:
        sys.exit('unknown nozzle size(s): %s\nknown: %s\n(0.2 is not an INDX '
                 'size - the smallest Prusa defines is 0.25)'
                 % (', '.join(unknown), ', '.join(sorted(NOZZLES))))

    vendor = load(args.vendor)
    version = vendor.get('vendor', {}).get('config_version', '?')

    buf = io.StringIO()
    w = buf.write
    w('# Print profiles for the Prusa CORE One INDX (8T / 4T), by hyiger.\n')
    w('# Generated by tools/build_print_profiles.py from PrusaResearch.ini\n')
    w('# config_version %s. Geometry comes from Prusa per-nozzle commons.\n' % version)
    w('#\n')
    w('# Install: copy this file and the .idx into <datadir>/vendor/\n')
    w('# templates_profile = 1 lets these attach to the Prusa-vendor INDX\n')
    w('# printer while still loading as read-only system presets.\n')
    w('\n[vendor]\n')
    w('repo_id = non-prusa-fff\n')
    w('name = %s\n' % BUNDLE_NAME)
    w('config_version = %s\n' % BUNDLE_VERSION)
    w('templates_profile = 1\n')

    report = []
    for dia in sorted(wanted, key=float):
        noz = NOZZLES[dia]
        common, variants = build_nozzle(vendor, noz, report)
        w('\n# ---- %s mm : resolved copy of Prusa %s\n' % (dia, noz.common))
        if not noz.validated:
            w('# UNVALIDATED: %s\n' % noz.note)
        w('\n[print:%s]\n' % noz.hidden_common)
        for k in sorted(common):
            w('%s = %s\n' % (k, common[k]))
        for name, over in variants.items():
            w('\n[print:%s]\n' % name)
            w('inherits = %s\n' % noz.hidden_common)
            for k in sorted(over):
                w('%s = %s\n' % (k, over[k]))

    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(buf.getvalue())

    print('wrote %s  (from PrusaResearch config_version %s)' % (args.out, version))
    warn = False
    for noz, names, common in report:
        print('\n%s mm  <- %s   %d keys sourced' % (noz.dia, noz.common, len(common)))
        if not noz.validated:
            warn = True
            print('  !! UNVALIDATED: %s' % noz.note)
        for n in names:
            print('     %s' % n)
    if warn:
        print('\n!! At least one size is unvalidated. Calibrate max volumetric')
        print('   speed before trusting any of those speeds.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
