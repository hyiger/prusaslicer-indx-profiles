#!/usr/bin/env python3
"""
Derive INDX filament presets for a standard (non-high-flow) 0.4 or 0.25 mm
nozzle from Prusa's own profiles.

All 19 of Prusa's INDX filaments require `nozzle_high_flow[0]` except Generic
FLEX and Prusament TPU 95A, which bind on diameter alone. Eleven pin
`nozzle_diameter[0]==0.4`; the PET/ABS/BVOH eight bind by exclusion
(`nozzle_diameter[0]!=0.8 and !=0.6 and !=0.5`), via *PETHFC1INDX* and
*ABSHFC1INDX*, so those also reach a high-flow 0.25 or 0.3. Either way, on a
standard nozzle the filament list is almost empty.

PrusaResearch.ini already holds the pieces for standard nozzles, unused:
INDX STD bases (*PLAPGC1INDX*, *PETPGC1INDX*, *ABSPGC1INDX*, *PCPGC1INDX*),
INDX 0.25 bases (*PLA025PGC1INDX*, *PET025PGC1INDX*), and commented-out drafts
of "Prusament PLA/PETG @COREONEINDX 0.25". Each preset here is built from those.
Nothing is ratio-scaled, which is why this works at 0.25 where
derive_filaments.py has to refuse.

0.4 (standard)
  * Parents swapped: the CORE One HF0.4 parent becomes its CORE One STD
    counterpart, and the INDX HF base becomes Prusa's INDX STD base. The INDX
    preset's own overrides (toolchanger retraction, purge, cooling) are kept.
  * filament_max_volumetric_speed = min(INDX HF0.4 value, CORE One STD value
    of the same filament).
  * Pressure advance stays the INDX HF0.4 preset's own value. Prusa ships no
    concrete INDX STD 0.4 preset; for PET, ABS and PC its STD and HF 0.4 bases
    share one PA base (*C1INDX_PET_04_PA* 0.048, _ABS_ 0.02, _PC_ 0.05), and a
    concrete preset's own override is kept over it. Only the PLA family has no
    INDX standard figure at all. On the CORE One, STD and HF0.4 are close.

0.25 (standard)
  * Only filaments whose CORE One STD profile Prusa allows on a 0.25 nozzle.
    That rules out carbon fiber and Woodfill. FLEX is skipped: the INDX has no
    0.25 FLEX base.
  * Prusament PLA and PETG are Prusa's drafts, as written.
  * Others get the CORE One STD parent plus the INDX 0.25 base (PLA, PET
    families) or INDX STD base (ABS, PC families). Nozzle-dependent own keys
    are dropped so the swapped-in base supplies them. The INDX STD bases
    (ABS/PC) define no filament_retract_* or filament_travel_max_lift, so for
    those families the key is released to the printer preset's own value
    instead; every such key is named in the preset's filament_notes. Cooling: ABS/PC families keep their own (those bases do not
    vary with the nozzle); PLA/PET families keep a value they set themselves
    that differs from the flagship's, follow the flagship's draft where they
    matched it at HF0.4, and otherwise take the 0.25 base.
  * Pressure advance comes from the INDX 0.25 base (PLA 0.1, PET 0.15) or,
    where there is none, the CORE One's own 0.25 value swapped into the INDX
    start G-code, which keeps M906 P2 and friends.
  * filament_max_volumetric_speed = min(INDX HF0.4, CORE One STD, 0.25 chain).

Every number is Prusa's. Calibrate pressure advance and max volumetric speed
before trusting them.

    python3 derive_std_filaments.py PrusaResearch.ini out.ini --nozzle 0.4
    python3 derive_std_filaments.py PrusaResearch.ini out.ini --nozzle 0.25
"""
import argparse
import collections
import re
import sys

from build_print_profiles import load, load_drafts, resolve
from nozzles import STD_VALIDATED

INDX_SUFFIX = ' @COREONEINDX HF0.4'
MODELS = 'printer_model=~/(COREONE_INDX8T|COREONE_INDX4T|COREONEL_INDX8T|COREONEL_INDX4T)/'
COND = {'0.4': MODELS + ' and nozzle_diameter[0]==0.4 and ! nozzle_high_flow[0]',
        '0.25': MODELS + ' and nozzle_diameter[0]==0.25'}

