# PrusaSlicer profiles for the Prusa CORE One INDX

Print and filament profiles for running INDX toolheads at nozzle sizes Prusa
doesn't ship profiles for.

Prusa's only INDX printer is **HF0.4** (high-flow 0.4 mm). `variants = HF0.4`
is the entire variant list for both `COREONE_INDX8T` and `COREONE_INDX4T`.
Prusa also ships print profiles for 0.25 and 0.3 mm, but no printer for them,
and its INDX filaments bind to a high-flow 0.4 nozzle. Fit any other toolhead
and the print profile list narrows to nothing and the filament dropdown empties.

The print profiles here install as **read-only system presets**: lock icon,
reset-to-system-value arrows, no clutter in your own preset list.

**Currently built:**

- **HF0.6**: high-flow 0.6 mm (Bondtech CHT).
- **0.4 standard**: a standard (non-high-flow) 0.4 mm nozzle. Not yet test printed.
- **0.25 standard**: a standard 0.25 mm nozzle, using Prusa's own 0.25 print profiles. Not yet test printed.

The generators handle other high-flow sizes too; see
[Adding a nozzle size](#adding-a-nozzle-size).

---

## What's here

```
vendor/
  hyigerINDX.ini                  vendor bundle — print profiles, all sizes
  hyigerINDX.idx                  version index
filaments/
  hyigerINDX-0.6-filaments.ini    19 filament presets for HF0.6, for import
  hyigerINDX-0.4-filaments.ini    17 filament presets for a standard 0.4
  hyigerINDX-0.25-filaments.ini   14 filament presets for a standard 0.25
personal/
  *.ini                           the author's own presets for filaments Prusa
                                  doesn't publish — not generated, not derived
                                  from PrusaResearch.ini, and not importable as
                                  a config bundle (see personal/README.md)
printer/
  Prusa CORE One INDX 8T HF0.6 nozzle.ini   flattened printer presets
  Prusa CORE One INDX 8T 0.4 nozzle.ini
  Prusa CORE One INDX 8T 0.25 nozzle.ini
tools/
  nozzles.py                      per-nozzle configuration table
  build_print_profiles.py         generates the vendor bundle
  derive_filaments.py             generates high-flow filament presets
  derive_std_filaments.py         generates standard-nozzle filament presets
  build_printer_preset.py         generates printer presets
```

One vendor bundle holds every nozzle size. The filename becomes the vendor ID,
so a second bundle would register a second vendor and risk duplicate-preset-name
errors. Filaments ship per size, since you only want the ones you have toolheads
for.

### Print profiles (0.6 mm)

| Profile | Layer | Perim | Ext perim | Infill | Solid | Top solid |
|---|---|---|---|---|---|---|
| `0.20mm Detail` | 0.20 | 205 | 155 | 235 | 210 | 110 |
| `0.25mm Balanced ★` | 0.25 | 165 | 130 | 190 | 170 | 90 |
| `0.32mm Draft` | 0.32 | 135 | 100 | 155 | 140 | 75 |

Speeds in mm/s. The star marks the recommended default, matching Prusa's own
convention (`0.10mm Fine` / `0.15mm Detail` / `0.20mm Balanced ★` /
`0.25mm Draft` at 0.4 mm).

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

### Print profiles (standard 0.4 mm)

Prusa's own four INDX HF0.4 print profiles, `0.10mm Fine`, `0.15mm Detail`,
`0.20mm Balanced ★` and `0.25mm Draft`, each named `@COREONEINDX 0.4`.
They are unchanged except that they bind to a standard nozzle
(`! nozzle_high_flow[0]`) instead of a high-flow one. On a standard nozzle the
filament's max volumetric speed is what slows them down.

A standard 0.25 needs no print profiles from here: Prusa ships
`0.07mm Extra Fine`, `0.10mm Fine ★` and `0.15mm Detail @COREONEINDX 0.25`.

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

## Requirements

- PrusaSlicer **2.9.6** or newer
- Prusa Research vendor bundle **config_version 2.5.12** or newer. Everything
  here was generated from 2.5.12, and the standard 0.25 setup uses the 0.25
  print profiles Prusa ships.
- INDX firmware **6.9.2** or newer, the version Prusa's 2.5.12 G-code asks for:
  the printer presets' start G-code carries `M115 U6.9.2+16336`, which warns on
  older firmware.
- A CORE One INDX 8T or 4T

Your PrusaSlicer data directory:

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/PrusaSlicer` |
| Windows | `%APPDATA%\PrusaSlicer` |
| Linux | `~/.config/PrusaSlicer` |

---

## Installation

### 1. Install the print profiles

Copy both files into the `vendor` folder of your data directory and restart.

```bash
# macOS
cp vendor/hyigerINDX.ini vendor/hyigerINDX.idx \
   ~/Library/Application\ Support/PrusaSlicer/vendor/
```

```powershell
# Windows
Copy-Item vendor\hyigerINDX.* "$env:APPDATA\PrusaSlicer\vendor\"
```

```bash
# Linux
cp vendor/hyigerINDX.ini vendor/hyigerINDX.idx ~/.config/PrusaSlicer/vendor/
```

No Configuration Wizard step. PrusaSlicer loads every `.ini` in `vendor/` at
startup, and these attach themselves to your existing Prusa INDX printer.

### 2. Install the printer preset

**Not optional.** Prusa declares `variants = HF0.4` for both INDX models, so
there is no HF0.6 or standard-nozzle printer to pick in the Configuration
Wizard. The print profiles bind on the nozzle (`nozzle_diameter[0]==0.6`, or
`nozzle_diameter[0]==0.4 and ! nozzle_high_flow[0]` for a standard 0.4); with
Prusa's HF0.4 printer selected they load correctly and are then filtered out of
the dropdown, which looks exactly like the bundle having failed to install.

Copy the preset for each nozzle you fit into `printer/` in your data directory:

```bash
# macOS
cp "printer/Prusa CORE One INDX 8T HF0.6 nozzle.ini" \
   "printer/Prusa CORE One INDX 8T 0.4 nozzle.ini" \
   "printer/Prusa CORE One INDX 8T 0.25 nozzle.ini" \
   ~/Library/Application\ Support/PrusaSlicer/printer/
```

These presets carry Prusa's own names. `load_presets` skips a user preset whose
name matches an already-loaded system preset, so if Prusa releases an INDX
printer of the same name, PrusaSlicer loads Prusa's and skips yours — enable that
variant in the Configuration Wizard then. Prusa already has commented-out drafts
for 8T and 4T at `0.25`, `HF0.6` and `HF0.8`, so the HF0.6, HF0.8 and 0.25
presets are all exposed to this. The standard 0.4 is the one Prusa has no draft
for.

Quit and relaunch, then select it. It appears as a normal user preset that
inherits from Prusa's shipping 0.4 profile, so every changed value keeps its
reset-to-system arrow.

These files are **fully flattened** on purpose. `load_presets` does
`preset.config = default_preset.config; preset.config.apply(config)` — a loose
user preset is applied over PrusaSlicer's defaults, *not* over its `inherits`
parent, so a delta-only file silently takes a default for every key it omits.

Only the 8T is committed. Generate others with:

```bash
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.5 -m 4T
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.8
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.4 -n 0.25 --std -m 4T
```

Each one names every key it changed and where the value came from, and says
loudly if the size has never been test printed. `default_print_profile` is built
from the same layer ladder `build_print_profiles.py` emits from, so it always
names a profile that is actually in the bundle — at 0.5 that is
`0.20mm Balanced ★ @COREONEINDX HF0.5`, not the `0.25mm` of the 0.6 lineup.

#### Or by hand

**Printer Settings → General**, Expert mode on, applied to **every tool**:

| Field | 0.5 mm | 0.6 mm |
|---|---|---|
| Nozzle diameter | `0.5` | `0.6` |
| High flow nozzle | checked | checked |
| Max layer height | `0.32` | `0.40` |
| Min layer height | `0.07` | `0.15` |
| `printer_variant` | `HF0.5` | `HF0.6` |

Prusa's own values, from `Prusa CORE One HF0.5 nozzle` and
`Prusa CORE One HF0.6 nozzle`. Prusa also sets `wipe = 1` above 0.4; the
generator carries that across, so set it if you are matching by hand.

0.8 is not in the table because its retraction differs as well. Prusa's
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
it unvalidated. By hand, use those five values along with nozzle diameter `0.8`,
max layer height `0.6`, min `0.2`, `printer_variant HF0.8` and `wipe` on.

For a standard nozzle, uncheck **High flow nozzle** on every tool and set
`printer_variant` to `0.4`. For 0.25, set `printer_variant` to `0.25` instead,
plus nozzle diameter `0.25`, retraction length `0.7`, lift Z `0.15`, and layer
heights `0.05` to `0.15`: the values in Prusa's own unreleased INDX 0.25
printer.

### 3. Import the filament presets

**File → Import → Import Config Bundle…** and select the file for your nozzle
size: `filaments/hyigerINDX-0.6-filaments.ini`, `-0.4-` or `-0.25-`.

These import as user presets, which is deliberate — see
[Why filaments aren't in the vendor bundle](#why-filaments-arent-in-the-vendor-bundle).

### 4. Verify

Select the printer preset from step 2, not the shipping `HF0.4` one. You
should see:

| Printer | Print profiles | Filaments |
|---|---|---|
| HF0.6 | 3, with a lock icon | 19 |
| 0.4 (standard) | 4, with a lock icon | 17, plus Prusa's Generic FLEX and TPU 95A |
| 0.25 (standard) | Prusa's 3 | 14 |

If the print profiles don't appear, check `nozzle_diameter` and **High flow
nozzle** really are set on every tool. The print profiles bind on
`printer_model=~/(COREONE_INDX8T|COREONE_INDX4T)/ and nozzle_diameter[0]==0.6`
(HF0.6) or `... and nozzle_diameter[0]==0.4 and ! nozzle_high_flow[0]`
(standard 0.4).

Also check **Preferences → General → "Suppress ' Template ' filament presets"**
is off. That preference gates the preset combo boxes on
`preset.vendor->templates_profile` without testing the preset type
(`PresetComboBoxes.cpp` 323/335, 1138, 1419), and this bundle is a templates
profile, so ticking it hides these print profiles as well as template filaments.

The profiles are read-only system presets, so nothing shows up under Print
Settings until a printer satisfies that condition. "The bundle didn't install",
"no compatible printer is selected" and "templates are suppressed" all look
identical from the dropdown.

---

## Calibrate before trusting these

Every number is a **starting point**. Order:

1. **Max volumetric speed** — the real governor. Print profile speeds are
   ceilings; MVS is what actually limits flow, and it is per filament.
2. **Pressure advance** — the shipped figure is Prusa's own for your nozzle,
   not a scaled one: at HF0.6 it comes from `*C1INDX_<FAM>_06_PA*`, or from
   Prusa's commented HF0.6 draft where that is more specific. Prusa's INDX PA
   *falls* as the nozzle grows (PLA 0.031 at 0.4 → 0.02 at 0.6), so do not
   assume a bigger nozzle wants more. A CHT does have a longer, split melt path
   than the Nextruder these descend from, so your measured value may land above
   Prusa's. Store it in the filament profile via `M572`, not EEPROM.
3. **Extrusion multiplier** — measure wall thickness, don't eyeball it.

On a standard 0.4 the pressure advance is the INDX HF0.4 preset's own value.
Prusa ships no concrete INDX standard-0.4 preset; for PET, ABS and PC its
standard and high-flow 0.4 bases share one PA base (`*C1INDX_PET_04_PA*` 0.048,
`_ABS_` 0.02, `_PC_` 0.05) and each concrete preset overrides it, so the
preset's own figure is kept. Only the PLA family has no INDX standard figure at
all. On a 0.25 it is Prusa's 0.25 value (PLA 0.1, PETG 0.15, PC 0.14,
ABS/ASA/BVOH 0.09), two to four times the 0.4 figure, so widen a PA test's range
to about 0.2.

---

## Adding a nozzle size

Everything is driven by the table in `tools/nozzles.py`.

```bash
python3 tools/build_print_profiles.py <PrusaResearch.ini> /dev/null --list
```

| Size | Upstream common | Layers | Status |
|---|---|---|---|
| 0.25 | `*INDX_025_common*` | 0.07 / 0.12 / 0.15 | shipped by Prusa, not built |
| 0.3 | `*INDX_03_common*` | 0.12 / 0.16 / 0.20 | shipped by Prusa, not built |
| 0.5 | `*INDX_05hf_common*` | 0.15 / 0.20 / 0.25 | **unvalidated** targets |
| 0.6 | `*INDX_06hf_common*` | 0.20 / 0.25 / 0.32 | validated, in use |
| 0.8 | `*INDX_08hf_common*` | 0.30 / 0.40 / 0.55 | **unvalidated** targets |

Prusa renamed the high-flow commons (`*INDX_06_common*` became
`*INDX_06hf_common*`) by PrusaResearch 2.5.11.

To build more than one size into the bundle:

```bash
python3 tools/build_print_profiles.py <PrusaResearch.ini> vendor/hyigerINDX.ini -n 0.6 -n 0.8
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

### There is no 0.2 mm

The smallest INDX nozzle Prusa defines is **0.25 mm** (`*INDX_025_common*`).
`--nozzle 0.2` is rejected.

### Prusa ships 0.25 and 0.3

Since PrusaResearch 2.5.x Prusa ships its own `@COREONEINDX 0.25` and
`@COREONEINDX 0.3` print profiles. They bind on diameter alone, so any INDX
printer with that nozzle picks them up. `build_print_profiles.py` refuses both
sizes rather than duplicate them.

Filaments are different. `derive_filaments.py` scales MVS off a CORE One
high-flow pair, and Prusa publishes none below 0.4, so it refuses 0.25 and 0.3.
`derive_std_filaments.py` builds a **standard** 0.25 without scaling, from the
0.25 bases and drafts Prusa already has (see
[Standard nozzles](#standard-nozzles-from-prusas-own-pieces)). 0.3 has neither.

### Standard nozzles

```bash
python3 tools/build_print_profiles.py <PrusaResearch.ini> vendor/hyigerINDX.ini -n 0.6 --std 0.4
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.4 -n 0.25 --std
python3 tools/derive_std_filaments.py <PrusaResearch.ini> filaments/hyigerINDX-0.4-filaments.ini -n 0.4
python3 tools/derive_std_filaments.py <PrusaResearch.ini> filaments/hyigerINDX-0.25-filaments.ini -n 0.25
```

Only sizes with a Prusa source are accepted: 0.4 (Prusa's HF0.4 prints and
the CORE One STD 0.4 printer) and 0.25 (Prusa's INDX 0.25 printer draft and
0.25 filament bases). Anything else is refused.

---

## Provenance

Almost nothing here is invented.

### Print profile geometry — sourced

PrusaResearch.ini contains per-nozzle INDX commons for 0.25, 0.3, 0.5, 0.6 and
0.8. Every one defines a complete geometry set. Prusa's own 0.25 and 0.3 print
profiles now use theirs; the high-flow 0.5, 0.6 and 0.8 commons are still
unreleased scaffolding: no variant declares those sizes and no *released* print
profile inherits from them. Prusa has drafted them, though, as commented-out
sections: ten `@COREONEINDX HF0.5` / `HF0.6` / `HF0.8` print profiles — four,
four and two (`PrusaResearch.ini:57206-57299`) — and six INDX printer drafts for
8T and 4T at
`0.25`, `HF0.6` and `HF0.8` (`56634-56710`). Those count as sourced here, and
the printer generator uses them (see
[Prusa's commented-out drafts](#prusas-commented-out-drafts) and
[Known gaps](#known-gaps)). The print drafts are not used: the HF0.5 and HF0.6
ones only restate the unreachable 250/200 they inherit, and the two HF0.8 ones,
though they set their own speeds, still run their perimeter at up to 65 mm³/s and
inherit an infill of 75–98 mm³/s, where no HF0.8 filament Prusa ships allows more
than 39 (see [Print profile speeds](#print-profile-speeds--derived-and-only-where-needed)).
This repo also prefers the CORE One HF0.6 layer ladder and its own three-tier
naming to Prusa's drafted Balanced/Draft/Coarse/Extra Coarse lineup.

`build_print_profiles.py` resolves the requested common and embeds it verbatim —
widths, solid-layer counts, support parameters, infill anchors, overhang speeds,
minimum thicknesses. Inheritance cannot cross bundle files, so values are copied
rather than referenced. Keys the chain doesn't set are left to PrusaSlicer's
defaults, exactly as Prusa's own profiles do.

Five keys are changed in the common of every size:

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
`(value, reason)` shape as the table above.

### Print profile speeds — derived, and only where needed

Of the five commons, only `*INDX_025_common*` has a real speed pass. The rest
inherit `perimeter_speed = 250` and `infill_speed = 300` from `*INDX_common*` —
at 0.68 × 0.25 that is 39–47 mm³/s, unreachable. No per-nozzle *common* carries
a pass, consistent with the missing variant declarations. Prusa's commented HF0.8
print drafts do set profile-level speeds (perimeter 200, external 160/120, small
160/120, solid 200/120), which at that common's 0.9 mm widths, each draft at its
own layer height, is 39–65 mm³/s; and they leave infill at the inherited 300,
which is 75–98 mm³/s. Prusa's own commented `Prusament PLA @COREONEINDX HF0.8`
draft resolves to an MVS of 36, so the drafted perimeter at the 0.40 mm layer (65)
and the inherited infill blow straight past it; they are not used either. The
HF0.5 and HF0.6 drafts merely restate what they inherit.

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
cooling-move behaviour). The 0.4 → size step comes from Prusa's own CORE One
`HF0.4` / `HF<dia>` pair for that material. Materials with no high-flow profile
fall back to the non-HF `@COREONE` → `@COREONE <dia>` pair.

Three rules, beside the pressure advance described under
[Calibrate before trusting these](#calibrate-before-trusting-these):

- `filament_max_volumetric_speed` is **ratio-scaled** off the INDX 0.4 value,
  because the INDX toolhead has its own flow baseline distinct from CORE One.
- **INDX toolchanger keys that Prusa sets per nozzle come from its per-nozzle
  common.** Since 2.5.12 Prusa's 0.6 and 0.8 INDX family sections inherit
  `*C1INDX_06_common*` / `*C1INDX_08_common*` in place of `*C1INDX_common*`:
  wipe-tower minimal purge 10 → 14 (20 at 0.8), and
  `filament_retract_restart_extra_toolchange` 0.04 (0.05 at 0.8). They arrived
  together with a toolchange G-code that no longer adds a fixed 0.04 mm to its
  post-toolchange retract, and which still records `retract_length +
  retract_restart_extra_toolchange` as retracted. Each key is applied wherever
  the 0.4 preset took the shared common's value, so Generic FLEX and Prusament
  TPU 95A keep their own purge of 15 (Prusa's HF0.6 drafts for them resolve to
  14).
- Every other key takes the CORE One value **only if INDX agreed with CORE One
  at 0.4**. Where INDX already differs it made a deliberate toolchanger-specific
  choice, and that choice is preserved. This is why Generic ABS keeps
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

### Prusa's commented-out drafts

Prusa keeps unreleased work in `PrusaResearch.ini` as commented-out sections —
`; [printer:...]` then `; key = value`. `load_drafts()` reads them, and they
count as sourced here: they are Prusa's own values, written for the INDX, and
usually more specific than anything a CORE One delta can supply. At 2.5.12
(unchanged from 2.5.11) they are:

| Draft | Used |
|---|---|
| 4 INDX printers: 8T/4T at `HF0.6`, `HF0.8` | **yes**, for the keys in `DRAFT_ADOPT` |
| 2 INDX printers: 8T/4T at `0.25` | **yes**, applied key for key — the sole source at that size |
| 2 INDX 0.25 filaments: `Prusament PLA` / `PETG` | **yes**, applied as written |
| 10 INDX print profiles at `HF0.5` / `HF0.6` / `HF0.8` (4 / 4 / 2) | no — HF0.5/HF0.6 restate what they inherit; HF0.8 sets its own speeds but leaves infill at 300 |
| 416 INDX filament drafts at `HF0.5` / `HF0.6` / `HF0.8` — 135 / 144 / 137 sections, 144 distinct filaments | pressure advance only; see [Known gaps](#known-gaps) |

For the high-flow printers, `build_printer_preset.py` applies the CORE One delta
first, then compares the result against Prusa's draft for that size. (`--std 0.25`
works differently: there is no CORE One delta to apply, so the draft is taken
whole over the parent it names, with no comparison — at that size it is the only
INDX-specific source there is.) Where they disagree on a
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
multi-tool PETG prints never get the dock fan at 100. Reported as
[prusa3d/PrusaSlicer-settings-prusa-fff#50](https://github.com/prusa3d/PrusaSlicer-settings-prusa-fff/issues/50);
the generator stops applying it once Prusa's pattern changes.

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

### Why a filament bundle is needed at all

Selecting an INDX printer at 0.6 mm leaves you with **no filament profiles
whatsoever**. Three separate mechanisms each rule out one source:

| Source | Count | Result | Reason |
|---|---|---|---|
| `@COREONEINDX HF0.4` | 20 | excluded | all but FLEX and TPU 95A require `nozzle_high_flow[0]`; 11 pin `nozzle_diameter[0]==0.4` and the PET/ABS/BVOH/PVA nine bind by exclusion (`!=0.8 and !=0.6 and !=0.5`) |
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

---

## Known gaps

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
  though, so
  `derive_filaments.py` prints every divergence instead of hiding it. Pressure
  advance is the exception: it is taken from Prusa's figures, drafted or not.
- **Only HF0.6 is validated.** The standard 0.4 and 0.25 values are all
  Prusa's, but sourced is not printed: they carry an UNVALIDATED banner until
  test printed on an INDX. Every generator marks an unvalidated size in the file
  it writes as well as on stdout. 0.5 and 0.8 flow targets are extrapolated. The
  0.8 case is weakest: Prusa's `@COREONE 0.8` MVS figures are for a standard
  brass nozzle (Prusament PLA = 19, *below* the HF0.6 figure of 30) and don't
  transfer to a high-flow CHT. Its *printer* preset is better founded — Prusa
  drafted one — but still unprinted.
- **Three tiers per size, not four.** Prusa's 0.4 lineup has a `Fine` as well.
  Add it in `nozzles.py`.
- **Draft keeps the common extrusion width.** Prusa's 0.4 Draft widens
  extrusions ~11% over its common parent. Left alone because 0.68 at 0.32 mm is
  already a healthy 2.1:1 aspect ratio, and widening compounds flow demand.
- **High-flow filament binding includes `nozzle_high_flow[0]`.** Upstream
  commons check diameter only. It keeps the HF0.6 filaments off a standard 0.6
  nozzle, which nothing here supports.
- **Standard 0.4 pressure advance is the HF0.4 preset's own value.** Prusa ships
  no concrete INDX standard-0.4 preset. For the PET, ABS and PC families the
  standard and high-flow 0.4 bases inherit the same `*C1INDX_<fam>_04_PA*`
  section; only the PLA family has no INDX standard figure at all. See
  [Calibrate before trusting these](#calibrate-before-trusting-these). Calibrate
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
  this bundle's copies then. The printer presets are exposed the same way, and
  Prusa already has commented drafts for 8T/4T at 0.25, HF0.6 and HF0.8 — there
  `load_presets` simply skips yours in favour of Prusa's, which is harmless.
- **Generic PVA is not built at any size.** Prusa added it in 2.5.12 as an
  INDX-only preset (Verbatim BVOH plus its own overrides), with no CORE One PVA
  behind it. `derive_filaments.py` has no CORE One pair to scale its MVS by and
  skips it; `derive_std_filaments.py` skips it by name (`STD_SKIP`), so any
  *other* new material without a CORE One standard profile still stops the
  build. Prusa's own HF0.4 preset covers a high-flow 0.4.
- **The personal presets in `personal/` don't import.** They carry two keys no
  PrusaSlicer defines, so Import Config Bundle rejects them. See
  `personal/README.md`; the fix belongs in the Filament DB exporter.

---

## License

The generators, the documentation and the derivation choices in this repo are
licensed under the **GNU AGPL v3** — see [LICENSE](LICENSE) — matching
PrusaSlicer itself.

The generated profiles are a different matter, and worth being straight about:
they are resolved copies of, and derivations from, Prusa Research's own profile
data in `PrusaResearch.ini`. That data lives in
[prusa3d/PrusaSlicer-settings-prusa-fff](https://github.com/prusa3d/PrusaSlicer-settings-prusa-fff),
which declares **no license at all**. So the AGPL grant above covers this repo's
own work, not Prusa's underlying data, and nothing here can grant you rights to
that data which Prusa has not granted. Use the profiles as the convenience they
are; if you intend to redistribute them, ask Prusa.

## Credits

Profiles by **hyiger**. Geometry and filament scaling data are Prusa Research's,
extracted from PrusaResearch.ini. Not affiliated with or endorsed by Prusa
Research or Bondtech.
