# PrusaSlicer profiles for the Prusa CORE One INDX

Prusa's only INDX printer profile is for a **high-flow 0.4 mm** nozzle, and
nearly every INDX print and filament profile it ships is tied to that nozzle. It
also ships print profiles for 0.25 and 0.3 mm, but no printer for them. Fit any
other INDX toolhead and PrusaSlicer's print and filament lists go empty or
nearly so ([Verify](#verify) lists what still appears).

This repo fills the gap for four nozzles: print profiles that install as
read-only system presets (lock icon, reset arrows, nothing added to your own
preset list), a printer preset per nozzle, and a filament bundle per nozzle.
Nearly every value is read out of Prusa's own `PrusaResearch.ini`, not invented;
[docs/PROVENANCE.md](docs/PROVENANCE.md) says where each one comes from.

## What you get

| Nozzle | Print profiles | Filaments | Status |
|---|---|---|---|
| **HF0.6** (Bondtech CHT) | `0.20mm Detail`, `0.25mm Balanced ★`, `0.32mm Draft` | 19 | test printed |
| **HF1.0** (Bondtech CHT) | `0.38mm Detail`, `0.50mm Balanced ★`, `0.69mm Draft` | 19 | not test printed; scaled from 0.8 ([why](#known-gaps)) |
| **0.4 standard** | Prusa's four HF0.4 profiles, rebound to a standard nozzle: `0.10mm Fine`, `0.15mm Detail`, `0.20mm Balanced ★`, `0.25mm Draft`, each `@COREONEINDX 0.4` | 17 | not test printed |
| **0.25 standard** | none needed: Prusa ships `0.07mm Extra Fine`, `0.10mm Fine ★` and `0.15mm Detail`, each `@COREONEINDX 0.25` | 14 | not test printed |

The star marks the recommended default for each nozzle. Print speeds, in mm/s:

| Profile | Perimeter | External | Infill | Solid | Top solid |
|---|---|---|---|---|---|
| `0.20mm Detail @COREONEINDX HF0.6` | 205 | 155 | 235 | 210 | 110 |
| `0.25mm Balanced ★ @COREONEINDX HF0.6` | 165 | 130 | 190 | 170 | 90 |
| `0.32mm Draft @COREONEINDX HF0.6` | 135 | 100 | 155 | 140 | 75 |
| `0.38mm Detail @COREONEINDX HF1.0` | 80 | 60 | 95 | 85 | 40 |
| `0.50mm Balanced ★ @COREONEINDX HF1.0` | 65 | 50 | 70 | 65 | 30 |
| `0.69mm Draft @COREONEINDX HF1.0` | 45 | 35 | 55 | 50 | 25 |

Each filament's max volumetric speed (MVS) caps these, so a slow filament runs
slower than the table. The MVS of every filament, and the HF1.0 pressure
advance, are listed in [docs/PROVENANCE.md](docs/PROVENANCE.md#what-the-bundles-contain);
where each size's pressure advance comes from is under
[Pressure advance by size](docs/PROVENANCE.md#pressure-advance-by-size).

```
vendor/hyigerINDX.ini, .idx       print profiles for HF0.6, HF1.0 and standard 0.4 (one bundle)
printer/*.ini                     one printer preset per nozzle (8T)
filaments/hyigerINDX-<size>-filaments.ini   one filament bundle per nozzle
personal/                         the author's own extra filaments, exported from Filament DB (see its README)
tools/, tests/                    the generators for vendor/hyigerINDX.ini, printer/ and filaments/
```

## Requirements

- PrusaSlicer **2.9.6** or newer
- Prusa Research profiles **2.5.12** or newer (PrusaSlicer updates these itself)
- INDX firmware **6.9.2** or newer: the start G-code checks for it
  (`M115 U6.9.2+16336`) and warns on older firmware
- A CORE One INDX 8T or 4T. The committed printer presets are for the 8T; see
  [Building it yourself](#building-it-yourself) for a 4T.

Your PrusaSlicer data directory:

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/PrusaSlicer` |
| Windows | `%APPDATA%\PrusaSlicer` |
| Linux | `~/.config/PrusaSlicer` (Flatpak: `~/.var/app/com.prusa3d.PrusaSlicer/config/PrusaSlicer`) |

Not sure which folder? **Help → Show Configuration Folder** opens it.

## Install

Quit PrusaSlicer first.

### 1. Install the print profiles

Copy both files into the `vendor` folder of your data directory:

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
# Linux (Flatpak: ~/.var/app/com.prusa3d.PrusaSlicer/config/PrusaSlicer/vendor/)
cp vendor/hyigerINDX.ini vendor/hyigerINDX.idx ~/.config/PrusaSlicer/vendor/
```

No Configuration Wizard step is needed: PrusaSlicer loads every bundle in
`vendor/` at startup, and these attach to your existing Prusa INDX printer.

### 2. Install the printer preset

**This step is not optional.** Prusa's INDX printer is HF0.4 only, so there is
no HF0.6, HF1.0 or standard-nozzle INDX printer to pick in the Configuration
Wizard, and the print profiles stay hidden until the selected printer has the
right nozzle. Copy the preset for each nozzle you fit into the `printer` folder:

```bash
# macOS (Windows and Linux: the printer folder of the same data directory)
cp "printer/Prusa CORE One INDX 8T HF0.6 nozzle.ini" \
   "printer/Prusa CORE One INDX 8T HF1.0 nozzle.ini" \
   "printer/Prusa CORE One INDX 8T 0.4 nozzle.ini" \
   "printer/Prusa CORE One INDX 8T 0.25 nozzle.ini" \
   ~/Library/Application\ Support/PrusaSlicer/printer/
```

Start PrusaSlicer and select it. It shows as a user preset based on Prusa's
INDX printer, so every changed value keeps its reset-to-system arrow.

**Or set it up by hand.** Select Prusa's INDX printer, turn on Expert mode, and
in **Printer Settings** set these on each **Extruder** page (Extruder 1 to 8 on
the 8T, 1 to 4 on the 4T), then save under a new name:

| Setting | HF0.6 | HF1.0 | 0.4 standard | 0.25 standard |
|---|---|---|---|---|
| Nozzle diameter | 0.6 | 1.0 | 0.4 | 0.25 |
| High flow nozzle | on | on | off | off |
| Max layer height | 0.40 | 0.75 | 0.3 | 0.15 |
| Min layer height | 0.15 | 0.25 | 0.07 | 0.05 |
| Retraction length | 0.7 | 0.6 | 0.8 | 0.7 |
| Retraction / deretraction speed | 40 / 30 | 25 / 15 | 40 / 30 | 40 / 30 |
| Wipe while retracting | on | on | off | off |
| Retract amount before wipe | 80% | 50% | 80% | 80% |

Leave **Lift height** alone: Prusa's INDX turns on **Use ramping lift** (1.5 mm)
on every tool, which greys that field out, so don't untick it. The preset files
still record Prusa's drafted lift (0.25 on HF1.0, 0.15 on 0.25), which has no
effect while ramping lift is on.

The preset files also set three things PrusaSlicer does not let you edit:
`printer_variant`, and the default print and filament profiles it uses as a
tie-breaker when it picks profiles after a printer switch. They also fix one bug
in Prusa's layer G-code: in a multi-tool print with PETG and no low-temp
material such as PLA, the dock fan stays off instead of running at the S100 (of
255) Prusa intends from layer 3
([details](docs/PROVENANCE.md#one-fix-to-prusas-printer-g-code)). A hand-made
printer has none of these, so check which print and filament profiles are
selected after switching to it.

### 3. Import the filament presets

**File → Import → Import Config Bundle…** and pick the bundle for your nozzle:
`filaments/hyigerINDX-0.6-filaments.ini`, `-1.0-`, `-0.4-` or `-0.25-`. They
import as ordinary user presets.

## Verify

Select the printer preset from step 2, not Prusa's HF0.4 one. You should see:

| Printer | Print profiles | Filaments |
|---|---|---|
| HF0.6 | 3, with a lock icon | 19 |
| HF1.0 | 3, with a lock icon | 19, plus some of Prusa's own (see below) |
| 0.4 standard | 4, with a lock icon | 17, plus Prusa's Generic FLEX and Prusament TPU 95A |
| 0.25 standard | Prusa's 3 | 14 |

**On HF1.0, pick only the `@COREONEINDX HF1.0` filaments.** Up to nine of
Prusa's own `@COREONEINDX HF0.4` presets also appear (Prusament ASA, PETG, PETG
V0 and PETG Carbon Fiber, Generic ABS, PETG and PVA, and both BVOHs, whichever
you have installed). They carry 0.4 speed limits and pressure advance, and this
repo can't hide them. PrusaSlicer keeps a still-compatible filament when you
switch printers, so a tool holding one of them on the HF0.4 printer keeps it on
HF1.0 without warning.

If the print profiles don't appear:

- Check **Nozzle diameter** and **High flow nozzle** are set on **every** tool.
  The profiles bind on `nozzle_diameter[0]==0.6` (HF0.6), `==1.0` (HF1.0), or
  `==0.4 and ! nozzle_high_flow[0]` (0.4 standard).
- Check **Preferences → General → "Suppress ' Template ' filament presets"** is
  off. Despite its name, it hides this bundle's print profiles too.
- Check both files from step 1 are in `vendor/`, and restart PrusaSlicer.

"Not installed", "wrong nozzle" and "templates suppressed" all look the same
from the dropdown: an empty list.

## Calibrate before trusting these

Every number is a starting point. Calibrate in this order:

1. **Max volumetric speed (MVS).** It is what actually limits flow, per
   filament; the print speeds are only ceilings.
2. **Pressure advance.** Store it in the filament profile with `M572`, not in
   the printer's EEPROM.
   - HF0.6: Prusa's own 0.6 figure.
   - HF1.0: Prusa's 0.8 figure, because Prusa publishes none at 1.0. Prusa's
     values fall as the nozzle grows, so expect yours to come out lower.
   - 0.4 standard: the HF0.4 preset's figure.
   - 0.25 standard: Prusa's 0.25 figures (PLA 0.1, PETG 0.15, PC 0.14,
     ABS/ASA/BVOH 0.09), about two to four and a half times the 0.4 ones. Widen a pressure
     advance test to about 0.2.
3. **Extrusion multiplier.** Measure wall thickness; don't judge it by eye.

## Known gaps

- **Only HF0.6 has been test printed.** The standard 0.4 and 0.25 values are
  Prusa's own, but nobody has printed them on an INDX yet.
- **HF1.0 is the least proven.** Prusa publishes nothing at 1.0 mm, so it is the
  0.8 setup with its line widths and layer heights scaled by 1.25, its print
  speeds re-solved from 0.8's flow targets for the wider line, and the filament
  speed limits and pressure advance kept at 0.8's.
  The generators refuse to build it this way if Prusa ever adds 1.0 data.
  [How it is built](docs/PROVENANCE.md#the-10-mm-nozzle-is-scaled-not-sourced).
- **Prusa's own 0.4 filaments show up on HF1.0.** See [Verify](#verify).
- **The 0.25 setup rests on Prusa's unreleased work.** Its printer comes from a
  draft Prusa has not shipped, and one key in Prusa's 0.25 print profiles is
  misspelled upstream, so top solid infill runs at 100 mm/s instead of 60. Set
  it by hand if top surfaces suffer.
- **Three print profiles per high-flow nozzle, not four.** Prusa's 0.4 lineup
  also has a Fine profile; the standard 0.4 copies all four.
- **Generic PVA is not included** at any nozzle: Prusa has no CORE One PVA to
  base it on.
- **Prusa may ship presets with the same names.** For the print profiles,
  PrusaSlicer then reports duplicates until you remove this repo's copies. For
  the printer and filament presets, the Prusa profile update that adds the name
  deletes your file (a copy stays in the configuration snapshot PrusaSlicer
  takes before updating), and a new Prusa printer stays hidden until you enable
  it in the Configuration Wizard. Save your own edits under a different name.
- **The files in `personal/` don't import as a config bundle**; see
  [personal/README.md](personal/README.md).

More on each, and the smaller ones, in
[docs/PROVENANCE.md](docs/PROVENANCE.md#gaps-in-detail).

## Building it yourself

The print, printer and filament files are generated by the Python tools in
`tools/` from a copy of `PrusaResearch.ini` (`personal/` is exported from
Filament DB and the `.idx` is handwritten), and the tools refuse to build
anything they cannot source. The exact commands are in
[CLAUDE.md](CLAUDE.md#regenerate-and-verify), and the tests run with
`python3 -m unittest discover -s tests`.
[Adding a nozzle size](docs/PROVENANCE.md#adding-a-nozzle-size) covers other
high-flow nozzles (HF0.5, HF0.8), which need the print profiles and a filament
bundle built as well as a printer preset, and
[Other sizes and the 4T](docs/PROVENANCE.md#other-sizes-and-the-4t) covers the 4T.

## License

The generators, documentation and derivation choices are licensed under the
**GNU AGPL v3** (see [LICENSE](LICENSE)), matching PrusaSlicer.

The generated profiles are another matter. They are copies of, and derivations
from, Prusa Research's own profile data, which lives in
[prusa3d/PrusaSlicer-settings-prusa-fff](https://github.com/prusa3d/PrusaSlicer-settings-prusa-fff)
and declares **no license at all**. The AGPL covers this repo's own work, not
Prusa's data, and nothing here can grant rights to that data that Prusa has
not. Use the profiles as the convenience they are; to redistribute them, ask
Prusa.

## Credits

Profiles by **hyiger**. Geometry and filament data are Prusa Research's,
extracted from PrusaResearch.ini. Not affiliated with or endorsed by Prusa
Research or Bondtech.
