# CLAUDE.md

Context for AI assistants working in this repo. `README.md` is for users; this
file is for whoever edits the code.

## What this is

PrusaSlicer profiles for Prusa CORE One INDX toolheads at nozzle sizes Prusa
doesn't ship: high-flow sizes (HF0.6) and standard, non-high-flow nozzles
(0.4 and 0.25). Print profiles install as read-only **system presets** via a
vendor bundle; filament presets ship as an importable config bundle; printer
presets ship as flattened user presets.

Nearly everything is **generated** from Prusa's own `PrusaResearch.ini`. The
value of this repo is its provenance discipline, not its cleverness. Preserve
that.

## Non-negotiables

1. **Never invent a slicer value.** Every number is either resolved from
   `PrusaResearch.ini` or derived by a documented, reproducible rule. If
   neither is possible, the tool must **refuse** — see `derive_filaments.py`
   rejecting 0.25/0.3, and `nozzles.py` giving 0.3 no flow targets. A loud
   failure beats a plausible fabrication.
2. **Record provenance for anything changed.** `COMMON_EDITS` in `nozzles.py`
   carries a reason string per key. Keep that pattern.
3. **Mark unvalidated output as unvalidated.** `Nozzle.validated` drives a
   warning banner in stdout and a comment in the emitted bundle. Don't quietly
   promote extrapolated numbers.
4. **Byline is `hyiger`.** Never use a real name in profiles, commits, README
   or generated file headers.
5. **Regenerate, don't hand-edit.** `vendor/*.ini` and `filaments/*.ini` are
   build artifacts. Editing them directly desynchronises them from the tools.

## Layout

```
vendor/hyigerINDX.ini      GENERATED  print profiles, all nozzle sizes
vendor/hyigerINDX.idx      handwritten  version index
filaments/hyigerINDX-*.ini GENERATED  one bundle per nozzle size
printer/*.ini              GENERATED  flattened printer presets
tools/nozzles.py           handwritten  per-nozzle config table — start here
tools/build_print_profiles.py  GENERATOR  vendor bundle (HF sizes, --std 0.4)
tools/build_printer_preset.py  GENERATOR  printer presets (HF sizes, --std)
tools/derive_filaments.py      GENERATOR  high-flow filament bundles
tools/derive_std_filaments.py  GENERATOR  standard-nozzle filament bundles
```

The other `filaments/*.ini` files (Bambu_PC.ini and the like) are hand-made
personal presets, not generator output.

Generated artifacts **are** committed. Users download and import them; requiring
a local `PrusaResearch.ini` plus Python to get a usable file would defeat the
purpose.

## Regenerate and verify

```bash
PR=~/Library/Application\ Support/PrusaSlicer/vendor/PrusaResearch.ini

python3 tools/build_print_profiles.py "$PR" /dev/null --list
python3 tools/build_print_profiles.py "$PR" vendor/hyigerINDX.ini -n 0.6 --std 0.4
python3 tools/build_printer_preset.py "$PR" printer -n 0.6
python3 tools/build_printer_preset.py "$PR" printer -n 0.4 -n 0.25 --std
python3 tools/derive_filaments.py "$PR" filaments/hyigerINDX-0.6-filaments.ini -n 0.6
python3 tools/derive_std_filaments.py "$PR" filaments/hyigerINDX-0.4-filaments.ini -n 0.4
python3 tools/derive_std_filaments.py "$PR" filaments/hyigerINDX-0.25-filaments.ini -n 0.25
```

The committed artifacts were generated from PrusaResearch **2.5.11**. Run the
tools without `python3 -I`: they import each other from `tools/`.

After any change to the generators, confirm the committed bundle is still
reproduced exactly:

```python
import sys; sys.path.insert(0, 'tools')
from build_print_profiles import load, resolve
a, b = load('/tmp/new.ini'), load('vendor/hyigerINDX.ini')
names = [k for k in a if k.startswith('print:') and not k.startswith('print:*')]
assert all(resolve(a, k) == resolve(b, k) for k in names)
```

Compare **resolved** profiles, not raw text. Which keys sit in the hidden common
versus the tier overrides is an implementation detail that shifts legitimately.

