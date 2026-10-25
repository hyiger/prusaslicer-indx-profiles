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

from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP


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
                   # Never built here (shipped). Prusa's pass is test printed
                   # only as part of the standard 0.25 setup: STD_VALIDATED.
                   flow=None, validated=False,
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
    '0.4': True,    # Prusa's HF0.4 prints and the CORE One HF0.4 -> 0.4 delta;
                    # test printed on an INDX, reported 2026-10-22
    '0.25': True,   # Prusa's unreleased INDX 0.25 draft and 0.25 bases;
                    # test printed on an INDX, reported 2026-10-22
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


# --- MIXED TOOL LAYOUTS ------------------------------------------------------
# Prusa's own "experimental printing with different nozzle diameters" workflow
# (help.prusa3d.com article 821176), applied to the INDX: one toolchanger with
# different nozzles on different tools, roles split between them.
#
# Nothing is invented here either. A layout composes presets this repo already
# builds for each nozzle on its own, and PrusaSlicer decides, per role, which
# tool's nozzle a width or speed belongs to:
#
#   * PrintRegion::flow (PrintRegion.cpp:63, version_2.9.6) takes the nozzle
#     diameter of the extruder assigned to the role being extruded. So once a
#     role is pinned to one tool, every per-role width and speed key belongs to
#     exactly one nozzle, and can be taken from that nozzle's own Prusa source.
#     That is why the widths stay explicit instead of being zeroed to "auto" as
#     Prusa's article suggests: auto would recompute them as 1.125 x nozzle
#     (Flow::auto_extrusion_width, Flow.cpp:33) and throw away Prusa's own
#     tuned figures.
#   * ExtruderFilaments::update_compatible_internal (Preset.cpp:2404-2415)
#     copies every per-extruder key's value at tool N into index 0 before
#     evaluating a filament's compatible_printers_condition, whenever
#     single_extruder_multi_material is 0 - which the INDX sets. So each tool's
#     filament list filters on its own nozzle and the filament bundles in this
#     repo need no change at all for a mixed layout.
#   * Print presets get no such adjustment (Preset.cpp:1352-1368): they are
#     evaluated against the printer as written, so a layout's print profiles
#     bind on the tools by index, which is what BIND below does. An index past
#     the end of a vector reads element 0 rather than throwing
#     (PlaceholderParser.cpp:1074), so testing tool 2 is safe on any printer.
#
# A layout stays validated=False until printed as a layout. Being composed from
# sizes that are themselves test printed is not the same thing: the role split,
# the tool changes and the combined infill are exercised by nothing else.

# PrusaSlicer's own per-extruder keys: PrintConfigDef::init_extruder_option_keys
# (PrintConfig.cpp:4124-4131, version_2.9.6). These are the only printer keys a
# layout may vary from tool to tool; any other key that differs between two
# tools' presets is printer-wide and needs a human decision (MIXED_SCALAR in
# build_printer_preset.py).
EXTRUDER_KEYS = frozenset("""
    nozzle_diameter min_layer_height max_layer_height extruder_offset
    retract_length retract_lift retract_lift_above retract_lift_below
    retract_speed deretract_speed retract_before_wipe retract_restart_extra
    retract_before_travel wipe travel_slope travel_max_lift
    travel_ramping_lift travel_lift_before_obstacle retract_layer_change
    retract_length_toolchange retract_restart_extra_toolchange extruder_colour
    default_filament_profile nozzle_high_flow
""".split())

# Print roles PrusaSlicer can pin to a tool, and the width and speed keys that
# follow each one. The mapping is PrintRegion::extruder (PrintRegion.cpp:22-35)
# and PrintRegion::flow (PrintRegion.cpp:38-65): gap fill rides the perimeter
# flow, bridges and top surfaces ride the solid-infill flow. A role left on
# Prusa's 0 ("current extruder") is not pinned and its keys stay at the base
# tool's values, which is why a layout must pin every role whose tool it means
# to change.
ROLE_KEYS = {
    'perimeter_extruder': ('perimeter_extrusion_width',
                           'external_perimeter_extrusion_width',
                           'perimeter_speed', 'external_perimeter_speed',
                           'small_perimeter_speed', 'gap_fill_speed'),
    'infill_extruder': ('infill_extrusion_width', 'infill_speed'),
    'solid_infill_extruder': ('solid_infill_extrusion_width',
                              'top_infill_extrusion_width',
                              'solid_infill_speed', 'top_solid_infill_speed',
                              'bridge_speed'),
    'support_material_extruder': ('support_material_extrusion_width',
                                  'support_material_speed'),
    'support_material_interface_extruder': (),
}

# Where a role moved onto another tool takes its width and its volumetric rate
# from: a print profile Prusa itself ships at that nozzle, which carries a
# width, a layer height and a speed together. The width transfers as written;
# the speed is re-solved so the rate matches Prusa's at the layout's own
# geometry (solve_role() in build_print_profiles.py), because the layer height
# is the base tool's, not this profile's.
ROLE_ANCHOR = {
    'HF0.4': ('0.20mm Balanced \u2605 @COREONEINDX HF0.4',
              "Prusa's own starred INDX HF0.4 profile, and the same anchor the "
              'flow targets above are measured against: 20.4 mm3/s perimeter, '
              '24.4 infill'),
}