# Prusa's INDX HF0.4 bases -> its unused STD bases, per nozzle.
BASE_SWAP = {
    '0.4': {'*PLAHFC1INDX*': '*PLAPGC1INDX*', '*PETHFC1INDX*': '*PETPGC1INDX*',
            '*ABSHFC1INDX*': '*ABSPGC1INDX*', '*PCHFC1INDX*': '*PCPGC1INDX*'},
    '0.25': {'*PLAHFC1INDX*': '*PLA025PGC1INDX*', '*PETHFC1INDX*': '*PET025PGC1INDX*',
             '*ABSHFC1INDX*': '*ABSPGC1INDX*', '*PCHFC1INDX*': '*PCPGC1INDX*'},
}
# Keys that depend on the nozzle: flow, PA, retraction, speed limits.
NOZZLE_KEYS = {'filament_max_volumetric_speed', 'start_filament_gcode', 'slowdown_below_layer_time',
               'filament_retract_length', 'filament_retract_length_toolchange',
               'filament_travel_max_lift', 'filament_retract_before_wipe', 'filament_wipe',
               'min_print_speed', 'filament_infill_max_speed', 'filament_infill_max_crossing_speed'}
COOLING_KEYS = {'fan_below_layer_time', 'min_fan_speed', 'max_fan_speed', 'bridge_fan_speed',
                'enable_dynamic_fan_speeds', 'overhang_fan_speed_0', 'overhang_fan_speed_1',
                'overhang_fan_speed_2', 'overhang_fan_speed_3',
                'cooling_perimeter_transition_distance'}
# INDX 0.25 bases and the flagship filament whose Prusa draft sets the family's tune.
FLAGSHIP_025 = {'*PLA025PGC1INDX*': 'Prusament PLA', '*PET025PGC1INDX*': 'Prusament PETG'}
CORE_ONE_025 = 'Prusa CORE One 0.25 nozzle'


def fmt(v):
    v = float(v)
    return str(int(v)) if v == int(v) else str(v)


def evaluate(cond, printer):
    """Evaluate a compatible_printers_condition against a resolved printer.

    =~ is regex_match (full string) over boost::regex, where . matches newline,
    hence fullmatch with re.S. Anything this cannot parse raises, so a filament
    is never included or excluded on a guess."""
    first = lambda key: printer.get(key, '').split(',')[0].strip()
    env = {'printer_model': printer.get('printer_model', ''),
           'printer_notes': printer.get('printer_notes', '').replace('\\n', '\n'),
           'nozzle_diameter[0]': float(first('nozzle_diameter')),
           'nozzle_high_flow[0]': first('nozzle_high_flow') == '1',
           'single_extruder_multi_material': first('single_extruder_multi_material') == '1'}

    def regex(m):
        hit = re.fullmatch(m.group(3), env[m.group(1)], re.S) is not None
        return ' %s ' % (hit if m.group(2) == '=~' else not hit)

    expr = re.sub(r'(printer_model|printer_notes)\s*(=~|!~)\s*/(.*?)/', regex, cond)
    for var in sorted(env, key=len, reverse=True):
        expr = expr.replace(var, ' %r ' % env[var])
    expr = re.sub(r'!(?!=)', ' not ', expr)
    try:
        return bool(eval(expr, {'__builtins__': {}}, {}))
    except Exception as e:
        raise SystemExit('refusing: cannot evaluate condition %r (%s)' % (cond, e))


def pa_025(gcode):
    """The 0.25 mm pressure advance in a start_filament_gcode: the M572 branch of a
    nozzle-conditional expression, or a plain M572 value."""
    if 'M572 S' in gcode:
        gcode = gcode[gcode.find('M572 S'):]  # skip a legacy M900 branch before it
    m = re.search(r'==0\.25\}([\d.]+)', gcode) or re.search(r'M572 S([\d.]+)', gcode)
    if not m:
        raise SystemExit('refusing: no 0.25 pressure advance in %r' % gcode[:80])
    return m.group(1)


