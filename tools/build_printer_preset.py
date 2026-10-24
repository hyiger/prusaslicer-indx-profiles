#!/usr/bin/env python3
"""
Build a fully-flattened PrusaSlicer *user* printer preset for the CORE One INDX
at a nozzle size Prusa does not ship a variant for.

Prusa declares `variants = HF0.4` for both INDX models, so there is no HF0.6
INDX printer to pick in the Configuration Wizard, and the print profiles in
vendor/hyigerINDX.ini bind on `nozzle_diameter[0]==<dia>`. Without a printer
carrying that diameter they are registered but permanently filtered out of the
dropdown. This emits that printer.

Why flattened: PresetCollection::load_presets does

    preset.config = default_preset.config;
    preset.config.apply(config);

so a loose user preset in <datadir>/printer/ is applied over PrusaSlicer's
*defaults*, not over its `inherits` parent. A delta-only file silently picks up
a default for every key it omits. (Config bundles resolve `inherits` only
between sections of the same file, so they need flattening too.) `inherits`
is still written, and it is required, not cosmetic. It drives the UI's
reset-to-system arrows and modified-value markers, and although it is not
consulted when loading this file's own config, a user preset has no vendor of
its own: PresetCollection::get_preset_with_vendor_profile walks the `inherits`
chain to find one, and is_compatible_with_printer then tests that vendor against
the active printer's. Drop `inherits` and Prusa's own print and filament presets
stop being offered - the 0.25 preset loses Prusa's three @COREONEINDX 0.25 print
profiles, the 0.4 preset loses Generic FLEX and Prusament TPU 95A.

Nothing here is invented, except at HF1.0, which Prusa publishes nothing for:
build_scaled() builds the HF0.8 preset and scales only its layer-height limits
by 1.25, moving the size labels (SCALED_PRINTER; nozzles.py, SCALED SIZES).
Everywhere else, the nozzle-size delta is read out of Prusa's own
CORE One `HF0.4` -> `HF<dia>` pair at run time, and each key transfers to INDX
only where INDX agreed with CORE One at 0.4 - the rule derive_filaments.py
applies to non-MVS keys.

Prusa also keeps commented-out INDX printer drafts in PrusaResearch.ini for
8T/4T at 0.25, HF0.6 and HF0.8. Those are INDX values for an INDX toolchanger,
so they outrank anything derived from a CORE One delta: where a draft disagrees
with the delta on a key in DRAFT_ADOPT, the draft wins and says so in the header.
A draft disagreement on any other key, or a delta key that is not in TRANSFER
and that no draft answers, is a refusal rather than a guess.

--std builds a standard (non-high-flow) nozzle instead, named the way Prusa
names its own STD variants ("Prusa CORE One INDX 8T 0.4 nozzle"):

  0.4   the CORE One HF0.4 -> 0.4 delta, under the same agreed-at-0.4 rule.
        Upstream it is nozzle_high_flow, printer_variant and the two defaults.
  0.25  Prusa's own commented-out "[printer:Prusa CORE One INDX <model> 0.25
        nozzle]" draft in PrusaResearch.ini, applied key for key. The CORE One
        HF0.4 -> 0.25 delta is not applied, only compared with the result, and
        each key where they differ is printed (STD_CHECK).

Every preset also gets one fix to Prusa's layer G-code. Its PET-family dock-fan
check, `filament_type[N]=~/(PET|CPE|PCTG)/`, must match the whole type, so it
never matches PETG, the type of every PET-family INDX filament Prusa ships.
Reported as prusa3d/PrusaSlicer-settings-prusa-fff#50.

--layout builds a mixed tool layout instead: different nozzles on different
tools, composed from the single-nozzle presets above tool by tool. Only
PrusaSlicer's own per-extruder keys may differ between tools; anything else the
two nozzles' presets disagree on stops the build. See nozzles.py, MIXED TOOL
LAYOUTS.

    python3 build_printer_preset.py PrusaResearch.ini printer/ -n 0.6
    python3 build_printer_preset.py PrusaResearch.ini printer/ -n 0.6 -m 4T
    python3 build_printer_preset.py PrusaResearch.ini printer/ -n 0.4 -n 0.25 --std
"""
import argparse
import os
import re
import sys
import textwrap

from build_print_profiles import (assert_unsourced, layout_balanced_profile,
                                  load, load_drafts, resolve)
from nozzles import (EXTRUDER_KEYS, LAYOUTS, NOZZLES, STD_VALIDATED, TIERS,
                     scale, split_tag, tool_runs)

BYLINE = 'hyiger'

# INDX models, and the shipping 0.4 preset each derives from.
MODELS = {
    '8T': ('COREONE_INDX8T', 'Prusa CORE One INDX 8T HF0.4 nozzle'),
    '4T': ('COREONE_INDX4T', 'Prusa CORE One INDX 4T HF0.4 nozzle'),
}

