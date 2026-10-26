# Provenance and design notes

The [README](../README.md) is the user guide: what you get, how to install it,
how to check it worked. This file is for anyone who wants to know **where every
number comes from**, why the repo is built the way it is, and what it would take
to add a size. Nearly everything here is read out of Prusa's own
`PrusaResearch.ini`; the few values that are not are named, with the reason.

Line numbers into `PrusaResearch.ini` are 2.5.12's unless stated; line numbers
into PrusaSlicer's source are its `version_2.9.6` tag.

## Contents

- [What the bundles contain](#what-the-bundles-contain)
- [Provenance](#provenance)
- [Printer presets in detail](#printer-presets-in-detail)
- [Adding a nozzle size](#adding-a-nozzle-size)
- [Design notes](#design-notes)
- [Gaps in detail](#gaps-in-detail)

---

## What the bundles contain

### Filament presets (0.6 mm)

Nineteen of the twenty materials Prusa publishes for the INDX. The twentieth,
Generic PVA (new in PrusaResearch 2.5.12), exists only as an INDX preset
upstream: there is no CORE One PVA at any size to scale from, so it is skipped.

| Material | MVS 0.4 → 0.6 | Material | MVS 0.4 → 0.6 |
|---|---|---|---|
| Prusament PLA | 28 → **35** | Prusament ASA | 30 → **39** |
| Prusament PETG | 20 → **25** | Prusament PC Blend | 22 → **28** |
| Prusament PLA Blend | 12.5 → **15** | Prusament PC Blend Carbon Fiber | 13 → **19** |
| Prusament rPLA | 10 → **14** | Generic PLA | 17 → **23** |
| Prusament Woodfill | 10 → **12** | Generic PETG | 17 → **22** |
| Generic PLA Silk | 12.5 → **16** | Generic ABS | 25 → **34** |
| Prusament PETG V0 | 16 → **22** | Prusament PETG Carbon Fiber | 12 → **17** |
| Prusament PVB | 6 → **16** | Prusament TPU 95A | 2 → **3** |
| Generic FLEX | 2 → **3** | Verbatim BVOH | 4 → **5** |
| Fiberlogy BVOH | 4 → **5** | | |

MVS in mm³/s.

### Filament presets (0.8 mm)

Nineteen of the twenty INDX materials, built by the same rules as 0.6 (see
[how filaments are derived](#filament-presets--derived)). MVS is the INDX 0.4
value scaled by Prusa's CORE One 0.4 to 0.8 ratio for that material: the
high-flow `HF0.4` → `HF0.8` pair for 8 materials, the standard `@COREONE` →
`@COREONE 0.8` pair for the other 11. Pressure advance is Prusa's own
`*C1INDX_<FAM>_08_PA*` figure, except FLEX and TPU, which keep the
nozzle-independent `*C1INDX_FLEX_PA*`. Wipe-tower purge (20) and the
toolchange deretract (0.05) come from `*C1INDX_08_common*`; FLEX and TPU keep
their own purge of 15. Generic PVA is skipped, as at 0.6.

| Material | MVS 0.4 → 0.8 | PA | Material | MVS 0.4 → 0.8 | PA |
|---|---|---|---|---|---|
| Fiberlogy BVOH | 4 → **8** | 0.01 | Prusament PETG Carbon Fiber | 12 → **22** | 0.02 |
| Generic ABS | 25 → **36** | 0.01 | Prusament PETG V0 | 16 → **27** | 0.02 |
| Generic FLEX | 2 → **6** | 0 | Prusament PLA | 28 → **42** | 0.013 |
| Generic PETG | 17 → **28** | 0.02 | Prusament PLA Blend | 12.5 → **20** | 0.013 |
| Generic PLA | 17 → **28** | 0.013 | Prusament PVB | 6 → **19** | 0.013 |
| Generic PLA Silk | 12.5 → **21** | 0.013 | Prusament TPU 95A | 2 → **6** | 0 |
| Prusament ASA | 30 → **42** | 0.01 | Prusament Woodfill | 10 → **15** | 0.013 |
| Prusament PC Blend | 22 → **36** | 0.016 | Prusament rPLA | 10 → **14** | 0.013 |
| Prusament PC Blend Carbon Fiber | 13 → **26** | 0.016 | Verbatim BVOH | 4 → **8** | 0.01 |
| Prusament PETG | 20 → **31** | 0.02 | | | |

MVS in mm³/s.

### Filament presets (1.0 mm)

The filaments are exactly the HF0.8 presets above, rebound to a 1.0 nozzle, so
max volumetric speed (MVS, mm³/s) and pressure advance (PA) are 0.8's:

| Material | MVS | PA | Material | MVS | PA |
|---|---|---|---|---|---|
| Fiberlogy BVOH | 8 | 0.01 | Prusament PETG Carbon Fiber | 22 | 0.02 |
| Generic ABS | 36 | 0.01 | Prusament PETG V0 | 27 | 0.02 |
| Generic FLEX | 6 | 0 | Prusament PLA | 42 | 0.013 |
| Generic PETG | 28 | 0.02 | Prusament PLA Blend | 20 | 0.013 |
| Generic PLA | 28 | 0.013 | Prusament PVB | 19 | 0.013 |
| Generic PLA Silk | 21 | 0.013 | Prusament TPU 95A | 6 | 0 |
| Prusament ASA | 42 | 0.01 | Prusament Woodfill | 15 | 0.013 |
| Prusament PC Blend | 36 | 0.016 | Prusament rPLA | 14 | 0.013 |
| Prusament PC Blend Carbon Fiber | 26 | 0.016 | Verbatim BVOH | 8 | 0.01 |
| Prusament PETG | 31 | 0.02 | | | |

### Filament presets for a mixed layout — none

The `0.25+HF0.4` layout adds no filament bundle. Each tool is offered the
filaments for its own nozzle, so tool 1 uses the 0.25 bundle below and tools 2
to 8 use Prusa's own `@COREONEINDX HF0.4` presets
([why](#mixed-tool-layouts--composed-not-derived)).

### Filament presets (standard 0.4 and 0.25 mm)

Prusa's INDX filaments rebuilt on the standard-nozzle bases Prusa already has
in PrusaResearch.ini but doesn't use yet. MVS is capped at Prusa's own CORE One
standard-nozzle value. See [Standard nozzles](#standard-nozzles-from-prusas-own-pieces)
for how each one is built.

| Material | MVS HF0.4 → 0.4 → 0.25 | Material | MVS HF0.4 → 0.4 → 0.25 |
|---|---|---|---|
| Prusament PLA | 28 → **15** → **10** | Prusament ASA | 30 → **15** → **15** |
| Prusament PETG | 20 → **12** → **10** | Prusament PC Blend | 22 → **12** → **12** |
| Prusament PLA Blend | 12.5 → **7.5** → **7.5** | Prusament PC Blend Carbon Fiber | 13 → **9** → n/a |
| Prusament rPLA | 10 → **10** → **10** | Generic PLA | 17 → **15** → **10** |
| Prusament Woodfill | 10 → **10** → n/a | Generic PETG | 17 → **12** → **12** |
| Generic PLA Silk | 12.5 → **7** → **7** | Generic ABS | 25 → **15** → **15** |
| Prusament PETG V0 | 16 → **10** → **10** | Prusament PETG Carbon Fiber | 12 → **12** → n/a |
| Prusament PVB | 6 → **6** → **6** | Verbatim BVOH | 4 → **4** → **4** |
| Fiberlogy BVOH | 4 → **4** → **4** | | |

n/a means not built: Prusa does not allow carbon fiber or Woodfill on a 0.25
nozzle. Generic FLEX and Prusament TPU 95A are not rebuilt: Prusa's own INDX
presets for them already accept a standard 0.4, and the INDX has no 0.25 FLEX
base. Generic PVA is not built at either size: with no CORE One PVA there is no
standard parent to swap in and no standard-nozzle MVS to cap at.

---

## Provenance

### Print profile geometry — sourced

PrusaResearch.ini contains per-nozzle INDX commons for 0.25, 0.3, 0.5, 0.6 and
0.8. Every one defines a complete geometry set. Prusa's own 0.25 and 0.3 print
profiles now use theirs (there is no 0.3 INDX nozzle, so the 0.3 set is
scaffolding); the high-flow 0.5, 0.6 and 0.8 commons are still unreleased
scaffolding: no variant declares those sizes and no *released* print
profile inherits from them. Prusa has drafted them, though, as commented-out
sections: ten `@COREONEINDX HF0.5` / `HF0.6` / `HF0.8` print profiles — four,
four and two (`PrusaResearch.ini:57206-57299`) — and six INDX printer drafts for
8T and 4T at
`0.25`, `HF0.6` and `HF0.8` (`56634-56710`). Those count as sourced here, and
the printer generator uses them (see
[Prusa's commented-out drafts](#prusas-commented-out-drafts) and
[Gaps in detail](#gaps-in-detail)). The print drafts are not used. The HF0.5 and HF0.6
ones restate the 250/200 speeds they inherit; their other keys are
per-layer values (HF0.6 sets support and raft contact distance to the layer
height, where the profiles here keep the common's 0.3 / 0.25). The two HF0.8
ones set their own speeds, but every one overruns the filaments (39–65 mm³/s)
and they inherit an infill of 75–98 mm³/s, where no HF0.8 filament Prusa ships
allows more than 39 (see [Print profile speeds](#print-profile-speeds--derived-and-only-where-needed)).
This repo also prefers the CORE One HF0.6 layer ladder and its own three-tier
naming to Prusa's drafted Balanced/Draft/Coarse/Extra Coarse lineup.

`build_print_profiles.py` resolves the requested common and embeds it verbatim
(except at 1.0, whose widths are scaled and size labels moved; see
[The 1.0 mm nozzle is scaled, not sourced](#the-10-mm-nozzle-is-scaled-not-sourced)) —
widths, solid-layer counts, support parameters, infill anchors, overhang speeds,
minimum thicknesses. Inheritance cannot cross bundle files, so values are copied
rather than referenced. Keys the chain doesn't set are left to PrusaSlicer's
defaults, exactly as Prusa's own profiles do.

Five keys are changed in the common of every size, 1.0 included:

| Key | Upstream | Here | Why |
|---|---|---|---|
| `bridge_speed` | 50 | 30 | 50 mm/s at a 0.6 bridge is ~14 mm³/s |
| `interlocking_beam_width` | — (unset; PrusaSlicer default 0.8) | 2 × nozzle | 0.8 is only ~1.2 extrusions wide at 0.68 |
| `print_settings_id` | — | empty | system preset hygiene |
| `notes` | — | empty | system preset hygiene |
| `compatible_printers` | — | empty | condition-based binding only |

Three more are changed per *tier* rather than per size, so `0.20mm Detail`
deviates from the resolved common in seven keys, `0.32mm Draft` in six, and
`0.25mm Balanced ★` in exactly the five above:

| Key | Tier | Value | Why |
|---|---|---|---|
| `top_solid_layers` | Detail | 5 | matches Prusa `0.20mm BALANCED @COREONE HF0.6` |
| `bottom_solid_layers` | Detail | 4 | matches Prusa `0.20mm BALANCED @COREONE HF0.6` |
| `min_bead_width` | Draft | 90% | Prusa's own Draft tier uses 90% (`0.25mm Draft @COREONEINDX HF0.4`); a deliberate transfer of that tier choice, not the 85% every `@COREONE HF0.6` profile carries |

They live in `Nozzle.extra` in `tools/nozzles.py`, in the same
`(value, reason)` shape as the table above. The bundle's header lists every key
in both tables whose value it changes, with its reason, ahead of each size's
profiles (`notes` is already empty upstream, so it is not listed). The
standard 0.4 section does the same for its two `STD_EDITS` keys.

### Print profile speeds — derived, and only where needed

Of the five commons, only `*INDX_025_common*` has a real speed pass. The rest
inherit `perimeter_speed = 250` and `infill_speed = 300` from `*INDX_common*`.
At HF0.6's 0.68 mm width and a 0.25 mm layer that is 39–47 mm³/s, past every
`@COREONE HF0.6` filament Prusa ships (max 34). No per-nozzle *common* carries
a pass, consistent with the missing variant declarations. Prusa's commented HF0.8
print drafts do set profile-level speeds (perimeter 200, external 160/120, small
160/120, solid 200/120), which at that common's 0.9 mm widths, each draft at its
own layer height, is 39–65 mm³/s; and they leave infill at the inherited 300,
which is 75–98 mm³/s. Prusa's own commented `Prusament PLA @COREONEINDX HF0.8`
draft resolves to an MVS of 36, so every drafted speed (39.1 mm³/s at the
lowest) and the inherited infill overrun it; they are not used either. The
HF0.5 and HF0.6 drafts restate the inherited speeds; their other keys are
per-layer values the profiles here do not use (see
[Print profile geometry](#print-profile-geometry--sourced)).

Where a size has flow targets in `nozzles.py`, six speeds are solved backward
from them using PrusaSlicer's own extrusion geometry,
`A = w·h − h²(1 − π/4)`. For 0.6:

| Target | mm³/s |
|---|---|
| Perimeter | 26 |
| External perimeter | 20 |
| Small perimeter | 18 |
| Infill | 30 |
| Solid infill | 27 |
| Top solid infill | 11.3 |

All three tiers land on the same rates, so changing layer height changes
resolution rather than flow demand. Prusa's starred `0.20mm Balanced ★
@COREONEINDX HF0.4` runs 20.4 mm³/s perimeter and 24.4 infill; these aim modestly
above that one tier, because a CHT melts faster. Across its four tiers the
shipping 0.4 lineup spans 8.6–33.5 mm³/s, the upper ones riding the un-passed
250/300, so these are not above the whole shipping range.

Where a size has no targets, upstream speeds are left untouched and the
generator says so loudly.

### Filament presets — derived

Each preset starts from its `@COREONEINDX HF0.4` parent, which carries the
INDX-specific toolchanger settings (multitool ramming, purge volumes,
cooling-move behavior). The 0.4 → size step comes from Prusa's own CORE One
`HF0.4` / `HF<dia>` pair for that material. Materials with no high-flow profile
fall back to the non-HF `@COREONE` → `@COREONE <dia>` pair.

Three rules, beside the pressure advance described under
[Pressure advance by size](#pressure-advance-by-size):

- `filament_max_volumetric_speed` is **ratio-scaled** off the INDX 0.4 value,
  because the INDX toolhead has its own flow baseline distinct from CORE One.
- **INDX toolchanger keys that Prusa sets per nozzle come from its per-nozzle
  common.** Since 2.5.12 Prusa's 0.6 and 0.8 INDX family sections inherit
  `*C1INDX_06_common*` / `*C1INDX_08_common*` in place of `*C1INDX_common*`:
  wipe-tower minimal purge 10 → 14 (20 at 0.8), and
  `filament_retract_restart_extra_toolchange` 0.04 (0.05 at 0.8). They arrived
  together with a toolchange G-code that no longer adds a fixed 0.04 mm to its
  post-toolchange retract, and which still records `retract_length +
  retract_restart_extra_toolchange` as retracted. Most of Prusa's HF0.6 drafts
  inherit a sized INDX family section in place of the 0.4 one
  (`*PLAHFC1INDX*` → `*PLA06HFC1INDX*`), so the generator re-resolves each INDX
  0.4 preset with its family swapped that way and takes these keys from that
  chain. A value the 0.4 preset sets in its own body is kept, as an own
  override, whether or not it agreed with anything: Generic FLEX and Prusament
  TPU 95A keep their own purge of 15, where Prusa's HF0.6 drafts for them
  resolve to 14. Only keys reviewed into `COMMON_ADOPT`, each with its reason,
  are taken, and the bundle header records them. A per-nozzle common that
  changes any other key stops the build, as do a family with no sized
  counterpart upstream and a toolchanger key set anywhere but the common.
- Of the other keys, only the 11 cooling and speed-limit keys in `TRANSFER` take
  the CORE One value, and **only if INDX agreed with CORE One at 0.4**; any other
  key keeps the INDX 0.4 value. Where INDX already differs it made a deliberate
  toolchanger-specific choice, and that choice is preserved. This is why Generic ABS keeps
  `filament_infill_max_crossing_speed = 140` rather than taking CORE One's `0`,
  and why `filament_cooling_final_speed = 0` survives throughout.

Every preset, high-flow or standard, keeps the `printer_model` clause of its
INDX HF0.4 base. Since 2.5.12 Prusa binds its ABS, PC and PA INDX families to
the CORE One INDX alone and gives the CORE One L INDX its own chamber values
(`*C1LINDX_CH_*`, 60/50 °C against 55/40), so Generic ABS, Prusament ASA, both
PC Blends and both BVOHs bind to `COREONE_INDX8T|COREONE_INDX4T`; the rest
also list `COREONEL_INDX8T|COREONEL_INDX4T`, as Prusa's do. PrusaResearch 2.5.12
has no CORE One L INDX printer yet, so today this changes nothing you can see.

Prusa's own `filament_notes` are kept and the derivation note is appended:
the INDX start G-code reads markers such as `MBL160` (Prusament TPU 95A) from
them to choose the bed-probing temperature.

### Standard nozzles, from Prusa's own pieces

Nothing is scaled or extrapolated for a standard nozzle. PrusaResearch.ini
already holds what is needed, unused: INDX standard-nozzle filament bases
(`*PLAPGC1INDX*`, `*PETPGC1INDX*`, `*ABSPGC1INDX*`, `*PCPGC1INDX*`), INDX 0.25
bases (`*PLA025PGC1INDX*`, `*PET025PGC1INDX*`), and commented-out drafts of an
INDX 0.25 printer and of `Prusament PLA` / `Prusament PETG @COREONEINDX 0.25`.

**Printers.** The 0.4 applies Prusa's CORE One `HF0.4 → 0.4` delta under the
same agreed-at-0.4 rule as the high-flow sizes: `nozzle_high_flow` off,
`printer_variant 0.4`, and the default profiles moved to `@COREONEINDX 0.4`.
The 0.25 is Prusa's draft applied key for key, plus a default filament the
draft leaves unset.

**Print profiles.** Prusa's four HF0.4 profiles with one change, the binding,
which becomes `! nozzle_high_flow[0]`. Prusa's CORE One STD and HF0.4 prints
differ by only a few speeds, and on a standard nozzle the filament MVS cap does
the limiting.

**Filaments, 0.4.** Each INDX HF0.4 preset keeps its own toolchanger settings,
but on Prusa's standard parents: its CORE One HF0.4 parent becomes the CORE One
STD one, and the INDX high-flow base becomes the INDX STD base. MVS is the
lower of the INDX HF0.4 value and Prusa's CORE One STD value for the same
filament. Pressure advance stays the INDX HF0.4 value.

**Filaments, 0.25.** Only what Prusa allows on a CORE One 0.25 nozzle, which
rules out carbon fiber and Woodfill; FLEX is skipped because the INDX has no
0.25 FLEX base. Prusament PLA and PETG are Prusa's drafts as written. The others
get the CORE One STD parent plus the INDX 0.25 base (PLA and PET families) or
the INDX STD base (ABS and PC families), with nozzle-dependent keys left to
the swapped-in chain:

- **Cooling.** ABS/PC families keep their own; their INDX bases do not change
  with the nozzle. PLA/PET families keep a value they set themselves (PVB's
  20 s minimum layer time, for example), follow the flagship's draft where they
  matched it at HF0.4, and take the 0.25 base otherwise.
- **Pressure advance.** The INDX 0.25 base supplies it for the PLA (0.1) and
  PET (0.15) families; the ABS, ASA, PC and BVOH families take the CORE One's own
  0.25 value (0.09, PC 0.14). Either way the figure is swapped into the INDX
  start G-code rather than replacing it, so the INDX skeleton survives — `M573 R`
  on every preset, and `M906 P2` (BVOH's reduced E current) on the two BVOHs.
- **MVS.** The lowest of the INDX HF0.4, CORE One STD and 0.25-base values.
- **Retraction.** The INDX STD bases for ABS and PC define no
  `filament_retract_*` or `filament_travel_max_lift`, so Prusament ASA (0.8 / 0.6)
  and Prusament PC Blend (1 / 1) release those two keys to the printer preset —
  at 0.25 that is `retract_length = 0.7` and `travel_max_lift = 1.5`, so ASA's
  travel lift rises from 0.6. Each affected preset names the released keys in its
  `filament_notes`.

**Toolchanger keys, both sizes.** The INDX STD and 0.25 bases come in whole, and
with them the INDX toolchanger common they stand on: at 2.5.12 that is
`*C1INDX_common*` for every one. The high-flow bundle's gate applies here too.
Each preset must reach that common through exactly one swapped-in base and by
no other route, so a new high-flow family with no standard base stops the build
rather than reaching a standard nozzle. Nothing that overrides that base may
set a toolchanger key either, at any depth: a parent listed after the base, or
after the section that holds it, or the own body of such a holding section. In
PrusaSlicer's chain the last parent wins and a body beats its parents, so the
value would replace the common's and be passed off as the preset's own. A per-nozzle common Prusa later puts
under a standard base may change only keys reviewed into `COMMON_ADOPT`, and
the bundle header and `filament_notes` record them.

### Mixed tool layouts — composed, not derived

Prusa documents fitting **different nozzle diameters to different tools** of one
toolchanger as an experimental workflow
([article 821176](https://help.prusa3d.com/article/experimental-printing-with-different-nozzle-diameters_821176)),
written for the XL. `LAYOUTS` in `tools/nozzles.py` carries one INDX layout,
`0.25+HF0.4`: a standard 0.25 on tool 1, Prusa's shipping HF0.4 on tools 2 to 8,
test printed as a layout on 2026-10-24.

Nothing new is derived for it. Four PrusaSlicer behaviors decide what a layout
can and cannot be, and all four were read out of `version_2.9.6`:

- **A role's flow uses that role's extruder's nozzle.** `PrintRegion::flow`
  (`PrintRegion.cpp:63`) looks up `nozzle_diameter` at
  `this->extruder(role) - 1`, where `extruder(role)` is `perimeter_extruder`,
  `infill_extruder` or `solid_infill_extruder` (`PrintRegion.cpp:22-35`). So once
  a role is pinned to one tool, every per-role width and speed key belongs to
  exactly one nozzle and can be taken from that nozzle's own Prusa source. This
  is why the widths stay explicit here, where Prusa's article says to zero them:
  auto width would recompute each from the nozzle alone — 1.125 × nozzle for
  perimeters, infill and solid infill, 1.0 × for top solid infill and supports —
  (`Flow::auto_extrusion_width`, `Flow.cpp:33`) and discard Prusa's tuned
  figures. A role left at Prusa's `0`, "whichever tool is loaded", has no
  knowable nozzle, so a layout must pin every role it means to move.
- **Filament lists are already per tool.**
  `ExtruderFilaments::update_compatible_internal` (`Preset.cpp:2404-2415`) copies
  every per-extruder key's value at tool N into index 0 before evaluating a
  filament's `compatible_printers_condition`, whenever
  `single_extruder_multi_material` is 0 — which the INDX sets. A condition
  written as `nozzle_diameter[0]==0.4 and nozzle_high_flow[0]` therefore tests
  *that tool's* nozzle. **The filament bundles in this repo need no change at all
  for a mixed layout**, and none was made: tool 1 is offered the 14
  `@COREONEINDX 0.25` presets from `filaments/hyigerINDX-0.25-filaments.ini`, and
  tools 2 to 8 Prusa's own 20 `@COREONEINDX HF0.4` presets. The one key the
  shift skips is `default_filament_profile`, so a layout's printer preset writes
  the base tool's and nothing per tool.
- **Print presets get no such shift.** `PresetCollection::update_compatible_internal`
  (`Preset.cpp:1352-1368`) evaluates them against the printer as written, so a
  layout's print profiles bind on tools by index. An index past the end of a
  vector reads element 0 instead of throwing
  (`PlaceholderParser.cpp:1074`), so a clause on tool 2 is safe to evaluate on a
  single-extruder printer; it simply compares tool 1 with itself and fails.
- **Organic supports are recommended, not forced.** With a wipe tower and
  non-soluble supports, `Print::validate` rejects the slice unless both support
  extruders are `0` — *except* when the style is organic, which skips that
  branch (gate `Print.cpp:681`, rejection `Print.cpp:688-690`). But that gate,
  and the dialog that enforces the same rule (`ConfigManipulation.cpp:178-180`),
  are reached only when `Print::has_wipe_tower()` is true
  (`Print.cpp:1396-1402`), and **every INDX print profile inherits
  `wipe_tower = 0`** from Prusa's `*INDX_common*`. So nothing forces organic as
  shipped, and `_WIPE_TOWER_NOZZLE_DIAMETER_DIFFER` (`Print.cpp:567`) cannot
  fire either: the INDX purges at its Purge Station. Organic is chosen because
  PrusaSlicer itself prescribes exactly this pair for mixed nozzles — "switch to
  Organic supports and assign a specific extruder for supports"
  (`Plater.cpp:2335-2348`) — because Prusa's article recommends it, because it
  keeps the slice legal if a user switches a tower on, and because the layout
  was test printed with it. It costs one restriction: an object with a varying
  layer-height profile cannot be sliced with organic supports
  (`Print.cpp:548-554`).
- **Pinning the support extruders is a separate decision, and does not move the
  support width.** It silences `_SUPPORT_NOZZLE_DIAMETER_DIFFER`
  (`Print.cpp:675-679`), whose condition tests only those two keys. It does not
  change the width: at `0`, `support_material_flow` already falls back to
  `min_nozzle_diameter()`, the smallest nozzle fitted (`Flow.cpp:245-252`) —
  the same 0.25 here. `Layout.extra` records both halves.

#### The printer preset

`build_mixed()` in `build_printer_preset.py` composes, tool by tool, the presets
this repo already builds for each nozzle on its own — here the 0.25 preset (from
Prusa's commented INDX 0.25 draft) and the shipping HF0.4 preset. Six keys end up
differing per tool:

| Key | Tool 1 (0.25) | Tools 2-8 (HF0.4) |
|---|---|---|
| `nozzle_diameter` | 0.25 | 0.4 |
| `nozzle_high_flow` | 0 | 1 |
| `min_layer_height` | 0.05 | 0.07 |
| `max_layer_height` | 0.15 | 0.3 |
| `retract_length` | 0.7 | 0.8 |
| `retract_lift` | 0.15 | 0.2 |

Only PrusaSlicer's own per-extruder keys may vary that way. `EXTRUDER_KEYS` in
`nozzles.py` is `PrintConfigDef::init_extruder_option_keys`
(`PrintConfig.cpp:4124-4131`) copied out. Any **other** key the two nozzles'
presets disagree on describes the machine rather than a nozzle, and the build
refuses unless `MIXED_SCALAR` says what to do with it — so a re-pin that moved,
say, a machine limit on one size only cannot be absorbed silently. `MIXED_SCALAR`
holds four keys, each with its reason: `printer_variant` (names the layout;
nothing binds on it, and `Preset::set_visible_from_appconfig` returns early for a
preset with no vendor of its own, `Preset.cpp:425`), `default_print_profile`,
`default_filament_profile` and `inherits`.

Two more refusals protect the premise rather than the values:
`single_extruder_multi_material` must be 0, because both the per-tool filament
shift (`Preset.cpp:2405`) and PrusaSlicer's own willingness to keep differing
nozzles (`Tab.cpp:2742-2756`) depend on it; and Prusa's start G-code must still
check each tool's own nozzle, `M862.1 T<n> P{nozzle_diameter[n]} …
F{nozzle_high_flow[n]}` per used tool. That per-tool check is what makes a mixed
layout safe to send to the printer — the firmware stops the print if a dock holds
something else — so if a release ever collapsed it to one tool, no mixed preset
is written.

#### The print profiles

`build_layout()` starts from **Prusa's own print profiles for the tool that
prints perimeters**, not from its common. Prusa tunes the 0.25 profiles per tier
— 11/9 top and bottom solid layers at 0.07 mm, 9/7 at 0.10, 6/5 at 0.15, where it
also widens the perimeters to 0.27 — and flattening the common over every tier
would have put the finest tier's shell on the coarsest. So the layer ladder is
Prusa's 0.07 / 0.10 / 0.15 and every tier carries Prusa's own counts.

The tiers are renamed to this repo's labels (`Detail`, `Balanced ★`, `Draft`).
That is forced, not cosmetic: a mixed printer satisfies Prusa's own
`nozzle_diameter[0]==0.25` condition too, so Prusa's three profiles are
compatible alongside these, and
`PresetCollection::update_compatible_internal` (`Preset.cpp:1388-1401`) marks a
templates-vendor preset incompatible whenever a compatible non-templates preset
shares its alias — the name before `@`. Keeping Prusa's tier names would have
hidden every profile in this layout behind Prusa's. (The `--std 0.4` copies share
Prusa's aliases harmlessly because no printer accepts both bindings; a mixed
printer does.)

One role moves, so two keys move with it:

- `infill_extrusion_width` → **0.45**, Prusa's own HF0.4 width, taken as written
  from `0.20mm Balanced ★ @COREONEINDX HF0.4` (`ROLE_ANCHOR`, the same starred
  profile the flow targets elsewhere in this repo are anchored against).
- `infill_speed` → solved so the **volumetric rate matches that profile's own**:
  0.45 mm × 0.20 mm at 300 mm/s is 24.4 mm³/s, and the speed is re-solved for the
  layout's geometry with the same `Flow::mm3_per_mm` formula used everywhere else,
  then capped at that profile's own 300 mm/s. It is never asked to run faster
  than Prusa runs the same nozzle.

`wipe_tower_extruder` stays at Prusa's `0` although the article names extruder 1
for the wipe tower. `0` means "use the one that is available"
(`PrintConfig.cpp:3932`) and applies only to the tower's perimeter, so it costs
no extra tool change, and the tower already carries per-extruder properties for
every tool (`Print.cpp:1501`). Holding an upstream value needs no derivation;
forcing a tool change on every tower layer would.

Everything else — perimeter, solid, top, support and bridge widths and speeds,
accelerations, solid-layer counts, first layer — stays at Prusa's 0.25 values,
because those roles stay on the 0.25 tool. `ROLE_KEYS` lists which keys follow
which role, from `PrintRegion::flow`; `bridge_speed` is deliberately absent from
the solvable set, so moving solid infill to another tool refuses until someone
works through `Flow::bridging_flow`, whose width and height both come from the
nozzle rather than from a width key.

`infill_every_layers` is set per tier to the most PrusaSlicer will actually
combine: `PrintObject::combine_infill` (`PrintObject.cpp:3128-3132`) caps the
combined height at the **smaller of the infill and solid-infill extruders'
nozzles**, so keeping top surfaces on the 0.25 tool caps combining at 0.25 mm
however big the infill nozzle is. With a manual `infill_every_layers` that is
the whole of PrusaSlicer's limit. `combine_cap()` applies a second term of its
own — 0.75 × the infill nozzle, the value PrusaSlicer defaults
`max_layer_height` to when a printer leaves it unset (`Slicing.cpp:48`) — so a
combined extrusion is never taller than that nozzle is asked to lay down
anywhere else. That term is this repo's choice, not PrusaSlicer's, and it does
not bind here (0.75 × 0.4 = 0.3, against the 0.25 cap). The result is 3 layers
at 0.07, 2 at 0.10 and 1 — no combining — at 0.15. Combining also cuts the tool
changes a split role costs from one pair per layer to one pair per group, which
is most of why it is worth doing.

Two keys the moved role owns are **held** at the base tool's value, and
`build_layout()` refuses on any third one that appears: `infill_anchor` (1 mm
here, 2 at Prusa's HF0.4), because the anchor runs along the base tool's own
perimeter, and `infill_acceleration` (3000 against Prusa's 7000), because
acceleration is the one gantry both tools share and because that is what was
test printed. The second has a visible consequence: reaching 300 mm/s from rest
takes about 15 mm at 3000 mm/s², so the solved rate is a ceiling that short
infill moves do not reach. Both are listed in the bundle header with these
reasons (`ROLE_HELD`, and `ROLE_STEMS` is what makes the refusal general).

The binding tests only the tools the layout prints with:

```
printer_model=~/(COREONE_INDX8T|COREONE_INDX4T)/ and nozzle_diameter[0]==0.25
  and ! nozzle_high_flow[0] and nozzle_diameter[1]==0.4 and nozzle_high_flow[1]
```

The model clause is Prusa's own, kept from the base profiles. A tool the layout
never uses says nothing about the layout, so requiring a particular nozzle in a
spare dock would only make the profiles vanish when that dock changed. The
`printer_model` clause names both models because Prusa's does, so the same
profiles fit a 4T wired the same way — build the 4T printer preset for it.

#### What a layout refuses

| Refusal | Why |
|---|---|
| a base tool that is not in `LAYOUT_BASE` | the base tool's profiles supply the ladder and all the surface geometry; the wrong one would build the layout on the wrong nozzle |
| Prusa shipping a different number of base-tool profiles than there are tiers | which of them map to Detail / Balanced / Draft is a human decision |
| no `ROLE_ANCHOR` for a tool a role is moved onto | that role's widths and rate would have no source |
| a width, speed or layer height that is a percentage or `0` | neither can be carried to another nozzle's geometry |
| a non-per-extruder key the tools disagree on | it describes the machine; one value has to be chosen for it, with a reason |
| a per-extruder key one tool's preset leaves unset, or sets non-uniformly | there is no single value to fit that tool |
| `single_extruder_multi_material` not 0 | the per-tool filament shift and differing nozzles both depend on it |
| a start G-code without a per-tool `M862.1` | the firmware could not tell the layout is fitted as the G-code assumes |
| a tool count that does not match the model's preset | the layout names tools the printer does not have |

### The 1.0 mm nozzle is scaled, not sourced

PrusaResearch 2.5.12 has nothing at 1.0 mm: no INDX common, no CORE One 1.0 or
HF1.0 variant, no print, printer or filament profile, no commented draft and no
pressure-advance section. Everything else in this repo is read out of Prusa's
data; 1.0 cannot be, so it is the one size built by a rule instead.

**The rule.** Start from the 0.8 mm setup, built from Prusa's sources as usual.
Scale only the values that are lengths proportional to the nozzle, by
1.0 / 0.8 = 1.25, rounded half-up to 0.01. That is Prusa's own rounding: it
writes 1.125 × 0.6 = 0.675 as 0.68 in `*INDX_06hf_common*`. PrusaSlicer agrees
independently: for a width left unset it uses 1.125 × the nozzle diameter, which
at 1.0 is 1.125, the 1.13 below before rounding. Scaled:

- the eight line widths (0.9 → 1.13, first layer 1 → 1.25, top infill 0.8 → 1,
  support 0.65 → 0.81)
- the layer ladder (0.30 / 0.40 / 0.55 → 0.38 / 0.50 / 0.69)
- the printer's layer-height limits (max 0.6 → 0.75, min 0.2 → 0.25)

Values that only name the size are moved to 1.0 rather than scaled: the profile
binding (`nozzle_diameter[0]==1.0`), the G-code file name (`_1.0n_`), the
printer's `nozzle_diameter`, `printer_variant` and default profiles.

**Everything else is held at 0.8**, as this repo builds 0.8: the flow targets
the speeds are solved from; each filament's MVS (Prusament PLA 42, the INDX 0.4
value 28 scaled by Prusa's CORE One HF0.4 → HF0.8 pair, 24 → 36, the same method
that gives HF0.6 its test-printed 35; materials with no Prusa high-flow profile
fall back to the plain `@COREONE` → `@COREONE 0.8` pair, as each preset's notes
record); Prusa's own 0.8 pressure advance (`*C1INDX_<FAM>_08_PA*`); and the
retraction from Prusa's commented INDX HF0.8 printer draft. The per-size
`COMMON_EDITS` still apply, so `interlocking_beam_width` is 2 × nozzle: 2 at
1.0, where 0.8 builds 1.6.

What holding buys: the speeds are solved from 0.8's flow targets, so each
feature runs within about 6% below to 12% above 0.8's rate (the 5 mm/s
rounding), and the held filament MVS caps both sizes alike. The pressure
advance is 0.8's only because Prusa publishes none at 1.0. Prusa's own
0.4 → 0.6 → 0.8 trend falls, which suggests 1.0 wants less, so the held figure
probably over-retracts and must be re-measured.

The tools check the premise every time: if the PrusaResearch.ini they read
publishes anything at 1.0, whether a common, a PA section, a material family
section, a profile, a draft or a binding, all three refuse to scale and say
what they found.

Held does not mean right. Between 0.6 and 0.8 Prusa itself also changes, among
others, `top_solid_min_thickness` (0.9 → 1.2), `bottom_solid_min_thickness`,
`support_material_contact_distance`, `support_tree_tip_diameter`, the perimeter
accelerations and `fill_density`. At 1.0 all of these stay at their 0.8 values.
So does `first_layer_height` (0.2), which leaves it below the scaled
`min_layer_height` (0.25). PrusaSlicer 2.9.6 still slices it: `Print::validate`
only rejects a first layer taller than the nozzle, and the first layer is not
clamped to `min_layer_height`. Every scaled width also passes its width check
(wider than the layer, narrower than 3 × the nozzle).
This is all unvalidated, and the generators say so in every file they write.

### Prusa's commented-out drafts

Prusa keeps unreleased work in `PrusaResearch.ini` as commented-out sections —
`; [printer:...]` then `; key = value`. `load_drafts()` reads them, and they
count as sourced here: they are Prusa's own values, written for the INDX, and
usually more specific than anything a CORE One delta can supply. At 2.5.12
(unchanged from 2.5.11) they are:

| Draft | Used |
|---|---|
| 4 INDX printers: 8T/4T at `HF0.6`, `HF0.8` | **yes**, for the keys in `DRAFT_ADOPT` |
| 2 INDX printers: 8T/4T at `0.25` | **yes**, applied key for key; the CORE One 0.25 delta is only compared with it, on stdout |
| 2 INDX 0.25 filaments: `Prusament PLA` / `PETG` | **yes**, applied as written |
| 10 INDX print profiles at `HF0.5` / `HF0.6` / `HF0.8` (4 / 4 / 2) | no — HF0.5/HF0.6 restate the inherited speeds and set per-layer contact distances and solid counts; HF0.8 sets its own speeds but every one overruns the filaments |
| 3 INDX print profiles at `HF0.4` (Balanced Strength, Soluble Full, Soluble Interface) | no — `--std 0.4` copies only Prusa's four released HF0.4 prints |
| 416 INDX filament drafts at `HF0.5` / `HF0.6` / `HF0.8` — 135 / 144 / 137 sections, 144 distinct filaments | pressure advance only; see [Gaps in detail](#gaps-in-detail) |
| 624 other INDX filament drafts: 137 at `HF0.4`, 244 unsized standard-nozzle `<mat> @COREONEINDX`, 125 standard 0.6, 113 standard 0.8, 5 hidden | no — no generator reads them; the standard-0.4 ones disagree with the 0.4 bundle in places (Prusament PETG PA 0.048 against 0.058) |

For the high-flow printers, `build_printer_preset.py` applies the CORE One delta
first, then compares the result against Prusa's draft for that size. (`--std 0.25`
works differently: the draft is taken whole over the parent it names. The CORE
One HF0.4 → 0.25 delta is not applied; the generator prints each key where it
disagrees with the result, at 2.5.12 jerk (8,8 against 10,8) and
`retract_length` (0.8 against 0.7).) Where they disagree on a
key listed in `DRAFT_ADOPT` — the five retraction keys — the draft wins and the
generated header records it. A disagreement on **any other key stops the build**,
because Prusa having drafted a different value is evidence, not noise, and
absorbing it silently is exactly what this repo refuses to do.

That is why the committed HF0.6 printer preset carries `retract_length = 0.7`
rather than the `0.8` it inherits from Prusa's HF0.4 chain: 0.7 is what Prusa
drafted for an INDX at 0.6. It is also why `HF0.8` can be built at all — the five
retraction keys outside `TRANSFER` are all set in Prusa's HF0.8 draft.

### One fix to Prusa's printer G-code

Every printer preset here changes the dock-fan check in Prusa's INDX layer
G-code from `filament_type[N]=~/(PET|CPE|PCTG)/` to `=~/(PET|CPE|PCTG).*/`.
PrusaSlicer's `=~` must match the whole string, so the stock pattern never
matches `PETG`, the type of every PET-family INDX filament Prusa ships, and
multi-tool PETG prints never get the dock fan's S100 (of 255) from layer 3. Reported as
[prusa3d/PrusaSlicer-settings-prusa-fff#50](https://github.com/prusa3d/PrusaSlicer-settings-prusa-fff/issues/50);
the generator stops applying it once Prusa's pattern changes.

---

## Printer presets in detail

### Why they are flattened

These files are **fully flattened** on purpose. `load_presets` does
`preset.config = default_preset.config; preset.config.apply(config)` — a loose
user preset is applied over PrusaSlicer's defaults, *not* over its `inherits`
parent, so a delta-only file silently takes a default for every key it omits.

### Name collisions with Prusa

These presets carry Prusa's own names. If a Prusa profile update releases an
INDX printer of the same name, `PresetUpdater::priv::perform_updates`
(`PresetUpdater.cpp:982-994`) deletes the same-named file from `printer/`, and
does the same in `filament/` for the imported filament presets, after taking an
upgrade snapshot that still holds it. Enable Prusa's variant in the
Configuration Wizard then. Prusa already has commented-out drafts
for 8T and 4T at `0.25`, `HF0.6` and `HF0.8`, so the HF0.6, HF0.8 and 0.25
presets are all exposed to this. The standard 0.4 and HF1.0 are the ones Prusa
has no draft for.

### Other sizes and the 4T

Only the 8T is committed: HF0.6, HF0.8, HF1.0, 0.4, 0.25 and the `0.25+HF0.4`
mixed layout. Generate others with, for example:

```bash
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.5 -m 4T
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.6 -n 0.8 -n 1.0 -m 4T
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.4 -n 0.25 --std -m 4T
```

Each one names every key it changed and where the value came from, and says
loudly if the size has never been test printed. `default_print_profile` is built
from the same layer ladder `build_print_profiles.py` emits from, so it names a
profile that is in the bundle once `build_print_profiles.py` has been run with
the same `-n` (the committed bundle holds HF0.6, HF0.8, HF1.0, standard 0.4 and
the `0.25+HF0.4` layout; see [Adding a nozzle size](#adding-a-nozzle-size)). At
0.5 that is `0.20mm Balanced ★ @COREONEINDX HF0.5`, not the `0.25mm` of the 0.6
lineup.

`-m 4T` applies to `-n` sizes only. A layout declares a nozzle per tool and its
print profiles bind on those tools by index, so it is tied to one tool count:
`--layout` with a conflicting `-m` refuses rather than writing an 8-tool preset
under a 4T name. A four-tool arrangement is a separate `LAYOUTS` entry, and its
print profiles would need their own binding; the `0.25+HF0.4` profiles already
accept a 4T printer, because the `printer_model` clause they keep from Prusa
names both models.

### Setting a printer up by hand, every size

For a mixed layout, whose values differ from tool to tool, see
[Mixed nozzles](../README.md#mixed-nozzles-025-on-tool-1-hf04-on-the-rest)
in the README.

**Printer Settings → Extruder 1** to **Extruder 8** (1 to 4 on the 4T), Expert
mode on, the same on every tool:

| Field | 0.5 mm | 0.6 mm |
|---|---|---|
| Nozzle diameter | `0.5` | `0.6` |
| High flow nozzle | checked | checked |
| Max layer height | `0.32` | `0.40` |
| Min layer height | `0.07` | `0.15` |
| Retraction length | `0.8` (unchanged) | `0.7` |

Prusa's own values, from `Prusa CORE One HF0.5 nozzle` and
`Prusa CORE One HF0.6 nozzle`, except the 0.6 retraction length, which comes
from Prusa's commented INDX HF0.6 printer draft (`DRAFT_ADOPT`; see
[Prusa's commented-out drafts](#prusas-commented-out-drafts)). The generated presets also set `printer_variant`
(`HF0.5`, `HF0.6`, and so on), but PrusaSlicer shows no field for it (it is not
in `Tab.cpp`) and nothing filters a user preset on it, so a hand-made printer can
leave it alone. Prusa also sets `wipe = 1` above 0.4; the
generator carries that across, so set it if you are matching by hand.

0.8 is not in the table because all five of its retraction keys differ. Prusa's
HF0.4 → HF0.8 delta moves five keys that sit outside `TRANSFER`, the reviewed
whitelist of size-dependent keys, so the delta never transfers them:
`retract_length`, `retract_speed`, `deretract_speed`, `retract_lift`,
`retract_before_wipe`. On three of them (`retract_length`, `retract_speed`,
`deretract_speed`) INDX also diverged from CORE One at 0.4, so even a widened
`TRANSFER` would not reproduce Prusa's INDX values; on `retract_lift` and
`retract_before_wipe` INDX and CORE One agreed. Prusa
answers them itself: its commented `[printer:Prusa CORE One INDX 8T HF0.8
nozzle]` draft sets all five for an INDX toolchanger — `retract_length 0.6`,
`retract_speed 25`, `deretract_speed 15`, `retract_lift 0.25`,
`retract_before_wipe 50%` — so the generator builds 0.8 from the draft and marks
it unvalidated. By hand, use the other four (`retract_lift` is grayed out while
**Use ramping lift** is on, as it is on every INDX tool, so leave it) along with
nozzle diameter `0.8`,
max layer height `0.6`, min `0.2` and `wipe` on.

1.0 has no Prusa values to copy. The generated preset is the 0.8 one above
with nozzle diameter `1.0`, max layer height `0.75` and min `0.25`; retraction
and `wipe` stay at 0.8's.

For a standard nozzle, uncheck **High flow nozzle** on every tool. For 0.25,
also set nozzle diameter `0.25`, retraction length `0.7` (leave lift height:
ramping lift grays it out),
and layer heights `0.05` to `0.15`: the values in Prusa's own unreleased INDX
0.25 printer.

---

## Adding a nozzle size

Everything is driven by the table in `tools/nozzles.py`.

```bash
python3 tools/build_print_profiles.py <PrusaResearch.ini> /dev/null --list
```

| Size | Upstream common | Layers | Status |
|---|---|---|---|
| 0.25 | `*INDX_025_common*` | 0.07 / 0.12 / 0.15 | shipped by Prusa, not built |
| 0.3 | `*INDX_03_common*` | 0.12 / 0.16 / 0.20 | shipped by Prusa, not built; no such INDX nozzle |
| 0.5 | `*INDX_05hf_common*` | 0.15 / 0.20 / 0.25 | **unvalidated** targets |
| 0.6 | `*INDX_06hf_common*` | 0.20 / 0.25 / 0.32 | validated, in use |
| 0.8 | `*INDX_08hf_common*` | 0.30 / 0.40 / 0.55 | built (bundle 0.6.0); **unvalidated** targets |
| 1.0 | `*INDX_08hf_common*`, scaled ×1.25 | 0.38 / 0.50 / 0.69 | **scaled from 0.8**, unvalidated; [no Prusa source](#the-10-mm-nozzle-is-scaled-not-sourced) |

Prusa renamed the high-flow commons (`*INDX_06_common*` became
`*INDX_06hf_common*`) by PrusaResearch 2.5.11.

To build more than one size into the bundle — and note that the bundle is
**replaced**, not merged, so every command that writes `vendor/hyigerINDX.ini`
has to name every family it should still contain, the `--layout` included:

```bash
python3 tools/build_print_profiles.py <PrusaResearch.ini> vendor/hyigerINDX.ini -n 0.5 -n 0.6 -n 0.8 -n 1.0 --std 0.4 --layout 0.25+HF0.4
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.5
python3 tools/derive_filaments.py <PrusaResearch.ini> filaments/hyigerINDX-0.5-filaments.ini -n 0.5
```

Layer-height ladders are Prusa's own CORE One ladders for the same nozzle, read
straight out of the shipping print profiles. Where Prusa ships both a standard
and a high-flow variant at one diameter the basis is chosen per size, not by one
rule. 0.6 uses `@COREONE HF0.6`, the variant matching the nozzle. 0.5 uses
0.15/0.20/0.25 from the standard `@COREONE 0.5` ladder, because `@COREONE HF0.5`
has nothing below 0.20 — and those three rungs are also exactly the first three of
Prusa's own commented `@COREONEINDX HF0.5` print draft lineup. At 0.8 the two
ladders are identical.

### There is no 0.2 or 0.3 mm

There is no 0.2 mm or 0.3 mm INDX nozzle. The smallest INDX common Prusa defines
is **0.25 mm** (`*INDX_025_common*`), and `--nozzle 0.2` is rejected. Prusa does
define a 0.3 common and three 0.3 print profiles (below), but they are
scaffolding: no 0.3 INDX printer exists, released or drafted.

### Prusa ships 0.25 and 0.3

Since PrusaResearch 2.5.x Prusa ships its own `@COREONEINDX 0.25` and
`@COREONEINDX 0.3` print profiles. They bind on diameter alone, so any INDX
printer with that nozzle picks them up; only 0.25 is a real INDX nozzle. `build_print_profiles.py` refuses both
sizes rather than duplicate them.

Filaments are different. `derive_filaments.py` scales MVS off a CORE One
high-flow pair, and Prusa publishes none below 0.4, so it refuses 0.25 and 0.3.
`derive_std_filaments.py` builds a **standard** 0.25 without scaling, from the
0.25 drafts and INDX 0.25 or standard bases Prusa already has (see
[Standard nozzles](#standard-nozzles-from-prusas-own-pieces)).

### Standard nozzles

```bash
python3 tools/build_print_profiles.py <PrusaResearch.ini> vendor/hyigerINDX.ini -n 0.6 -n 0.8 -n 1.0 --std 0.4 --layout 0.25+HF0.4
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.4 -n 0.25 --std
python3 tools/derive_std_filaments.py <PrusaResearch.ini> filaments/hyigerINDX-0.4-filaments.ini -n 0.4
python3 tools/derive_std_filaments.py <PrusaResearch.ini> filaments/hyigerINDX-0.25-filaments.ini -n 0.25
```

Only sizes with a Prusa source are accepted: 0.4 (Prusa's HF0.4 prints and
the CORE One STD 0.4 printer) and 0.25 (Prusa's INDX 0.25 printer draft and
0.25 filament bases). Anything else is refused.

### Adding a mixed tool layout

A layout is an entry in `LAYOUTS` in `tools/nozzles.py`, not a nozzle size. It
names the nozzle fitted to each tool as the printer presets name their variants
(`0.25`, `HF0.4`), pins every print role to a 1-based tool, and records its own
print-key decisions in `extra` with a reason each.

```bash
python3 tools/build_print_profiles.py <PrusaResearch.ini> vendor/hyigerINDX.ini -n 0.6 -n 0.8 -n 1.0 --std 0.4 --layout 0.25+HF0.4
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ --layout 0.25+HF0.4
```

No filament work: PrusaSlicer filters each tool's filament list by that tool's
own nozzle, so the existing bundles cover a layout as they are
([why](#mixed-tool-layouts--composed-not-derived)).

A new layout needs, as well as the entry:

- the tool that prints perimeters listed in `LAYOUT_BASE`
  (`build_print_profiles.py`), naming the Prusa profile suffix its tiers come
  from — the base tool's profiles supply the ladder and all the surface geometry;
- a `ROLE_ANCHOR` entry for every tool a role is moved **onto**, naming a Prusa
  profile that ships at that nozzle, since that is where the moved role's widths
  and its volumetric rate come from;
- a printer preset buildable here for each tool's nozzle, because the layout's
  printer preset is composed from them;
- `validated=False` until it has been printed.

Each layout is one tool arrangement. The bindings test tools by index, so
swapping which dock holds which nozzle is a different layout, not the same one.

---

## Design notes

### How these load as system presets

The bundle sets `templates_profile = 1`. PrusaSlicer normally rejects a preset
whose vendor differs from the active printer's vendor:

```cpp
// Preset.cpp
if (preset.vendor != nullptr && preset.vendor != active_printer.vendor
    && !preset.vendor->templates_profile)
    return false;
```

Your INDX printer resolves to the Prusa Research vendor, so without that flag
these profiles would be invisible. The flag also exempts the bundle from needing
its own `[printer_model:]` section, which is what lets it attach to the Prusa
printer instead of cloning it. Prusa's own `Templates.ini` uses the same
mechanism.

### One vendor bundle, filaments per size

One vendor bundle holds every nozzle size. PrusaSlicer takes the vendor ID from
the bundle's filename stem, and preset names must be unique across all vendors,
so a second bundle would register a second vendor and risk duplicate-preset-name
errors. Filaments ship one bundle per size, since you only want the ones you
have toolheads for.

### Why a filament bundle is needed at all

Selecting an INDX printer at 0.6 mm leaves you with **no filament profiles
whatsoever**. Three separate mechanisms each rule out one source:

| Source | Count | Result | Reason |
|---|---|---|---|
| `@COREONEINDX HF0.4` | 20 | excluded | all but FLEX and TPU 95A require `nozzle_high_flow[0]`; 11 pin `nozzle_diameter[0]==0.4` and the PET/ABS/BVOH/PVA nine bind by exclusion (`!=0.8 and !=0.6 and !=0.5`), which does not name 1.0, so those nine do reach an HF1.0 printer |
| `@COREONE HF0.6` | 143 | excluded | `printer_model` uses `regex_match`, so `COREONE_INDX8T` does not match `/(COREONE\|COREONEOAK\|…)/` |
| `Templates.ini` | 201 | excluded | every profile carries `printer_notes!~/.*NO_TEMPLATES.*/`, and Prusa puts `NO_TEMPLATES` in the INDX printer notes |

Counts are from PrusaResearch 2.5.12 and Templates.ini 2.0.4. A standard nozzle
hits the same wall one step earlier: 18 of the 20 INDX filaments also require
`nozzle_high_flow[0]`, leaving only Generic FLEX and Prusament TPU 95A on a
standard 0.4, and none on a 0.25.

The last one is easy to get wrong. `printer_notes` holds real newlines after
`unescape_string_cstyle`, so under `std::regex` the pattern `.*NO_TEMPLATES.*`
would fail and the exclusion would silently not fire. But `USE_CPP11_REGEX` is
commented out in `PlaceholderParser.cpp`, so PrusaSlicer builds against
**boost::regex**, where `.` matches newline unless `match_not_dot_newline` is
passed — and no match flags are passed. The exclusion fires as intended. The
same detail is what makes the ~400 other `printer_notes=~/…/` conditions in
PrusaResearch.ini work at all.

### Why filaments aren't in the vendor bundle

Two things happen to filament presets in a templates bundle that don't happen to
print presets:

1. `PresetBundle.cpp` appends ` @Template` to every filament preset name.
2. `Preset.cpp` hides them entirely when the `no_templates` preference is set.

Print presets are exempt from both of those, so they stay in the vendor bundle
while filaments ship as an importable config bundle.

There is a third gate, and it is *not* type-aware: `PresetComboBoxes.cpp` fills
the preset combo boxes only `if (allow_templates)` for any preset whose vendor is
a templates profile (lines 323/335 in `PresetComboBox::update`, 1138 in
`PlaterPresetComboBox::update`, 1419 in `TabPresetComboBox::update`), where
`allow_templates` is `!app_config->get_bool("no_templates")`. So ticking
**Preferences → General → "Suppress ' Template ' filament presets"** hides this
bundle's *print* profiles too. It is off by default; if the print profiles
vanish, check it first.

A fourth gate is type-agnostic too. `PresetCollection::update_compatible_internal`
(`Preset.cpp:1387-1398`) marks a templates-vendor preset incompatible whenever a
compatible non-templates preset has the same alias, the name before `@`. The
standard 0.4 print profiles share all four aliases with Prusa's HF0.4 prints. It
never fires only because the two sets bind on opposite `nozzle_high_flow[0]`
tests, so no printer accepts both.

---

## Gaps in detail

The README lists these in short. Here is each one in full.

- **Speeds are derived, not sourced.** If Prusa completes the speed pass on the
  per-nozzle commons, prefer theirs.
- **Mixed nozzles are Prusa's experimental workflow.** The `0.25+HF0.4` layout
  is test printed (2026-10-24, a 0.25 standard nozzle on tool 1 and a 0.4 CHT on
  tool 2), but Prusa warns that some nozzle combinations can fail, and this repo
  carries only that one pair. Every value in it is Prusa's own except
  `infill_speed`, which is solved from the 24.4 mm³/s Prusa's own starred HF0.4
  profile runs infill at — a ceiling, since `infill_acceleration` is held at the
  base tool's 3000. The role split costs a purge per tool change, which infill
  combining reduces but does not remove; it goes to the printer's Purge Station,
  not to a wipe tower, because every INDX profile ships `wipe_tower = 0`, which
  is also why `_WIPE_TOWER_NOZZLE_DIAMETER_DIFFER` never fires as shipped. The
  layout's
  profiles also carry Prusa's upstream `top solid_infill_speed` typo as written,
  so top solid infill runs at the inherited 100 mm/s rather than the 60 Prusa
  evidently meant — the same as on the plain 0.25 setup, which was test printed
  that way.
- **Prusa's commented HF filament drafts are reported, not adopted.** Prusa keeps
  144 commented-out `@COREONEINDX HF0.6` filament drafts. Four figures in them —
  three MVS and one cooling figure — disagree with what the ratio rule derives:
  Prusament PLA MVS 30 against 35 and `slowdown_below_layer_time` 15 against 9,
  Generic FLEX 3.5 against 3, Prusament TPU 95A 4 against 3. The ratio rule wins
  because each of the three MVS figures, although typed in the draft's own body,
  restates the value its CORE One parent already supplies (FLEX 3.5, PLA 30,
  TPU 4), and taking it would swap the INDX flow baseline (2 / 28 / 2) for the
  CORE One one — and HF0.6 is test printed at 35. These are Prusa's own numbers,
  though, so `derive_filaments.py` prints every divergence the drafts type on a
  watched key (MVS, `slowdown_below_layer_time`) instead of hiding it. The same
  holds at HF0.8, where Prusa's drafts type a higher MVS for Generic FLEX (7.5
  against 6) and Prusament TPU 95A (8 against 6); both restate their CORE One
  0.8 parent exactly, against an INDX 0.4 baseline of 2. Drafts
  that differ only through inherited values (Prusament ASA, PC Blend CF, Generic
  PETG, Generic PLA) are not reported. Pressure advance is the exception: it is
  taken from Prusa's figures, drafted or not.
- **HF0.6, standard 0.4 and standard 0.25 are validated**, meaning test
  printed on an INDX; HF0.8 and HF1.0 are not. Every standard value is Prusa's,
  but sourced is not printed, so the standard sizes carried an UNVALIDATED
  banner until they were printed (dropped October 2026, vendor bundle 0.6.1).
  Every generator marks an unvalidated size in the file it writes as well as on
  stdout. 0.5 and 0.8 flow targets are extrapolated. The 0.8 case is weakest:
  Prusa's `@COREONE 0.8` MVS figures are for a standard brass nozzle
  (Prusament PLA = 19, *below* the HF0.6 figure of 30) and don't transfer to a
  high-flow CHT. Its *printer* preset is better founded (Prusa
  drafted one) but still unprinted. **HF1.0** is weaker still: it rests on the
  0.8 numbers plus a scaling rule, with no Prusa source at 1.0 at all. See
  [The 1.0 mm nozzle is scaled, not sourced](#the-10-mm-nozzle-is-scaled-not-sourced) for what is held at 0.8 and
  what Prusa varies between sizes that is held anyway.
- **Prusa's own HF0.4 filaments reach HF1.0.** Prusa binds its PET, ABS, BVOH
  and PVA `@COREONEINDX HF0.4` presets by excluding 0.5, 0.6 and 0.8 rather than
  by naming 0.4 (see
  [Why a filament bundle is needed at all](#why-a-filament-bundle-is-needed-at-all)),
  and 1.0 is not in that list, so up to nine of them pass. They carry 0.4 speed
  limits and pressure advance (Prusament PETG: MVS 20 and PA 0.058, against 31
  and 0.02 in the HF1.0 preset). `derive_filaments.py -n 1.0` lists them.
  Prusa's bindings can't be changed from this repo.
- **Three tiers per high-flow size, not four.** Prusa's 0.4 lineup has a `Fine` as well.
  Add it in `nozzles.py`.
- **Draft keeps the common extrusion width.** Prusa's 0.4 Draft widens
  extrusions ~11% over its common parent. Left alone because 0.68 at 0.32 mm is
  already a healthy 2.1:1 aspect ratio, and widening compounds flow demand.
- **High-flow filament binding includes `nozzle_high_flow[0]`.** That is the
  test Prusa's own sized HF filament families already use; it is an addition
  only for Generic FLEX and Prusament TPU 95A, whose Prusa 0.6 family binds on
  diameter alone. The HF0.6 *print* profiles bind on diameter alone, as
  `*INDX_06hf_common*` does. It keeps the HF0.6 filaments off a standard 0.6
  nozzle, which nothing here supports.
- **Standard 0.4 pressure advance is the HF0.4 preset's own value.** Prusa ships
  no concrete INDX standard-0.4 preset. For the PET, ABS and PC families the
  standard and high-flow 0.4 bases inherit the same `*C1INDX_<fam>_04_PA*`
  section; only the PLA family has no INDX standard figure at all. See
  [Pressure advance by size](#pressure-advance-by-size). Calibrate
  it.
- **The standard 0.25 rests on unreleased Prusa work.** Its printer is Prusa's
  commented-out draft, and Prusa's 0.25 print profiles have no released printer
  behind them. One of their keys is misspelled upstream (`top solid_infill_speed`,
  with a space), so top solid infill runs at the inherited 100 mm/s instead of
  the 60 every other Prusa 0.25 profile uses. Set it by hand if top surfaces
  suffer.
- **Prusa may release the same names.** The standard 0.4 print profiles are
  named the way Prusa would name them. If Prusa ships identically named
  presets, PrusaSlicer reports duplicates across the two vendor bundles; remove
  this bundle's copies then. The printer and filament presets are exposed
  differently. Prusa already has commented drafts with their names (8T/4T
  printers at 0.25, HF0.6 and HF0.8; filaments at HF0.6 and 0.25), and the
  update that releases one deletes your same-named file. See
  [Name collisions with Prusa](#name-collisions-with-prusa).
- **Generic PVA is not built at any size.** Prusa added it in 2.5.12 as an
  INDX-only preset (Verbatim BVOH plus its own overrides), with no CORE One PVA
  behind it. `derive_filaments.py` has no CORE One pair to scale its MVS by and
  skips it; `derive_std_filaments.py` skips it by name (`STD_SKIP`), so any
  *other* new material without a CORE One standard profile still stops the
  build. Prusa's own HF0.4 preset covers a high-flow 0.4.
- **The personal presets in `personal/` don't import.** They carry two keys no
  PrusaSlicer defines, so Import Config Bundle rejects them. See
  `personal/README.md`; the fix belongs in the Filament DB exporter.

### Pressure advance by size

The shipped figure is Prusa's own for your nozzle where Prusa publishes one,
never a scaled one. At HF0.6 it comes from `*C1INDX_<FAM>_06_PA*`, or from
Prusa's commented HF0.6 draft where that is more specific. Prusa's INDX PA
*falls* as the nozzle grows (PLA 0.031 at 0.4, 0.02 at 0.6), so do not assume
a bigger nozzle wants more. A CHT does have a longer, split melt path than the
Nextruder these descend from, so a measured value may land above Prusa's.

On a standard 0.4 the pressure advance is the INDX HF0.4 preset's own value.
Prusa ships no concrete INDX standard-0.4 preset; for PET, ABS and PC its
standard and high-flow 0.4 bases share one PA base (`*C1INDX_PET_04_PA*` 0.048,
`_ABS_` 0.02, `_PC_` 0.05) and each concrete preset overrides it, so the
preset's own figure is kept. Only the PLA family has no INDX standard figure at
all. On a 0.25 it is Prusa's 0.25 value (PLA 0.1, PETG 0.15, PC 0.14,
ABS/ASA/BVOH 0.09), about two to four and a half times the 0.4 figure, so widen a PA test's range
to about 0.2. At HF0.8 it is Prusa's own 0.8 figure (`*C1INDX_<FAM>_08_PA*`),
lower again than 0.6's (PLA 0.013, PET 0.02, ABS 0.01, PC 0.016). At HF1.0 it
is that same 0.8 figure, held,
because Prusa publishes none at 1.0; given Prusa's falling trend, expect your
measured value to land below it. See
[The 1.0 mm nozzle is scaled, not sourced](#the-10-mm-nozzle-is-scaled-not-sourced).
