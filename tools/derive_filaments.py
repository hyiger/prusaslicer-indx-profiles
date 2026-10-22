#!/usr/bin/env python3
"""
Derive INDX filament presets for a given nozzle size from Prusa's own profiles.

Prusa ships 20 filament profiles for the INDX (Generic PVA joined in 2.5.12).
All of them require a high-flow nozzle except Generic FLEX and Prusament TPU
95A: 11 pin `nozzle_diameter[0]==0.4` and the PET/ABS/BVOH/PVA nine bind by
exclusion (`!=0.8 and !=0.6 and !=0.5`). Either way, select a 0.6 toolhead and
the filament dropdown empties.

Method
------
Base: <mat> @COREONEINDX HF0.4  -- carries the INDX toolchanger settings
      (multitool ramming, purge volumes, cooling-move behaviour).

Scaling reference: the CORE One HF0.4 -> HF<dia> pair for the same material,
which is Prusa's measured answer to "what changes when this filament moves to a
<dia> high-flow nozzle". Falls back to the non-HF @COREONE -> @COREONE <dia>
pair where Prusa published no high-flow profile.

Four rules:
  * filament_max_volumetric_speed is always ratio-scaled off the INDX 0.4 value,
    because the INDX toolhead has its own flow baseline distinct from CORE One.
  * pressure advance is Prusa's own figure for this nozzle, not a scaled one:
    the M572 value in `*C1INDX_<FAM>_<dia>_PA*`, or the one Prusa typed into its
    commented `<mat> @COREONEINDX HF<dia>` draft where that is more specific.
    Prusa's INDX PA falls as the nozzle grows (PLA 0.031 at 0.4 -> 0.02 at 0.6),
    so carrying the 0.4 figure across would over-retract on deceleration.
  * the INDX toolchanger keys Prusa sets per nozzle come from its per-nozzle
    common. Each base reaches *C1INDX_common* through one INDX family section
    (`*PLAHFC1INDX*`, `*FLEX04PGC1INDX*`), found by structure. Its sized
    counterpart (`*PLA06HFC1INDX*`, `*FLEX06PGC1INDX*`) is named by the token
    swap PA uses; most of Prusa's HF<dia> drafts inherit exactly that section in
    place of the 0.4 family. The common is
    whichever parent of the counterpart reaches *C1INDX_common*, under any
    name; since 2.5.12 that is `*C1INDX_06_common*` at 0.6 (wipe-tower minimal
    purge 10 -> 14, filament_retract_restart_extra_toolchange 0.04, the
    toolchange G-code having dropped its fixed 0.04 retract). The base is
    re-resolved with the family swapped, so these keys take the value the sized
    family gives them, except where the 0.4 preset sets one in its own body: an
    own override is kept, whether or not it agreed with anything. Only keys in
    COMMON_ADOPT, each with its reason, are taken. A changed key outside it, a
    per-nozzle common that drops a shared key, a toolchanger key set after the
    common, or a missing or ambiguous family all refuse.
  * of the other keys, only those in TRANSFER take the CORE One <dia> value,
    and ONLY if INDX agreed with CORE One at 0.4; any other key keeps the INDX
    0.4 value. Where INDX already differs it made a deliberate
    toolchanger-specific choice, so that choice is preserved.

Each preset keeps its base's printer_model clause (see printer_models()), so it
binds to exactly the INDX models Prusa binds that material to.

Prusa's commented HF<dia> filament drafts are reported side by side with the
derived values but, PA aside, are not adopted. Every figure the report can show
is typed in the draft's own body - load_drafts() reads nothing else - and at 0.6
each of the three divergent MVS figures restates the value its CORE One parent
already supplies (Generic FLEX 3.5 = Generic FLEX @COREONE 0.6, Prusament PLA
30 = Prusament PLA @COREONE HF0.6, Prusament TPU 95A 4 = Prusament TPU 95A
@COREONE 0.6). Adopting one would swap the INDX flow baseline (INDX HF0.4: 2 /
28 / 2) for the CORE One one, which is what the first rule exists to prevent.
The fourth divergence, Prusament PLA slowdown_below_layer_time 15 against 9, is
not an MVS, and restates both parents: Prusa's own *PLA06HFC1INDX* types 15
too. See README "Known gaps".

At HF1.0, which Prusa publishes nothing for (nozzles.py, SCALED SIZES), every
value - MVS and pressure advance included - is derived at 0.8 as above and only
renamed and rebound to a 1.0 nozzle. Nothing is scaled. The tool refuses if the
PrusaResearch.ini it reads has any 1.0 source after all.

These are Prusa nozzle ratios applied to a Bondtech CHT. Treat every number as a
starting point and calibrate MVS before trusting it.

    python3 derive_filaments.py PrusaResearch.ini out.ini --nozzle 0.6
"""
import argparse
import collections
import re
import sys