# The reference pair. Prusa ships CORE One HF0.4/0.5/0.6/0.8 only, which is why
# 0.25 and 0.3 refuse here exactly as they do in derive_filaments.py.
REF_DIA = '0.4'
REF_BASE = 'Prusa CORE One HF0.4 nozzle'
REF_FMT = 'Prusa CORE One HF%s nozzle'

# Keys allowed to cross from the CORE One delta onto an INDX preset, each with
# the reason it is size-dependent rather than machine-dependent. Anything else
# showing up in the delta stops the build - a future PrusaResearch.ini that
# changes more keys should force a human decision, not be silently absorbed.
TRANSFER = {
    'nozzle_diameter':  'the nozzle itself',
    'max_layer_height': 'ladder ceiling scales with nozzle',
    'min_layer_height': 'ladder floor scales with nozzle',
    'printer_variant':  'variant tag names the nozzle',
    'wipe':             'larger nozzles ooze more; Prusa enables it above 0.4',
    'nozzle_high_flow': 'standard vs high-flow nozzle',
}

# INDX sets these to its own profile family. Keep the family, move the size.
# The print-profile pointer is built from the same NOZZLES/TIERS table
# build_print_profiles.py emits from, so it can never name a profile that is not
# in the bundle; hardcoding the layer tag here would dangle at any size whose
# Balanced tier is not 0.25 mm.
RETARGET = {
    'default_print_profile': None,      # computed, see balanced_profile()
    'default_filament_profile': '"Prusament PLA @COREONEINDX HF%s"',
}

# Keys where Prusa's own commented INDX HF<dia> printer draft is adopted over the
# value the CORE One HF0.4 -> HF<dia> delta produces, each with the reason. The
# draft is the more specific source: Prusa wrote it for this nozzle on this
# toolchanger, where the delta can only keep whatever the HF0.4 chain resolved.
# A draft disagreement on any key NOT listed here stops the build - Prusa having
# drafted a different value is sourced evidence and must not be absorbed silently.
DRAFT_ADOPT = {
    'retract_length': 'retraction at this nozzle, drafted for the INDX itself; '
                      'the delta keeps the less specific HF0.4 chain value',
    'retract_lift': 'lift at this nozzle, drafted for the INDX itself',
    'retract_speed': 'retraction speed at this nozzle, drafted for the INDX itself',
    'deretract_speed': 'deretraction speed at this nozzle, drafted for the INDX itself',
    'retract_before_wipe': 'wipe fraction at this nozzle, drafted for the INDX itself',
}
# Draft keys that are structure or pointers, never values to adopt.
DRAFT_SKIP = {'inherits'} | set(RETARGET)

# Standard nozzles: where each size's delta comes from.
STD_PAIR = {'0.4': 'Prusa CORE One 0.4 nozzle'}          # vs REF_BASE
STD_DRAFT = {'0.25': 'Prusa CORE One INDX %s 0.25 nozzle'}  # % model
# The CORE One printer at each drafted size. Its REF_BASE -> <dia> delta is not
# applied: the draft is the INDX-specific source and wins whole. It is compared
# with the draft-built preset, and every key where the two differ is printed, so a
# re-pin that moves either side is seen. At 2.5.12 that is jerk (CORE One 8,8;
# INDX 10,8, which the draft leaves) and retract_length (CORE One 0.8; draft 0.7).
STD_CHECK = {'0.25': 'Prusa CORE One 0.25 nozzle'}
# A standard nozzle keeps Prusa's default profile names and moves the size tag.
STD_TAG = (' @COREONEINDX HF0.4', ' @COREONEINDX %s')

# Prusa's PET-family dock-fan check in layer_gcode. =~ is regex_match, a
# full-string match, so the stock pattern never matches "PETG".
DOCK_FAN = ('=~/(PET|CPE|PCTG)/', '=~/(PET|CPE|PCTG).*/',
            'PET-family dock-fan check never matched PETG (=~ must match the '
            'whole type); prusa3d/PrusaSlicer-settings-prusa-fff#50')


def balanced_profile(dia):
    """The Balanced profile build_print_profiles.py emits for this size."""
    key, label, idx = next(t for t in TIERS if t[0] == 'balanced')
    return '%.2fmm %s @COREONEINDX %s' % (NOZZLES[dia].layers[idx], label,
                                          NOZZLES[dia].tag)


def draft_for(drafts, dia, model, high_flow=True):
    """Prusa's own commented INDX printer draft for this size, or {}."""
    name = 'printer:Prusa CORE One INDX %s %s%s nozzle' % (
        model, 'HF' if high_flow else '', dia)
    return drafts.get(name, {})


def uniform(value):
    """INDX carries per-extruder vectors. Return the single value, or None."""
    parts = [p.strip() for p in value.split(',')]
    return parts[0] if len(set(parts)) == 1 else None