def set_pa(gcode, pa):
    """Swap the M572 value in a quoted start_filament_gcode, keeping the rest."""
    if not re.search(r'M572 S[\d.]+', gcode):
        raise SystemExit('refusing: no M572 to set in %r' % gcode[:80])
    return re.sub(r'M572 S[\d.]+', 'M572 S' + pa, gcode)


def supplied_by(S, parents):
    """Keys the swapped-in parent chain actually defines."""
    keys = set()
    for p in parents:
        if 'filament:' + p in S:
            keys |= set(resolve(S, 'filament:' + p))
    return keys


def tune_025(own, parents, hf, S, drafts):
    """Nozzle and cooling keys of a 0.25 preset that has no Prusa draft of its own.

    Returns the keys dropped that no swapped-in parent re-supplies, which
    therefore fall through to the printer preset's own value."""
    flagship = next((FLAGSHIP_025[p] for p in parents if p in FLAGSHIP_025), None)
    if flagship is None:
        supplied = supplied_by(S, parents)
        released = sorted(k for k in NOZZLE_KEYS - {'slowdown_below_layer_time'}
                          if k in own and k not in supplied)
        for k in NOZZLE_KEYS - {'slowdown_below_layer_time'}:
            own.pop(k, None)
        return released
    flag_hf = resolve(S, 'filament:' + flagship + INDX_SUFFIX)
    tune = drafts['filament:%s @COREONEINDX 0.25' % flagship]
    for k in (NOZZLE_KEYS | COOLING_KEYS) - {'filament_max_volumetric_speed', 'start_filament_gcode'}:
        mine = own.pop(k, None)
        if mine is not None and mine != flag_hf.get(k):
            own[k] = mine
        elif hf.get(k) == flag_hf.get(k) and k in tune:
            own[k] = tune[k]
    own.pop('filament_max_volumetric_speed', None)
    own.pop('start_filament_gcode', None)
    return []