from build_print_profiles import (assert_unsourced, load, load_drafts, printer_models,
                                  resolve)
from nozzles import NOZZLES

INDX_SUFFIX = ' @COREONEINDX HF0.4'
BIND_TMPL = ' and nozzle_diameter[0]==%s and nozzle_high_flow[0]'
# Prusa's shared INDX toolchanger common. Each INDX HF0.4 base reaches it through
# one family section; Prusa's per-nozzle chain swaps that whole section for its
# sized counterpart, which may stand on a per-nozzle common (2.5.12: 0.6 and 0.8).
COMMON = '*C1INDX_common*'
# A 0.4 family section -> Prusa's name for it at another nozzle, the token swap
# PA uses too: *PLAHFC1INDX* -> *PLA06HFC1INDX*, *FLEX04PGC1INDX* -> *FLEX06PGC1INDX*.
FAMILY_SIZED = [(re.compile(r'^\*([A-Z]+)HFC1INDX\*$'), '*%sHFC1INDX*'),
                (re.compile(r'^\*([A-Z]+)04PGC1INDX\*$'), '*%sPGC1INDX*')]
# Keys a per-nozzle common may change, each reviewed with its reason. A per-nozzle
# common that changes any other key refuses: review it and add it here first.
# derive_std_filaments.py gates the commons under its STD bases on this list too.
COMMON_ADOPT = {
    'filament_minimal_purge_on_wipe_tower':
        'Prusa sets the INDX wipe-tower minimal purge per nozzle (2.5.12: 14 at 0.6, '
        '20 at 0.8, over the shared 10)',
    'filament_retract_restart_extra_toolchange':
        "Prusa's per-nozzle extra deretract after an INDX toolchange (2.5.12: 0.04 at "
        '0.6, 0.05 at 0.8), released with the toolchange G-code that dropped its fixed '
        '0.04 mm post-toolchange retract',
}

# Keys worth transferring when INDX and CORE One agreed at 0.4.
TRANSFER = ['slowdown_below_layer_time', 'fan_below_layer_time', 'min_print_speed',
            'filament_infill_max_speed', 'filament_infill_max_crossing_speed',
            'filament_cooling_final_speed', 'bridge_fan_speed', 'max_fan_speed',
            'min_fan_speed', 'disable_fan_first_layers', 'full_fan_speed_layer']

# Prusa's per-family, per-nozzle pressure-advance sections. The nozzle token is
# the diameter without its dot, exactly as Prusa writes it: 0.6 -> 06.
PA_SIZED = re.compile(r'^\*C1INDX_([A-Z]+)_(\d+)_PA\*$')
PA_FLAT = re.compile(r'^\*C1INDX_([A-Z]+)_PA\*$')     # nozzle independent, e.g. FLEX
# A name match is necessary, not sufficient: the polyamide chamber section
# *C1INDX_CH_PA* matches PA_FLAT, so pa_source() also requires an M572.
# Keys from Prusa's commented HF<dia> drafts to show against the derived values.
DRAFT_WATCH = ['filament_max_volumetric_speed', 'slowdown_below_layer_time']


def pa_token(dia):
    """Prusa's per-nozzle section token, for PA and common sections alike:
    '0.6' -> '06', '0.25' -> '025'."""
    return dia.replace('.', '')


def inherits(S, name):
    """The direct parents of section `name`, in order."""
    return [x.strip() for x in (S.get(name) or {}).get('inherits', '').split(';') if x.strip()]


