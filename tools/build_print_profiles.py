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

--layout emits profiles for a mixed tool layout instead of one nozzle size:
different nozzles on different tools of one toolchanger, which is Prusa's own
"experimental printing with different nozzle diameters" workflow
(help.prusa3d.com article 821176). The profiles are Prusa's own, for whichever
tool prints the perimeters, with every role pinned to a tool; a role on another
tool takes that tool's own width from Prusa's profile for it and a speed
re-solved to that profile's own volumetric rate. See nozzles.py, MIXED TOOL
LAYOUTS.

    python3 build_print_profiles.py PrusaResearch.ini out.ini --nozzle 0.6
    python3 build_print_profiles.py PrusaResearch.ini out.ini -n 0.6 -n 0.8
    python3 build_print_profiles.py PrusaResearch.ini out.ini -n 0.6 --std 0.4
    python3 build_print_profiles.py PrusaResearch.ini out.ini --layout 0.25+HF0.4
"""
import argparse
import collections
from decimal import Decimal
import io
import re
import sys
import textwrap

from nozzles import (LAYOUTS, NOZZLES, ROLE_ANCHOR, ROLE_KEYS, STD_VALIDATED,
                     TIERS, COMMON_EDITS, SIZE_LABELS, area, combine_layers,
                     is_width, scale, speed_for, split_tag, tool_runs)

BUNDLE_NAME = 'hyiger INDX'
BUNDLE_VERSION = '0.7.1'

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


# --- mixed tool layouts ------------------------------------------------------
# Prusa's "experimental printing with different nozzle diameters" workflow
# (help.prusa3d.com article 821176) on an INDX. See nozzles.py, MIXED TOOL
# LAYOUTS, for what PrusaSlicer does with a mixed printer and why the widths
# stay explicit here.

# Prusa's own print profiles for a layout's base tool - the tool that prints
# perimeters, whose nozzle therefore sets the layer ladder and the surface
# geometry. A layout is built from these, one per tier, not from the bare
# common: Prusa tunes the solid-layer counts per tier (11/9 at 0.07 mm down to
# 6/5 at 0.15, where it also widens the perimeters), and flattening the common
# over every tier would silently put the finest tier's shell on the coarsest.
# A tag that is not listed cannot be a base tool.
LAYOUT_BASE = {
    '0.25': ('@COREONEINDX 0.25',
             "Prusa's own INDX 0.25 prints, on the one INDX common with a real "
             'speed pass. 0.25 has no high-flow variant upstream, so these are '
             "a standard 0.25 nozzle's profiles"),
}

# The width each moved role's speed is solved against, from PrintRegion::flow
# (PrintRegion.cpp:38-65). bridge_speed is deliberately absent: a bridge runs on
# Flow::bridging_flow, whose width and height both come from the nozzle rather
# than from a width key, so moving solid infill to another tool must stop the
# build until someone works that formula through.
ROLE_SPEED_WIDTH = {
    'perimeter_speed': 'perimeter_extrusion_width',
    'external_perimeter_speed': 'external_perimeter_extrusion_width',
    'small_perimeter_speed': 'external_perimeter_extrusion_width',
    'gap_fill_speed': 'perimeter_extrusion_width',
    'infill_speed': 'infill_extrusion_width',
    'solid_infill_speed': 'solid_infill_extrusion_width',
    'top_solid_infill_speed': 'top_infill_extrusion_width',
}

ROLE_WHY = ('tool %d carries the %s nozzle and prints this role. Every role a '
            'layout moves must be pinned: left at Prusa\'s 0 it follows '
            'whichever tool happens to be loaded, so neither its width nor its '
            'speed could be attributed to a nozzle')

# Why the tiers are renamed rather than keeping Prusa's own names. Unlike the
# --std 0.4 copies, which share Prusa's aliases harmlessly because no printer
# accepts both bindings, a mixed printer satisfies Prusa's own base-tool
# condition too (nozzle_diameter[0]==0.25), so Prusa's profiles are compatible
# alongside these. PresetCollection::update_compatible_internal
# (Preset.cpp:1388-1401) then marks a templates-vendor preset incompatible
# whenever a compatible non-templates preset has the same alias - the name
# before '@' - which would hide every profile in this layout behind Prusa's.
RENAME_WHY = ('renamed to this repo\'s own tier labels: a mixed printer also '
              'satisfies Prusa\'s own %s condition, so sharing an alias with '
              'Prusa\'s profiles would hide these behind them '
              '(Preset.cpp:1388-1401)')


def layout_tiers(vendor, layout):
    """Prusa's own profiles for the base tool, one per tier, coarsest last.

    Returns [(tier_label, emitted name, resolved Prusa profile, Prusa's name)].
    """
    base_tag = layout.tool_tag(layout.base_tool)
    if base_tag not in LAYOUT_BASE:
        raise SystemExit(
            'refusing: %s is not a reviewed base tool for a layout (known: %s).\n'
            '          The base tool prints perimeters, so its profiles supply the\n'
            '          ladder and the surface geometry; naming the wrong one would\n'
            '          silently build the whole layout on the wrong nozzle.'
            % (base_tag, ', '.join(sorted(LAYOUT_BASE))))
    suffix = LAYOUT_BASE[base_tag][0]
    sources = [k for k in vendor
               if k.startswith('print:') and k.endswith(' ' + suffix)]
    if len(sources) != len(TIERS):
        raise SystemExit(
            'refusing: Prusa ships %d "%s" print profiles, and a layout emits %d '
            'tiers.\n          Which of them map to %s is a human decision.\n'
            '            %s'
            % (len(sources), suffix, len(TIERS),
               '/'.join(label for _k, label, _i in TIERS),
               '\n            '.join(sorted(sources)) or '(none)'))
    resolved = []
    for key in sources:
        r = collections.OrderedDict(resolve(vendor, key))
        resolved.append((absolute(r.get('layer_height'), key + ' layer_height'),
                         key[len('print:'):], r))
    resolved.sort()
    out = []
    for (h, prusa_name, r), (_tier_key, label, _idx) in zip(resolved, TIERS):
        out.append((label, '%.2fmm %s @COREONEINDX %s' % (h, label, layout.key),
                    r, prusa_name))
    return out


def layout_balanced_profile(vendor, layout):
    """The Balanced profile this layout emits: the printer preset's pointer.
    Read through layout_tiers() so the two generators can never disagree."""
    label = next(l for k, l, _i in TIERS if k == 'balanced')
    return next(name for lbl, name, _c, _p in layout_tiers(vendor, layout)
                if lbl == label)


def absolute(value, what):
    """A width, speed or height this repo can do arithmetic on. A percentage is
    relative to something else and 0 means "auto", so neither can be carried
    across to another nozzle's geometry."""
    if value is None or value.endswith('%') or float(value) <= 0:
        raise SystemExit('refusing: %s is %s, not an absolute value, so it '
                         'cannot be moved to another tool\'s geometry'
                         % (what, shown(value)))
    return float(value)


def anchor_rate(anchor, speed_key, name):
    """The volumetric rate Prusa's own profile for that nozzle runs this role
    at: its width and its layer height carry its speed."""
    width_key = ROLE_SPEED_WIDTH.get(speed_key)
    if width_key is None:
        raise SystemExit(
            'refusing: %s has no width to solve it against (ROLE_SPEED_WIDTH), so '
            'it\n          cannot be moved to another tool. bridge_speed is the '
            'known case:\n          a bridge runs on Flow::bridging_flow, not on a '
            'width key.' % speed_key)
    w = absolute(anchor.get(width_key), '%s %s' % (name, width_key))
    h = absolute(anchor.get('layer_height'), '%s layer_height' % name)
    q = area(w, h) * absolute(anchor.get(speed_key), '%s %s' % (name, speed_key))
    return q, width_key


def combine_cap(layout):
    """The combined sparse-infill height PrusaSlicer will allow in this layout.

    PrintObject::combine_infill (PrintObject.cpp:3126-3132) caps it at the
    smaller of the infill and solid-infill extruders' nozzles - so a layout that
    keeps solid infill on the small nozzle is capped by the small nozzle however
    large the infill one is. The second term is PrusaSlicer's own default
    ceiling for a nozzle's layer height, 0.75 x diameter (Slicing.cpp:48), which
    keeps a combined extrusion inside what that nozzle is asked to lay down
    anywhere else.
    """
    infill = float(layout.dia(layout.roles['infill_extruder']))
    solid = float(layout.dia(layout.roles['solid_infill_extruder']))
    return min(min(infill, solid), 0.75 * infill)


def role_anchor(vendor, layout, role, pos):
    tag = layout.tool_tag(pos)
    if tag not in ROLE_ANCHOR:
        raise SystemExit(
            'refusing: no Prusa print profile is recorded for a %s tool '
            '(ROLE_ANCHOR),\n          so role %s cannot be moved onto tool %d: '
            'its widths and its\n          volumetric rate would have no source.'
            % (tag, role, pos))
    name, why = ROLE_ANCHOR[tag]
    if 'print:' + name not in vendor:
        raise SystemExit('refusing: ROLE_ANCHOR names [print:%s], which this '
                         'PrusaResearch.ini\n          does not define.' % name)
    return name, why, collections.OrderedDict(resolve(vendor, 'print:' + name))


def build_layout(vendor, layout, report, edits):
    """A mixed-nozzle tool layout: Prusa's own profiles for the base tool, with
    every role pinned to a tool, and each role that sits on another tool taking
    that tool's own width from Prusa's profile for it plus a speed re-solved to
    that profile's own volumetric rate at this layout's geometry."""
    unpinned = sorted(set(ROLE_KEYS) - set(layout.roles))
    unknown = sorted(set(layout.roles) - set(ROLE_KEYS))
    if unpinned or unknown:
        raise SystemExit(
            'refusing: layout %s %s.\n'
            '          A layout must pin every role PrusaSlicer can assign: one\n'
            '          left at Prusa\'s 0 follows whichever tool is loaded, so its\n'
            '          nozzle - and so its widths and speeds - cannot be known.'
            % (layout.key,
               ' and '.join(filter(None, [
                   'leaves %s unpinned' % ', '.join(unpinned) if unpinned else '',
                   'pins %s, which is not a role in ROLE_KEYS'
                   % ', '.join(unknown) if unknown else '']))))

    base_pos = layout.base_tool
    base_tag = layout.tool_tag(base_pos)
    tiers = layout_tiers(vendor, layout)
    base_dia = split_tag(base_tag)[0]

    moved = [(role, pos) for role, pos in sorted(layout.roles.items())
             if pos != base_pos and ROLE_KEYS[role]]
    cap = combine_cap(layout)
    combining = any('infill_speed' in ROLE_KEYS[role] for role, _pos in moved)

    changes, profiles, rates = [], collections.OrderedDict(), []
    for label, name, cfg, prusa_name in tiers:
        cfg.pop('renamed_from', None)   # names Prusa's preset, never this one
        h = absolute(cfg.get('layer_height'), name + ' layer_height')

        def change(key, val, why, _name=name, _cfg=cfg):
            changes.append((_name, key, _cfg.get(key), val, why))
            _cfg[key] = val

        for key, (val, why) in COMMON_EDITS.items():
            if key == 'interlocking_beam_width':
                # 2 x nozzle has no meaning with two nozzles fitted, and the key
                # is inert unless interlocking beams are on. Left unset, as on
                # the --std path.
                continue
            change(key, val, why)
        for role, pos in sorted(layout.roles.items()):
            change(role, str(pos), ROLE_WHY % (pos, layout.tool_tag(pos)))
        for key, (val, why) in sorted(layout.extra.items()):
            change(key, val, why)

        # Sparse infill is the one role whose extrusion is not one layer tall:
        # with combining on, PrusaSlicer stacks up to n layers into a single
        # extrusion, so that is the height its speed must be solved at.
        n = combine_layers(cap, h) if combining else 1
        if combining:
            change('infill_every_layers', str(n),
                   'up to %g mm of combined sparse infill at this layer height, '
                   'which is all PrusaSlicer will combine here '
                   '(PrintObject.cpp:3126-3132, Slicing.cpp:48). It also cuts the '
                   'tool changes a split role costs from one pair per layer to '
                   'one pair per %d' % (cap, n))

        for role, pos in moved:
            anchor_name, anchor_why, anchor = role_anchor(vendor, layout, role, pos)
            # Widths first: each speed is solved against the width this profile
            # will actually emit, not the one it inherited.
            for key in sorted(ROLE_KEYS[role],
                              key=lambda k: not k.endswith('_extrusion_width')):
                if key.endswith('_extrusion_width'):
                    # Must be a length to be a nozzle's own width. Kept exactly
                    # as Prusa writes it rather than reformatted.
                    absolute(anchor.get(key), '%s %s' % (anchor_name, key))
                    change(key, anchor[key],
                           'tool %d\'s own width: Prusa\'s %s. %s'
                           % (pos, anchor_name, anchor_why))
                    continue
                q, width_key = anchor_rate(anchor, key, anchor_name)
                height = h * n if key == 'infill_speed' else h
                w = absolute(cfg.get(width_key), '%s %s' % (name, width_key))
                own = int(float(anchor[key]))
                speed = min(speed_for(q, w, height), own)
                if speed <= 0:
                    raise SystemExit(
                        'refusing: %s solves to %d mm/s at %g x %g mm. PrusaSlicer '
                        'reads\n          0 as "auto", not as "very slow", so this '
                        'cannot be emitted.' % (key, speed, w, height))
                change(key, str(speed),
                       'tool %d (%s) prints this role: solved to the %.1f mm3/s '
                       'Prusa\'s %s runs it at, over %g mm wide and %g mm tall, '
                       'and never past that profile\'s own %d mm/s. %s'
                       % (pos, layout.tool_tag(pos), q, anchor_name, w, height,
                          own, anchor_why))
                rates.append((name, key, pos, layout.tool_tag(pos), n, speed,
                              area(w, height) * speed, q, own, anchor_name))

        for key, (pattern, what) in sorted(SIZE_LABELS.items()):
            if key == 'compatible_printers_condition':
                continue        # built from the layout below, not moved

            old = cfg.get(key, '')
            want, got = pattern % base_dia, pattern % layout.key
            hits = len(re.findall(re.escape(want) + r'(?![\d.])', old))
            if hits != 1:
                raise SystemExit('refusing: %s %s names %s mm %d times, not once, '
                                 'so the layout label cannot be moved safely:\n  %s'
                                 % (prusa_name, key, base_dia, hits, old))
            change(key, re.sub(re.escape(want) + r'(?![\d.])', got, old),
                   'layout label, moved from the base tool\'s %s to %s: %s'
                   % (base_dia, layout.key, what))

        clauses = [printer_models(cfg.get('compatible_printers_condition', ''))]
        for pos in layout.pinned_tools:
            clauses.append('nozzle_diameter[%d]==%s' % (pos - 1, layout.dia(pos)))
            clauses.append('%snozzle_high_flow[%d]'
                           % ('' if layout.high_flow(pos) else '! ', pos - 1))
        change('compatible_printers_condition', ' and '.join(clauses),
               'binds on each tool this layout prints with, by index, and on '
               'nothing else: a tool it never uses says nothing about the layout. '
               'Print presets are matched against the printer as written '
               '(Preset.cpp:1352-1368), and an index past the end of a vector '
               'reads element 0 rather than throwing (PlaceholderParser.cpp:1074), '
               'so a clause on tool 2 is safe to evaluate on any printer')

        changes.append((name, 'profile name', prusa_name, name,
                        RENAME_WHY % LAYOUT_BASE[base_tag][0]))
        profiles[name] = cfg

    # A change every tier makes identically is reported once, without a tier
    # name; one that differs per tier is reported per tier.
    order, grouped = [], collections.OrderedDict()
    for name, key, old, new, why in changes:
        if old == new:
            continue
        grouped.setdefault((key, old, new, why), []).append(name)
        if key not in order:
            order.append(key)
    for key in order:
        for (k, old, new, why), names in grouped.items():
            if k != key:
                continue
            where = '' if len(names) == len(profiles) else ', '.join(names)
            edits.append((where, key, old, new, why))

    first = next(iter(profiles.values()))
    common = collections.OrderedDict(
        (k, v) for k, v in first.items() if all(p.get(k) == v for p in profiles.values()))
    variants = collections.OrderedDict(
        (n, collections.OrderedDict((k, v) for k, v in p.items() if k not in common))
        for n, p in profiles.items())
    report.append((layout, list(variants), common, rates))
    return common, variants


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
    ap.add_argument('--layout', action='append', dest='layouts', default=[],
                    choices=sorted(LAYOUTS), metavar='KEY',
                    help='also emit profiles for a mixed tool layout; '
                         'repeatable (known: %s)' % ', '.join(sorted(LAYOUTS)))
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
        for key, lo in sorted(LAYOUTS.items()):
            base = lo.tool_tag(lo.base_tool)
            print('%-12s %-24s %-14s %s'
                  % (key, LAYOUT_BASE.get(base, ('?',))[0], 'as Prusa ' + base,
                     'MIXED LAYOUT %s - %s'
                     % (lo.model, 'validated' if lo.validated else 'UNVALIDATED')))
            print('%-12s   %s' % ('', tool_runs(lo.tools)))
        return 0

    # 0.6 only as the bare default; asking for a --std size or a --layout
    # on its own must not drag a high-flow size in with it.
    wanted = args.nozzles or ([] if args.stds or args.layouts else ['0.6'])
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
    w('# rebound to a non-high-flow nozzle; a mixed tool layout is Prusa\'s own\n')
    w('# profiles for the tool that prints perimeters, with each role pinned to\n')
    w('# a tool and the moved ones taking that tool\'s width and rate.\n')
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

    layout_report = []
    for key in sorted(set(args.layouts)):
        layout = LAYOUTS[key]
        edits = []
        common, variants = build_layout(vendor, layout, layout_report, edits)
        base_tag = layout.tool_tag(layout.base_tool)
        w('\n# ---- %s : MIXED tool layout on an INDX %s\n' % (layout.key, layout.model))
        w('#      %s\n' % tool_runs(layout.tools))
        w(''.join('#      %s\n' % l for l in textwrap.wrap(
            'Prusa\'s own "%s" print profiles, renamed and rebound: tool %d\'s %s '
            'nozzle prints the perimeters, so its profiles carry the layer ladder '
            'and the surface geometry. %s'
            % (LAYOUT_BASE[base_tag][0], layout.base_tool, base_tag,
               LAYOUT_BASE[base_tag][1]), 68)))
        w('#      Roles:  %s\n' % '; '.join(
            '%s tool %d (%s)' % (role.replace('_extruder', ''), pos,
                                 layout.tool_tag(pos))
            for role, pos in sorted(layout.roles.items())))
        if not layout.validated:
            w('# UNVALIDATED: %s\n' % layout.note)
        if edits:
            w('#\n# Changed from Prusa\'s own profiles (COMMON_EDITS, the role '
              'pinning, the\n# layout\'s own decisions, then the moved roles). A '
              'change named with a\n# profile applies to that tier only:\n')
            w(''.join(l + '\n' for l in why_lines(edits)))
        rates = next(r for lo, _n, _c, r in layout_report if lo is layout)
        if rates:
            w('#\n# Moved roles, tier by tier. Each speed is solved so the rate '
              'matches the one\n# Prusa\'s own profile for that tool runs the role '
              'at, and is never faster than\n# that profile\'s own speed:\n')
            for name, k, pos, tag, n, speed, got, want, cap, src in rates:
                w('#   %-42s %s = %s mm/s on tool %d (%s)\n'
                  % (name, k, speed, pos, tag))
                w('#       %.1f mm3/s against Prusa\'s %.1f%s\n'
                  % (got, want, '' if speed < cap
                     else ', capped at that profile\'s own %d mm/s' % cap))
                if k == 'infill_speed':
                    w('#       over %d x %s mm, since infill_every_layers = %d\n'
                      % (n, variants[name].get('layer_height', '?'), n))
        w('\n[print:%s]\n' % layout.hidden_common)
        for k in sorted(common):
            w('%s = %s\n' % (k, common[k]))
        for name, over in variants.items():
            w('\n[print:%s]\n' % name)
            w('inherits = %s\n' % layout.hidden_common)
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
    for layout, names, common, rates in layout_report:
        base_tag = layout.tool_tag(layout.base_tool)
        print('\n%s  <- Prusa\'s own "%s" prints, renamed, rebound and '
              'split   %d shared keys'
              % (layout.key, LAYOUT_BASE[base_tag][0], len(common)))
        print('     %s' % tool_runs(layout.tools))
        for role, pos in sorted(layout.roles.items()):
            print('     %-36s tool %d (%s)%s'
                  % (role, pos, layout.tool_tag(pos),
                     '' if pos == layout.base_tool else '   <- moved'))
        for name, k, pos, tag, n, speed, got, want, cap, _src in rates:
            print('     %-42s %s = %s -> %.1f mm3/s (Prusa %.1f%s)'
                  % (name, k, speed, got, want,
                     '' if speed < cap else ', capped at %d mm/s' % cap))
        if not layout.validated:
            warn = True
            print('  !! UNVALIDATED: %s' % layout.note)
        for n in names:
            print('     %s' % n)
    if warn:
        print('\n!! At least one size is unvalidated. Calibrate max volumetric')
        print('   speed before trusting any of those speeds.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
