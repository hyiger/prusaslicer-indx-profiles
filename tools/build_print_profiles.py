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

Geometry is sourced verbatim, except at HF1.0, which Prusa publishes nothing for:
there the line widths and layer ladder are 0.8's scaled by 1.25 (nozzles.py,
SCALED SIZES). Speeds are only derived where Prusa has not done
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
from decimal import Decimal
import io
import re
import sys
import textwrap

from nozzles import (NOZZLES, STD_VALIDATED, TIERS, COMMON_EDITS, SIZE_LABELS,
                     is_width, scale, speed_for)

BUNDLE_NAME = 'hyiger INDX'
BUNDLE_VERSION = '0.6.1'

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


def printer_models(cond):
    """The leading `printer_model=~/(...)/` clause of a compatible_printers_condition.

    Prusa scopes INDX filaments per family (since 2.5.12 the ABS, PC and PA ones
    leave out the CORE One L INDX, for which Prusa has only staged chamber
    values; there is no L INDX printer yet), so a derived preset keeps its
    base's clause rather than a fixed list of models."""
    m = re.match(r'\s*(printer_model\s*=~\s*/[^/]*/)', cond or '')
    if not m:
        raise SystemExit('refusing: no printer_model clause to keep in %r' % (cond or '')[:80])
    return m.group(1)


def assert_unsourced(sections, drafts, dia):
    """Refuse to scale a size Prusa has published anything for.

    The scaling rule (nozzles.py, SCALED SIZES) is approved only for a size with
    no Prusa source at all, and every scaled artifact says "Prusa publishes
    nothing at <dia> mm". This checks that claim against the file being built
    from instead of assuming it: any INDX common, PA section, sized material
    family (*PLA10HFC1INDX*), printer size common, print, printer or filament
    profile, draft, binding or printer nozzle at <dia> stops the build,
    so a re-pinned PrusaResearch.ini that adds a 1.0 source cannot be silently
    ignored in favor of the scaled 0.8 values."""
    tok = dia.replace('.', '')                                   # '1.0' -> '10'
    num = format(Decimal(dia).normalize(), 'f')                  # '1.0' -> '1'
    names = re.compile('|'.join([
        r'\*INDX_%s(hf)?_common\*' % tok,                        # per-nozzle INDX print common
        r'\*C1INDX_%s_common\*' % tok,                           # per-nozzle INDX filament common
        r'\*C1INDX_\w+_%s_PA\*' % tok,                           # per-nozzle INDX PA
        r'\*[A-Z]+%s(HF|PG|XL)[A-Za-z0-9+]*\*' % tok,            # sized family: *PLA10HFC1INDX*,
                                                                 #   *FLEX10PGC1INDX*, *ABS10HF*
        r'\*C1L?_%s\*' % tok,                                     # CORE One printer size common
        r'\*\w+_common%s\*' % tok,                                # other printers' size commons
        r'HF%s(?![\d.])' % re.escape(dia),                       # HF1.0 anything
        r'@COREONE(INDX)? %s(?![\d.])' % re.escape(dia),         # standard <dia> variants
        r' %s nozzle(?![\w])' % re.escape(dia),                  # <dia> printers
    ]))
    bound = re.compile(r'nozzle_diameter\[\d+\]\s*==\s*%s(\.0+)?(?![\d.])' % re.escape(num))
    fitted = re.compile(r'^\s*%s(\.0+)?\s*(,|$)' % re.escape(num))
    hits = []
    for where, secs in (('', sections), ('commented draft ', drafts)):
        for name, keys in secs.items():
            if names.search(name):
                hits.append('%s[%s]' % (where, name))
            if bound.search(keys.get('compatible_printers_condition', '')):
                hits.append('%s[%s] binds on nozzle_diameter == %s' % (where, name, dia))
            if name.startswith('printer:') and fitted.match(keys.get('nozzle_diameter', '')):
                hits.append('%s[%s] has a %s mm nozzle' % (where, name, dia))
    if hits:
        raise SystemExit(
            'refusing: %s mm is built by the scaling rule only because Prusa publishes\n'
            '          nothing at %s mm, but this PrusaResearch.ini does:\n            %s\n'
            '          Read Prusa\'s %s mm data instead of scaling past it; that needs a\n'
            '          human decision (CLAUDE.md, non-negotiable 1).'
            % (dia, dia, '\n            '.join(sorted(set(hits))[:12]), dia))


