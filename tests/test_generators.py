"""
Synthetic-INI tests for the generators' refusals and guards.

Each test writes a tiny PrusaResearch.ini-shaped file, runs a generator on it the
way the CLAUDE.md recipe does, and checks what it emitted, or that it refused and
wrote nothing. None needs a real PrusaResearch.ini.

    python3 -m unittest discover -s tests -v
"""
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'tools')


def ini(*sections):
    return '\n'.join(textwrap.dedent(s).strip() + '\n' for s in sections)


VENDOR = '''
[vendor]
config_version = 0.0.1
'''

INDX_COMMON = '''
[filament:*C1INDX_common*]
filament_multitool_ramming = 1
filament_minimal_purge_on_wipe_tower = 10
'''

COND_HF04 = ('printer_model=~/(COREONE_INDX8T|COREONE_INDX4T)/ and '
             'nozzle_diameter[0]==0.4 and nozzle_high_flow[0]')


class Tool(unittest.TestCase):
    """Runs one generator in a scratch directory."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def run_tool(self, tool, text, *args, out='out.ini'):
        vendor = os.path.join(self.dir, 'PrusaResearch.ini')
        with open(vendor, 'w', encoding='utf-8') as f:
            f.write(text)
        self.out = os.path.join(self.dir, out)
        return subprocess.run([sys.executable, os.path.join(TOOLS, tool), vendor, self.out]
                              + list(args), cwd=self.dir, capture_output=True, text=True)

    def assertRefuses(self, result, *needles):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('refusing:', result.stderr)
        for needle in needles:
            self.assertIn(needle, result.stderr)
        self.assertFalse(os.path.exists(self.out), 'a refusal must write no output file')

    def assertBuilds(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(self.out, encoding='utf-8') as f:
            return f.read()


# --- derive_filaments.py: which section is the PA section ------------------

def hf_material(mat, family, sized, family_inherits, sized_inherits, extra=''):
    """An INDX HF0.4 material, its family, the family's 0.6 counterpart and the
    CORE One HF0.4 -> HF0.6 pair it scales against."""
    return [
        '''
        [filament:%s]
        inherits = %s
        compatible_printers_condition = %s
        ''' % (family, family_inherits, COND_HF04),
        '''
        [filament:%s]
        inherits = %s
        ''' % (sized, sized_inherits),
        '''
        [filament:%s @COREONE HF0.4]
        filament_max_volumetric_speed = 20
        ''' % mat,
        '''
        [filament:%s @COREONE HF0.6]
        filament_max_volumetric_speed = 30
        ''' % mat,
        '''
        [filament:%s @COREONEINDX HF0.4]
        inherits = %s
        filament_max_volumetric_speed = 10
        %s
        ''' % (mat, family, extra),
    ]


PA_SECTIONS = '''
[filament:*C1INDX_06_common*]
inherits = *C1INDX_common*

[filament:*C1INDX_PA_04_PA*]
start_filament_gcode = "M572 S0.05 ; Pressure advance"

[filament:*C1INDX_PA_06_PA*]
start_filament_gcode = "M572 S0.03 ; Pressure advance"

[filament:*C1INDX_FLEX_PA*]
start_filament_gcode = "M572 S0.1 ; Pressure advance"

[filament:*C1INDX_CH_PA*]
chamber_temperature = 55
chamber_minimal_temperature = 40
'''


class PressureAdvanceSource(Tool):

    def test_polyamide_chamber_section_is_not_taken_for_pa(self):
        # *C1INDX_CH_PA* comes first in the chain and its name matches PA_FLAT.
        # Taken for a PA section it would make polyamide nozzle independent and
        # keep the 0.4 PA (0.05) instead of Prusa's 0.6 figure (0.03).
        text = ini(VENDOR, INDX_COMMON, PA_SECTIONS, *hf_material(
            'Generic PA', '*PAHFC1INDX*', '*PA06HFC1INDX*',
            '*C1INDX_CH_PA*; *C1INDX_common*; *C1INDX_PA_04_PA*',
            '*C1INDX_CH_PA*; *C1INDX_06_common*; *C1INDX_PA_06_PA*'))
        out = self.assertBuilds(self.run_tool('derive_filaments.py', text, '-n', '0.6'))
        self.assertIn('M572 S0.03', out)
        self.assertIn('PA 0.05 -> 0.03 from *C1INDX_PA_06_PA*', out)
        self.assertNotIn('nozzle independent', out)

    def test_refuses_two_pa_sections(self):
        text = ini(VENDOR, INDX_COMMON, PA_SECTIONS, *hf_material(
            'Generic PA', '*PAHFC1INDX*', '*PA06HFC1INDX*',
            '*C1INDX_common*; *C1INDX_PA_04_PA*; *C1INDX_FLEX_PA*',
            '*C1INDX_06_common*; *C1INDX_PA_06_PA*'))
        self.assertRefuses(self.run_tool('derive_filaments.py', text, '-n', '0.6'),
                           'more than one INDX PA section',
                           '*C1INDX_FLEX_PA*, *C1INDX_PA_04_PA*')


# --- derive_std_filaments.py: the per-nozzle common gate --------------------

def std_material(mat='Prusament PLA', hf_family='*PLAHFC1INDX*', own=''):
    """An INDX HF0.4 material on `hf_family`, with its CORE One HF0.4 and STD
    parents."""
    return [
        '''
        [filament:%s @COREONE]
        filament_max_volumetric_speed = 15
        compatible_printers_condition = printer_model=~/(COREONE)/
        ''' % mat,
        '''
        [filament:%s @COREONE HF0.4]
        filament_max_volumetric_speed = 25
        ''' % mat,
        '''
        [filament:%s @COREONEINDX HF0.4]
        inherits = %s @COREONE HF0.4; %s
        compatible_printers_condition = %s
        filament_max_volumetric_speed = 20
        %s
        ''' % (mat, mat, hf_family, COND_HF04, own),
    ]


HF_PLA = '''
[filament:*PLAHFC1INDX*]
inherits = *C1INDX_common*
'''


def std_pla(inherits='*C1INDX_common*', body=''):
    return '''
    [filament:*PLAPGC1INDX*]
    inherits = %s
    %s
    ''' % (inherits, body)


COMMON_04 = '''
[filament:*C1INDX_04_common*]
inherits = *C1INDX_common*
%s
'''


class StdCommonGate(Tool):

    def derive(self, *sections, nozzle='0.4'):
        text = ini(VENDOR, INDX_COMMON, HF_PLA, *sections)
        return self.run_tool('derive_std_filaments.py', text, '-n', nozzle)

    def test_builds_on_the_shared_common(self):
        out = self.assertBuilds(self.derive(std_pla(), *std_material()))
        self.assertIn('[filament:Prusament PLA @COREONEINDX 0.4]', out)
        self.assertIn('filament_minimal_purge_on_wipe_tower = 10', out)
        self.assertNotIn('per-nozzle INDX common', out)

    def test_refuses_unreviewed_key_in_a_per_nozzle_common(self):
        self.assertRefuses(
            self.derive(COMMON_04 % 'filament_load_time = 12',
                        std_pla('*C1INDX_04_common*'), *std_material()),
            '*C1INDX_04_common* changes keys not in COMMON_ADOPT', 'filament_load_time')

    def test_records_a_reviewed_key_from_a_per_nozzle_common(self):
        out = self.assertBuilds(self.derive(
            COMMON_04 % 'filament_minimal_purge_on_wipe_tower = 12',
            std_pla('*C1INDX_04_common*'), *std_material()))
        self.assertIn('filament_minimal_purge_on_wipe_tower = 12', out)
        self.assertIn("# From Prusa's per-nozzle INDX common *C1INDX_04_common*", out)
        self.assertIn('filament_minimal_purge_on_wipe_tower: 10 -> 12, on 1 of 1 presets', out)
        self.assertIn('*C1INDX_04_common*: filament_minimal_purge_on_wipe_tower 10 -> 12.', out)

    def test_own_override_of_a_reviewed_key_is_kept_and_recorded(self):
        out = self.assertBuilds(self.derive(
            COMMON_04 % 'filament_minimal_purge_on_wipe_tower = 12',
            std_pla('*C1INDX_04_common*'),
            *std_material(own='filament_minimal_purge_on_wipe_tower = 15')))
        self.assertIn('filament_minimal_purge_on_wipe_tower = 15', out)
        self.assertIn('the rest keep their own value', out)
        self.assertIn('own filament_minimal_purge_on_wipe_tower 15 kept over 12', out)

    def test_refuses_toolchanger_key_set_after_the_common(self):
        # The STD base's own body overrides the common: a value nothing reviewed.
        self.assertRefuses(
            self.derive(std_pla(body='filament_minimal_purge_on_wipe_tower = 20'),
                        *std_material()),
            '*PLAPGC1INDX* sets INDX toolchanger key(s) filament_minimal_purge_on_wipe_tower '
            'in its own body')

    def test_refuses_toolchanger_key_set_by_a_later_parent(self):
        # A parent the preset lists after its STD base overrides the common in
        # PrusaSlicer's chain (the last parent wins), yet it neither reaches the
        # common nor sits in the base's own chain. Unchecked, its 99 would be
        # emitted and credited as the preset's own override.
        self.assertRefuses(
            self.derive(std_pla(), '[filament:*LATER*]\nfilament_minimal_purge_on_wipe_tower = 99\n',
                        *std_material(hf_family='*PLAHFC1INDX*; *LATER*')),
            'Prusament PLA @COREONEINDX 0.4 inherits *LATER* after its INDX STD base '
            '*PLAPGC1INDX*', 'filament_minimal_purge_on_wipe_tower')

    def test_later_parent_without_toolchanger_keys_still_builds(self):
        out = self.assertBuilds(self.derive(
            std_pla(), '[filament:*LATER*]\ntemperature = 215\n',
            *std_material(hf_family='*PLAHFC1INDX*; *LATER*')))
        self.assertIn('temperature = 215', out)
        self.assertIn('filament_minimal_purge_on_wipe_tower = 10', out)

    def test_refuses_toolchanger_key_after_the_base_inside_a_wrapper(self):
        # The base can sit one level down. *LATER* follows it inside *WRAPPER*,
        # so it still overrides the common, though the preset's own parent list
        # holds only *WRAPPER*.
        self.assertRefuses(
            self.derive(std_pla(),
                        '[filament:*WRAPPER*]\ninherits = *PLAPGC1INDX*; *LATER*\n',
                        '[filament:*LATER*]\nfilament_minimal_purge_on_wipe_tower = 99\n',
                        *std_material(hf_family='*WRAPPER*')),
            'inherits *LATER* after its INDX STD base *PLAPGC1INDX* (within *WRAPPER*)',
            'filament_minimal_purge_on_wipe_tower')

    def test_refuses_toolchanger_key_in_a_wrapper_body(self):
        # A wrapper's own body comes after its parents, so it overrides the
        # common too.
        self.assertRefuses(
            self.derive(std_pla(),
                        '[filament:*WRAPPER*]\ninherits = *PLAPGC1INDX*\n'
                        'filament_minimal_purge_on_wipe_tower = 99\n',
                        *std_material(hf_family='*WRAPPER*')),
            'through *WRAPPER*, whose own body sets INDX toolchanger key(s) '
            'filament_minimal_purge_on_wipe_tower')

    def test_wrapper_without_toolchanger_keys_still_builds(self):
        out = self.assertBuilds(self.derive(
            std_pla(), '[filament:*WRAPPER*]\ninherits = *PLAPGC1INDX*; *LATER*\ntemperature = 210\n',
            '[filament:*LATER*]\nbed_temperature = 60\n', *std_material(hf_family='*WRAPPER*')))
        self.assertIn('filament_minimal_purge_on_wipe_tower = 10', out)

    def test_a_generated_wrapper_keeps_its_own_values(self):
        # Like Fiberlogy BVOH on Verbatim BVOH: a preset whose parent is one this
        # tool built earlier inherits that preset's own overrides, as Prusa's own
        # chain does, so the wrapper-body check must not refuse it.
        out = sections(self.assertBuilds(self.derive(
            std_pla(), *std_material(own='filament_minimal_purge_on_wipe_tower = 15'),
            *std_material('Generic PLA', 'Prusament PLA @COREONEINDX HF0.4'))))
        self.assertEqual(out['filament:Generic PLA @COREONEINDX 0.4']
                         ['filament_minimal_purge_on_wipe_tower'], '15')

    def test_refuses_a_family_with_no_std_base(self):
        # A new HF family BASE_SWAP has no STD base for would otherwise be kept
        # as it is, high-flow values and all, on a standard nozzle.
        self.assertRefuses(
            self.derive(std_pla(), '[filament:*PAHFC1INDX*]\ninherits = *C1INDX_common*\n',
                        *std_material('Generic PA', '*PAHFC1INDX*')),
            'Generic PA @COREONEINDX 0.4 reaches *C1INDX_common* through nothing')

    def test_refuses_a_second_route_to_the_common(self):
        self.assertRefuses(
            self.derive(std_pla(), *std_material(
                hf_family='*PLAHFC1INDX*; *C1INDX_common*')),
            'also reaches *C1INDX_common* other than through *PLAPGC1INDX*')


# --- renamed_from never reaches a generated preset --------------------------

def print_common_06(extra=''):
    """*INDX_06hf_common* with the keys build_nozzle() needs at 0.6."""
    widths = '\n'.join('%s = 0.68' % k for k in (
        'perimeter_extrusion_width', 'external_perimeter_extrusion_width',
        'infill_extrusion_width', 'solid_infill_extrusion_width',
        'top_infill_extrusion_width'))
    return '''
[print:*INDX_06hf_common*]
compatible_printers_condition = nozzle_diameter[0]==0.6
min_bead_width = 85%%
top_solid_layers = 4
bottom_solid_layers = 3
%s
%s
''' % (widths, extra)


PRINTERS = '''
[printer:Prusa CORE One HF0.4 nozzle]
nozzle_diameter = 0.4
nozzle_high_flow = 1

[printer:Prusa CORE One HF0.6 nozzle]
nozzle_diameter = 0.6
nozzle_high_flow = 1
renamed_from = "Original Prusa CORE One HF0.6 nozzle"

[printer:Prusa CORE One 0.4 nozzle]
nozzle_diameter = 0.4
nozzle_high_flow = 0
renamed_from = "Original Prusa CORE One 0.4 nozzle"

[printer:Prusa CORE One INDX 8T HF0.4 nozzle]
printer_model = COREONE_INDX8T
nozzle_diameter = 0.4,0.4
nozzle_high_flow = 1,1
default_print_profile = 0.20mm Balanced @COREONEINDX HF0.4
default_filament_profile = "Prusament PLA @COREONEINDX HF0.4"
renamed_from = "Original Prusa CORE One INDX 8T"

; [printer:Prusa CORE One INDX 8T 0.25 nozzle]
; inherits = Prusa CORE One INDX 8T HF0.4 nozzle
; nozzle_diameter = 0.25,0.25
; nozzle_high_flow = 0,0
; renamed_from = "Prusa CORE One INDX 8T 0.25"
'''


class RenamedFrom(Tool):

    def printer(self, *args):
        result = self.run_tool('build_printer_preset.py', ini(VENDOR, PRINTERS), *args,
                               out='printer')
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def emitted(self, name):
        with open(os.path.join(self.out, name), encoding='utf-8') as f:
            return f.read()

    def test_printer_hf(self):
        self.printer('-n', '0.6')
        out = self.emitted('Prusa CORE One INDX 8T HF0.6 nozzle.ini')
        self.assertIn('nozzle_diameter = 0.6,0.6', out)
        self.assertNotIn('renamed_from', out)

    def test_printer_std(self):
        self.printer('-n', '0.4', '-n', '0.25', '--std')
        for dia in ('0.4', '0.25'):
            out = self.emitted('Prusa CORE One INDX 8T %s nozzle.ini' % dia)
            self.assertIn('nozzle_high_flow = 0,0', out)
            self.assertNotIn('renamed_from', out)

    def test_print_bundle_hf(self):
        text = ini(VENDOR, print_common_06('renamed_from = "*INDX_06_common*"'))
        out = self.assertBuilds(self.run_tool('build_print_profiles.py', text, '-n', '0.6'))
        self.assertIn('[print:0.25mm Balanced ★ @COREONEINDX HF0.6]', out)
        self.assertNotIn('renamed_from', out)


# --- build_printer_preset.py: the CORE One 0.25 delta is reported, not applied

PRINTERS_025 = '''
[printer:Prusa CORE One HF0.4 nozzle]
nozzle_diameter = 0.4
machine_max_jerk_x = 10,8
retract_length = 0.7

[printer:Prusa CORE One 0.25 nozzle]
nozzle_diameter = 0.25
machine_max_jerk_x = 8,8
retract_length = 0.8

[printer:Prusa CORE One INDX 8T HF0.4 nozzle]
printer_model = COREONE_INDX8T
nozzle_diameter = 0.4,0.4,0.4
machine_max_jerk_x = 10,8
retract_length = 0.8,0.8,0.8
default_print_profile = 0.20mm Balanced @COREONEINDX HF0.4
default_filament_profile = "Prusament PLA @COREONEINDX HF0.4"

; [printer:Prusa CORE One INDX 8T 0.25 nozzle]
; inherits = Prusa CORE One INDX 8T HF0.4 nozzle
; nozzle_diameter = 0.25,0.25,0.25
; retract_length = 0.7,0.7,0.7
'''


class CoreOne025CrossCheck(Tool):

    def build(self, text):
        result = self.run_tool('build_printer_preset.py', text, '-n', '0.25', '--std',
                               out='printer')
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(os.path.join(self.out, 'Prusa CORE One INDX 8T 0.25 nozzle.ini'),
                  encoding='utf-8') as f:
            return result.stdout, f.read()

    def test_disagreements_are_printed_and_not_applied(self):
        stdout, out = self.build(ini(VENDOR, PRINTERS_025))
        self.assertIn('CORE One HF0.4 -> 0.25 delta, reported and not applied', stdout)
        self.assertRegex(stdout, r'machine_max_jerk_x +CORE One 10,8 -> 8,8; INDX HF0.4 '
                                 r'10,8; emitted 10,8 \(not in the draft\)')
        self.assertRegex(stdout, r"retract_length +CORE One 0.7 -> 0.8; INDX HF0.4 0.8; "
                                 r"emitted 0.7 \(Prusa's draft\)")
        # nozzle_diameter agrees once the per-tool vector is read as one value.
        self.assertNotRegex(stdout, r'nozzle_diameter +CORE One')
        self.assertIn('machine_max_jerk_x = 10,8', out)
        self.assertIn('retract_length = 0.7,0.7,0.7', out)
        self.assertNotIn('CORE One HF0.4 -> 0.25', out)

    def test_no_core_one_025_printer(self):
        text = ini(VENDOR, PRINTERS_025.replace('[printer:Prusa CORE One 0.25 nozzle]',
                                                '[printer:Prusa CORE One 0.3 nozzle]'))
        stdout, _ = self.build(text)
        self.assertIn('no [printer:Prusa CORE One 0.25 nozzle] upstream; nothing to '
                      'cross-check', stdout)


# --- build_print_profiles.py: the header records every change and its reason

HF04_PRINT = '''
[print:0.20mm Balanced @COREONEINDX HF0.4]
compatible_printers_condition = printer_model=~/(COREONE_INDX8T)/ and nozzle_diameter[0]==0.4 and nozzle_high_flow[0]
layer_height = 0.2
'''


class PrintBundleReasons(Tool):

    def header(self, text, *args):
        out = self.assertBuilds(self.run_tool('build_print_profiles.py', text, *args))
        return [l for l in out.splitlines() if l.startswith('#')]

    def test_common_and_tier_edits_carry_their_reasons(self):
        lines = self.header(ini(VENDOR, print_common_06('bridge_speed = 50\nnotes = ')),
                            '-n', '0.6')
        for line in ('#   bridge_speed: 50 -> 30',
                     '#       inherited 50 is ~14 mm3/s at a 0.6 bridge',
                     '#   interlocking_beam_width: unset -> 1.2',
                     '#   compatible_printers: unset -> (empty)',
                     '#   0.20mm Detail @COREONEINDX HF0.6: top_solid_layers: 4 -> 5',
                     '#   0.32mm Draft @COREONEINDX HF0.6: min_bead_width: 85% -> 90%'):
            self.assertIn(line, lines)
        # notes is already empty upstream, so COMMON_EDITS changes nothing there.
        self.assertFalse([l for l in lines if l.startswith('#   notes')])
        self.assertTrue([l for l in lines if l.startswith('# Speeds: ')])

    def test_std_edits_carry_their_reasons(self):
        lines = self.header(ini(VENDOR, print_common_06(), HF04_PRINT),
                            '-n', '0.6', '--std', '0.4')
        start = lines.index("# Changed from Prusa's prints, in every profile (STD_EDITS):")
        self.assertEqual(lines[start + 1:start + 5], [
            '#   print_settings_id: unset -> (empty)', '#       system preset hygiene',
            '#   compatible_printers: unset -> (empty)', '#       condition-based binding only'])


# --- nozzles.py SCALED SIZES: 1.0, which Prusa publishes nothing for ---------

sys.path.insert(0, TOOLS)
from decimal import Decimal  # noqa: E402
from nozzles import NOZZLES, scale  # noqa: E402

WIDTH_KEYS = ('extrusion_width', 'perimeter_extrusion_width',
              'external_perimeter_extrusion_width', 'infill_extrusion_width',
              'solid_infill_extrusion_width', 'top_infill_extrusion_width',
              'first_layer_extrusion_width', 'support_material_extrusion_width')


def print_common_08(width='0.9', cond='nozzle_diameter[0]==0.8',
                    fname='{input_filename_base}_0.8n_{layer_height}mm.gcode'):
    """*INDX_08hf_common* with absolute widths, both size labels, and two keys
    the rule must leave alone."""
    return '\n'.join(['[print:*INDX_08hf_common*]',
                      'compatible_printers_condition = ' + cond,
                      'output_filename_format = ' + fname,
                      'top_solid_layers = 4',
                      'fill_density = 15%']
                     + ['%s = %s' % (k, width) for k in WIDTH_KEYS]) + '\n'


PRINTERS_08 = '\n'.join([
    '[printer:Prusa CORE One HF0.4 nozzle]', 'nozzle_diameter = 0.4',
    'max_layer_height = 0.3', 'min_layer_height = 0.07', 'printer_variant = HF0.4', '',
    '[printer:Prusa CORE One HF0.8 nozzle]', 'nozzle_diameter = 0.8',
    'max_layer_height = 0.6', 'min_layer_height = 0.2', 'printer_variant = HF0.8', '',
    '[printer:Prusa CORE One INDX 8T HF0.4 nozzle]', 'printer_model = COREONE_INDX8T',
    'nozzle_diameter = 0.4,0.4', 'max_layer_height = 0.3,0.3',
    'min_layer_height = 0.07,0.07', 'printer_variant = HF0.4', 'retract_length = 0.8,0.8',
    'default_print_profile = 0.20mm Balanced ★ @COREONEINDX HF0.4',
    'default_filament_profile = "Prusament PLA @COREONEINDX HF0.4"']) + '\n'

FILAMENTS_08 = '\n'.join([
    '[filament:*C1INDX_PLA_04_PA*]',
    'start_filament_gcode = "M572 S0.031 ; Pressure advance\\nM573 R"', '',
    '[filament:*C1INDX_PLA_08_PA*]',
    'start_filament_gcode = "M572 S0.013 ; Pressure advance"', '',
    '[filament:*PLAHFC1INDX*]', 'inherits = *C1INDX_common*; *C1INDX_PLA_04_PA*',
    'compatible_printers_condition = ' + COND_HF04, '',
    '[filament:*PLA08HFC1INDX*]', 'inherits = *C1INDX_common*; *C1INDX_PLA_08_PA*', '',
    '[filament:Prusament PLA @COREONE HF0.4]', 'filament_max_volumetric_speed = 24', '',
    '[filament:Prusament PLA @COREONE HF0.8]', 'filament_max_volumetric_speed = 36', '',
    '[filament:Prusament PLA @COREONEINDX HF0.4]', 'inherits = *PLAHFC1INDX*',
    'filament_max_volumetric_speed = 28']) + '\n'


def sections(text):
    """{section: {key: value}} of an emitted .ini, for whole-preset comparison."""
    out, cur = {}, None
    for line in text.splitlines():
        if line.startswith('['):
            cur = out.setdefault(line.strip('[]'), {})
        elif cur is not None and ' = ' in line:
            k, v = line.split(' = ', 1)
            cur[k] = v
    return out


class ScaledSize(Tool):

    def test_rule_rounds_half_up_as_prusa_does(self):
        # Prusa writes 1.125 x 0.6 = 0.675 as 0.68 in *INDX_06hf_common*.
        self.assertEqual(scale('0.6', Decimal('1.125')), '0.68')
        self.assertEqual(scale('0.9', Decimal('1.25')), '1.13')
        self.assertEqual(scale('0.8', Decimal('1.25')), '1')
        self.assertEqual(scale('0.55', Decimal('1.25')), '0.69')

    def test_10_is_08_with_its_ladder_scaled_and_all_else_held(self):
        n, src = NOZZLES['1.0'], NOZZLES['0.8']
        self.assertEqual((n.scaled_from, n.common), ('0.8', src.common))
        self.assertEqual(n.layers, (0.38, 0.5, 0.69))
        self.assertIs(n.flow, src.flow)
        self.assertFalse(n.validated)

    def test_print_bundle_scales_widths_moves_labels_holds_the_rest(self):
        out = self.assertBuilds(self.run_tool(
            'build_print_profiles.py', ini(VENDOR, print_common_08()), '-n', '1.0'))
        common = sections(out)['print:*COREONEINDX HF1.0*']
        for k in WIDTH_KEYS:
            self.assertEqual(common[k], '1.13', k)
        self.assertEqual(common['compatible_printers_condition'], 'nozzle_diameter[0]==1.0')
        self.assertIn('_1.0n_', common['output_filename_format'])
        self.assertNotIn('0.8n', common['output_filename_format'])
        self.assertEqual(common['top_solid_layers'], '4')   # held
        self.assertEqual(common['fill_density'], '15%')     # held
        for name in ('0.38mm Detail', '0.50mm Balanced ★', '0.69mm Draft'):
            self.assertIn('[print:%s @COREONEINDX HF1.0]' % name, out)
        self.assertIn('SCALED from Prusa *INDX_08hf_common* (0.8 mm)', out)
        self.assertIn('#   perimeter_extrusion_width: 0.9 -> 1.13', out)

    def test_refuses_a_percentage_width(self):
        self.assertRefuses(self.run_tool(
            'build_print_profiles.py', ini(VENDOR, print_common_08(width='112.5%')),
            '-n', '1.0'), 'is not an absolute width')

    def test_refuses_a_size_label_it_cannot_find_once(self):
        self.assertRefuses(self.run_tool(
            'build_print_profiles.py',
            ini(VENDOR, print_common_08(cond='printer_model=~/COREONE_INDX8T/')),
            '-n', '1.0'), 'names 0.8 mm 0 times')

    def test_printer_is_08_with_six_keys_moved(self):
        r08 = self.run_tool('build_printer_preset.py', ini(VENDOR, PRINTERS_08), '-n', '0.8',
                            out='printer')
        r10 = self.run_tool('build_printer_preset.py', ini(VENDOR, PRINTERS_08), '-n', '1.0',
                            out='printer')
        self.assertEqual((r08.returncode, r10.returncode), (0, 0), r08.stderr + r10.stderr)

        def read(name):
            with open(os.path.join(self.out, name), encoding='utf-8') as f:
                return sections('[p]\n' + f.read())['p']
        p08 = read('Prusa CORE One INDX 8T HF0.8 nozzle.ini')
        p10 = read('Prusa CORE One INDX 8T HF1.0 nozzle.ini')
        moved = {k for k in set(p08) | set(p10) if p08.get(k) != p10.get(k)}
        self.assertEqual(moved, {'nozzle_diameter', 'printer_variant', 'max_layer_height',
                                 'min_layer_height', 'default_print_profile',
                                 'default_filament_profile'})
        self.assertEqual(p10['max_layer_height'], '0.75,0.75')
        self.assertEqual(p10['min_layer_height'], '0.25,0.25')
        self.assertEqual(p10['default_print_profile'],
                         '0.50mm Balanced ★ @COREONEINDX HF1.0')
        self.assertEqual(p10['retract_length'], p08['retract_length'])   # held

    def test_filaments_are_08_rebound(self):
        text = ini(VENDOR, INDX_COMMON, FILAMENTS_08)
        f08 = sections(self.assertBuilds(self.run_tool('derive_filaments.py', text, '-n', '0.8')))
        f10 = sections(self.assertBuilds(self.run_tool('derive_filaments.py', text, '-n', '1.0')))
        a = f08['filament:Prusament PLA @COREONEINDX HF0.8']
        b = f10['filament:Prusament PLA @COREONEINDX HF1.0']
        self.assertEqual({k for k in set(a) | set(b) if a.get(k) != b.get(k)},
                         {'compatible_printers_condition', 'filament_notes'})
        self.assertIn('nozzle_diameter[0]==1.0', b['compatible_printers_condition'])
        self.assertEqual(b['filament_max_volumetric_speed'], '42')   # 28 x 36/24, held
        self.assertIn('M572 S0.013', b['start_filament_gcode'])       # Prusa's 0.8 PA, held
        self.assertTrue(b['filament_notes'].startswith('"INDX 1.0 seed, held at HF0.8'))

    # A PrusaResearch.ini that publishes anything at 1.0 must stop all three
    # generators: the scaled values would otherwise ignore Prusa's own 1.0 data
    # while every file still claimed Prusa publishes nothing at 1.0.
    UNSOURCED_BREAKERS = {
        'a 1.0 INDX common': '[print:*INDX_10hf_common*]\nperimeters = 2\n',
        'a 1.0 PA section': '[filament:*C1INDX_PLA_10_PA*]\nstart_filament_gcode = "M572 S0.01"\n',
        'a commented HF1.0 printer draft':
            '; [printer:Prusa CORE One INDX 8T HF1.0 nozzle]\n; retract_length = 0.5\n',
        # Prusa's sized family sections, which it adds before (or without) any
        # concrete profile: *PLA06HFC1INDX*, *FLEX06PGC1INDX* and so on at 0.6.
        'a 1.0 high-flow family': '[filament:*PLA10HFC1INDX*]\nfilament_wipe = 1\n',
        'a 1.0 standard family': '[filament:*FLEX10PGC1INDX*]\nfilament_wipe = 1\n',
        'a 1.0 INDX filament common': '[filament:*C1INDX_10_common*]\nfilament_wipe = 1\n',
        'a CORE One 1.0 printer common': '[printer:*C1_10*]\nmax_layer_height = 0.75\n',
    }

    def test_every_generator_refuses_once_prusa_publishes_10(self):
        cases = [('build_print_profiles.py', ini(VENDOR, print_common_08()), 'out.ini'),
                 ('build_printer_preset.py', ini(VENDOR, PRINTERS_08), 'printer'),
                 ('derive_filaments.py', ini(VENDOR, INDX_COMMON, FILAMENTS_08), 'out.ini')]
        for what, extra in self.UNSOURCED_BREAKERS.items():
            for tool, text, out in cases:
                with self.subTest(tool=tool, source=what):
                    r = self.run_tool(tool, text + '\n' + extra, '-n', '1.0', out=out)
                    self.assertNotEqual(r.returncode, 0, r.stdout)
                    self.assertIn('Prusa publishes', r.stderr)
                    self.assertIn('nothing at 1.0 mm, but this PrusaResearch.ini does', r.stderr)
                    written = (os.listdir(self.out) if os.path.isdir(self.out)
                               else [self.out] if os.path.exists(self.out) else [])
                    self.assertEqual(written, [], 'a refusal must write no output')


if __name__ == '__main__':
    unittest.main()


# --- mixed tool layouts: nozzles.py LAYOUTS ---------------------------------

PRINT_025 = '''
[print:*INDX_025_common*]
compatible_printers_condition = printer_model=~/(COREONE_INDX8T|COREONE_INDX4T)/ and nozzle_diameter[0]==0.25
output_filename_format = {input_filename_base}_0.25n_{layer_height}mm.gcode
extrusion_width = 0.27
perimeter_extrusion_width = 0.25
external_perimeter_extrusion_width = 0.25
infill_extrusion_width = 0.27
solid_infill_extrusion_width = 0.27
top_infill_extrusion_width = 0.25
support_material_extrusion_width = 0.25
perimeter_speed = 150
infill_speed = 100
solid_infill_speed = 140
support_material_speed = 70
layer_height = 0.1
infill_every_layers = 1
support_material = 1
support_material_style = snug
support_material_extruder = 0
support_material_interface_extruder = 0
perimeter_extruder = 1
infill_extruder = 1
solid_infill_extruder = 1
top_solid_layers = 11
bottom_solid_layers = 8

[print:0.07mm Extra Fine @COREONEINDX 0.25]
inherits = *INDX_025_common*
layer_height = 0.07
top_solid_layers = 11
bottom_solid_layers = 9

[print:0.10mm Fine ★ @COREONEINDX 0.25]
inherits = *INDX_025_common*
layer_height = 0.1
top_solid_layers = 9
bottom_solid_layers = 7

[print:0.15mm Detail @COREONEINDX 0.25]
inherits = *INDX_025_common*
layer_height = 0.15
top_solid_layers = 6
bottom_solid_layers = 5
'''

ANCHOR_HF04 = '''
[print:0.20mm Balanced ★ @COREONEINDX HF0.4]
compatible_printers_condition = %s
layer_height = 0.2
infill_extrusion_width = 0.45
infill_speed = 300
''' % COND_HF04


def indx_8t(extra='', tools=8, semm='0', check=True):
    """A shipping INDX base with `tools` tools, and Prusa's per-tool nozzle
    check in its start G-code."""
    vec = lambda v: ','.join([v] * tools)
    gcode = '\\n'.join(
        '{if (is_extruder_used[%d])}M862.1 T%d P{nozzle_diameter[%d]} '
        'F{(nozzle_high_flow[%d] ? 1 : 0)}{endif}' % (n, n, n, n)
        for n in range(tools)) if check else 'M862.1 P{nozzle_diameter[0]}'
    return '''
    [printer:Prusa CORE One INDX 8T HF0.4 nozzle]
    printer_model = COREONE_INDX8T
    single_extruder_multi_material = %s
    nozzle_diameter = %s
    nozzle_high_flow = %s
    min_layer_height = %s
    max_layer_height = %s
    retract_length = %s
    machine_max_jerk_x = 10,8
    start_gcode = %s
    default_print_profile = 0.20mm Balanced ★ @COREONEINDX HF0.4
    default_filament_profile = "Prusament PLA @COREONEINDX HF0.4"
    %s
    ''' % (semm, vec('0.4'), vec('1'), vec('0.07'), vec('0.3'), vec('0.8'),
           gcode, extra)


DRAFT_025 = '''
; [printer:Prusa CORE One INDX 8T 0.25 nozzle]
; inherits = Prusa CORE One INDX 8T HF0.4 nozzle
; nozzle_diameter = 0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25
; nozzle_high_flow = 0,0,0,0,0,0,0,0
; min_layer_height = 0.05,0.05,0.05,0.05,0.05,0.05,0.05,0.05
; max_layer_height = 0.15,0.15,0.15,0.15,0.15,0.15,0.15,0.15
; retract_length = 0.7,0.7,0.7,0.7,0.7,0.7,0.7,0.7
'''


class LayoutPrintProfiles(Tool):
    """build_print_profiles.py --layout"""

    def build(self, *sections):
        return self.assertBuilds(self.run_tool(
            'build_print_profiles.py', ini(*sections), '--layout', '0.25+HF0.4'))

    def test_prusa_tiers_are_renamed_rebound_and_split(self):
        out = self.build(VENDOR, PRINT_025, ANCHOR_HF04)
        # Prusa's own three layer heights, this repo's tier labels: sharing an
        # alias with Prusa's own 0.25 profiles would hide these behind them.
        for name in ('0.07mm Detail @COREONEINDX 0.25+HF0.4',
                     '0.10mm Balanced ★ @COREONEINDX 0.25+HF0.4',
                     '0.15mm Draft @COREONEINDX 0.25+HF0.4'):
            self.assertIn('[print:%s]' % name, out)
        self.assertNotIn('Extra Fine @COREONEINDX 0.25+HF0.4', out)
        # Binds on both pinned tools, by index, and on the high-flow flag of each.
        self.assertIn('compatible_printers_condition = printer_model=~/'
                      '(COREONE_INDX8T|COREONE_INDX4T)/ and nozzle_diameter[0]==0.25 '
                      'and ! nozzle_high_flow[0] and nozzle_diameter[1]==0.4 and '
                      'nozzle_high_flow[1]', out)
        self.assertIn('output_filename_format = {input_filename_base}_0.25+HF0.4n_', out)
        # Roles pinned; supports organic, which is what lets a pinned support
        # extruder coexist with the wipe tower.
        self.assertIn('infill_extruder = 2', out)
        self.assertIn('perimeter_extruder = 1', out)
        self.assertIn('solid_infill_extruder = 1', out)
        self.assertIn('support_material_extruder = 1', out)
        self.assertIn('support_material_interface_extruder = 1', out)
        self.assertIn('support_material_style = organic', out)
        # The moved role takes tool 2's own width; nothing else moves.
        self.assertIn('infill_extrusion_width = 0.45', out)
        self.assertIn('solid_infill_extrusion_width = 0.27', out)
        self.assertIn('perimeter_extrusion_width = 0.25', out)
        self.assertIn('perimeter_speed = 150', out)
        # Prusa's per-tier solid-layer counts survive the split.
        self.assertRegex(out, r'top_solid_layers = 11')
        self.assertRegex(out, r'bottom_solid_layers = 5')

    def test_infill_is_combined_and_the_speed_solved_to_prusa_s_rate(self):
        out = self.build(VENDOR, PRINT_025, ANCHOR_HF04)
        tiers = dict(sections(out))
        # 0.25 mm of combined height is all PrusaSlicer allows here: solid infill
        # is on the 0.25 tool, and the cap is the smaller of the two nozzles.
        self.assertEqual(tiers['print:0.07mm Detail @COREONEINDX 0.25+HF0.4']
                         ['infill_every_layers'], '3')
        self.assertEqual(tiers['print:0.10mm Balanced ★ @COREONEINDX 0.25+HF0.4']
                         ['infill_every_layers'], '2')
        self.assertEqual(tiers['print:0.15mm Draft @COREONEINDX 0.25+HF0.4']
                         ['infill_every_layers'], '1')
        # Prusa's own HF0.4 infill rate is 0.45 x 0.2 at 300 mm/s = 24.4 mm3/s.
        # Solved at 0.45 x (n x layer), and never past Prusa's own 300 mm/s.
        self.assertEqual(tiers['print:0.07mm Detail @COREONEINDX 0.25+HF0.4']
                         ['infill_speed'], '285')
        self.assertEqual(tiers['print:0.10mm Balanced ★ @COREONEINDX 0.25+HF0.4']
                         ['infill_speed'], '300')
        self.assertEqual(tiers['print:0.15mm Draft @COREONEINDX 0.25+HF0.4']
                         ['infill_speed'], '300')

    def test_every_change_carries_a_reason(self):
        out = self.build(VENDOR, PRINT_025, ANCHOR_HF04)
        header = out[:out.index('[print:*COREONEINDX')]
        for needle in ('Preset.cpp:1388-1401',      # why the tiers are renamed
                       'Print.cpp:685-692',          # why supports are organic
                       'PrintObject.cpp:3126-3132',  # why infill combines this far
                       'PlaceholderParser.cpp:1074'):  # why a tool-2 clause is safe
            self.assertIn(needle, header)

    def test_refuses_a_tier_count_mismatch(self):
        text = ini(VENDOR, PRINT_025, ANCHOR_HF04,
                   '''
                   [print:0.20mm Rough @COREONEINDX 0.25]
                   inherits = *INDX_025_common*
                   layer_height = 0.2
                   ''')
        self.assertRefuses(
            self.run_tool('build_print_profiles.py', text, '--layout', '0.25+HF0.4'),
            'Prusa ships 4 "@COREONEINDX 0.25" print profiles',
            'human decision')

    def test_refuses_without_the_moved_role_s_anchor(self):
        self.assertRefuses(
            self.run_tool('build_print_profiles.py', ini(VENDOR, PRINT_025),
                          '--layout', '0.25+HF0.4'),
            'ROLE_ANCHOR names [print:0.20mm Balanced ★ @COREONEINDX HF0.4]')

    def test_refuses_an_unsolvable_anchor_width(self):
        text = ini(VENDOR, PRINT_025,
                   ANCHOR_HF04.replace('infill_extrusion_width = 0.45',
                                       'infill_extrusion_width = 112%'))
        self.assertRefuses(
            self.run_tool('build_print_profiles.py', text, '--layout', '0.25+HF0.4'),
            'not an absolute value')


class LayoutPrinterPreset(Tool):
    """build_printer_preset.py --layout"""

    NAME = 'Prusa CORE One INDX 8T 0.25+HF0.4 nozzles.ini'

    def run_layout(self, *sections):
        return self.run_tool('build_printer_preset.py', ini(*sections),
                             '--layout', '0.25+HF0.4', out='printer')

    def build(self, *sections):
        result = self.run_layout(*sections)
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(os.path.join(self.out, self.NAME), encoding='utf-8') as f:
            return f.read()

    def assertLayoutRefuses(self, result, *needles):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('refusing:', result.stderr)
        for needle in needles:
            self.assertIn(needle, result.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.out, self.NAME)),
                         'a refusal must write no preset')

    def base(self, **kw):
        return ini(VENDOR, PRINT_025, ANCHOR_HF04, PRINTERS_025, indx_8t(**kw),
                   DRAFT_025)

    def test_per_extruder_keys_are_composed_tool_by_tool(self):
        out = self.build(VENDOR, PRINT_025, ANCHOR_HF04, PRINTERS_025,
                         indx_8t(), DRAFT_025)
        self.assertIn('nozzle_diameter = 0.25,0.4,0.4,0.4,0.4,0.4,0.4,0.4', out)
        self.assertIn('nozzle_high_flow = 0,1,1,1,1,1,1,1', out)
        self.assertIn('min_layer_height = 0.05,0.07,0.07,0.07,0.07,0.07,0.07,0.07', out)
        self.assertIn('max_layer_height = 0.15,0.3,0.3,0.3,0.3,0.3,0.3,0.3', out)
        self.assertIn('retract_length = 0.7,0.8,0.8,0.8,0.8,0.8,0.8,0.8', out)
        # Printer-wide decisions, including a pointer at the layout's own Balanced
        # profile rather than at one nozzle's.
        self.assertIn('printer_variant = 0.25+HF0.4', out)
        self.assertIn('default_print_profile = 0.10mm Balanced ★ @COREONEINDX '
                      '0.25+HF0.4', out)
        self.assertIn('default_filament_profile = "Prusament PLA @COREONEINDX 0.25"',
                      out)
        self.assertIn('inherits = Prusa CORE One INDX 8T HF0.4 nozzle', out)
        self.assertNotIn('renamed_from', out)
        self.assertIn('UNVALIDATED: this layout has not been test printed.', out)

    def test_refuses_a_printer_wide_disagreement(self):
        # A draft key that is not per-extruder: the two nozzles would be claiming
        # different machine limits.
        self.assertLayoutRefuses(
            self.run_layout(VENDOR, PRINT_025, ANCHOR_HF04, PRINTERS_025, indx_8t(),
                            DRAFT_025 + '; machine_max_jerk_x = 9,9\n'),
            'disagree on keys a layout may not vary',
            'machine_max_jerk_x', 'MIXED_SCALAR')

    def test_refuses_single_extruder_multi_material(self):
        self.assertLayoutRefuses(
            self.run_layout(VENDOR, PRINT_025, ANCHOR_HF04, PRINTERS_025,
                            indx_8t(semm='1'), DRAFT_025),
            'single_extruder_multi_material = 1', 'Preset.cpp:2405')

    def test_refuses_without_a_per_tool_firmware_nozzle_check(self):
        self.assertLayoutRefuses(
            self.run_layout(VENDOR, PRINT_025, ANCHOR_HF04, PRINTERS_025,
                            indx_8t(check=False), DRAFT_025),
            'does not check tool 1, 2, 3, 4, 5, 6, 7, 8 with its own',
            'must\n          not be written')

    def test_refuses_a_tool_count_mismatch(self):
        self.assertLayoutRefuses(
            self.run_layout(VENDOR, PRINT_025, ANCHOR_HF04, PRINTERS_025,
                            indx_8t(tools=4), DRAFT_025),
            'has 4 tools but layout 0.25+HF0.4 names 8')


class LayoutTableGuards(unittest.TestCase):
    """nozzles.py LAYOUTS entries, checked in process: these guard the table
    itself, so no PrusaResearch.ini can reach them."""

    def setUp(self):
        sys.path.insert(0, TOOLS)
        self.addCleanup(lambda: sys.path.remove(TOOLS))
        import nozzles
        import build_print_profiles
        self.nozzles, self.build = nozzles, build_print_profiles

    def test_every_role_must_be_pinned(self):
        layout = self.nozzles.LAYOUTS['0.25+HF0.4']
        saved = dict(layout.roles)
        self.addCleanup(lambda: layout.roles.update(saved))
        del layout.roles['support_material_extruder']
        with self.assertRaises(SystemExit) as caught:
            self.build.build_layout({}, layout, [], [])
        self.assertIn('leaves support_material_extruder unpinned', str(caught.exception))

    def test_an_unknown_role_is_refused(self):
        layout = self.nozzles.LAYOUTS['0.25+HF0.4']
        self.addCleanup(lambda: layout.roles.pop('brim_extruder', None))
        layout.roles['brim_extruder'] = 1
        with self.assertRaises(SystemExit) as caught:
            self.build.build_layout({}, layout, [], [])
        self.assertIn('not a role in ROLE_KEYS', str(caught.exception))

    def test_a_role_on_a_tool_the_layout_does_not_have(self):
        layout = self.nozzles.LAYOUTS['0.25+HF0.4']
        with self.assertRaises(SystemExit) as caught:
            layout.tool_tag(len(layout.tools) + 1)
        self.assertIn('to pin a role to', str(caught.exception))

    def test_combining_is_capped_by_the_smaller_nozzle(self):
        # Solid infill on the 0.25 tool caps combining at 0.25 mm, not 0.4.
        layout = self.nozzles.LAYOUTS['0.25+HF0.4']
        self.assertAlmostEqual(self.build.combine_cap(layout), 0.25)
        self.assertEqual([self.nozzles.combine_layers(0.25, h)
                          for h in (0.07, 0.1, 0.15)], [3, 2, 1])