def derive(S, drafts, dia):
    """Yield (name, config, provenance) for every derivable preset at this size."""
    core_one_025 = resolve(S, 'printer:' + CORE_ONE_025) if dia == '0.25' else None
    built = {}
    for key in [k for k in S if k.startswith('filament:') and k.endswith(INDX_SUFFIX)]:
        mat = key[len('filament:'):-len(INDX_SUFFIX)]
        hf = resolve(S, key)
        if 'nozzle_high_flow' not in hf.get('compatible_printers_condition', ''):
            continue  # FLEX/TPU: binds on diameter alone; no INDX 0.25 FLEX base
        co_std = 'filament:%s @COREONE' % mat
        if co_std not in S:
            raise SystemExit('refusing: %s has no CORE One STD counterpart' % key)
        if dia == '0.25' and not evaluate(resolve(S, co_std).get('compatible_printers_condition', ''),
                                          core_one_025):
            continue  # Prusa does not allow it on a 0.25 nozzle

        name = '%s @COREONEINDX %s' % (mat, dia)
        draft = drafts.get('filament:' + name) if dia == '0.25' else None
        released = []
        if draft is not None:
            own = collections.OrderedDict(draft)
            parents = [p.strip() for p in own.pop('inherits').split(';')]
            how = 'Prusa\'s draft'
        else:
            own = collections.OrderedDict(S[key])
            parents = []
            for p in [x.strip() for x in own.pop('inherits', '').split(';') if x.strip()]:
                if p.endswith(INDX_SUFFIX):
                    p = p[:-len(INDX_SUFFIX)] + ' @COREONEINDX ' + dia   # built earlier
                elif p.endswith(' HF0.4') and 'filament:' + p[:-6] in S:
                    p = p[:-6]                                          # CORE One STD parent
                parents.append(BASE_SWAP[dia].get(p, p))
            if dia == '0.25':
                released = tune_025(own, parents, hf, S, drafts)
            else:
                own.pop('filament_max_volumetric_speed', None)
            how = 'parents %s' % '; '.join(parents)

        S['filament:' + name] = collections.OrderedDict(own, inherits='; '.join(parents))
        cfg = collections.OrderedDict(resolve(S, 'filament:' + name))
        caps = [hf['filament_max_volumetric_speed'], resolve(S, co_std)['filament_max_volumetric_speed']]
        if dia == '0.25':
            caps.append(cfg['filament_max_volumetric_speed'])
        cfg['filament_max_volumetric_speed'] = fmt(min(float(c) for c in caps))

        pa_note = 'PA kept from HF0.4'
        if dia == '0.25':
            if draft is not None:
                pa_note = 'PA from Prusa\'s own 0.25 draft'
            elif set(FLAGSHIP_025) & set(parents):
                # tune_025 dropped the whole INDX start G-code to reach the 0.25
                # base's PA. Rebuild it around that value so the rest of the INDX
                # start G-code - M573 R, M906 P2 - survives.
                cfg['start_filament_gcode'] = set_pa(
                    hf['start_filament_gcode'], pa_025(cfg['start_filament_gcode']))
                pa_note = 'PA from the INDX 0.25 base'
            else:
                cfg['start_filament_gcode'] = set_pa(
                    hf['start_filament_gcode'], pa_025(resolve(S, co_std)['start_filament_gcode']))
                pa_note = 'PA from the CORE One 0.25 value'

        cfg.pop('renamed_from', None)  # a new preset, not a rename of the source
        cfg['compatible_printers_condition'] = COND[dia]
        cfg['compatible_printers'] = ''
        cfg['filament_settings_id'] = ''
        provenance = ('INDX %s STD seed from %s (%s). MVS %s (min of INDX HF0.4 %s, CORE One STD %s%s). '
                      '%s. Calibrate PA and MVS.'
                      % (dia, mat + INDX_SUFFIX, how, cfg['filament_max_volumetric_speed'],
                         fmt(caps[0]), fmt(caps[1]), ', 0.25 chain %s' % fmt(caps[2]) if dia == '0.25' else '',
                         pa_note))
        if released:
            provenance += (' Released to the printer preset (no swapped-in INDX base '
                           'defines them): %s.' % ', '.join(released))
        notes = cfg.get('filament_notes', '""').strip('"')
        cfg['filament_notes'] = '"%s"' % ((notes + '\\n' if notes else '') + provenance)
        built[name] = cfg
        yield name, cfg, (mat, fmt(caps[0]), cfg['filament_max_volumetric_speed'], how, pa_note)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('vendor', help='path to PrusaResearch.ini')
    ap.add_argument('out', help='output config bundle .ini')
    ap.add_argument('-n', '--nozzle', required=True, choices=sorted(COND),
                    help='standard nozzle size')
    args = ap.parse_args()
    dia = args.nozzle

    S = load(args.vendor)
    drafts = load_drafts(args.vendor)
    version = S.get('vendor', {}).get('config_version', '?')
    out = ['# INDX %s mm standard (non-high-flow) nozzle filament presets, by hyiger.' % dia,
           '# Generated by tools/derive_std_filaments.py from PrusaResearch.ini %s.' % version,
           '# Import via File > Import > Import Config Bundle.',
           '# Calibrate pressure advance and MVS before trusting them.']
    if not STD_VALIDATED.get(dia, False):
        out.append('# UNVALIDATED: not yet test printed on a standard %s mm INDX nozzle.' % dia)
    out.append('')
    report = []
    for name, cfg, row in derive(S, drafts, dia):
        out.append('[filament:%s]' % name)
        for k in sorted(cfg):
            out.append('%s = %s' % (k, cfg[k]))
        out.append('')
        report.append(row)
    if not report:
        sys.exit('no INDX filament profiles derivable at %s mm' % dia)

    with open(args.out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))

    w = max(len(r[0]) for r in report)
    print('%-*s %7s %7s  %s' % (w, 'material', 'MVS HF', 'MVS ' + dia, 'source'))
    print('-' * (w + 60))
    for mat, a, b, how, pa in report:
        print('%-*s %7s %7s  %s; %s' % (w, mat, a, b, how, pa))
    print('\n%d presets -> %s' % (len(report), args.out))
    if not STD_VALIDATED.get(dia, False):
        print('!! UNVALIDATED: not yet test printed on a standard %s mm nozzle' % dia)
    return 0


if __name__ == '__main__':
    sys.exit(main())
