#!/usr/bin/env python3
"""
Build a PrusaSlicer system vendor bundle of print profiles for the Prusa
CORE One INDX, for nozzle sizes Prusa does not ship print profiles for.

Prusa's only INDX printer variant is `HF0.4`. It ships print profiles for HF0.4
and, since PrusaResearch 2.5.x, for 0.25 and 0.3 as well. PrusaResearch.ini
also contains high-flow commons for 0.5 / 0.6 / 0.8 (`*INDX_06hf_common*` and
so on), complete with widths, solid-layer counts, support parameters and infill
anchors, that no released profile inherits from.

This resolves the requested commons and emits them as usable profiles.

Geometry is sourced verbatim. Speeds are only derived where Prusa has not done
a speed pass on the size-specific common - see tools/nozzles.py. Inheritance
cannot cross bundle files, so values are embedded rather than referenced. Keys
the chain does not set are left to PrusaSlicer's defaults, as upstream does.

--std 0.4 adds profiles for a standard (non-high-flow) 0.4 mm nozzle. Prusa's
four INDX HF0.4 prints all bind on `nozzle_high_flow[0]`, so a standard 0.4
toolhead gets no print profile at all. They are re-emitted unchanged except for
that binding, which becomes `! nozzle_high_flow[0]`. The filament's max
volumetric speed (see derive_std_filaments.py) is what slows a standard nozzle
down, exactly as on Prusa's CORE One, whose STD and HF0.4 prints differ by only
a few speeds.

    python3 build_print_profiles.py PrusaResearch.ini out.ini --nozzle 0.6
    python3 build_print_profiles.py PrusaResearch.ini out.ini -n 0.6 -n 0.8
    python3 build_print_profiles.py PrusaResearch.ini out.ini -n 0.6 --std 0.4
"""
import argparse
import collections
import io
import re
import sys

from nozzles import NOZZLES, STD_VALIDATED, TIERS, COMMON_EDITS, speed_for

BUNDLE_NAME = 'hyiger INDX'
BUNDLE_VERSION = '0.4.0'

# Standard-nozzle sizes: Prusa's print profiles for the matching HF size, rebound.
STD_SOURCE = {'0.4': '@COREONEINDX HF0.4'}
STD_BIND = ('nozzle_diameter[0]==%s and nozzle_high_flow[0]',
            'nozzle_diameter[0]==%s and ! nozzle_high_flow[0]')
# Edits applied to every standard-nozzle profile, with the reason recorded.
STD_EDITS = {
    'print_settings_id': ('', 'system preset hygiene'),
    'compatible_printers': ('', 'condition-based binding only'),
}


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


def load_drafts(path):
    """Prusa's commented-out sections ("; [printer:...]" then "; key = value"),
    uncommented. They are Prusa's unreleased profiles, e.g. INDX 0.25."""
    drafts, cur = collections.OrderedDict(), None
    with open(path, encoding='utf-8') as f:
        for line in f:
            s = line.rstrip('\n')
            m = re.match(r'^;\s*\[(\w+:.+)\]\s*$', s)
            if m:
                cur = drafts.setdefault(m.group(1), collections.OrderedDict())
            elif cur is not None and s.startswith('; ') and '=' in s:
                k, v = s[2:].split('=', 1)
                cur[k.strip()] = v.strip()
            else:
                cur = None
    return drafts


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
    # PrusaSlicer never inherits renamed_from; it belongs to one concrete preset.
    out.pop('renamed_from', None)
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