SPEED_KEYS = [('perimeter_speed', 'perim', 'perimeter_extrusion_width'),
              ('external_perimeter_speed', 'ext', 'external_perimeter_extrusion_width'),
              ('small_perimeter_speed', 'small', 'external_perimeter_extrusion_width'),
              ('infill_speed', 'infill', 'infill_extrusion_width'),
              ('solid_infill_speed', 'solid', 'solid_infill_extrusion_width'),
              ('top_solid_infill_speed', 'top', 'top_infill_extrusion_width')]


def shown(value):
    return 'unset' if value is None else value or '(empty)'


def why_lines(edits):
    """Header lines for [(where, key, old, new, why)], in the printer presets'
    `key: old -> new` / reason layout."""
    lines = []
    for where, key, old, new, why in edits:
        lines.append('#   %s%s: %s -> %s' % (where and where + ': ', key, shown(old), shown(new)))
        lines += ['#       ' + l for l in textwrap.wrap(why, 68)]
    return lines


def build_nozzle(vendor, noz, report, edits):
    """`edits` collects every key changed from the resolved common, with its
    reason: the COMMON_EDITS, then the per-tier Nozzle.extra."""
    common = collections.OrderedDict(resolve(vendor, 'print:' + noz.common))
    common.pop('renamed_from', None)  # new presets, not a rename of the common

    for key, (val, why) in COMMON_EDITS.items():
        if key == 'interlocking_beam_width':
            val = '%g' % (float(noz.dia) * 2)
        if common.get(key) != val:
            edits.append(('', key, common.get(key), val, why))
        common[key] = val

    if noz.scaled_from:
        scale_common(common, noz, edits)

    variants = collections.OrderedDict()
    for tier_key, tier_label, idx in TIERS:
        h = noz.layers[idx]
        o = collections.OrderedDict()
        o['layer_height'] = '%g' % h
        if noz.flow:
            for key, qk, wk in SPEED_KEYS:
                o[key] = str(speed_for(noz.flow[qk], float(common[wk]), h))
        # Prusa writes layer heights to two decimals: 0.20mm, 0.32mm.
        name = '%.2fmm %s @COREONEINDX %s' % (h, tier_label, noz.tag)
        for key, (val, why) in noz.extra.get(tier_key, {}).items():
            if common.get(key) != val:
                edits.append((name, key, common.get(key), val, why))
            o[key] = val
        variants[name] = o

    always = set.intersection(*(set(d) for d in variants.values()))
    for k in always:
        common.pop(k, None)
    missing = set().union(*(set(d) for d in variants.values())) - always - set(common)
    if missing:
        raise RuntimeError('%s: keys overridden by some tiers but absent from '
                           'the common: %s' % (noz.dia, sorted(missing)))

    report.append((noz, list(variants), common))
    return common, variants


def scale_common(common, noz, edits):
    """A size Prusa publishes nothing for (nozzles.py, SCALED SIZES): scale the
    source size's line widths by the diameter ratio and move its size labels.
    Every other key of the source common is held as it is."""
    src = noz.scaled_from
    widths = sorted(k for k in common if is_width(k))
    if not widths:
        raise SystemExit('refusing: %s has no line widths to scale for %s mm'
                         % (noz.common, noz.dia))
    for key in widths:
        old = common[key]
        # A percentage is already relative to the nozzle, and 0 means "auto":
        # scaling either would double-scale or invent a width. Refuse.
        if old.endswith('%') or float(old) <= 0:
            raise SystemExit('refusing: %s %s = %s is not an absolute width, so it '
                             'cannot be scaled to %s mm' % (noz.common, key, old, noz.dia))
        new = scale(old, noz.ratio)
        edits.append(('', key, old, new,
                      'line width: Prusa\'s %s mm value x %s/%s, half-up to 0.01. '
                      'Prusa publishes nothing at %s mm' % (src, noz.dia, src, noz.dia)))
        common[key] = new
    for key, (pattern, what) in sorted(SIZE_LABELS.items()):
        old = common.get(key, '')
        want, got = pattern % src, pattern % noz.dia
        hits = len(re.findall(re.escape(want) + r'(?![\d.])', old))
        if hits != 1:
            raise SystemExit('refusing: %s %s names %s mm %d times, not once, so the '
                             'size label cannot be moved to %s mm safely:\n  %s'
                             % (noz.common, key, src, hits, noz.dia, old))
        new = re.sub(re.escape(want) + r'(?![\d.])', got, old)
        edits.append(('', key, old, new, 'size label, moved from %s to %s mm: %s'
                      % (src, noz.dia, what)))
        common[key] = new