def widen(template, value):
    """Match the arity of the key being replaced."""
    return ','.join([value] * len(template.split(',')))


def build(vendor, drafts, dia, model, report):
    if dia not in NOZZLES:
        raise SystemExit('refusing: %s is not in the nozzles.py table' % dia)
    if model not in MODELS:
        raise SystemExit('refusing: unknown model %s' % model)
    if NOZZLES[dia].shipped:
        raise SystemExit('refusing: Prusa ships print profiles for %s mm itself, so '
                         'build_print_profiles.py\n          emits none and '
                         'default_print_profile would dangle.' % dia)
    if NOZZLES[dia].scaled_from:
        return build_scaled(vendor, drafts, NOZZLES[dia], model, report)
    printer_model, base_name = MODELS[model]

    ref_name = REF_FMT % dia
    if 'printer:' + ref_name not in vendor:
        raise SystemExit(
            'refusing: no [printer:%s] upstream, so there is no sourced\n'
            '          0.4 -> %s delta to apply. Prusa ships CORE One HF0.4,\n'
            '          HF0.5, HF0.6 and HF0.8 only.' % (ref_name, dia))

    draft = draft_for(drafts, dia, model)
    cfg = dict(resolve(vendor, 'printer:' + base_name))
    cfg.pop('renamed_from', None)  # a new preset, not a rename of the base
    changed = apply_delta(vendor, cfg, ref_name, 'HF' + dia,
                          lambda key: retarget_hf(key, dia), report, draft)
    apply_draft(cfg, draft, changed, report, 'HF' + dia)
    fix_dock_fan(cfg, changed, report)
    cfg['inherits'] = base_name
    assert cfg['printer_model'] == printer_model, 'model mismatch'
    return cfg, changed


# A size Prusa publishes nothing for (nozzles.py, SCALED SIZES): the keys that
# move, each with what it is. Every other key is held at the source size's preset.
SCALED_PRINTER = {
    'nozzle_diameter': 'the nozzle itself',
    'printer_variant': 'variant tag names the nozzle',
    'max_layer_height': None,   # scaled: a length proportional to the nozzle
    'min_layer_height': None,
    'default_print_profile': 'INDX pointer, moved to the Balanced profile this bundle emits',
    'default_filament_profile': 'INDX pointer, moved to the filament this bundle emits',
}


def build_scaled(vendor, drafts, noz, model, report):
    """The source size's preset, built from Prusa's own sources as usual, with
    only the keys in SCALED_PRINTER moved to the new size. Retraction, wipe and
    everything else stay exactly as the source size has them: at 1.0 that is
    Prusa's own commented INDX HF0.8 printer draft."""
    src = noz.scaled_from
    cfg, changed = build(vendor, drafts, src, model, report)
    at = {c[0]: i for i, c in enumerate(changed)}

    def move(key, new, why):
        if key in at:   # changed already on the way to the source size
            k, old, _, why0 = changed[at[key]]
            changed[at[key]] = (k, old, new, '%s; then for %s mm, %s' % (why0, noz.dia, why))
        else:
            changed.append((key, cfg[key], new, why))
        cfg[key] = new

    for key, why in SCALED_PRINTER.items():
        if key == 'nozzle_diameter':
            new = widen(cfg[key], noz.dia)
        elif key == 'printer_variant':
            new = 'HF' + noz.dia
        elif key == 'default_print_profile':
            new = balanced_profile(noz.dia)
        elif key == 'default_filament_profile':
            new = RETARGET[key] % noz.dia
        else:
            one = uniform(cfg[key])
            if one is None:
                raise SystemExit('refusing: HF%s %s is not uniform across tools (%s); '
                                 'cannot scale it' % (src, key, cfg[key]))
            new = widen(cfg[key], scale(one, noz.ratio))
            why = ('HF%s value %s x %s/%s, half-up to 0.01: Prusa publishes nothing '
                   'at %s mm' % (src, one, noz.dia, src, noz.dia))
        move(key, new, why)
    report.append('  SCALED: Prusa publishes nothing at %s mm. Built as HF%s, then the '
                  '%d keys above moved;\n          every other key is held at HF%s.'
                  % (noz.dia, src, len(SCALED_PRINTER), src))
    return cfg, changed


def retarget_hf(key, dia):
    if key == 'default_print_profile':
        return balanced_profile(dia)
    return RETARGET[key] % dia


