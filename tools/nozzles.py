"""
Per-nozzle configuration for the Prusa CORE One INDX profile generators.

Everything here is either lifted from PrusaResearch.ini or explicitly flagged as
unvalidated. Adding a nozzle size means adding one entry below.

Layer-height ladders are Prusa's own CORE One ladders for the same nozzle,
read out of the shipping print profiles:

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

# PrusaSlicer Flow::mm3_per_mm for a non-bridge extrusion.
def area(w, h):
    return w * h - h * h * (1.0 - 3.141592653589793 / 4.0)


def speed_for(q, w, h, round_to=5):
    return int(round(q / area(w, h) / round_to) * round_to)


class Nozzle:
    def __init__(self, dia, common, layers, flow=None, validated=False,
                 extra=None, note='', shipped=None):
        self.dia = dia              # nozzle diameter, e.g. '0.6'
        self.common = common        # upstream section, e.g. '*INDX_06hf_common*'
        self.layers = layers        # (detail, balanced, draft) layer heights
        self.flow = flow            # dict of volumetric targets, or None
        self.validated = validated  # have these targets actually been printed?
        self.extra = extra or {}    # per-profile key overrides
        self.note = note
        self.shipped = shipped      # Prusa's own print profiles for this size, if any

    @property
    def tag(self):
        """Preset-name suffix for the high-flow sizes built here, e.g. 'HF0.6'.
        Standard (non-HF) nozzles are handled separately: see --std."""
        return 'HF' + self.dia

    @property
    def hidden_common(self):
        return '*COREONEINDX %s*' % self.tag


# Volumetric targets validated on 0.6 CHT toolheads. The shipping 0.4 INDX
# profiles sit at 20-24 mm3/s; these aim modestly above that.
FLOW_06 = dict(perim=26.0, ext=20.0, small=18.0,
               infill=30.0, solid=27.0, top=11.3)


def _scaled(factor):
    return {k: round(v * factor, 1) for k, v in FLOW_06.items()}


NOZZLES = {
    # Prusa did a full speed pass on *INDX_025_common* (perimeter 150, infill
    # 100, perimeters 3, 11/8 solid layers) and, since PrusaResearch 2.5.x,
    # ships its own "@COREONEINDX 0.25" print profiles built on it. Building
    # them here would only duplicate Prusa's, so the generator refuses.
    '0.25': Nozzle('0.25', '*INDX_025_common*', (0.07, 0.12, 0.15),
                   flow=None, validated=True,
                   note='upstream speed pass present; speeds left untouched',
                   shipped='0.07mm Extra Fine / 0.10mm Fine ★ / 0.15mm Detail @COREONEINDX 0.25'),

    # Prusa ships "@COREONEINDX 0.3" print profiles since PrusaResearch 2.5.x.
    # Before that there was no upstream speed pass, and linear extrapolation
    # from the 0.4/0.6 anchors collapses below 0.4, so none was derived here.
    '0.3': Nozzle('0.3', '*INDX_03_common*', (0.12, 0.16, 0.20),
                  flow=None, validated=False,
                  note='NO upstream speed pass and no trustworthy targets; '
                       'inherits 250/300 from the 0.4 chain until measured',
                  shipped='0.10mm Fine / 0.15mm Detail ★ / 0.20mm Balanced @COREONEINDX 0.3'),

    # Prusa renamed the high-flow commons *INDX_05_common* -> *INDX_05hf_common*
    # (likewise 0.6 and 0.8) by PrusaResearch 2.5.11.

    # No upstream speed pass. Interpolated between the 0.4 anchor (20.4 perim /
    # 24.4 infill, measured off the shipping profiles) and the 0.6 targets.
    '0.5': Nozzle('0.5', '*INDX_05hf_common*', (0.15, 0.20, 0.25),
                  flow=_scaled(23.0 / 26.0), validated=False,
                  note='targets interpolated between the 0.4 and 0.6 anchors'),

    '0.6': Nozzle('0.6', '*INDX_06hf_common*', (0.20, 0.25, 0.32),
                  flow=FLOW_06, validated=True,
                  extra={'draft': {'min_bead_width': '90%'},
                         'detail': {'top_solid_layers': '5',
                                    'bottom_solid_layers': '4'}},
                  note='geometry sourced verbatim; speeds derived and in use'),

    # No upstream speed pass. Prusa's own @COREONE 0.8 MVS figures are for a
    # standard brass nozzle (Prusament PLA = 19, BELOW the HF0.6 figure of 30)
    # and do not transfer to a high-flow CHT, so these are extrapolated.
    '0.8': Nozzle('0.8', '*INDX_08hf_common*', (0.30, 0.40, 0.55),
                  flow=_scaled(32.0 / 26.0), validated=False,
                  note='targets extrapolated past the 0.6 anchor; the upstream '
                       '0.8 MVS data is non-high-flow and unusable here'),
}

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
    'interlocking_beam_width': (None, 'set to 2x nozzle; 0.8 is too narrow past 0.4'),
    'print_settings_id': ('', 'system preset hygiene'),
    'notes': ('', 'system preset hygiene'),
    'compatible_printers': ('', 'condition-based binding only'),
}
