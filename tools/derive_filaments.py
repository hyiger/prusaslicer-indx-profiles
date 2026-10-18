#!/usr/bin/env python3
"""
Derive INDX filament presets for a given nozzle size from Prusa's own profiles.

Prusa ships 19 filament profiles for the INDX. All of them require a high-flow
nozzle except Generic FLEX and Prusament TPU 95A: 11 pin
`nozzle_diameter[0]==0.4` and the PET/ABS/BVOH eight bind by exclusion
(`!=0.8 and !=0.6 and !=0.5`). Either way, select a 0.6 toolhead and the
filament dropdown empties.

Method
------
Base: <mat> @COREONEINDX HF0.4  -- carries the INDX toolchanger settings
      (multitool ramming, purge volumes, cooling-move behaviour).

Scaling reference: the CORE One HF0.4 -> HF<dia> pair for the same material,
which is Prusa's measured answer to "what changes when this filament moves to a
<dia> high-flow nozzle". Falls back to the non-HF @COREONE -> @COREONE <dia>
pair where Prusa published no high-flow profile.

Three rules:
  * filament_max_volumetric_speed is always ratio-scaled off the INDX 0.4 value,
    because the INDX toolhead has its own flow baseline distinct from CORE One.
  * pressure advance is Prusa's own figure for this nozzle, not a scaled one:
    the M572 value in `*C1INDX_<FAM>_<dia>_PA*`, or the one Prusa typed into its
    commented `<mat> @COREONEINDX HF<dia>` draft where that is more specific.
    Prusa's INDX PA falls as the nozzle grows (PLA 0.031 at 0.4 -> 0.02 at 0.6),
    so carrying the 0.4 figure across would over-retract on deceleration.
  * every other key takes the CORE One <dia> value ONLY if INDX agreed with
    CORE One at 0.4. Where INDX already differs it made a deliberate
    toolchanger-specific choice, so that choice is preserved.

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

These are Prusa nozzle ratios applied to a Bondtech CHT. Treat every number as a
starting point and calibrate MVS before trusting it.

    python3 derive_filaments.py PrusaResearch.ini out.ini --nozzle 0.6
"""
import argparse
import collections
import re
import sys

from build_print_profiles import load, load_drafts, resolve
from nozzles import NOZZLES

INDX_SUFFIX = ' @COREONEINDX HF0.4'
COND_TMPL = ('printer_model=~/(COREONE_INDX8T|COREONE_INDX4T|COREONEL_INDX8T|COREONEL_INDX4T)/ '
             'and nozzle_diameter[0]==%s and nozzle_high_flow[0]')

# Keys worth transferring when INDX and CORE One agreed at 0.4.
TRANSFER = ['slowdown_below_layer_time', 'fan_below_layer_time', 'min_print_speed',
            'filament_infill_max_speed', 'filament_infill_max_crossing_speed',
            'filament_cooling_final_speed', 'bridge_fan_speed', 'max_fan_speed',
            'min_fan_speed', 'disable_fan_first_layers', 'full_fan_speed_layer']

# Prusa's per-family, per-nozzle pressure-advance sections. The nozzle token is
# the diameter without its dot, exactly as Prusa writes it: 0.6 -> 06.
PA_SIZED = re.compile(r'^\*C1INDX_([A-Z]+)_(\d+)_PA\*$')
PA_FLAT = re.compile(r'^\*C1INDX_([A-Z]+)_PA\*$')     # nozzle independent, e.g. FLEX
# Keys from Prusa's commented HF<dia> drafts to show against the derived values.
DRAFT_WATCH = ['filament_max_volumetric_speed', 'slowdown_below_layer_time']