def apply_delta(vendor, cfg, ref_name, label, retarget, report, draft=None):
    """Move cfg along Prusa's CORE One REF_BASE -> ref_name delta.

    A delta key that is not reviewed in TRANSFER is a refusal, unless Prusa's own
    INDX draft for this size answers it - then the draft supplies the value and
    apply_draft() records it."""
    draft = draft or {}
    ref04 = resolve(vendor, 'printer:' + REF_BASE)
    ref = resolve(vendor, 'printer:' + ref_name)
    for r in (ref04, ref):
        r.pop('renamed_from', None)  # each names its own preset; never a nozzle delta

    delta = sorted(k for k in set(ref04) | set(ref) if ref04.get(k) != ref.get(k))
    unexpected = [k for k in delta if k not in TRANSFER and k not in RETARGET
                  and not (k in draft and k in DRAFT_ADOPT)]
    if unexpected:
        raise SystemExit(
            'refusing: upstream HF0.4 -> %s delta touches unreviewed keys:\n'
            '          %s\n'
            '          Add them to TRANSFER with a reason, or handle them.\n'
            '          (Prusa\'s own commented INDX %s printer draft does not answer '
            'them either.)' % (label, ', '.join(unexpected), label))
    delta = [k for k in delta if k in TRANSFER or k in RETARGET]

    changed = []
    for key in delta:
        if key in RETARGET:
            new = retarget(key)
            changed.append((key, cfg[key], new, 'INDX pointer, retargeted to %s' % label))
            cfg[key] = new
            continue

        # Transfer only where INDX agreed with CORE One at 0.4.
        indx_at_04 = uniform(cfg[key])
        if indx_at_04 is None:
            raise SystemExit(
                'refusing: INDX %s is not uniform across tools (%s);\n'
                '          cannot infer intent.' % (key, cfg[key]))
        if indx_at_04 != ref04[key]:
            report.append('  SKIPPED %s: INDX chose %s where CORE One had %s '
                          '- deliberate, preserved'
                          % (key, indx_at_04, ref04[key]))
            continue
        new = widen(cfg[key], ref[key])
        changed.append((key, cfg[key], new,
                        'CORE One %s; INDX agreed at 0.4 (%s == %s)'
                        % (label, indx_at_04, ref04[key])))
        cfg[key] = new
    return changed


def apply_draft(cfg, draft, changed, report, label):
    """Adopt Prusa's own INDX draft where it disagrees with the derived value."""
    if not draft:
        report.append('  no Prusa INDX %s printer draft upstream; delta only' % label)
        return
    unreviewed = []
    for key, value in sorted(draft.items()):
        if key in DRAFT_SKIP or key not in cfg:
            continue
        one = uniform(value)
        if one is None:
            raise SystemExit('refusing: Prusa\'s INDX %s draft %s is not uniform '
                             'across tools (%s)' % (label, key, value))
        if uniform(cfg[key]) == one:
            continue
        if key not in DRAFT_ADOPT:
            unreviewed.append('%s: draft %s, derived %s'
                              % (key, one, uniform(cfg[key])))
            continue
        new = widen(cfg[key], one)
        changed.append((key, cfg[key], new, 'Prusa\'s commented INDX %s printer '
                        'draft: %s' % (label, DRAFT_ADOPT[key])))
        cfg[key] = new
    if unreviewed:
        raise SystemExit(
            'refusing: Prusa\'s commented INDX %s printer draft disagrees on keys that\n'
            '          have not been reviewed:\n            %s\n'
            '          The draft is INDX-specific and outranks the CORE One delta, so\n'
            '          this needs a human decision: add each key to DRAFT_ADOPT with a\n'
            '          reason, or explain why the derived value stands.'
            % (label, '\n            '.join(unreviewed)))


def fix_dock_fan(cfg, changed, report):
    stock, fixed, why = DOCK_FAN
    gcode = cfg.get('layer_gcode', '')
    if stock not in gcode:
        report.append('  dock-fan check not present upstream; nothing to fix')
        return
    cfg['layer_gcode'] = gcode.replace(stock, fixed)
    changed.append(('layer_gcode', stock, fixed, '%s (x%d)' % (why, gcode.count(stock))))


def per_tool(value, cfg):
    """`value` as one value if it is a uniform vector with one entry per tool of
    `cfg`, else as written: machine limits are (normal, stealth) pairs, and a
    CORE One has one tool, so its 8,8 jerk must stay 8,8."""
    if value is None:
        return 'unset'
    tools = len(cfg.get('nozzle_diameter', '').split(','))
    one = uniform(value)
    return one if tools > 1 and len(value.split(',')) == tools and one is not None else value