def build_std(vendor, dia, report):
    """Prusa's HF<dia> INDX prints, rebound to a standard nozzle of the same size."""
    suffix = STD_SOURCE[dia]
    sources = [k for k in vendor if k.startswith('print:') and k.endswith(' ' + suffix)]
    if not sources:
        raise SystemExit('refusing: no "%s" print profiles in PrusaResearch.ini' % suffix)

    hf_bind, std_bind = STD_BIND[0] % dia, STD_BIND[1] % dia
    profiles = collections.OrderedDict()
    for key in sources:
        r = collections.OrderedDict(resolve(vendor, key))
        cond = r.get('compatible_printers_condition', '')
        if cond.count(hf_bind) != 1:
            raise SystemExit('refusing: %s binds with %r, not on %r; the rebinding '
                             'needs a human decision' % (key, cond, hf_bind))
        r['compatible_printers_condition'] = cond.replace(hf_bind, std_bind)
        for k, (val, _why) in STD_EDITS.items():
            r[k] = val
        r.pop('renamed_from', None)
        name = key[len('print:'):-len(suffix)] + '@COREONEINDX ' + dia
        profiles[name] = r

    first = next(iter(profiles.values()))
    common = collections.OrderedDict(
        (k, v) for k, v in first.items() if all(p.get(k) == v for p in profiles.values()))
    variants = collections.OrderedDict(
        (n, collections.OrderedDict((k, v) for k, v in p.items() if k not in common))
        for n, p in profiles.items())
    report.append(('%s (standard)' % dia, list(variants), common))
    return common, variants


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('vendor', help='path to PrusaResearch.ini')
    ap.add_argument('out', help='output vendor bundle .ini')
    ap.add_argument('-n', '--nozzle', action='append', dest='nozzles',
                    metavar='DIA', help='nozzle size; repeatable (default: 0.6)')
    ap.add_argument('--std', action='append', dest='stds', default=[], metavar='DIA',
                    help='also emit standard (non-HF) nozzle profiles; repeatable '
                         '(known: %s)' % ', '.join(sorted(STD_SOURCE)))
    ap.add_argument('--list', action='store_true', help='list known sizes and exit')
    args = ap.parse_args()

    if args.list:
        print('%-6s %-22s %-22s %s' % ('dia', 'upstream common', 'layers', 'status'))
        for d, n in sorted(NOZZLES.items(), key=lambda kv: float(kv[0])):
            status = 'validated' if n.validated else 'UNVALIDATED'
            if n.flow is None and not n.validated:
                status = 'NO TARGETS - speeds untouched'
            if n.shipped:
                status = 'SHIPPED BY PRUSA - not built'
            print('%-6s %-22s %-22s %s' % (
                d, n.common, '/'.join('%.2f' % x for x in n.layers), status))
            print('%-6s %s' % ('', '  ' + (n.shipped or n.note)))
        for d, suffix in sorted(STD_SOURCE.items()):
            print('%-6s %-22s %-22s %s' % (d + ' STD', suffix, 'as Prusa HF' + d,
                                           'rebinding of Prusa\'s own profiles'))
        return 0

    wanted = args.nozzles or ['0.6']
    unknown = [d for d in wanted if d not in NOZZLES]
    if unknown:
        sys.exit('unknown nozzle size(s): %s\nknown: %s\n(0.2 is not an INDX '
                 'size - the smallest Prusa defines is 0.25)'
                 % (', '.join(unknown), ', '.join(sorted(NOZZLES))))
    shipped = [d for d in wanted if NOZZLES[d].shipped]
    if shipped:
        sys.exit('refusing: Prusa ships print profiles for %s mm itself (%s). '
                 'Building them here would only duplicate Prusa\'s.'
                 % (', '.join(shipped), '; '.join(NOZZLES[d].shipped for d in shipped)))
    bad_std = [d for d in args.stds if d not in STD_SOURCE]
    if bad_std:
        sys.exit('refusing --std %s: only %s has Prusa high-flow prints to rebind. '
                 'Prusa\'s 0.25 and 0.3 INDX prints already bind on diameter alone.'
                 % (', '.join(bad_std), ', '.join(sorted(STD_SOURCE))))

    vendor = load(args.vendor)
    version = vendor.get('vendor', {}).get('config_version', '?')

    buf = io.StringIO()
    w = buf.write
    w('# Print profiles for the Prusa CORE One INDX (8T / 4T), by hyiger.\n')
    w('# Generated by tools/build_print_profiles.py from PrusaResearch.ini\n')
    w('# config_version %s. Geometry comes from Prusa per-nozzle commons;\n' % version)
    w('# standard-nozzle (STD) profiles are Prusa\'s HF ones of the same size,\n')
    w('# rebound to a non-high-flow nozzle.\n')
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

    std_report = []
    for dia in sorted(set(args.stds), key=float):
        common, variants = build_std(vendor, dia, std_report)
        hidden = '*COREONEINDX %s*' % dia
        w('\n# ---- %s mm standard nozzle : Prusa\'s "%s" prints, binding\n'
          '#      changed from nozzle_high_flow[0] to ! nozzle_high_flow[0]\n'
          % (dia, STD_SOURCE[dia]))
        if not STD_VALIDATED.get(dia, False):
            w('# UNVALIDATED: not yet test printed on a standard %s mm INDX nozzle.\n' % dia)
        w('\n[print:%s]\n' % hidden)
        for k in sorted(common):
            w('%s = %s\n' % (k, common[k]))
        for name, over in variants.items():
            w('\n[print:%s]\n' % name)
            w('inherits = %s\n' % hidden)
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
    for dia, (label, names, common) in zip(sorted(set(args.stds), key=float), std_report):
        print('\n%s  <- Prusa\'s own profiles, rebound   %d shared keys' % (label, len(common)))
        if not STD_VALIDATED.get(dia, False):
            warn = True
            print('  !! UNVALIDATED: not yet test printed on a standard nozzle')
        for n in names:
            print('     %s' % n)
    if warn:
        print('\n!! At least one size is unvalidated. Calibrate max volumetric')
        print('   speed before trusting any of those speeds.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