def family_at(S, mat, dia):
    """(0.4 family, its <dia> counterpart) for an INDX HF0.4 material.

    The 0.4 family is found by structure: the one section of the base's chain
    that inherits *C1INDX_common* directly. Its counterpart is found by Prusa's
    naming, the token swap PA uses. Refuses where either is missing or there is
    more than one family, so nothing falls back to the shared common unseen."""
    name = 'filament:' + mat + INDX_SUFFIX
    fams = sorted({p for p in parents(S, name) if COMMON in inherits(S, 'filament:' + p)})
    if len(fams) != 1:
        sys.exit('refusing: %s reaches %s through %s, not through exactly one INDX '
                 'family section' % (mat + INDX_SUFFIX, COMMON, ', '.join(fams) or 'nothing'))
    for pat, tmpl in FAMILY_SIZED:
        m = pat.match(fams[0])
        if m:
            sized = tmpl % (m.group(1) + pa_token(dia))
            if 'filament:' + sized not in S:
                sys.exit('refusing: no %s upstream, the %s counterpart of %s'
                         % (sized, dia, fams[0]))
            return fams[0], sized
    sys.exit('refusing: %s is not a family section this tool can size' % fams[0])


def sized_common(S, family):
    """The common Prusa's sized family section stands on: its one direct parent
    that is or inherits *C1INDX_common*, whatever it is called. COMMON itself
    where Prusa has no per-nozzle common for the size.

    Refuses if the family's own body, or a parent listed after that common, sets
    an INDX toolchanger key (a *C1INDX_common* or COMMON_ADOPT key). That value
    would override the common in Prusa's chain, so it would either be missed or
    be credited to the wrong section; either way it needs reviewing first."""
    inh = inherits(S, 'filament:' + family)
    via = [i for i, p in enumerate(inh) if p == COMMON or COMMON in parents(S, 'filament:' + p)]
    if len(via) != 1:
        sys.exit('refusing: %s reaches %s through %s, not through exactly one parent'
                 % (family, COMMON, ', '.join(inh[i] for i in via) or 'nothing'))
    toolchanger = set(resolve(S, 'filament:' + COMMON)) | set(COMMON_ADOPT)
    later = [('its own body', {k for k in S['filament:' + family] if k != 'inherits'})]
    later += [(p, set(resolve(S, 'filament:' + p))) for p in inh[via[0] + 1:]]
    for where, keys in later:
        hit = sorted(keys & toolchanger)
        if hit:
            sys.exit('refusing: %s sets INDX toolchanger key(s) %s in %s, after its common '
                     '%s; review them first' % (family, ', '.join(hit), where, inh[via[0]]))
    return inh[via[0]]


def common_delta(S, sec):
    """{key: (shared value, per-nozzle value)} for the keys the per-nozzle common
    `sec` changes from *C1INDX_common*; empty for COMMON itself. Refuses if `sec`
    drops a shared key (it could not stand in for it), or on a changed key not
    in COMMON_ADOPT."""
    if sec == COMMON:
        return {}
    shared, sized = resolve(S, 'filament:' + COMMON), resolve(S, 'filament:' + sec)
    dropped = sorted(set(shared) - set(sized))
    if dropped:
        sys.exit('refusing: %s does not carry every %s key (%s), so it cannot stand in '
                 'for it' % (sec, COMMON, ', '.join(dropped)))
    delta = {k: (shared.get(k), v) for k, v in sized.items() if shared.get(k) != v}
    unreviewed = sorted(set(delta) - set(COMMON_ADOPT))
    if unreviewed:
        sys.exit('refusing: %s changes keys not in COMMON_ADOPT:\n%s\n'
                 '          Review each and add it to COMMON_ADOPT with a reason.'
                 % (sec, '\n'.join('          %s %s -> %s' % (k, delta[k][0] or 'unset',
                                                             delta[k][1])
                                   for k in unreviewed)))
    return delta


