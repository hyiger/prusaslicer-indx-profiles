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
- **0.4 standard**: a standard (non-high-flow) 0.4 mm nozzle.
- **0.25 standard**: a standard 0.25 mm nozzle, using Prusa's own 0.25 print profiles.

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

All nineteen materials Prusa publishes for the INDX:

| Material | MVS 0.4 → 0.6 | Material | MVS 0.4 → 0.6 |
|---|---|---|---|
| Prusament PLA | 28 → **35** | Prusament ASA | 30 → **39** |
| Prusament PETG | 20 → **25** | Prusament PC Blend | 22 → **28** |
| Prusament PLA Blend | 12.5 → **15** | Prusament PC Blend CF | 13 → **19** |
| Prusament rPLA | 10 → **14** | Generic PLA | 17 → **23** |
| Prusament Woodfill | 10 → **12** | Generic PETG | 17 → **22** |
| Generic PLA Silk | 12.5 → **16** | Generic ABS | 25 → **34** |
| Prusament PETG V0 | 16 → **22** | Prusament PETG CF | 12 → **17** |
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
| Prusament PLA Blend | 12.5 → **7.5** → **7.5** | Prusament PC Blend CF | 13 → **9** → n/a |
| Prusament rPLA | 10 → **10** → **10** | Generic PLA | 17 → **15** → **10** |
| Prusament Woodfill | 10 → **10** → n/a | Generic PETG | 17 → **12** → **12** |
| Generic PLA Silk | 12.5 → **7** → **7** | Generic ABS | 25 → **15** → **15** |
| Prusament PETG V0 | 16 → **10** → **10** | Prusament PETG CF | 12 → **12** → n/a |
| Prusament PVB | 6 → **6** → **6** | Verbatim BVOH | 4 → **4** → **4** |
| Fiberlogy BVOH | 4 → **4** → **4** | | |

n/a means not built: Prusa does not allow carbon fiber or Woodfill on a 0.25
nozzle. Generic FLEX and Prusament TPU 95A are not rebuilt: Prusa's own INDX
presets for them already accept a standard 0.4, and the INDX has no 0.25 FLEX
base.

---

## Requirements

- PrusaSlicer **2.9.6** or newer
- Prusa Research vendor bundle **config_version 2.5.11** or newer. Everything
  here was generated from 2.5.11, and the standard 0.25 setup uses the 0.25
  print profiles it ships.
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