def build_std(vendor, dia, report, edits):
    """Prusa's HF<dia> INDX prints, rebound to a standard nozzle of the same size.
    `edits` collects each STD_EDITS key that changes a value, with its reason."""
    suffix = STD_SOURCE[dia]
    sources = [k for k in vendor if k.startswith('print:') and k.endswith(' ' + suffix)]
    if not sources:
        raise SystemExit('refusing: no "%s" print profiles in PrusaResearch.ini' % suffix)

    hf_bind, std_bind = STD_BIND[0] % dia, STD_BIND[1] % dia
    profiles = collections.OrderedDict()
    before = collections.defaultdict(set)   # STD_EDITS key -> Prusa's values
    for key in sources:
        r = collections.OrderedDict(resolve(vendor, key))
        cond = r.get('compatible_printers_condition', '')
        if cond.count(hf_bind) != 1:
            raise SystemExit('refusing: %s binds with %r, not on %r; the rebinding '
                             'needs a human decision' % (key, cond, hf_bind))
        r['compatible_printers_condition'] = cond.replace(hf_bind, std_bind)
        for k, (val, _why) in STD_EDITS.items():
            before[k].add(r.get(k))
            r[k] = val
        r.pop('renamed_from', None)
        name = key[len('print:'):-len(suffix)] + '@COREONEINDX ' + dia
        profiles[name] = r

    for k, (val, why) in STD_EDITS.items():
        if before[k] != {val}:
            old = next(iter(before[k])) if len(before[k]) == 1 else 'varies by profile'
            edits.append(('', k, old, val, why))

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
            if n.scaled_from:
                status = 'SCALED FROM %s - UNVALIDATED' % n.scaled_from
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
    scaled = [d for d in sorted(set(wanted), key=float) if NOZZLES[d].scaled_from]
    if scaled:
        drafts = load_drafts(args.vendor)
        for dia in scaled:
            assert_unsourced(vendor, drafts, dia)

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
    for dia in sorted(set(wanted), key=float):
        noz = NOZZLES[dia]
        edits = []
        common, variants = build_nozzle(vendor, noz, report, edits)
        if noz.scaled_from:
            w('\n# ---- %s mm : SCALED from Prusa %s (%s mm). Prusa publishes nothing\n'
              '#      at %s mm: line widths and layers x%s, everything else held at %s mm\n'
              '#      apart from the per-size COMMON_EDITS listed below.\n'
              % (dia, noz.common, noz.scaled_from, dia, noz.ratio.normalize(), noz.scaled_from))
        else:
            w('\n# ---- %s mm : resolved copy of Prusa %s\n' % (dia, noz.common))
        if not noz.validated:
            w('# UNVALIDATED: %s\n' % noz.note)
        if edits:
            w('#\n# Changed from Prusa\'s common (COMMON_EDITS%s, then per tier '
              'Nozzle.extra):\n' % (', then the %s/%s scaling and size labels'
                                     % (dia, noz.scaled_from) if noz.scaled_from else ''))
            w(''.join(l + '\n' for l in why_lines(edits)))
        if noz.flow:
            targets = ', '.join('%s %g' % (key[:-len('_speed')].replace('_', ' '), noz.flow[qk])
                                for key, qk, _ in SPEED_KEYS)
            w(''.join('# %s\n' % l for l in textwrap.wrap(
                'Speeds: the six main speeds of each tier are solved from the nozzles.py '
                'flow targets, in mm3/s: %s.' % targets, 74)))
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
        edits = []
        common, variants = build_std(vendor, dia, std_report, edits)
        hidden = '*COREONEINDX %s*' % dia
        w('\n# ---- %s mm standard nozzle : Prusa\'s "%s" prints, binding\n'
          '#      changed from nozzle_high_flow[0] to ! nozzle_high_flow[0]\n'
          % (dia, STD_SOURCE[dia]))
        if not STD_VALIDATED.get(dia, False):
            w('# UNVALIDATED: not yet test printed on a standard %s mm INDX nozzle.\n' % dia)
        if edits:
            w('#\n# Changed from Prusa\'s prints, in every profile (STD_EDITS):\n')
            w(''.join(l + '\n' for l in why_lines(edits)))
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
        if noz.scaled_from:
            print('\n%s mm  <- %s, SCALED from %s mm x%s   %d keys'
                  % (noz.dia, noz.common, noz.scaled_from, noz.ratio.normalize(), len(common)))
        else:
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
