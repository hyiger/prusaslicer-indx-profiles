# PrusaSlicer profiles for the Prusa CORE One INDX

Prusa's only INDX printer profile is for a **high-flow 0.4 mm** nozzle, and
nearly every INDX print and filament profile it ships is tied to that nozzle. It
also ships print profiles for 0.25 and 0.3 mm, but no printer for them. Fit any
other INDX toolhead and PrusaSlicer's print and filament lists go empty or
nearly so ([Verify](#verify) lists what still appears).

This repo fills the gap for five nozzles: print profiles that install as
read-only system presets (lock icon, reset arrows, nothing added to your own
preset list), a printer preset per nozzle, and a filament bundle per nozzle.
It also covers one **mixed** setup, different nozzles on different tools of the
same toolchanger ([Mixed nozzles](#mixed-nozzles-025-on-tool-1-hf04-on-the-rest)).
Nearly every value is read out of Prusa's own `PrusaResearch.ini`, not invented;
[docs/PROVENANCE.md](docs/PROVENANCE.md) says where each one comes from.

## What you get

| Nozzle | Print profiles | Filaments | Status |
|---|---|---|---|
| **HF0.6** (Bondtech CHT) | `0.20mm Detail`, `0.25mm Balanced ★`, `0.32mm Draft` | 19 | test printed |
| **HF0.8** (Bondtech CHT) | `0.30mm Detail`, `0.40mm Balanced ★`, `0.55mm Draft` | 19 | not test printed; print speeds extrapolated ([why](#known-gaps)) |
| **HF1.0** (Bondtech CHT) | `0.38mm Detail`, `0.50mm Balanced ★`, `0.69mm Draft` | 19 | not test printed; scaled from 0.8 ([why](#known-gaps)) |
| **0.4 standard** | Prusa's four HF0.4 profiles, rebound to a standard nozzle: `0.10mm Fine`, `0.15mm Detail`, `0.20mm Balanced ★`, `0.25mm Draft`, each `@COREONEINDX 0.4` | 17 | test printed |
| **0.25 standard** | none needed: Prusa ships `0.07mm Extra Fine`, `0.10mm Fine ★` and `0.15mm Detail`, each `@COREONEINDX 0.25` | 14 | test printed |
| **0.25 + HF0.4 mixed** (0.25 on tool 1, HF0.4 on tools 2-8) | `0.07mm Detail`, `0.10mm Balanced ★`, `0.15mm Draft`, each `@COREONEINDX 0.25+HF0.4` | 14 on tool 1, Prusa's own 20 on the rest | not test printed ([details](#mixed-nozzles-025-on-tool-1-hf04-on-the-rest)) |

The star marks the recommended default for each nozzle. Print speeds, in mm/s:

| Profile | Perimeter | External | Infill | Solid | Top solid |
|---|---|---|---|---|---|
| `0.20mm Detail @COREONEINDX HF0.6` | 205 | 155 | 235 | 210 | 110 |
| `0.25mm Balanced ★ @COREONEINDX HF0.6` | 165 | 130 | 190 | 170 | 90 |
| `0.32mm Draft @COREONEINDX HF0.6` | 135 | 100 | 155 | 140 | 75 |
| `0.30mm Detail @COREONEINDX HF0.8` | 130 | 100 | 145 | 130 | 65 |
| `0.40mm Balanced ★ @COREONEINDX HF0.8` | 100 | 75 | 115 | 100 | 50 |
| `0.55mm Draft @COREONEINDX HF0.8` | 75 | 55 | 85 | 75 | 35 |
| `0.38mm Detail @COREONEINDX HF1.0` | 80 | 60 | 95 | 85 | 40 |
| `0.50mm Balanced ★ @COREONEINDX HF1.0` | 65 | 50 | 70 | 65 | 30 |
| `0.69mm Draft @COREONEINDX HF1.0` | 45 | 35 | 55 | 50 | 25 |

Each filament's max volumetric speed (MVS) caps these, so a slow filament runs
slower than the table. The MVS of every filament, and the HF0.8 and HF1.0
pressure advance, are listed in [docs/PROVENANCE.md](docs/PROVENANCE.md#what-the-bundles-contain);
where each size's pressure advance comes from is under
[Pressure advance by size](docs/PROVENANCE.md#pressure-advance-by-size).

```
vendor/hyigerINDX.ini, .idx       print profiles for HF0.6, HF0.8, HF1.0, standard 0.4 and the 0.25+HF0.4 mix (one bundle)
printer/*.ini                     one printer preset per nozzle, plus one for the 0.25+HF0.4 mix (8T)
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
no HF0.6, HF0.8, HF1.0 or standard-nozzle INDX printer to pick in the Configuration
Wizard, and the print profiles stay hidden until the selected printer has the
right nozzle. Copy the preset for each nozzle you fit into the `printer` folder:

```bash
# macOS (Windows and Linux: the printer folder of the same data directory)
cp "printer/Prusa CORE One INDX 8T HF0.6 nozzle.ini" \
   "printer/Prusa CORE One INDX 8T HF0.8 nozzle.ini" \
   "printer/Prusa CORE One INDX 8T HF1.0 nozzle.ini" \
   "printer/Prusa CORE One INDX 8T 0.4 nozzle.ini" \
   "printer/Prusa CORE One INDX 8T 0.25 nozzle.ini" \
   "printer/Prusa CORE One INDX 8T 0.25+HF0.4 nozzles.ini" \
   ~/Library/Application\ Support/PrusaSlicer/printer/
```

Start PrusaSlicer and select it. It shows as a user preset based on Prusa's
INDX printer, so every changed value keeps its reset-to-system arrow.

**Or set it up by hand.** Select Prusa's INDX printer, turn on Expert mode, and
in **Printer Settings** set these on each **Extruder** page (Extruder 1 to 8 on
the 8T, 1 to 4 on the 4T), then save under a new name:

| Setting | HF0.6 | HF0.8 | HF1.0 | 0.4 standard | 0.25 standard |
|---|---|---|---|---|---|
| Nozzle diameter | 0.6 | 0.8 | 1.0 | 0.4 | 0.25 |
| High flow nozzle | on | on | on | off | off |
| Max layer height | 0.40 | 0.6 | 0.75 | 0.3 | 0.15 |
| Min layer height | 0.15 | 0.2 | 0.25 | 0.07 | 0.05 |
| Retraction length | 0.7 | 0.6 | 0.6 | 0.8 | 0.7 |
| Retraction / deretraction speed | 40 / 30 | 25 / 15 | 25 / 15 | 40 / 30 | 40 / 30 |
| Wipe while retracting | on | on | on | off | off |
| Retract amount before wipe | 80% | 50% | 50% | 80% | 80% |

The mixed preset is not in that table because its values differ from tool to
tool; [Mixed nozzles](#mixed-nozzles-025-on-tool-1-hf04-on-the-rest) has them.

Leave **Lift height** alone: Prusa's INDX turns on **Use ramping lift** (1.5 mm)
on every tool, which grays that field out, so don't untick it. The preset files
still record Prusa's drafted lift (0.25 on HF0.8 and HF1.0, 0.15 on 0.25), which has no
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
`filaments/hyigerINDX-0.6-filaments.ini`, `-0.8-`, `-1.0-`, `-0.4-` or `-0.25-`.
They import as ordinary user presets.

For the mixed setup, import `-0.25-` only. Tools 2 to 8 are HF0.4, which is the
one nozzle Prusa already ships filaments for, and PrusaSlicer offers each tool
the filaments for its own nozzle - see below.

## Mixed nozzles: 0.25 on tool 1, HF0.4 on the rest

Prusa documents an experimental workflow for fitting **different nozzle
diameters to different tools** of one toolchanger
([help.prusa3d.com article 821176](https://help.prusa3d.com/article/experimental-printing-with-different-nozzle-diameters_821176)),
written for the XL. This repo carries one worked INDX version of it: a standard
**0.25 mm** nozzle on tool 1 and Prusa's shipping **high-flow 0.4 mm** CHT on
tools 2 to 8. Fine perimeters and fine top surfaces from the small nozzle,
sparse infill from the big one.

It is **not test printed.** Prusa calls the workflow experimental and says some
nozzle combinations can fail; treat the first print as a test.

### What prints with which tool

| Role | Tool | Why |
|---|---|---|
| Perimeters, external perimeters, gap fill | 1 (0.25) | the reason for fitting a small nozzle |
| Solid infill **and top surfaces** | 1 (0.25) | PrusaSlicer has no separate top-surface extruder: `solid_infill_extruder` covers both |
| Sparse infill | 2 (HF0.4) | the one role where the CHT pays for the tool changes |
| Supports and support interfaces | 1 (0.25) | support width follows the smaller nozzle anyway, and pinning it is what keeps the wipe tower working |

Every role is pinned, so nothing is printed by "whichever tool is loaded". The
profiles switch supports to **Organic**, which is required rather than a
preference: with a wipe tower and non-soluble supports, PrusaSlicer rejects the
slice outright if a support extruder is pinned and the style is not organic.

Sparse infill runs at 0.45 mm wide, Prusa's own HF0.4 width, and is combined
across layers up to 0.25 mm of height — the most PrusaSlicer will combine here,
because it caps combining at the smaller of the infill and solid-infill nozzles.
Combining is also what keeps the tool changes down: one pair per combined group
instead of one pair per layer.

| Profile | Layer | Infill every | Infill | Perimeter | Solid | Infill rate |
|---|---|---|---|---|---|---|
| `0.07mm Detail @COREONEINDX 0.25+HF0.4` | 0.07 | 3 layers | 285 | 150 | 140 | 24.2 mm³/s |
| `0.10mm Balanced ★ @COREONEINDX 0.25+HF0.4` | 0.10 | 2 layers | 300 | 150 | 140 | 24.4 mm³/s |
| `0.15mm Draft @COREONEINDX 0.25+HF0.4` | 0.15 | 1 layer | 300 | 150 | 140 | 18.8 mm³/s |

Speeds in mm/s. The perimeter, solid and support speeds are Prusa's own
`@COREONEINDX 0.25` values, as are the layer heights and the solid-layer counts
(11/9, 9/7 and 6/5 top/bottom). Only the infill speed is this repo's, solved so
the rate matches the 24.4 mm³/s Prusa's own starred `0.20mm Balanced ★
@COREONEINDX HF0.4` runs infill at, and never faster than that profile's own
300 mm/s. For comparison, Prusa's 0.25 profiles run infill at 2.4 mm³/s — the
whole point of the exercise.

### Setting it up

1. **Fit the nozzles, then calibrate tool offsets.** Changing a nozzle changes
   the offsets.
2. **Tell the printer** which dock holds which nozzle, including the high-flow
   flag. The INDX start G-code asks the firmware to verify every used tool
   (`M862.1 T<n> P{nozzle_diameter[n]} … F{nozzle_high_flow[n]}`), so a dock set
   wrongly stops the print at the start rather than printing with the wrong
   nozzle.
3. **Install** the print bundle (step 1 above) and
   `printer/Prusa CORE One INDX 8T 0.25+HF0.4 nozzles.ini` (step 2), then import
   `filaments/hyigerINDX-0.25-filaments.ini` (step 3) — the 0.25 bundle only.
4. **Load filament per tool.** PrusaSlicer filters each tool's filament list by
   that tool's own nozzle, so tool 1 is offered this repo's 14 `@COREONEINDX
   0.25` presets and tools 2 to 8 Prusa's own 20 `@COREONEINDX HF0.4` presets.
   Nothing else is needed for the HF0.4 tools.

**Or set it up by hand.** Prusa's INDX printer, Expert mode, **Printer
Settings → Extruder N**, with different values per tool:

| Setting | Extruder 1 | Extruders 2-8 |
|---|---|---|
| Nozzle diameter | 0.25 | 0.4 |
| High flow nozzle | off | on |
| Max layer height | 0.15 | 0.3 |
| Min layer height | 0.05 | 0.07 |
| Retraction length | 0.7 | 0.8 |

Everything else is the same on every tool (retraction 40 / deretraction 30,
wipe off). PrusaSlicer only forces the nozzles to match on a single-extruder
multimaterial printer, which the INDX is not, so these stay as you set them.
Then set the roles in **Print Settings → Multiple Extruders → Extruders**:
perimeters 1, infill 2, solid infill 1, support and support interface 1; switch
supports to Organic under **Support material**; and set **Combine infill every**
per the table above.

### Two things to know

- **Prusa's own three `@COREONEINDX 0.25` profiles also appear** in the print
  dropdown, because a mixed printer satisfies their condition too
  (`nozzle_diameter[0]==0.25`). They are perfectly valid, but they print
  *everything* with tool 1 and ignore the CHT. The `0.25+HF0.4` profiles are the
  mixed ones.
- **Tool changes cost purge and time.** Splitting a role across tools means a
  wipe-tower purge per change. PrusaSlicer also warns that a wipe tower with
  different nozzle diameters is experimental; that warning is expected here.

## Verify

Select the printer preset from step 2, not Prusa's HF0.4 one. You should see:

| Printer | Print profiles | Filaments |
|---|---|---|
| HF0.6 | 3, with a lock icon | 19 |
| HF0.8 | 3, with a lock icon | 19 |
| HF1.0 | 3, with a lock icon | 19, plus some of Prusa's own (see below) |
| 0.4 standard | 4, with a lock icon | 17, plus Prusa's Generic FLEX and Prusament TPU 95A |
| 0.25 standard | Prusa's 3 | 14 |
| 0.25 + HF0.4 mixed | 3, with a lock icon, plus Prusa's 3 `@COREONEINDX 0.25` (see above) | per tool: 14 on tool 1, Prusa's 20 on tools 2-8 |

**On HF1.0, pick only the `@COREONEINDX HF1.0` filaments.** Up to nine of
Prusa's own `@COREONEINDX HF0.4` presets also appear (Prusament ASA, PETG, PETG
V0 and PETG Carbon Fiber, Generic ABS, PETG and PVA, and both BVOHs, whichever
you have installed). They carry 0.4 speed limits and pressure advance, and this
repo can't hide them. PrusaSlicer keeps a still-compatible filament when you
switch printers, so a tool holding one of them on the HF0.4 printer keeps it on
HF1.0 without warning.

If the print profiles don't appear:

- Check **Nozzle diameter** and **High flow nozzle** are set on **every** tool.
  The profiles bind on `nozzle_diameter[0]==0.6` (HF0.6), `==0.8` (HF0.8),
  `==1.0` (HF1.0), or
  `==0.4 and ! nozzle_high_flow[0]` (0.4 standard). The mixed profiles test
  two tools: `nozzle_diameter[0]==0.25 and ! nozzle_high_flow[0] and
  nozzle_diameter[1]==0.4 and nozzle_high_flow[1]`, so tools 1 and 2 both
  have to be set.
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
   - HF0.8: Prusa's own 0.8 figure.
   - HF1.0: the same 0.8 figure, because Prusa publishes none at 1.0. Prusa's
     values fall as the nozzle grows, so expect yours to come out lower.
   - 0.4 standard: the HF0.4 preset's figure.
   - 0.25 standard: Prusa's 0.25 figures (PLA 0.1, PETG 0.15, PC 0.14,
     ABS/ASA/BVOH 0.09), about two to four and a half times the 0.4 ones. Widen a pressure
     advance test to about 0.2.
   - 0.25 + HF0.4 mixed: per tool, since it lives in the filament preset —
     the 0.25 figures on tool 1, Prusa's HF0.4 ones on tools 2 to 8. Nothing
     to merge: each tool uses its own filament preset.
3. **Extrusion multiplier.** Measure wall thickness; don't judge it by eye.

## Known gaps

- **HF0.8 and HF1.0 have not been test printed.** HF0.6, standard 0.4 and
  standard 0.25 have. HF0.8's print speeds are extrapolated and HF1.0 is
  scaled from HF0.8; both are covered below.
- **HF0.8's print speeds are extrapolated.** Prusa has done no speed pass at
  0.8, so the speeds are solved from flow targets this repo extrapolated past
  HF0.6's. Everything else at 0.8 is Prusa's: the print settings, the printer
  (including retraction, from Prusa's own HF0.8 printer draft), each filament's
  pressure advance, and its max volumetric speed (the INDX 0.4 value scaled by
  the ratio between Prusa's own CORE One 0.4 and 0.8 profiles for that
  material).
- **HF1.0 is the least proven.** Prusa publishes nothing at 1.0 mm, so it is the
  0.8 setup with its line widths and layer heights scaled by 1.25, its print
  speeds re-solved from 0.8's flow targets for the wider line, and the filament
  speed limits and pressure advance kept at 0.8's.
  The generators refuse to build it this way if Prusa ever adds 1.0 data.
  [How it is built](docs/PROVENANCE.md#the-10-mm-nozzle-is-scaled-not-sourced).
- **Prusa's own 0.4 filaments show up on HF1.0.** See [Verify](#verify).
- **The mixed 0.25 + HF0.4 layout has not been test printed**, and Prusa calls
  the workflow experimental. Every value in it is Prusa's own except the infill
  speed, which is solved from Prusa's own HF0.4 infill rate.
  [Details](#mixed-nozzles-025-on-tool-1-hf04-on-the-rest).
- **The 0.25 setup rests on Prusa's unreleased work.** Its printer comes from a
  draft Prusa has not shipped, and one key in Prusa's 0.25 print profiles is
  misspelled upstream (`top solid_infill_speed`), so top solid infill runs at
  100 mm/s instead of 60. Set it by hand if top surfaces suffer. The mixed
  profiles are built on those same profiles and carry the typo as written,
  rather than quietly changing a speed the 0.25 setup was test printed with.
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
high-flow nozzles (HF0.5), which need the print profiles and a filament
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