def cross_check(vendor, base, cfg, draft, ref_name, label, report):
    """Report, without applying it, each key of the CORE One REF_BASE -> ref_name
    delta where the preset built from Prusa's INDX draft ends up elsewhere.
    RETARGET pointers are left out: they name INDX profiles, never CORE One ones."""
    if 'printer:' + ref_name not in vendor:
        report.append('  no [printer:%s] upstream; nothing to cross-check' % ref_name)
        return
    ref04 = resolve(vendor, 'printer:' + REF_BASE)
    ref = resolve(vendor, 'printer:' + ref_name)
    for r in (ref04, ref):
        r.pop('renamed_from', None)
    rows = []
    for key in sorted(k for k in set(ref04) | set(ref)
                      if ref04.get(k) != ref.get(k) and k not in RETARGET):
        mine = per_tool(cfg.get(key), cfg)
        if mine == per_tool(ref.get(key), ref):
            continue
        rows.append('    %-24s CORE One %s -> %s; INDX HF0.4 %s; emitted %s (%s)'
                    % (key, per_tool(ref04.get(key), ref04), per_tool(ref.get(key), ref),
                       per_tool(base.get(key), base), mine,
                       'Prusa\'s draft' if key in draft else 'not in the draft'))
    if rows:
        report.append('  CORE One HF0.4 -> %s delta, reported and not applied; the preset '
                      'built from Prusa\'s INDX %s draft differs on:' % (label, label))
        report += rows


def build_std(vendor, drafts, dia, model, report):
    """A standard (non-HF) nozzle, from Prusa's own sources only."""
    if model not in MODELS:
        raise SystemExit('refusing: unknown model %s' % model)
    printer_model, base_name = MODELS[model]
    cfg = dict(resolve(vendor, 'printer:' + base_name))
    cfg.pop('renamed_from', None)  # a new preset, not a rename of the base
    tag = lambda value: value.replace(STD_TAG[0], STD_TAG[1] % dia)

    if dia in STD_PAIR:
        # apply_delta lets a key past its refusal when the draft answers it, so
        # the draft must then be applied here too, or that key would be neither
        # refused nor set.
        draft = draft_for(drafts, dia, model, high_flow=False)
        changed = apply_delta(vendor, cfg, STD_PAIR[dia], dia,
                              lambda key: tag(cfg[key]), report, draft)
        apply_draft(cfg, draft, changed, report, dia)
    elif dia in STD_DRAFT:
        draft_name = 'printer:' + STD_DRAFT[dia] % model
        if draft_name not in drafts:
            raise SystemExit('refusing: no "%s" draft in PrusaResearch.ini' % draft_name)
        draft = dict(drafts[draft_name])
        parent = draft.pop('inherits', '')
        draft.pop('renamed_from', None)  # names Prusa's own preset, not this one
        base = cfg
        cfg = dict(resolve(vendor, 'printer:' + parent))
        cfg.pop('renamed_from', None)
        changed = []
        for key, value in draft.items():
            changed.append((key, cfg.get(key, ''), value, 'Prusa\'s INDX %s draft' % dia))
            cfg[key] = value
        for key in RETARGET:
            if STD_TAG[0] in cfg[key]:
                new = tag(cfg[key])
                changed.append((key, cfg[key], new,
                                'INDX pointer, retargeted to %s (not in the draft)' % dia))
                cfg[key] = new
        cross_check(vendor, base, cfg, draft, STD_CHECK[dia], dia, report)
    else:
        raise SystemExit('refusing: no Prusa source for a standard %s mm INDX nozzle '
                         '(known: %s)' % (dia, ', '.join(sorted(set(STD_PAIR) | set(STD_DRAFT)))))

    fix_dock_fan(cfg, changed, report)
    cfg['inherits'] = base_name
    assert cfg['printer_model'] == printer_model, 'model mismatch'
    return cfg, changed


# --- mixed tool layouts ------------------------------------------------------
# Prusa's "experimental printing with different nozzle diameters" workflow
# (help.prusa3d.com article 821176) on an INDX. A layout preset is composed, not
# derived: each tool's nozzle already has a preset here, built from Prusa's own
# sources, and the layout interleaves them tool by tool. Only PrusaSlicer's own
# per-extruder keys may vary that way (nozzles.py, EXTRUDER_KEYS, from
# PrintConfigDef::init_extruder_option_keys); any other key the two nozzles'
# presets disagree on describes the machine rather than a nozzle, and stops the
# build unless MIXED_SCALAR says what to do with it.

# The handful of keys a layout decides once for the whole printer.
MIXED_SCALAR = {
    'printer_variant': 'names the layout, not one nozzle. Nothing binds on it: '
                       'PrusaSlicer checks a variant only for system presets in '
                       'a vendor bundle (PresetBundle.cpp:1642-1659), and '
                       'Preset::set_visible_from_appconfig returns early for a '
                       'preset with no vendor of its own (Preset.cpp:425), which '
                       'is every user preset here - as the 0.25 and 0.4 presets, '
                       'whose tags Prusa does not declare either, already show',
    'default_print_profile': 'INDX pointer, retargeted to the Balanced profile '
                             'this layout emits',
    'default_filament_profile': 'the base tool\'s. PrusaSlicer reads index 0 '
                                'only: ExtruderFilaments::update_compatible_'
                                'internal skips this one key when it shifts a '
                                'tool\'s per-extruder values into index 0 '
                                '(Preset.cpp:2407-2409), so a per-tool vector '
                                'here would be written and never read',
    'inherits': 'the shipping HF0.4 preset, as in every preset here: it carries '
                'no values into a flattened file, but it is how a user preset '
                'gets a vendor, and so how Prusa\'s own print and filament '
                'presets stay on offer',
}


