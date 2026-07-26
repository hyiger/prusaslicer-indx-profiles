# PrusaSlicer profiles for the Prusa CORE One INDX

Print and filament profiles for running INDX toolheads at nozzle sizes Prusa
doesn't ship profiles for.

Prusa supports **0.4 mm only**. `variants = HF0.4` is the entire variant list
for both `COREONE_INDX8T` and `COREONE_INDX4T`, and every INDX print and
filament profile binds to `nozzle_diameter[0]==0.4`. Fit any other toolhead and
the print profile list narrows to nothing and the filament dropdown empties.

The print profiles here install as **read-only system presets** — lock icon,
reset-to-system-value arrows, no clutter in your own preset list.

**Currently built: 0.6 mm.** The generators handle other sizes too; see
[Adding a nozzle size](#adding-a-nozzle-size).

---

## What's here

```
vendor/
  hyigerINDX.ini                  vendor bundle — print profiles, all sizes
  hyigerINDX.idx                  version index
filaments/
  hyigerINDX-0.6-filaments.ini    12 filament presets for 0.6 mm, for import
tools/
  nozzles.py                      per-nozzle configuration table
  build_print_profiles.py         generates the vendor bundle
  derive_filaments.py             generates filament presets
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

All twelve materials Prusa publishes for the INDX:

| Material | MVS 0.4 → 0.6 | Material | MVS 0.4 → 0.6 |
|---|---|---|---|
| Prusament PLA | 28 → **35** | Prusament ASA | 30 → **39** |
| Prusament PETG | 20 → **25** | Prusament PC Blend | 22 → **28** |
| Prusament PLA Blend | 12.5 → **15** | Prusament PC Blend CF | 13 → **19** |
| Prusament rPLA | 10 → **14** | Generic PLA | 17 → **23** |
| Prusament Woodfill | 10 → **12** | Generic PETG | 17 → **22** |
| Generic PLA Silk | 12.5 → **16** | Generic ABS | 25 → **34** |

MVS in mm³/s.

---

## Requirements

- PrusaSlicer **2.9.6** or newer
- Prusa Research vendor bundle **config_version 2.5.5** or newer — this is
  where the INDX profiles live
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

### 2. Fix the printer preset

**Not optional.** A printer preset cloned from the shipping 0.4 mm INDX profile
still caps layer height at 0.3 mm, which silently hides any profile above it —
including `0.32mm Draft`.

In **Printer Settings → General**, Expert mode on:

| Field | 0.5 mm | 0.6 mm | 0.8 mm |
|---|---|---|---|
| Nozzle diameter | `0.5` | `0.6` | `0.8` |
| High flow nozzle | checked | checked | checked |
| Max layer height | `0.35` | `0.4` | `0.6` |
| Min layer height | `0.12` | `0.15` | `0.2` |

Set these on **every tool**. Then confirm `printer_variant` matches (`HF0.6`
and so on) and save the preset. The 0.6 values are Prusa's own, from
`Prusa CORE One HF0.6 nozzle`.

### 3. Import the filament presets

**File → Import → Import Config Bundle…** and select the file for your nozzle
size, e.g. `filaments/hyigerINDX-0.6-filaments.ini`.

These import as user presets, which is deliberate — see
[Why filaments aren't in the vendor bundle](#why-filaments-arent-in-the-vendor-bundle).

### 4. Verify

Select your INDX printer with the right toolhead size. You should see three
print profiles with a lock icon and twelve filaments in the dropdown.

If the print profiles don't appear, check `nozzle_diameter` really is set on
every tool. The binding condition is
`printer_model=~/(COREONE_INDX8T|COREONE_INDX4T)/ and nozzle_diameter[0]==<dia> and nozzle_high_flow[0]`.

---

## Calibrate before trusting these

Every number is a **starting point**. Order:

1. **Max volumetric speed** — the real governor. Print profile speeds are
   ceilings; MVS is what actually limits flow, and it is per filament.
2. **Pressure advance** — a CHT has a longer, split melt path than the
   Nextruder these values descend from. Expect a higher PA. Store it in the
   filament profile via `M572`, not EEPROM.
3. **Extrusion multiplier** — measure wall thickness, don't eyeball it.

---

## Adding a nozzle size

Everything is driven by the table in `tools/nozzles.py`.

```bash
python3 tools/build_print_profiles.py <PrusaResearch.ini> /dev/null --list
```

| Size | Upstream common | Layers | Status |
|---|---|---|---|
| 0.25 | `*INDX_025_common*` | 0.07 / 0.12 / 0.15 | speeds already tuned upstream |
| 0.3 | `*INDX_03_common*` | 0.12 / 0.16 / 0.20 | no targets — speeds left untouched |
| 0.5 | `*INDX_05_common*` | 0.15 / 0.20 / 0.25 | **unvalidated** targets |
| 0.6 | `*INDX_06_common*` | 0.20 / 0.25 / 0.32 | validated, in use |
| 0.8 | `*INDX_08_common*` | 0.30 / 0.40 / 0.55 | **unvalidated** targets |

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

### 0.25 and 0.3 need measurement, not generation

- **0.25** already has a complete upstream speed pass — `perimeter_speed 150`,
  `infill_speed 100`, `perimeters 3`, 11/8 solid layers. The generator emits the
  geometry and leaves those alone. This one is genuinely ready.
- **0.3** has no upstream speed pass and no trustworthy way to derive one.
  Linear extrapolation from the 0.4 and 0.6 anchors collapses below 0.4: it
  predicts ~17 mm³/s where the tuned 0.25 profile actually runs 3.7. So no
  targets are supplied and speeds stay at the inherited 0.4 values until
  measured.
- Neither size has **any** CORE One filament reference to scale MVS against —
  Prusa publishes filament variants for HF0.5, HF0.6, HF0.8 and 0.8 only.
  `derive_filaments.py` refuses rather than guessing.

---

## Provenance

Almost nothing here is invented.

### Print profile geometry — sourced

PrusaResearch.ini contains per-nozzle INDX commons for 0.25, 0.3, 0.5, 0.6 and
0.8. Every one defines a complete geometry set. Nothing uses them: no variant
declares those sizes and no print profile inherits from them. Unreleased
scaffolding.

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
| `@COREONEINDX HF0.4` | 12 | excluded | condition requires `nozzle_diameter[0]==0.4` |
| `@COREONE HF0.6` | 142 | excluded | `printer_model` uses `regex_match`, so `COREONE_INDX8T` does not match `/(COREONE\|COREONEOAK\|…)/` |
| `Templates.ini` | 207 | excluded | every profile carries `printer_notes!~/.*NO_TEMPLATES.*/`, and Prusa puts `NO_TEMPLATES` in the INDX printer notes |

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
- **Binding includes `nozzle_high_flow[0]`.** Upstream commons check diameter
  only. Harmless — every INDX toolhead is high-flow — but a deviation.

---

## Credits

Profiles by **hyiger**. Geometry and filament scaling data are Prusa Research's,
extracted from PrusaResearch.ini. Not affiliated with or endorsed by Prusa
Research or Bondtech.
