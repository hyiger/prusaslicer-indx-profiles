"""
Per-nozzle configuration for the Prusa CORE One INDX profile generators.

Everything here is either lifted from PrusaResearch.ini or explicitly flagged as
unvalidated. Adding a nozzle size means adding one entry below.

One size, 1.0, has no Prusa source at all, and is built by the scaling rule
below (see SCALED SIZES) rather than read out of PrusaResearch.ini.

Layer-height ladders are Prusa's own CORE One ladders for the same nozzle,
read out of the shipping print profiles. Where Prusa ships both a standard and
a high-flow variant at one diameter the basis is chosen per size, not by one
rule. The 0.6 row is @COREONE HF0.6, the variant matching the nozzle; TIERS uses
its first three rungs. The 0.5 row is @COREONE 0.5 rather than HF0.5, whose
ladder has nothing below 0.20; TIERS uses 0.15/0.20/0.25, which are also exactly
the first three rungs of Prusa's own commented @COREONEINDX HF0.5 print draft
lineup, an INDX-specific source. At 0.8 the standard and high-flow ladders are
identical. The 0.4 row is the INDX lineup itself:

    0.25    0.05  0.07  0.12  0.15
    0.3     0.12  0.16  0.20
    0.4     0.10  0.15  0.20  0.25      (the INDX lineup itself)
    0.5     0.10  0.15  0.20  0.25
    0.6     0.20  0.25  0.32  0.40
    0.8     0.30  0.40  0.55

Flow targets are only needed where Prusa has NOT done a speed pass on the
size-specific common. Where `flow` is None the generator leaves the upstream
speeds alone; where it is set, the six main speeds are solved backward from it.
"""

from decimal import Decimal, ROUND_HALF_UP


# PrusaSlicer Flow::mm3_per_mm for a non-bridge extrusion.
def area(w, h):
    return w * h - h * h * (1.0 - 3.141592653589793 / 4.0)


def speed_for(q, w, h, round_to=5):
    return int(round(q / area(w, h) / round_to) * round_to)


# --- SCALED SIZES ------------------------------------------------------------
# The rule the repo owner approved on 2026-10-21 for HF1.0, scaled from 0.8 by
# 1.0/0.8 - the one exception to "never invent a slicer value" (CLAUDE.md,
# non-negotiable 1). It exists because Prusa publishes nothing at 1.0: no INDX
# common, print, printer or filament profile, draft or pressure advance, which
# build_print_profiles.assert_unsourced() re-checks on every build. The code is
# general, but the approval is not: another size needs its own approval.
#
# The size is built from the sourced size, scaled by the diameter ratio,
# and only where the value is a length proportional to the nozzle: a line width,
# a layer height, a layer-height limit. Each is rounded half-up to 0.01, which is
# Prusa's own rounding (1.125 x 0.6 = 0.675 is written 0.68 in
# *INDX_06hf_common*). A value that merely names the size - a binding, a file
# name, a variant tag - is moved to the new size, not scaled.
#
# Every other value is HELD at the source size, as this repo builds that size:
# its flow targets, and each filament's max volumetric speed and pressure
# advance from derive_filaments.py at 0.8 (Prusament PLA: MVS 42, the INDX 0.4
# value 28 scaled by Prusa's CORE One HF0.4 -> HF0.8 pair, 24 -> 36; PA 0.013 from
# *C1INDX_PLA_08_PA*). The per-size COMMON_EDITS still apply, so
# interlocking_beam_width is 2 x nozzle (2 at 1.0). Speeds are solved from the
# held flow targets at the new geometry; rounding each to 5 mm/s leaves a
# feature within about -6% to +12% of 0.8's rate, and the held filament MVS
# caps both sizes alike. The held pressure advance is 0.8's only because Prusa
# publishes none at 1.0; its falling 0.4 -> 0.6 -> 0.8 trend suggests 1.0 wants
# less, so the held figure likely over-retracts and must be re-measured. The
# 0.8 settings are themselves unprinted, so a scaled size is always
# validated=False.
SCALE_STEP = Decimal('0.01')


def scale(value, ratio):
    """A length scaled by `ratio`, rounded half-up to 0.01, written as
    PrusaSlicer writes it ('1.13', '1', '0.5')."""
    v = (Decimal(str(value)) * ratio).quantize(SCALE_STEP, rounding=ROUND_HALF_UP)
    return format(v.normalize(), 'f')


def is_width(key):
    """A line-width key: the lengths the rule scales in a print common."""
    return key == 'extrusion_width' or key.endswith('_extrusion_width')


# Print-profile values that name the nozzle size rather than tune for it. A
# scaled size takes its own label in place of the source size's; holding the
# source's would label 1.0 output as 0.8 (G-code named "_0.8n_", profiles bound
# to a 0.8 nozzle). Each pattern must occur exactly once, or the build refuses.
SIZE_LABELS = {
    'compatible_printers_condition': ('nozzle_diameter[0]==%s',
                                      'binds the profiles to the nozzle size'),
    'output_filename_format': ('_%sn_', 'names the nozzle size in the G-code file'),
}