## PrusaSlicer behaviours that dictate the design

Verified against the `version_2.9.6` tag. Re-check before assuming any still
holds.

- **Inheritance never crosses bundle files.** `*INDX_06hf_common*` lives in
  `PrusaResearch.ini` and cannot be referenced from ours, so it is resolved and
  embedded. This is why the generators exist at all.
- **`templates_profile = 1` is load-bearing.** `Preset.cpp` rejects a preset
  whose vendor differs from the active printer's vendor unless the vendor is a
  templates profile. The INDX printer resolves to Prusa Research (vendor is
  inherited up the parent chain), so without the flag our profiles are
  invisible. The flag also exempts the bundle from needing a
  `[printer_model:]` section, which is what lets it attach to Prusa's printer
  instead of cloning it.
- **Filaments must not live in the vendor bundle.** `PresetBundle.cpp` appends
  ` @Template` to filament preset names in a templates bundle, and `Preset.cpp`
  hides them under the `no_templates` preference. Print presets are exempt from
  both checks.
- **`=~` is `regex_match`, not `regex_search`.** Full-string match. So
  `COREONE_INDX8T` does **not** match `/(COREONE|COREONEOAK|...)/`, which is why
  CORE One profiles never reach an INDX printer and why Prusa's INDX conditions
  spell the models out.
- **Regex is boost, not std.** `USE_CPP11_REGEX` is commented out in
  `PlaceholderParser.cpp`, so `.` matches newline by default
  (`match_not_dot_newline` is opt-in and no flags are passed). Multi-line
  `printer_notes` conditions therefore work. Testing these with `std::regex` or
  Python's default `re` gives the **wrong answer** — use `re.S` to emulate.
- **User preset files on disk must be fully flattened.** `load_presets` does
  `preset.config = default_preset.config; preset.config.apply(config)` — it
  applies over PrusaSlicer defaults, *not* over the `inherits` parent. A
  delta-only user preset silently gets wrong values. Config *bundles* are no
  different for installed parents: `flatten_configbundle_hierarchy` resolves
  `inherits` only between sections of the same file, and `load_configbundle`
  then loads each section as defaults plus its own keys. An `inherits` naming
  an installed system preset is kept as the link but never applied, so bundle
  sections must be flattened too, as every generator here does.
- **`renamed_from` is never inherited.** `flatten_configbundle_hierarchy`
  skips it when merging parents: it belongs to one concrete preset. `resolve()`
  drops it the same way, and generated presets are new presets, so they never
  carry one.
- **Prusa keeps unreleased profiles as comments.** `; [printer:...]` /
  `; key = value` blocks in PrusaResearch.ini (the INDX 0.25 printer, the
  `Prusament PLA/PETG @COREONEINDX 0.25` filaments). `load_drafts()` reads them.
  They are Prusa's own intent, so they count as sourced.
- **Vendor bundles may omit keys.** Anything the chain doesn't set falls back to
  PrusaSlicer defaults. Emit only what is sourced; pinning defaults risks
  freezing a value Prusa later changes.
- **Vendor ID is the filename stem**, and preset names must be globally unique
  across all vendors. Two bundles carrying the same preset names register as two
  vendors and produce duplicate-preset errors. Hence one bundle for all sizes.
- **`.idx` is not needed to load.** `load_system_presets` iterates `.ini` files
  in `<datadir>/vendor/` only. The `.idx` exists for the online update
  mechanism and convention.
- **Config bundle export omits system presets.** `export_configbundle` skips
  them unless `export_system_settings` is true, and nothing in the GUI sets it.
  If someone shares a config bundle expecting it to contain installed Prusa
  profiles, it won't. Ask for `PrusaResearch.ini` instead, or have them use
  File → Export → Export Config, which writes `full_config()` — the resolved
  print + filament + printer values regardless of origin.

## Data model

`PrusaResearch.ini` contains per-nozzle INDX commons for 0.25 / 0.3 / 0.5 / 0.6
/ 0.8 (the high-flow ones named `*INDX_05hf_common*` and so on since 2.5.11).
All define complete geometry. Prusa's own 0.25 and 0.3 print profiles use
theirs; the high-flow ones are still unreleased scaffolding.