The standard-nozzle presets carry Prusa's names for those variants, so if
Prusa ever releases an INDX printer with the same name, PrusaSlicer loads
Prusa's and skips yours. Enable that variant in the Configuration Wizard then.

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
python3 tools/build_printer_preset.py <PrusaResearch.ini> printer/ -n 0.4 -n 0.25 --std -m 4T
```

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

0.8 is not listed. Prusa's HF0.4 → HF0.8 delta also moves five retraction
keys (`retract_length`, `retract_speed`, `deretract_speed`, `retract_lift`,
`retract_before_wipe`), and whether those transfer to a toolchanger running
`retract_toolchange = 8` has not been established. The generator refuses 0.8
rather than guess.

For a standard nozzle, uncheck **High flow nozzle** on every tool and set
`printer_variant` to `0.4`. For 0.25, also set nozzle diameter `0.25`,
retraction length `0.7`, lift Z `0.15`, and layer heights `0.05` to `0.15`:
the values in Prusa's own unreleased INDX 0.25 printer.

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

The profiles are read-only system presets, so nothing shows up under Print
Settings until a printer satisfies that condition. "The bundle didn't install"
and "no compatible printer is selected" look identical from the dropdown.

---

## Calibrate before trusting these

Every number is a **starting point**. Order:

1. **Max volumetric speed** — the real governor. Print profile speeds are
   ceilings; MVS is what actually limits flow, and it is per filament.
2. **Pressure advance** — a CHT has a longer, split melt path than the
   Nextruder these values descend from. Expect a higher PA. Store it in the
   filament profile via `M572`, not EEPROM.
3. **Extrusion multiplier** — measure wall thickness, don't eyeball it.

On a standard 0.4 the pressure advance is still Prusa's HF0.4 value, since
Prusa publishes none for a standard INDX 0.4. On a 0.25 it is Prusa's 0.25 value
(PLA 0.1, PETG 0.15, PC 0.14, ABS/ASA/BVOH 0.09), two to four times the 0.4
figure, so widen a PA test's range to about 0.2.

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
straight out of the shipping print profiles.

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
unreleased scaffolding: no variant declares those sizes and no print profile
inherits from them.

`build_print_profiles.py` resolves the requested common and embeds it verbatim —
widths, solid-layer counts, support parameters, infill anchors, overhang speeds,
minimum thicknesses. Inheritance cannot cross bundle files, so values are copied
rather than referenced. Keys the chain doesn't set are left to PrusaSlicer's
defaults, exactly as Prusa's own profiles do.

Five keys are changed per size:

| Key | Upstream | Here | Why |
|---|---|---|---|
| `bridge_speed` | 50 | 30 | 50 mm/s at a 0.6 bridge is ~14 mm³/s |
| `interlocking_beam_width` | 0.8 | 2 × nozzle | 0.8 is only ~1.2 extrusions wide at 0.68 |
| `print_settings_id` | — | empty | system preset hygiene |
| `notes` | — | empty | system preset hygiene |
| `compatible_printers` | — | empty | condition-based binding only |

### Print profile speeds — derived, and only where needed

Of the five commons, only `*INDX_025_common*` has a real speed pass. The rest
inherit `perimeter_speed = 250` and `infill_speed = 300` from `*INDX_common*` —
at 0.68 × 0.25 that is 39–47 mm³/s, unreachable. The pass hasn't happened
upstream, consistent with the missing variant declarations.

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
resolution rather than flow demand. The shipping 0.4 INDX profiles sit at
20–24 mm³/s; these aim modestly above because a CHT melts faster.

Where a size has no targets, upstream speeds are left untouched and the
generator says so loudly.

### Filament presets — derived

Each preset starts from its `@COREONEINDX HF0.4` parent, which carries the
INDX-specific toolchanger settings (multitool ramming, purge volumes,
cooling-move behaviour). The 0.4 → size step comes from Prusa's own CORE One
`HF0.4` / `HF<dia>` pair for that material. Materials with no high-flow profile
fall back to the non-HF `@COREONE` → `@COREONE <dia>` pair.

Two rules:

- `filament_max_volumetric_speed` is **ratio-scaled** off the INDX 0.4 value,
  because the INDX toolhead has its own flow baseline distinct from CORE One.
- Every other key takes the CORE One value **only if INDX agreed with CORE One
  at 0.4**. Where INDX already differs it made a deliberate toolchanger-specific
  choice, and that choice is preserved. This is why Generic ABS keeps
  `filament_infill_max_crossing_speed = 140` rather than taking CORE One's `0`,
  and why `filament_cooling_final_speed = 0` survives throughout.

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
those bases:

- **Cooling.** ABS/PC families keep their own; their INDX bases do not change
  with the nozzle. PLA/PET families keep a value they set themselves (PVB's
  20 s minimum layer time, for example), follow the flagship's draft where they
  matched it at HF0.4, and take the 0.25 base otherwise.
- **Pressure advance.** The INDX 0.25 base supplies it for PLA (0.1) and PET
  (0.15). Other families take the CORE One's own 0.25 value, swapped into the
  INDX start G-code so that `M906 P2` (BVOH's reduced E current) survives.
- **MVS.** The lowest of the INDX HF0.4, CORE One STD and 0.25-base values.

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
| `@COREONEINDX HF0.4` | 19 | excluded | condition requires `nozzle_diameter[0]==0.4` |
| `@COREONE HF0.6` | 143 | excluded | `printer_model` uses `regex_match`, so `COREONE_INDX8T` does not match `/(COREONE\|COREONEOAK\|…)/` |
| `Templates.ini` | 201 | excluded | every profile carries `printer_notes!~/.*NO_TEMPLATES.*/`, and Prusa puts `NO_TEMPLATES` in the INDX printer notes |

Counts are from PrusaResearch 2.5.11. A standard nozzle hits the same wall
one step earlier: 17 of the 19 INDX filaments also require
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

Print presets are exempt from both, so they stay in the vendor bundle while
filaments ship as an importable config bundle.

---

## Known gaps

- **Speeds are derived, not sourced.** If Prusa completes the speed pass on the
  per-nozzle commons, prefer theirs.
- **Only 0.6 is validated.** 0.5 and 0.8 targets are extrapolated. The 0.8 case
  is weakest: Prusa's `@COREONE 0.8` MVS figures are for a standard brass nozzle
  (Prusament PLA = 19, *below* the HF0.6 figure of 30) and don't transfer to a
  high-flow CHT.
- **Three tiers per size, not four.** Prusa's 0.4 lineup has a `Fine` as well.
  Add it in `nozzles.py`.
- **Draft keeps the common extrusion width.** Prusa's 0.4 Draft widens
  extrusions ~11% over its common parent. Left alone because 0.68 at 0.32 mm is
  already a healthy 2.1:1 aspect ratio, and widening compounds flow demand.
- **High-flow filament binding includes `nozzle_high_flow[0]`.** Upstream
  commons check diameter only. It keeps the HF0.6 filaments off a standard 0.6
  nozzle, which nothing here supports.
- **Standard 0.4 pressure advance is the HF0.4 value.** Prusa publishes no INDX
  standard 0.4 figure. Calibrate it.
- **The standard 0.25 rests on unreleased Prusa work.** Its printer is Prusa's
  commented-out draft, and Prusa's 0.25 print profiles have no released printer
  behind them. One of their keys is misspelled upstream (`top solid_infill_speed`,
  with a space), so top solid infill runs at the inherited 100 mm/s instead of
  the 60 every other Prusa 0.25 profile uses. Set it by hand if top surfaces
  suffer.
- **Prusa may release the same names.** The standard 0.4 print profiles are
  named the way Prusa would name them. If Prusa ships identically named
  presets, PrusaSlicer reports duplicates across the two vendor bundles; remove
  this bundle's copies then.

---

## Credits

Profiles by **hyiger**. Geometry and filament scaling data are Prusa Research's,
extracted from PrusaResearch.ini. Not affiliated with or endorsed by Prusa
Research or Bondtech.