class Nozzle:
    def __init__(self, dia, common, layers, flow=None, validated=False,
                 extra=None, note='', shipped=None, scaled_from=None):
        self.dia = dia              # nozzle diameter, e.g. '0.6'
        self.common = common        # upstream section, e.g. '*INDX_06hf_common*'
        self.layers = layers        # (detail, balanced, draft) layer heights
        self.flow = flow            # dict of volumetric targets, or None
        self.validated = validated  # have these targets actually been printed?
        # Per-tier key overrides, {tier: {key: (value, reason)}}. The same
        # (value, reason) shape as COMMON_EDITS: every deviation from the
        # resolved common records why, the per-tier ones included.
        self.extra = extra or {}
        self.note = note
        self.shipped = shipped      # Prusa's own print profiles for this size, if any
        # For HF1.0 only (see SCALED SIZES): the sourced size it is scaled from.
        # None for every size read out of PrusaResearch.ini.
        self.scaled_from = scaled_from

    @property
    def ratio(self):
        """New size over source size, exact: Decimal('1.0') / Decimal('0.8') = 1.25."""
        return Decimal(self.dia) / Decimal(self.scaled_from)

    @property
    def tag(self):
        """Preset-name suffix for the high-flow sizes built here, e.g. 'HF0.6'.
        Standard (non-HF) nozzles are handled separately: see --std."""
        return 'HF' + self.dia

    @property
    def hidden_common(self):
        return '*COREONEINDX %s*' % self.tag


# Volumetric targets validated on 0.6 CHT toolheads. Prusa's starred
# "0.20mm Balanced @COREONEINDX HF0.4" runs 20.4 mm3/s perimeter / 24.4 infill;
# these aim modestly above that one tier. Across its four tiers the shipping 0.4
# lineup spans 8.6-33.5 mm3/s, the upper tiers riding the un-passed 250/300 from
# *INDX_common*, so these are not above the whole shipping range.
FLOW_06 = dict(perim=26.0, ext=20.0, small=18.0,
               infill=30.0, solid=27.0, top=11.3)


def _scaled(factor):
    """FLOW_06 scaled by one factor. Uniform, not per-key: `top` moves with the
    rest even where the 0.4 and 0.6 anchors agree on it."""
    return {k: round(v * factor, 1) for k, v in FLOW_06.items()}


NOZZLES = {
    # Prusa did a full speed pass on *INDX_025_common* (perimeter 150, infill
    # 100, perimeters 3, 11/8 solid layers) and, since PrusaResearch 2.5.x,
    # ships its own "@COREONEINDX 0.25" print profiles built on it. Building
    # them here would only duplicate Prusa's, so the generator refuses.
    '0.25': Nozzle('0.25', '*INDX_025_common*', (0.07, 0.12, 0.15),
                   flow=None, validated=False,  # Prusa's pass is sourced, not printed here
                   note='upstream speed pass present; speeds left untouched',
                   shipped='0.07mm Extra Fine / 0.10mm Fine ★ / 0.15mm Detail @COREONEINDX 0.25'),

    # Prusa ships "@COREONEINDX 0.3" print profiles since PrusaResearch 2.5.x.
    # Before that there was no upstream speed pass, and linear extrapolation
    # from the 0.4/0.6 anchors collapses below 0.4, so none was derived here.
    '0.3': Nozzle('0.3', '*INDX_03_common*', (0.12, 0.16, 0.20),
                  flow=None, validated=False,
                  note='no INDX 0.3 nozzle exists; Prusa\'s 0.3 common and prints '
                       'are scaffolding',
                  shipped='0.10mm Fine / 0.15mm Detail ★ / 0.20mm Balanced @COREONEINDX 0.3'),

    # Prusa renamed the high-flow commons *INDX_05_common* -> *INDX_05hf_common*
    # (likewise 0.6 and 0.8) by PrusaResearch 2.5.11.

    # No upstream speed pass, and Prusa's commented HF0.5 print drafts restate
    # the 250/200 they inherit (their other keys are per-layer). FLOW_06 is scaled by one
    # factor, the perimeter target interpolated between the 0.4 anchor (20.4
    # perim / 24.4 infill, measured off Prusa's 0.20mm Balanced profile) and the
    # 0.6 target. Being uniform, that leaves `top` at 10.0 although both anchors
    # say 11.3 - low, so safe, but not an interpolation of that key.
    '0.5': Nozzle('0.5', '*INDX_05hf_common*', (0.15, 0.20, 0.25),
                  flow=_scaled(23.0 / 26.0), validated=False,
                  note='FLOW_06 scaled by the interpolated perimeter ratio '
                       '23/26; top not re-anchored'),

    '0.6': Nozzle('0.6', '*INDX_06hf_common*', (0.20, 0.25, 0.32),
                  flow=FLOW_06, validated=True,
                  extra={'draft': {'min_bead_width': (
                             '90%', "Prusa's own Draft tier uses 90% "
                             '(0.25mm Draft @COREONEINDX HF0.4); a deliberate '
                             'transfer of that tier choice, not the 85% every '
                             '@COREONE HF0.6 profile carries')},
                         'detail': {'top_solid_layers': (
                                        '5', 'matches Prusa 0.20mm BALANCED '
                                        '@COREONE HF0.6'),
                                    'bottom_solid_layers': (
                                        '4', 'matches Prusa 0.20mm BALANCED '
                                        '@COREONE HF0.6')}},
                  note='common sourced verbatim; the speeds and three per-tier '
                       'overrides are this repo\'s, each with a reason'),

    # *INDX_08hf_common* sets no main speed keys. Prusa's two commented
    # "@COREONEINDX HF0.8" print drafts DO set profile-level speeds (perimeter
    # 200, external 160/120, small 160/120, solid 200/120), which at the 0.9 mm
    # widths in that common, each draft at its own layer height, is 39-65 mm3/s;
    # and they leave infill at the inherited 300, which is 75-98 mm3/s. Prusa's
    # own commented Prusament PLA @COREONEINDX HF0.8 draft resolves to an MVS of
    # 36 (it types none; 36 comes from Prusament PLA @COREONE HF0.8), and the
    # perimeter at the 0.40 mm layer (65) and the inherited infill blow straight
    # past it, so they are not used. Prusa's own @COREONE 0.8 MVS figures are for
    # a standard brass nozzle (Prusament PLA = 19, BELOW the HF0.6 figure of 30)
    # and do not transfer to a high-flow CHT either, so these are extrapolated.
    '0.8': Nozzle('0.8', '*INDX_08hf_common*', (0.30, 0.40, 0.55),
                  flow=_scaled(32.0 / 26.0), validated=False,
                  note='targets extrapolated past the 0.6 anchor; the upstream '
                       '0.8 MVS data is non-high-flow and the drafted 0.8 speeds '
                       'imply 39-65 mm3/s, so neither is usable here'),
}