def substituted(S, name, old, new):
    """`name` resolved as if each section of its chain that inherits `old`
    inherited `new` in its place: the family swap most of Prusa's HF<dia>
    drafts make (*PLAHFC1INDX* -> *PLA06HFC1INDX*)."""
    S2 = collections.OrderedDict(S)
    for sec in [name] + ['filament:' + p for p in parents(S, name)]:
        inh = inherits(S2, sec)
        if old in inh:
            S2[sec] = collections.OrderedDict(
                S2[sec], inherits='; '.join(new if x == old else x for x in inh))
    return resolve(S2, name)


def parents(S, name, out=None):
    """Every parent in the raw inherits chain of `name`, depth first."""
    out = [] if out is None else out
    raw = S.get(name)
    if raw is None:
        return out
    kind = name.split(':', 1)[0]
    for p in [x.strip() for x in raw.get('inherits', '').split(';') if x.strip()]:
        out.append(p)
        parents(S, kind + ':' + p, out)
    return out


def pa_source(S, mat):
    """The INDX PA section this material inherits at 0.4, or None.

    A PA section is named like one and types an M572 in its own body. The name
    alone is not enough: PA_FLAT also matches the polyamide chamber section
    *C1INDX_CH_PA*, which would pass a polyamide base off as nozzle independent.
    Refuses on more than one, rather than letting chain order pick."""
    name = 'filament:' + mat + INDX_SUFFIX
    found = sorted({p for p in parents(S, name)
                    if (PA_SIZED.match(p) or PA_FLAT.match(p))
                    and m572(S.get('filament:' + p, {}).get('start_filament_gcode')) is not None})
    if len(found) > 1:
        sys.exit('refusing: %s inherits more than one INDX PA section (%s)'
                 % (mat + INDX_SUFFIX, ', '.join(found)))
    return found[0] if found else None


def m572(gcode):
    m = re.search(r'M572 S([\d.]+)', gcode or '')
    return m.group(1) if m else None


def pressure_advance(S, drafts, mat, dia):
    """(value, provenance) for this nozzle's PA, or (None, why not)."""
    sec = pa_source(S, mat)
    if sec is None:
        return None, 'no INDX PA section in the HF0.4 chain'

    # Prusa's own draft for this material at this size is the most specific source.
    draft = drafts.get('filament:%s @COREONEINDX HF%s' % (mat, dia), {})
    drafted = m572(draft.get('start_filament_gcode', ''))
    if drafted is not None:
        return drafted, "Prusa's commented %s @COREONEINDX HF%s draft" % (mat, dia)

    if PA_FLAT.match(sec):
        return None, '%s is nozzle independent upstream' % sec
    fam = PA_SIZED.match(sec).group(1)
    want = '*C1INDX_%s_%s_PA*' % (fam, pa_token(dia))
    if 'filament:' + want not in S:
        return None, 'no %s upstream' % want
    value = m572(resolve(S, 'filament:' + want).get('start_filament_gcode', ''))
    if value is None:
        return None, 'no M572 in %s' % want
    return value, want


def set_pa(gcode, pa):
    """Swap the M572 value in a quoted start_filament_gcode, keeping the rest."""
    if not re.search(r'M572 S[\d.]+', gcode):
        sys.exit('refusing: no M572 to set in %r' % gcode[:80])
    return re.sub(r'M572 S[\d.]+', 'M572 S' + pa, gcode)


def foreign_at(S, dia):
    """Prusa's own INDX filaments whose binding also admits a <dia> high-flow INDX
    printer - e.g. *PETHFC1INDX* binds by excluding 0.5/0.6/0.8, which says
    nothing about 1.0. Only reported: Prusa's bindings cannot be changed here."""
    from derive_std_filaments import evaluate   # its =~ / regex_match semantics
    name = 'printer:Prusa CORE One INDX 8T HF0.4 nozzle'
    base = resolve(S, name) if name in S else {'printer_model': 'COREONE_INDX8T'}
    printer = dict(base, nozzle_diameter=dia, nozzle_high_flow='1')
    hits = []
    for k in S:
        if not k.startswith('filament:') or k.startswith('filament:*'):
            continue
        cond = resolve(S, k).get('compatible_printers_condition', '')
        if 'INDX' not in cond:
            continue
        try:
            if evaluate(cond, printer):
                hits.append(k[len('filament:'):])
        except SystemExit:   # a warning must never abort the build
            hits.append('%s (binding not evaluated: %s)' % (k[len('filament:'):], cond[:60]))
    return sorted(hits)