class Layout:
    """One INDX toolchanger with different nozzles on different tools.

    `tools` names the nozzle fitted to each tool, in tool order, exactly as the
    printer presets name their variants: '0.25' for a standard nozzle, 'HF0.4'
    for a high-flow one. Tool 1 is PrusaSlicer's Extruder 1, vector index 0.

    `roles` pins print roles to 1-based tools. Every role the layout means to
    move must be listed: PrusaSlicer's own 0 means "whichever tool is loaded",
    which makes the role's nozzle - and so its widths and speeds - unknowable,
    and raises _SUPPORT_NOZZLE_DIAMETER_DIFFER for supports (Print.cpp:675-679).

    `extra` holds the layout's own print-key decisions, {key: (value, reason)},
    the same shape as COMMON_EDITS.
    """

    def __init__(self, key, model, tools, roles, note, extra=None,
                 validated=False):
        self.key = key              # '0.25+HF0.4', the preset-name tag
        self.model = model          # INDX model the tool count belongs to
        self.tools = tuple(tools)   # per-tool variant tags, tool 1 first
        self.roles = dict(roles)    # print role -> 1-based tool
        self.note = note
        self.extra = dict(extra or {})
        self.validated = validated  # test printed as a mixed layout?

    @property
    def tag(self):
        return self.key

    @property
    def hidden_common(self):
        return '*COREONEINDX %s*' % self.key

    @property
    def base_tool(self):
        """The tool whose print common the profiles are built on: the one that
        prints perimeters, since that is what sets a profile's layer ladder and
        its surface quality."""
        return self.roles['perimeter_extruder']

    def tool_tag(self, pos):
        """The variant tag fitted to 1-based tool `pos`."""
        if not 1 <= pos <= len(self.tools):
            raise SystemExit('refusing: layout %s has %d tools, so there is no '
                             'tool %d to pin a role to' % (self.key, len(self.tools), pos))
        return self.tools[pos - 1]

    def dia(self, pos):
        return split_tag(self.tool_tag(pos))[0]

    def high_flow(self, pos):
        return split_tag(self.tool_tag(pos))[1]

    @property
    def pinned_tools(self):
        """Tools the profiles actually assign a role to, in order. These are the
        tools the binding tests: a layout says nothing about a tool it never
        prints with, so requiring a particular nozzle there would only make the
        profiles vanish when a spare dock is changed."""
        return sorted(set(self.roles.values()))


def split_tag(tag):
    """'HF0.4' -> ('0.4', True); '0.25' -> ('0.25', False)."""
    return (tag[2:], True) if tag.startswith('HF') else (tag, False)


def tool_runs(values, label=lambda v: v):
    """Per-tool values as runs: ['a','b','b'] -> 'tool 1 a, tools 2-3 b'."""
    out, start = [], 0
    for i in range(1, len(values) + 1):
        if i == len(values) or values[i] != values[start]:
            out.append('tool %d %s' % (start + 1, label(values[start]))
                       if i - start == 1 else
                       'tools %d-%d %s' % (start + 1, i, label(values[start])))
            start = i
    return ', '.join(out)


def combine_layers(cap, layer):
    """How many layers of sparse infill PrusaSlicer will combine at this layer
    height, given `cap` mm of combined height.

    PrintObject::combine_infill (PrintObject.cpp:3126-3132) caps the combined
    height at the smaller of the infill and solid-infill extruders' nozzle
    diameters, so a layout that keeps solid infill on the small nozzle is
    capped by the small nozzle however large the infill one is. 1 means no
    combining, which is what PrusaSlicer does below 2.
    """
    n = int((Decimal(str(cap)) / Decimal(str(layer))).to_integral_value(
        rounding=ROUND_FLOOR))
    return max(1, n)


# 0.25 mm standard nozzle on tool 1, 0.4 mm high-flow CHT on tools 2-8, which is
# Prusa's article worked through on an INDX 8T. Perimeters, solid infill, top
# surfaces and supports stay on the 0.25 for surface quality; sparse infill goes
# to the CHT, which is the one role where a 0.4 high-flow nozzle can pay for the
# tool changes. Layer ladder, and every key not listed in ROLE_KEYS for a moved
# role, are the 0.25 nozzle's.
LAYOUTS = {
    '0.25+HF0.4': Layout(
        '0.25+HF0.4', '8T', ('0.25',) + ('HF0.4',) * 7,
        roles={'perimeter_extruder': 1,
               'infill_extruder': 2,
               'solid_infill_extruder': 1,
               'support_material_extruder': 1,
               'support_material_interface_extruder': 1},
        extra={
            'support_material_style': (
                'organic',
                'required, not preference: with a wipe tower and non-soluble '
                'supports, Print.cpp:685-692 rejects the slice outright unless '
                'the support style is organic once a support extruder is pinned '
                '(both support extruders must otherwise be 0). Pinning them is '
                'what keeps support width off the smaller nozzle and silences '
                '_SUPPORT_NOZZLE_DIAMETER_DIFFER (Print.cpp:675-679). Prusa\'s '
                'article prescribes the same pair of changes'),
        },
        # Test printed on an INDX 8T with a 0.25 standard nozzle on tool 1 and
        # a 0.4 high-flow CHT on tool 2, reported 2026-10-24. Composition is
        # Prusa's own either way; this is the layout itself having been run.
        validated=True,
        note='mixed layout: composed from the 0.25 and HF0.4 presets this repo '
             'already builds, and test printed as a layout'),
}