def one_or_all(value):
    """A per-tool vector's single value, or the whole vector when the tools
    differ: a header must not show tool 1's value as if it were the printer's."""
    one = uniform(value)
    return value if one is None else one


def preset_for_tag(vendor, drafts, tag, model, report):
    """The preset this repo builds for one tool's nozzle on its own.

    HF0.4 is the shipping base itself, which needs no derivation - only the
    dock-fan fix every preset here carries.
    """
    dia, high_flow = split_tag(tag)
    _printer_model, base_name = MODELS[model]
    if tag == 'HF' + REF_DIA:
        cfg = dict(resolve(vendor, 'printer:' + base_name))
        cfg.pop('renamed_from', None)
        changed = []
        fix_dock_fan(cfg, changed, report)
        cfg['inherits'] = base_name
        return cfg
    if high_flow:
        return build(vendor, drafts, dia, model, report)[0]
    return build_std(vendor, drafts, dia, model, report)[0]


def assert_per_tool_nozzle_check(cfg, layout):
    """Prusa's INDX start G-code asks the firmware to verify each used tool's
    own nozzle - `M862.1 T<n> P{nozzle_diameter[<n>]} ... F{nozzle_high_flow[<n>]}`
    per tool. That per-tool check is what makes a mixed layout safe to send to
    the printer at all: the firmware refuses the print if a dock holds something
    other than what the G-code was sliced for. If a re-pin ever collapses it to
    one tool, a mixed preset must not be written."""
    # An INI stores newlines as the two characters \ and n, so split on that
    # rather than trusting a regex not to run past the end of a line.
    lines = cfg.get('start_gcode', '').split('\\n')
    missing = [n + 1 for n in range(len(layout.tools))
               if not any(re.search(r'M862\.1\s+T%d\s+P\{nozzle_diameter\[%d\]\}'
                                    % (n, n), line)
                          and 'nozzle_high_flow[%d]' % n in line for line in lines)]
    if missing:
        raise SystemExit(
            'refusing: Prusa\'s start G-code does not check tool %s with its own\n'
            '          M862.1 T<n> P{nozzle_diameter[<n>]} ... '
            '{nozzle_high_flow[<n>]}.\n'
            '          Without a per-tool check the firmware cannot tell that a '
            'mixed\n          layout is fitted the way the G-code assumes, so this '
            'preset must\n          not be written.'
            % ', '.join(str(n) for n in missing))


