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
a default for every key it omits. (Config *bundles* differ -
flatten_configbundle_hierarchy resolves `inherits` there - but these are not
bundles.) `inherits` is still written: it drives the UI's reset-to-system
arrows and modified-value markers, and is not consulted when loading config.

Nothing here is invented. The nozzle-size delta is read out of Prusa's own
CORE One `HF0.4` -> `HF<dia>` pair at run time, and each key transfers to INDX
only where INDX agreed with CORE One at 0.4 - the rule derive_filaments.py
applies to non-MVS keys. A key that appears in the upstream delta but is not
in TRANSFER, or where INDX deliberately disagreed, is a refusal rather than a
guess.

    python3 build_printer_preset.py PrusaResearch.ini printer/ -n 0.6
    python3 build_printer_preset.py PrusaResearch.ini printer/ -n 0.6 -m 4T
"""
import argparse
import os
import sys

from build_print_profiles import load, resolve
from nozzles import NOZZLES

BYLINE = 'hyiger'

# INDX models, and the shipping 0.4 preset each derives from.
MODELS = {
    '8T': ('COREONE_INDX8T', 'Prusa CORE One INDX 8T HF0.4 nozzle'),
    '4T': ('COREONE_INDX4T', 'Prusa CORE One INDX 4T HF0.4 nozzle'),
}

# The reference pair. Prusa ships CORE One HF0.4/0.5/0.6/0.8 only, which is why
# 0.25 and 0.3 refuse here exactly as they do in derive_filaments.py.
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
}

# INDX sets these to its own profile family. Keep the family, move the size.
RETARGET = {
    'default_print_profile': '0.25mm Balanced ★ @COREONEINDX HF%s',
    'default_filament_profile': '"Prusament PLA @COREONEINDX HF%s"',
}


def uniform(value):
    """INDX carries per-extruder vectors. Return the single value, or None."""
    parts = [p.strip() for p in value.split(',')]
    return parts[0] if len(set(parts)) == 1 else None


def widen(template, value):
    """Match the arity of the key being replaced."""
    return ','.join([value] * len(template.split(',')))


def build(vendor, dia, model, report):
    if dia not in NOZZLES:
        raise SystemExit('refusing: %s is not in the nozzles.py table' % dia)
    if model not in MODELS:
        raise SystemExit('refusing: unknown model %s' % model)
    printer_model, base_name = MODELS[model]

    ref_name = REF_FMT % dia
    if 'printer:' + ref_name not in vendor:
        raise SystemExit(
            'refusing: no [printer:%s] upstream, so there is no sourced\n'
            '          0.4 -> %s delta to apply. Prusa ships CORE One HF0.4,\n'
            '          HF0.5, HF0.6 and HF0.8 only.' % (ref_name, dia))

    ref04 = resolve(vendor, 'printer:' + REF_BASE)
    ref = resolve(vendor, 'printer:' + ref_name)
    cfg = dict(resolve(vendor, 'printer:' + base_name))

    delta = sorted(k for k in set(ref04) | set(ref) if ref04.get(k) != ref.get(k))
    unexpected = [k for k in delta if k not in TRANSFER and k not in RETARGET]
    if unexpected:
        raise SystemExit(
            'refusing: upstream HF0.4 -> HF%s delta touches unreviewed keys:\n'
            '          %s\n'
            '          Add them to TRANSFER with a reason, or handle them.'
            % (dia, ', '.join(unexpected)))

    changed = []
    for key in delta:
        if key in RETARGET:
            new = RETARGET[key] % dia
            changed.append((key, cfg[key], new, 'INDX pointer, retargeted to %s' % dia))
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
                        'CORE One HF%s; INDX agreed at 0.4 (%s == %s)'
                        % (dia, indx_at_04, ref04[key])))
        cfg[key] = new

    cfg['inherits'] = base_name
    assert cfg['printer_model'] == printer_model, 'model mismatch'
    return cfg, changed


def emit(path, cfg, changed, dia, model, validated):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# Prusa CORE One INDX %s, %s mm high flow. Generated by %s\n'
                % (model, dia, BYLINE))
        f.write('# tools/build_printer_preset.py from PrusaResearch.ini.\n')
        f.write('# Fully flattened - a loose user preset is applied over\n')
        f.write('# PrusaSlicer defaults, not over its inherits parent.\n')
        f.write('#\n')
        if not validated:
            f.write('# UNVALIDATED: this size has not been test printed.\n#\n')
        f.write('# Changed from the shipping 0.4 preset:\n')
        for key, old, new, why in changed:
            f.write('#   %s: %s -> %s\n'
                    % (key, old.split(',')[0], new.split(',')[0]))
            f.write('#       %s\n' % why)
        f.write('#\n')
        f.write('# wipe is the one behaviour change rather than a dimension.\n')
        f.write('# It is Prusa\'s own choice above 0.4, but has never run on an\n')
        f.write('# INDX toolchanger. Set it back to 0 if tool changes string.\n')
        f.write('\n')
        for k in sorted(cfg):
            f.write('%s = %s\n' % (k, cfg[k]))


def main():
    ap = argparse.ArgumentParser(
        description='Emit a flattened INDX printer preset for a given nozzle.')
    ap.add_argument('prusa_ini')
    ap.add_argument('outdir')
    ap.add_argument('-n', '--nozzle', action='append', required=True,
                    help='nozzle diameter, e.g. 0.6 (repeatable)')
    ap.add_argument('-m', '--model', action='append',
                    choices=sorted(MODELS), help='INDX model (default 8T)')
    a = ap.parse_args()

    vendor = load(a.prusa_ini)
    models = a.model or ['8T']
    os.makedirs(a.outdir, exist_ok=True)

    for dia in a.nozzle:
        for model in models:
            report = []
            cfg, changed = build(vendor, dia, model, report)
            name = 'Prusa CORE One INDX %s HF%s nozzle' % (model, dia)
            path = os.path.join(a.outdir, name + '.ini')
            validated = NOZZLES[dia].validated
            emit(path, cfg, changed, dia, model, validated)

            print('%s  (%d keys)' % (path, len(cfg)))
            for key, old, new, _ in changed:
                print('    %-26s %-22s -> %s'
                      % (key, old.split(',')[0][:21], new.split(',')[0][:44]))
            for line in report:
                print(line)
            if not validated:
                print('    !! UNVALIDATED - %s has not been printed' % dia)

    return 0


if __name__ == '__main__':
    sys.exit(main())