def ref_pair(S, mat, dia):
    """(lo, hi, label) CORE One profiles bracketing the 0.4 -> dia step."""
    for lo, hi, label in [(' @COREONE HF0.4', ' @COREONE HF%s' % dia, 'HF0.4->HF%s' % dia),
                          (' @COREONE', ' @COREONE %s' % dia, '0.4->%s (non-HF)' % dia)]:
        a, b = 'filament:' + mat + lo, 'filament:' + mat + hi
        if a in S and b in S:
            return resolve(S, a), resolve(S, b), label
    return None, None, None


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('vendor', help='path to PrusaResearch.ini')
    ap.add_argument('out', help='output config bundle .ini')
    ap.add_argument('-n', '--nozzle', default='0.6', help='nozzle size (default 0.6)')
    args = ap.parse_args()
    dia = args.nozzle

    S = load(args.vendor)
    drafts = load_drafts(args.vendor)
    version = S.get('vendor', {}).get('config_version', '?')
    mats = sorted(k[9:-len(INDX_SUFFIX)] for k in S
                  if k.startswith('filament:') and k.endswith(INDX_SUFFIX))
    if not mats:
        sys.exit('no @COREONEINDX HF0.4 filament profiles found in ' + args.vendor)

    # A size Prusa publishes nothing for (nozzles.py, SCALED SIZES) is derived at
    # its source size and only emitted as itself: every value is the source
    # size's, held, and only the names, the binding and the notes say `dia`.
    noz = NOZZLES.get(dia)
    src = noz.scaled_from if noz and noz.scaled_from else dia
    if src != dia:
        assert_unsourced(S, drafts, dia)
    stray = foreign_at(S, dia) if src != dia else []   # reported at the end

    # Refuse rather than guess if Prusa published no reference for this size.
    covered = [m for m in mats if ref_pair(S, m, src)[0] is not None]
    if not covered:
        sys.exit('no CORE One reference profiles at %s mm - cannot derive MVS.\n'
                 'Prusa publishes standard filament variants at 0.6 and 0.8 and high-flow\n'
                 'ones at HF0.5, HF0.6 and HF0.8; at %s mm there is nothing in either\n'
                 'family to scale against.%s Measure MVS directly instead.'
                 % (src, src, '\n%s mm is derived at %s mm (nozzles.py, SCALED SIZES).'
                    % (dia, src) if src != dia else ''))

    validated = bool(noz and noz.validated)
    out = ['# INDX %s mm filament presets, by hyiger.' % dia,
           '# Generated by tools/derive_filaments.py from PrusaResearch.ini %s.' % version,
           '# Import via File > Import > Import Config Bundle.',
           '# Calibrate MVS, then pressure advance, then extrusion multiplier.']
    if not validated:
        out.append('# UNVALIDATED: %s mm has not been test printed. Max volumetric speed is'
                   % dia)
        out.append('#              ratio-scaled off Prusa 0.4 values, not measured here.')
    if src != dia:
        out.append('# HELD AT HF%s: Prusa publishes nothing at %s mm. Each preset is the HF%s'
                   % (src, dia, src))
        out.append('#              derivation unchanged - max volumetric speed, pressure')
        out.append('#              advance and every other value are %s\'s - only renamed'
                   % src)
        out.append('#              and rebound to a %s nozzle.' % dia)
    header_end = len(out)  # the per-nozzle common's block goes here, once counted
    out.append('')
    report, pa_report, draft_report = [], [], []
    commons = collections.OrderedDict()   # per-nozzle common -> (delta, {key: (moved, kept)}, users)

    for mat in mats:
        base = resolve(S, 'filament:' + mat + INDX_SUFFIX)
        lo, hi, label = ref_pair(S, mat, src)
        if lo is None:
            report.append((mat, base.get('filament_max_volumetric_speed', '?'),
                           '-', 'NO REFERENCE - skipped', ''))
            continue

        new = collections.OrderedDict(base)
        try:
            mvs0 = float(base['filament_max_volumetric_speed'])
            lo_mvs = float(lo['filament_max_volumetric_speed'])
            hi_mvs = float(hi['filament_max_volumetric_speed'])
        except (KeyError, ValueError) as e:
            sys.exit('refusing: %s has no usable filament_max_volumetric_speed to scale '
                     '(%s).\n          Emitting the unscaled 0.4 value with a provenance '
                     'note claiming otherwise\n          would be a fabricated record. '
                     'Measure MVS directly for this material.' % (mat, e))
        if lo_mvs <= 0:
            sys.exit('refusing: CORE One reference %s for %s has '
                     'filament_max_volumetric_speed %g;\n          there is no ratio to '
                     'form.' % (label, mat, lo_mvs))
        ratio = hi_mvs / lo_mvs
        mvs1 = round(mvs0 * ratio)
        new['filament_max_volumetric_speed'] = '%g' % mvs1

        moved = []
        for k in TRANSFER:
            if k in lo and k in hi and lo[k] != hi[k] and base.get(k) == lo[k]:
                new[k] = hi[k]
                moved.append('%s %s->%s' % (k, lo[k], hi[k]))

        # Pressure advance is Prusa's own figure for this nozzle, never a scaled one.
        pa0 = m572(base.get('start_filament_gcode', ''))
        pa1, pa_why = pressure_advance(S, drafts, mat, src)
        if pa1 is not None and pa1 != pa0:
            new['start_filament_gcode'] = set_pa(base['start_filament_gcode'], pa1)
            pa_note = 'PA %s -> %s from %s' % (pa0, pa1, pa_why)
        elif pa1 is not None:
            pa_note = 'PA %s unchanged; %s agrees with 0.4' % (pa0, pa_why)
        else:
            pa_note = 'PA %s kept from 0.4: %s' % (pa0, pa_why)
        pa_report.append((mat, pa0 or '-', pa1 or pa0 or '-', pa_why))

        # Prusa's per-nozzle INDX common, placed where Prusa's chain places it:
        # re-resolve the base with its 0.4 family swapped for the sized one. The
        # 0.4 family and anything inherited before it give way; a value the 0.4
        # preset sets in its own body survives, as an own override always does.
        fam04, fam = family_at(S, mat, src)
        common_sec = sized_common(S, fam)
        if common_sec not in commons:
            commons[common_sec] = (common_delta(S, common_sec), collections.OrderedDict(), [])
        delta, creport, users = commons[common_sec]
        users.append(mat)
        common_notes = []
        if delta:
            sub = substituted(S, 'filament:' + mat + INDX_SUFFIX, fam04, fam)
            prusa = resolve(S, 'filament:' + fam)
        for k in sorted(delta):
            c_moved, c_kept = creport.setdefault(k, ([], []))
            if sub.get(k) != base.get(k):
                new[k] = sub[k]
                common_notes.append('%s %s -> %s' % (k, base.get(k) or 'unset', sub[k]))
                c_moved.append(mat)
            elif base.get(k) != prusa.get(k):
                common_notes.append('own %s %s kept over %s' % (k, base[k], prusa.get(k)))
                c_kept.append('%s %s' % (mat, base[k]))
        common_note = ' %s: %s.' % (common_sec, '; '.join(common_notes)) if common_notes else ''

        # Show what Prusa's commented draft for this size says, adopted or not.
        draft = drafts.get('filament:%s @COREONEINDX HF%s' % (mat, src), {})
        for k in DRAFT_WATCH:
            if k in draft and draft[k] != new.get(k):
                draft_report.append((mat, k, draft[k], new.get(k, '-')))

        new.pop('renamed_from', None)  # a new preset, not a rename of the base
        new['compatible_printers_condition'] = (
            printer_models(base.get('compatible_printers_condition')) + BIND_TMPL % dia)
        new['compatible_printers'] = ''
        new['filament_settings_id'] = ''
        # Keep Prusa's own notes: the INDX start G-code reads markers such as
        # MBL160 (Prusament TPU 95A) out of filament_notes to pick the probe temp.
        notes = base.get('filament_notes', '""').strip('"')
        held = ('INDX %s seed, held at HF%s: Prusa publishes nothing at %s mm, so every '
                'value is the HF%s derivation below, unchanged. ' % (dia, src, dia, src)
                if src != dia else '')
        new['filament_notes'] = '"%s%s%s"' % (
            notes + '\\n' if notes else '', held,
            'INDX %s seed. Base: %s. MVS %g -> %g via CORE One %s (x%.2f). %s.%s '
            'Prusa nozzle ratio applied to a Bondtech CHT - re-measure MVS and PA.'
            % (src, mat + INDX_SUFFIX, mvs0, mvs1, label, ratio, pa_note, common_note))

        out.append('[filament:%s @COREONEINDX HF%s]' % (mat, dia))
        for k in sorted(new):
            out.append('%s = %s' % (k, new[k]))
        out.append('')
        report.append((mat, '%g' % mvs0, '%g' % mvs1, label, '; '.join(moved)))

    block = []
    for common_sec, (delta, creport, users) in commons.items():
        if not delta:
            continue
        block += ['#', '# From Prusa\'s per-nozzle INDX common %s, which its %s family sections'
                  % (common_sec, src), '# stand on in place of %s (COMMON_ADOPT):' % COMMON]
        for k, (moved, kept) in creport.items():
            v0, v1 = delta[k]
            block.append('#   %s: %s -> %s, on %d of %d presets%s'
                         % (k, v0 or 'unset', v1, len(moved), len(users),
                            '; the rest keep their own 0.4 value' if kept else ''))
            block.append('#       %s' % COMMON_ADOPT[k])
    out[header_end:header_end] = block

    with open(args.out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))

    w = max(len(r[0]) for r in report)
    if src != dia:
        print('%s mm: Prusa publishes nothing here, so every value below is the HF%s '
              'derivation, held.\n' % (dia, src))
    print('%-*s %7s %7s  %-20s %s' % (w, 'material', 'MVS 0.4', 'MVS ' + dia,
                                      'reference', 'other transfers'))
    print('-' * (w + 92))
    for m, a, b, l, x in report:
        print('%-*s %7s %7s  %-20s %s' % (w, m, a, b, l, x or '-'))

    print('\n%-*s %8s %8s  %s' % (w, 'material', 'PA 0.4', 'PA ' + dia, 'source'))
    print('-' * (w + 60))
    for m, a, b, why in pa_report:
        print('%-*s %8s %8s  %s' % (w, m, a, b, why))

    for common_sec, (delta, creport, users) in commons.items():
        if not delta:
            continue
        print('\nPer-nozzle INDX common %s, over %s (%d presets):'
              % (common_sec, COMMON, len(users)))
        for k, (moved, kept) in creport.items():
            v0, v1 = delta[k]
            print('  %s %s -> %s on %d presets' % (k, v0 or 'unset', v1, len(moved)))
            print('    reason: %s' % COMMON_ADOPT[k])
            if kept:
                print('    own 0.4 value kept: %s' % ', '.join(kept))

    if draft_report:
        print('\nPrusa\'s commented "@COREONEINDX HF%s" drafts disagree here, and are not '
              'adopted\n(see README "Known gaps"):' % src)
        print('%-*s %-34s %8s %8s' % (w, 'material', 'key', 'draft', 'derived'))
        print('-' * (w + 54))
        for m, k, d, v in draft_report:
            print('%-*s %-34s %8s %8s' % (w, m, k, d, v))

    if src != dia:
        if stray:
            print('\n!! %d of Prusa\'s own INDX filaments also bind to a %s INDX printer, because'
                  % (len(stray), dia))
            print('   Prusa excludes sizes by listing them and %s is not listed. They carry 0.4'
                  % dia)
            print('   MVS and pressure advance; pick the @COREONEINDX HF%s presets instead:' % dia)
            for name in stray:
                print('     ' + name)

    print('\n%d presets -> %s' % (len([r for r in report if r[2] != '-']), args.out))
    if not validated:
        print('!! UNVALIDATED: %s mm has not been test printed. Calibrate MVS first.' % dia)
    return 0


if __name__ == '__main__':
    sys.exit(main())