def build_mixed(vendor, drafts, layout, model, report):
    """One printer preset for a mixed tool layout."""
    if model != layout.model:
        raise SystemExit('refusing: layout %s is an INDX %s layout (%d tools), '
                         'not %s' % (layout.key, layout.model,
                                     len(layout.tools), model))
    printer_model, base_name = MODELS[model]
    ref = dict(resolve(vendor, 'printer:' + base_name))
    ref.pop('renamed_from', None)
    tools = len(ref['nozzle_diameter'].split(','))
    if tools != len(layout.tools):
        raise SystemExit('refusing: %s has %d tools but layout %s names %d'
                         % (base_name, tools, layout.key, len(layout.tools)))

    per_tag = {}
    for tag in dict.fromkeys(layout.tools):
        sub = []
        per_tag[tag] = preset_for_tag(vendor, drafts, tag, model, sub)
        report += ['  tool nozzle %s: %s' % (tag, line.strip()) for line in sub]
    tool_cfgs = [per_tag[t] for t in layout.tools]

    cfg, composed, unexpected = {}, {}, []
    for key in sorted(set().union(*(set(c) for c in tool_cfgs))):
        vals = [c.get(key) for c in tool_cfgs]
        if key in MIXED_SCALAR:
            continue                                 # decided below
        if all(v == vals[0] for v in vals):
            cfg[key] = vals[0]
            continue
        if key not in EXTRUDER_KEYS:
            unexpected.append('%s: %s' % (key, tool_runs(
                [one_or_all(v) if v else 'unset' for v in vals])))
            continue
        ones = []
        for tag, value in zip(layout.tools, vals):
            if value is None:
                unexpected.append('%s: the %s preset does not set it while '
                                  'another tool\'s does' % (key, tag))
                break
            one = uniform(value)
            if one is None:
                unexpected.append('%s: the %s preset is not uniform across tools '
                                  '(%s), so there is no single value to fit this '
                                  'tool' % (key, tag, value))
                break
            ones.append(one)
        else:
            cfg[key] = ','.join(ones)
            composed[key] = ones
    if unexpected:
        raise SystemExit(
            'refusing: the tools in layout %s disagree on keys a layout may not '
            'vary:\n            %s\n'
            '          Only PrusaSlicer\'s own per-extruder keys can differ from '
            'tool to\n          tool (nozzles.py, EXTRUDER_KEYS). Anything else '
            'describes the\n          machine, so one value has to be chosen for '
            'it: add it to\n          MIXED_SCALAR with a reason, or resolve the '
            'disagreement.'
            % (layout.key, '\n            '.join(unexpected)))

    cfg['printer_variant'] = layout.key
    cfg['default_print_profile'] = layout_balanced_profile(vendor, layout)
    cfg['default_filament_profile'] = \
        tool_cfgs[layout.base_tool - 1]['default_filament_profile']
    cfg['inherits'] = base_name

    if cfg.get('single_extruder_multi_material') != '0':
        raise SystemExit(
            'refusing: %s has single_extruder_multi_material = %s. A mixed layout '
            'needs 0:\n          PrusaSlicer unifies the nozzles on a '
            'single-extruder multimaterial\n          printer (Tab.cpp:2742-2756) '
            'and stops shifting each tool\'s values into\n          index 0 when '
            'it filters that tool\'s filaments (Preset.cpp:2405), which is\n'
            '          what makes a per-tool filament list work at all.'
            % (base_name, cfg.get('single_extruder_multi_material')))
    assert_per_tool_nozzle_check(cfg, layout)
    assert cfg['printer_model'] == printer_model, 'model mismatch'

    changed = []
    for key in sorted(set(cfg) | set(ref)):
        if cfg.get(key) == ref.get(key):
            continue
        if key in composed:
            why = ('one value per tool - %s - each from the preset this repo '
                   'builds for that nozzle on its own. PrusaSlicer reads this key '
                   'per extruder (nozzles.py, EXTRUDER_KEYS)'
                   % tool_runs(composed[key]))
        elif key in MIXED_SCALAR:
            why = MIXED_SCALAR[key]
        elif key == 'layer_gcode':
            # The whole G-code block differs only by the dock-fan pattern;
            # report the pattern, as fix_dock_fan() does everywhere else.
            stock, fixed, why = DOCK_FAN
            if ref.get(key, '').replace(stock, fixed) != cfg.get(key):
                raise SystemExit('refusing: layer_gcode differs from the '
                                 'shipping preset by more than the dock-fan '
                                 'fix')
            changed.append((key, stock, fixed, '%s (x%d)'
                            % (why, ref.get(key, '').count(stock))))
            continue
        else:
            why = ('every tool\'s preset sets this value, so it is the layout\'s '
                   'too; see the per-nozzle presets for where it comes from')
        changed.append((key, ref.get(key, ''), cfg.get(key, ''), why))
    report.append('  composed from %s, tool by tool; %d keys vary per tool'
                  % (', '.join(sorted(per_tag)), len(composed)))
    return cfg, changed


def emit(path, cfg, changed, what, model, validated, note=None, version='?',
         unit='size'):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# Prusa CORE One INDX %s, %s. Generated by %s\n'
                % (model, what, BYLINE))
        f.write('# tools/build_printer_preset.py from PrusaResearch.ini %s.\n' % version)
        f.write('# Fully flattened - a loose user preset is applied over\n')
        f.write('# PrusaSlicer defaults, not over its inherits parent.\n')
        f.write('#\n')
        if not validated:
            f.write('# UNVALIDATED: this %s has not been test printed.\n#\n'
                    % unit)
        if note:
            f.write('# %s\n#\n' % note)
        f.write('# Changed from the shipping 0.4 preset:\n')
        for key, old, new, why in changed:
            f.write('#   %s: %s -> %s\n'
                    % (key, one_or_all(old), one_or_all(new)))
            for line in textwrap.wrap(why, 68):
                f.write('#       %s\n' % line)
        keys = [key for key, _, _, _ in changed]
        behavior = [k for k in ('wipe', 'retract_speed', 'deretract_speed',
                                 'retract_before_wipe') if k in keys]
        if behavior == ['wipe']:
            f.write('#\n')
            f.write('# wipe is the one behaviour change rather than a dimension.\n')
            f.write('# It is Prusa\'s own choice above 0.4, but has never run on an\n')
            f.write('# INDX toolchanger. Set it back to 0 if tool changes string.\n')
        elif behavior:
            f.write('#\n')
            f.write('# Behavior changes, not dimensions:\n')
            f.write('#   %s\n' % ', '.join(behavior))
            f.write('# All are Prusa\'s own, from its commented INDX printer draft\n')
            f.write('# (see above), and none has been printed here. Set wipe back\n')
            f.write('# to 0 if tool changes string.\n')
        f.write('\n')
        for k in sorted(cfg):
            f.write('%s = %s\n' % (k, cfg[k]))


