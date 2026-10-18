"""
Synthetic-INI tests for the generators' refusals and guards.

Each test writes a tiny PrusaResearch.ini-shaped file, runs a generator on it the
way the README recipe does, and checks what it emitted, or that it refused and
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


if __name__ == '__main__':
    unittest.main()