Only `*INDX_025_common*` has a real speed pass. The rest inherit
`perimeter_speed = 250` / `infill_speed = 300` from `*INDX_common*`, which at
0.68 × 0.25 is 39–47 mm³/s and unreachable. So:

- **geometry** → sourced verbatim, always
- **speeds** → derived only where upstream has no pass, and only where
  `nozzles.py` supplies flow targets

Speeds are solved backward from volumetric targets using PrusaSlicer's own
extrusion geometry, `A = w·h − h²(1 − π/4)` (`Flow::mm3_per_mm`). Keep that
formula exact; approximating it produces speeds that miss the target rate.

Filament MVS is ratio-scaled off the INDX 0.4 value using Prusa's CORE One
`HF0.4` → `HF<dia>` pair. Non-MVS keys transfer **only** where INDX agreed with
CORE One at 0.4 — where INDX differs it made a deliberate toolchanger choice
that must survive.

## Conventions

- Profile names: `<layer>mm <Tier> @COREONEINDX HF<dia>`, layer height to two
  decimals (`0.20mm`, not `0.2mm`). Prusa's format. Standard nozzles drop the
  `HF`: `@COREONEINDX 0.4`, `Prusa CORE One INDX 8T 0.4 nozzle`, as Prusa names
  its own STD variants.
- The star `★` marks the **recommended default only** — one per nozzle size, on
  Balanced. It is not a decoration for every profile.
- Hidden parents use asterisks: `*COREONEINDX HF0.6*`. PrusaSlicer strips these
  during flattening and never shows them.
- Commit messages explain *why* a value changed, with the number that motivated
  it. The git log is part of the provenance record.

## Adding a nozzle size

1. Add a `Nozzle(...)` entry to `NOZZLES` in `tools/nozzles.py`. Layer ladders
   come from Prusa's CORE One profiles for the same nozzle — read them out, do
   not invent them.
2. Supply `flow` targets only with a defensible basis, and set
   `validated=False` until printed.
3. Build with `-n <dia>`, generate the matching filament bundle, commit both.
4. Update the README tables and the `.idx`.

## Things that look wrong but aren't

- **`0.2` is rejected.** Prusa's smallest INDX common is 0.25. Not a bug.
- **0.3 has no flow targets.** Extrapolating from the 0.4/0.6 anchors predicts
  ~17 mm³/s where the tuned 0.25 profile runs 3.7 — the curve collapses below
  0.4. Deliberately left underived.
- **`derive_filaments.py` refuses 0.25 and 0.3.** Prusa publishes filament
  variants for HF0.5, HF0.6, HF0.8 and 0.8 only. Nothing to scale against.
- **…but `derive_std_filaments.py` builds 0.25.** It scales nothing: a
  standard 0.25 is built from Prusa's INDX 0.25 bases and drafts. The two tools
  answer different questions.
- **`build_print_profiles.py` refuses 0.25 and 0.3.** Prusa ships print
  profiles for both (`shipped` in `nozzles.py`); building them would duplicate
  Prusa's.
- **Standard 0.4 prints bind on `! nozzle_high_flow[0]`, HF0.6 on diameter
  only.** Without the flag the standard copies would appear on Prusa's HF0.4
  printer next to Prusa's own identical profiles.
- **Printer layer G-code differs from Prusa's in one place.** The PET-family
  dock-fan check is `=~/(PET|CPE|PCTG).*/`, because Prusa's `/(PET|CPE|PCTG)/`
  never matches `PETG` (full-string `regex_match`). Reported upstream as
  prusa3d/PrusaSlicer-settings-prusa-fff#50; `DOCK_FAN` in
  `build_printer_preset.py`, which goes quiet once Prusa changes the pattern.
- **Filament notes are appended to, never replaced.** The INDX start G-code
  reads `MBL160` / `HT_MBL10` out of `filament_notes`.
- **`@COREONE 0.8` MVS is lower than `HF0.6`** (Prusament PLA 19 vs 30). That is
  a standard brass nozzle, not high-flow. Do not use it as a CHT 0.8 anchor.
- **Binding includes `nozzle_high_flow[0]`** where upstream commons check
  diameter only. Intentional, harmless, documented in the README.