def main():
    ap = argparse.ArgumentParser(
        description='Emit a flattened INDX printer preset for a given nozzle.')
    ap.add_argument('prusa_ini')
    ap.add_argument('outdir')
    ap.add_argument('-n', '--nozzle', action='append', default=[],
                    help='nozzle diameter, e.g. 0.6 (repeatable)')
    ap.add_argument('--layout', action='append', dest='layouts', default=[],
                    choices=sorted(LAYOUTS), metavar='KEY',
                    help='a mixed tool layout, different nozzles on different '
                         'tools; repeatable (known: %s)'
                         % ', '.join(sorted(LAYOUTS)))
    ap.add_argument('-m', '--model', action='append',
                    choices=sorted(MODELS), help='INDX model (default 8T)')
    ap.add_argument('--std', action='store_true',
                    help='standard (non-high-flow) nozzle; sizes: %s'
                         % ', '.join(sorted(set(STD_PAIR) | set(STD_DRAFT))))
    a = ap.parse_args()
    if not a.nozzle and not a.layouts:
        ap.error('give at least one -n/--nozzle or --layout')
    if a.std and a.layouts:
        ap.error('--std applies to -n sizes; a layout names its own nozzles')

    vendor = load(a.prusa_ini)
    drafts = load_drafts(a.prusa_ini)
    version = vendor.get('vendor', {}).get('config_version', '?')
    if not a.std:
        for dia in a.nozzle:
            if dia in NOZZLES and NOZZLES[dia].scaled_from:
                assert_unsourced(vendor, drafts, dia)   # before any preset is written
    models = a.model or ['8T']
    os.makedirs(a.outdir, exist_ok=True)

    for dia in a.nozzle:
        for model in models:
            report = []
            if a.std:
                cfg, changed = build_std(vendor, drafts, dia, model, report)
                name = 'Prusa CORE One INDX %s %s nozzle' % (model, dia)
                validated = STD_VALIDATED.get(dia, False)  # True once test printed
                note = ('Standard (non-high-flow) nozzle. Source: ' +
                        ('the CORE One HF0.4 -> %s pair.' % dia if dia in STD_PAIR else
                         'Prusa\'s commented-out INDX %s draft, not yet released '
                         'by Prusa.' % dia))
                what = '%s mm standard nozzle' % dia
            else:
                cfg, changed = build(vendor, drafts, dia, model, report)
                name = 'Prusa CORE One INDX %s HF%s nozzle' % (model, dia)
                validated, note = NOZZLES[dia].validated, None
                what = '%s mm high flow' % dia
                src = NOZZLES[dia].scaled_from
                if src:
                    note = ('SCALED: Prusa publishes nothing at %s mm. This is the HF%s '
                            'preset with only\n# the nozzle, the layer-height limits (x%s) '
                            'and the size labels moved;\n# retraction and every other key '
                            'are held at HF%s.' % (dia, src, NOZZLES[dia].ratio.normalize(), src))
            path = os.path.join(a.outdir, name + '.ini')
            emit(path, cfg, changed, what, model, validated, note, version)

            print('%s  (%d keys)' % (path, len(cfg)))
            for key, old, new, _ in changed:
                print('    %-26s %-22s -> %s'
                      % (key, one_or_all(old)[:21], one_or_all(new)[:44]))
            for line in report:
                print(line)
            if not validated:
                print('    !! UNVALIDATED - %s has not been printed' % dia)

    for key in a.layouts:
        layout = LAYOUTS[key]
        report = []
        cfg, changed = build_mixed(vendor, drafts, layout, layout.model, report)
        name = 'Prusa CORE One INDX %s %s nozzles' % (layout.model, layout.key)
        note = ('Mixed tool layout, Prusa\'s own workflow for different nozzle '
                'diameters\n# (help.prusa3d.com article 821176): %s.\n'
                '# Composed tool by tool from the presets this repo builds for '
                'each\n# nozzle on its own; only PrusaSlicer\'s per-extruder '
                'keys vary per tool.' % tool_runs(layout.tools))
        path = os.path.join(a.outdir, name + '.ini')
        emit(path, cfg, changed, '%s mixed tool layout' % layout.key,
             layout.model, layout.validated, note, version, unit='layout')

        print('%s  (%d keys)' % (path, len(cfg)))
        for k, old, new, _ in changed:
            print('    %-26s %-22s -> %s'
                  % (k, one_or_all(old)[:21], one_or_all(new)[:44]))
        for line in report:
            print(line)
        if not layout.validated:
            print('    !! UNVALIDATED - layout %s has not been printed' % layout.key)

    return 0


if __name__ == '__main__':
    sys.exit(main())