def pa_token(dia):
    """Prusa's PA-section nozzle token: '0.6' -> '06', '0.25' -> '025'."""
    return dia.replace('.', '')


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
    """The INDX PA section this material inherits at 0.4, or None."""
    for p in parents(S, 'filament:' + mat + INDX_SUFFIX):
        if PA_SIZED.match(p) or PA_FLAT.match(p):
            return p
    return None


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

    # Refuse rather than guess if Prusa published no reference for this size.
    covered = [m for m in mats if ref_pair(S, m, dia)[0] is not None]
    if not covered:
        sys.exit('no CORE One reference profiles at %s mm - cannot derive MVS.\n'
                 'Prusa publishes standard filament variants at 0.6 and 0.8 and high-flow\n'
                 'ones at HF0.5, HF0.6 and HF0.8; at %s mm there is nothing in either\n'
                 'family to scale against. Measure MVS directly instead.' % (dia, dia))

    noz = NOZZLES.get(dia)
    validated = bool(noz and noz.validated)
    out = ['# INDX %s mm filament presets, by hyiger.' % dia,
           '# Generated by tools/derive_filaments.py from PrusaResearch.ini %s.' % version,
           '# Import via File > Import > Import Config Bundle.',
           '# Calibrate MVS, then pressure advance, then extrusion multiplier.']
    if not validated:
        out.append('# UNVALIDATED: %s mm has not been test printed. Max volumetric speed is'
                   % dia)
        out.append('#              ratio-scaled off Prusa 0.4 values, not measured here.')
    out.append('')
    report, pa_report, draft_report = [], [], []

    for mat in mats:
        base = resolve(S, 'filament:' + mat + INDX_SUFFIX)
        lo, hi, label = ref_pair(S, mat, dia)
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
        pa1, pa_why = pressure_advance(S, drafts, mat, dia)
        if pa1 is not None and pa1 != pa0:
            new['start_filament_gcode'] = set_pa(base['start_filament_gcode'], pa1)
            pa_note = 'PA %s -> %s from %s' % (pa0, pa1, pa_why)
        elif pa1 is not None:
            pa_note = 'PA %s unchanged; %s agrees with 0.4' % (pa0, pa_why)
        else:
            pa_note = 'PA %s kept from 0.4: %s' % (pa0, pa_why)
        pa_report.append((mat, pa0 or '-', pa1 or pa0 or '-', pa_why))

        # Show what Prusa's commented draft for this size says, adopted or not.
        draft = drafts.get('filament:%s @COREONEINDX HF%s' % (mat, dia), {})
        for k in DRAFT_WATCH:
            if k in draft and draft[k] != new.get(k):
                draft_report.append((mat, k, draft[k], new.get(k, '-')))

        new.pop('renamed_from', None)  # a new preset, not a rename of the base
        new['compatible_printers_condition'] = COND_TMPL % dia
        new['compatible_printers'] = ''
        new['filament_settings_id'] = ''
        # Keep Prusa's own notes: the INDX start G-code reads markers such as
        # MBL160 (Prusament TPU 95A) out of filament_notes to pick the probe temp.
        notes = base.get('filament_notes', '""').strip('"')
        new['filament_notes'] = '"%s%s"' % (
            notes + '\\n' if notes else '',
            'INDX %s seed. Base: %s. MVS %g -> %g via CORE One %s (x%.2f). %s. '
            'Prusa nozzle ratio applied to a Bondtech CHT - re-measure MVS and PA.'
            % (dia, mat + INDX_SUFFIX, mvs0, mvs1, label, ratio, pa_note))

        out.append('[filament:%s @COREONEINDX HF%s]' % (mat, dia))
        for k in sorted(new):
            out.append('%s = %s' % (k, new[k]))
        out.append('')
        report.append((mat, '%g' % mvs0, '%g' % mvs1, label, '; '.join(moved)))

    with open(args.out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))

    w = max(len(r[0]) for r in report)
    print('%-*s %7s %7s  %-20s %s' % (w, 'material', 'MVS 0.4', 'MVS ' + dia,
                                      'reference', 'other transfers'))
    print('-' * (w + 92))
    for m, a, b, l, x in report:
        print('%-*s %7s %7s  %-20s %s' % (w, m, a, b, l, x or '-'))

    print('\n%-*s %8s %8s  %s' % (w, 'material', 'PA 0.4', 'PA ' + dia, 'source'))
    print('-' * (w + 60))
    for m, a, b, why in pa_report:
        print('%-*s %8s %8s  %s' % (w, m, a, b, why))

    if draft_report:
        print('\nPrusa\'s commented "@COREONEINDX HF%s" drafts disagree here, and are not '
              'adopted\n(see README "Known gaps"):' % dia)
        print('%-*s %-34s %8s %8s' % (w, 'material', 'key', 'draft', 'derived'))
        print('-' * (w + 54))
        for m, k, d, v in draft_report:
            print('%-*s %-34s %8s %8s' % (w, m, k, d, v))

    print('\n%d presets -> %s' % (len([r for r in report if r[2] != '-']), args.out))
    if not validated:
        print('!! UNVALIDATED: %s mm has not been test printed. Calibrate MVS first.' % dia)
    return 0


if __name__ == '__main__':
    sys.exit(main())
