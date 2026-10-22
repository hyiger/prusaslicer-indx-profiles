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

### Filament presets (1.0 mm)

The filaments are exactly the HF0.8 presets, rebound to a 1.0 nozzle, so max
volumetric speed (MVS, mm³/s) and pressure advance (PA) are 0.8's:

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
rather than reaching a standard nozzle. A per-nozzle common Prusa later puts
under a standard base may change only keys reviewed into `COMMON_ADOPT`, and
the bundle header and `filament_notes` record them.

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

Only the 8T is committed. Generate others with:

```bash
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.5 -m 4T
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.8
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.4 -n 0.25 --std -m 4T
```

Each one names every key it changed and where the value came from, and says
loudly if the size has never been test printed. `default_print_profile` is built
from the same layer ladder `build_print_profiles.py` emits from, so it names a
profile that is in the bundle once `build_print_profiles.py` has been run with
the same `-n` (the committed bundle holds only HF0.6, HF1.0 and standard 0.4; see
[Adding a nozzle size](#adding-a-nozzle-size)). At 0.5 that is
`0.20mm Balanced ★ @COREONEINDX HF0.5`, not the `0.25mm` of the 0.6 lineup.

### Setting a printer up by hand, every size

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
it unvalidated. By hand, use the other four (`retract_lift` is greyed out while
**Use ramping lift** is on, as it is on every INDX tool, so leave it) along with
nozzle diameter `0.8`,
max layer height `0.6`, min `0.2` and `wipe` on.

1.0 has no Prusa values to copy. The generated preset is the 0.8 one above
with nozzle diameter `1.0`, max layer height `0.75` and min `0.25`; retraction
and `wipe` stay at 0.8's.

For a standard nozzle, uncheck **High flow nozzle** on every tool. For 0.25,
also set nozzle diameter `0.25`, retraction length `0.7` (leave lift height:
ramping lift greys it out),
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
| 0.8 | `*INDX_08hf_common*` | 0.30 / 0.40 / 0.55 | **unvalidated** targets |
| 1.0 | `*INDX_08hf_common*`, scaled ×1.25 | 0.38 / 0.50 / 0.69 | **scaled from 0.8**, unvalidated; [no Prusa source](#the-10-mm-nozzle-is-scaled-not-sourced) |

Prusa renamed the high-flow commons (`*INDX_06_common*` became
`*INDX_06hf_common*`) by PrusaResearch 2.5.11.

To build more than one size into the bundle:

```bash
python3 tools/build_print_profiles.py <PrusaResearch.ini> vendor/hyigerINDX.ini -n 0.6 -n 0.8 -n 1.0 --std 0.4
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.8
python3 tools/derive_filaments.py <PrusaResearch.ini> filaments/hyigerINDX-0.8-filaments.ini -n 0.8
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
python3 tools/build_print_profiles.py <PrusaResearch.ini> vendor/hyigerINDX.ini -n 0.6 -n 1.0 --std 0.4
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.4 -n 0.25 --std
python3 tools/derive_std_filaments.py <PrusaResearch.ini> filaments/hyigerINDX-0.4-filaments.ini -n 0.4
python3 tools/derive_std_filaments.py <PrusaResearch.ini> filaments/hyigerINDX-0.25-filaments.ini -n 0.25
```

Only sizes with a Prusa source are accepted: 0.4 (Prusa's HF0.4 prints and
the CORE One STD 0.4 printer) and 0.25 (Prusa's INDX 0.25 printer draft and
0.25 filament bases). Anything else is refused.

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
  watched key (MVS, `slowdown_below_layer_time`) instead of hiding it. Drafts
  that differ only through inherited values (Prusament ASA, PC Blend CF, Generic
  PETG, Generic PLA) are not reported. Pressure advance is the exception: it is
  taken from Prusa's figures, drafted or not.
- **Only HF0.6 is validated.** The standard 0.4 and 0.25 values are all
  Prusa's, but sourced is not printed: they carry an UNVALIDATED banner until
  test printed on an INDX. Every generator marks an unvalidated size in the file
  it writes as well as on stdout. 0.5 and 0.8 flow targets are extrapolated. The
  0.8 case is weakest: Prusa's `@COREONE 0.8` MVS figures are for a standard
  brass nozzle (Prusament PLA = 19, *below* the HF0.6 figure of 30) and don't
  transfer to a high-flow CHT. Its *printer* preset is better founded — Prusa
  drafted one — but still unprinted. **HF1.0** is weaker still: it rests on the
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
to about 0.2. At HF1.0 it is Prusa's 0.8 figure (`*C1INDX_<FAM>_08_PA*`), held,
because Prusa publishes none at 1.0; given Prusa's falling trend, expect your
measured value to land below it. See
[The 1.0 mm nozzle is scaled, not sourced](#the-10-mm-nozzle-is-scaled-not-sourced).