def scaled_nozzle(dia, src, note):
    """A size built from the sourced size `src` by the SCALED SIZES rule
    (approved for HF1.0 from 0.8 only): its layer ladder scaled; its common, flow targets and
    per-tier extras held at the source's."""
    r = Decimal(dia) / Decimal(src.dia)
    return Nozzle(dia, src.common, tuple(float(scale(h, r)) for h in src.layers),
                  flow=src.flow, validated=False, extra=src.extra, note=note,
                  scaled_from=src.dia)


# 1.0 (Bondtech CHT): PrusaResearch 2.5.12 has nothing at 1.0 mm - no INDX
# common, no CORE One 1.0 or HF1.0 variant, no print, printer or filament
# profile, no commented draft, no *C1INDX_*_10_PA* section. So it is 0.8 scaled
# by 1.25: layers 0.30/0.40/0.55 -> 0.38/0.50/0.69, line widths 0.9 -> 1.13.
# The flow targets are 0.8's, held, and 0.8's are themselves extrapolated, so
# this is the least-founded size here.
NOZZLES['1.0'] = scaled_nozzle(
    '1.0', NOZZLES['0.8'],
    note='SCALED from 0.8: Prusa publishes nothing at 1.0. Line widths and '
         'layers x1.25; flow targets and everything but the per-size '
         'COMMON_EDITS held at 0.8\'s, which are themselves extrapolated')

# Standard (non-high-flow) nozzles. Every value is Prusa's own, but sourced is
# not the same as printed: flip a size to True only once it has been test
# printed on an INDX. Drives the UNVALIDATED banner in all three --std outputs.
STD_VALIDATED = {
    '0.4': False,   # Prusa's HF0.4 prints and the CORE One HF0.4 -> 0.4 delta
    '0.25': False,  # Prusa's unreleased INDX 0.25 draft and 0.25 bases
}

# The three profiles emitted per nozzle. The star marks the recommended
# default, matching Prusa's own convention.
TIERS = [('detail', 'Detail', 0), ('balanced', 'Balanced \u2605', 1),
         ('draft', 'Draft', 2)]

# Edits applied to every generated common, with the reason recorded.
COMMON_EDITS = {
    'bridge_speed': ('30', 'inherited 50 is ~14 mm3/s at a 0.6 bridge'),
    'interlocking_beam_width': (None, 'introduced, not overridden: the chain '
                                'leaves it unset and PrusaSlicer defaults it to '
                                '0.8, too narrow past 0.4. Set to 2x nozzle. '
                                'Inert unless interlocking beams are enabled, '
                                'and not applied on the --std path'),
    'print_settings_id': ('', 'system preset hygiene'),
    'notes': ('', 'system preset hygiene'),
    'compatible_printers': ('', 'condition-based binding only'),
}
