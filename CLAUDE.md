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
2. **Record provenance for anything changed.** `COMMON_EDITS` and `Nozzle.extra`
   in `nozzles.py`, `STD_EDITS` in `build_print_profiles.py`, `TRANSFER` /
   `RETARGET` / `DRAFT_ADOPT` in `build_printer_preset.py`, `COMMON_ADOPT` in
   `derive_filaments.py` and `STD_SKIP` in `derive_std_filaments.py` all carry a
   reason string per key, and every generator writes its changed keys and their reasons
   into the file it emits. Keep that pattern: a new override channel without a
   reason string is the failure mode to watch for.
3. **Mark unvalidated output as unvalidated.** `Nozzle.validated` drives a
   warning banner in stdout and a comment in the emitted file, in the print
   bundle, the printer presets and the high-flow filament bundles alike; and
   `STD_VALIDATED` does the same for every `--std` output. Don't quietly
   promote extrapolated numbers, and don't treat sourced as validated:
   validated means test printed.
4. **Byline is `hyiger`.** Never use a real name in profiles, commits, README
   or generated file headers. Commit as
   `hyiger <43388146+hyiger@users.noreply.github.com>` — never a personal mail
   address. (`0370c2f` predates this rule and still carries one; rewriting it
   would need a force-push, so it is left alone deliberately.)
5. **Regenerate, don't hand-edit.** `vendor/*.ini` and `filaments/*.ini` are
   build artifacts. Editing them directly desynchronises them from the tools.

## Layout

```
vendor/hyigerINDX.ini      GENERATED  print profiles, all nozzle sizes
vendor/hyigerINDX.idx      handwritten  version index
filaments/hyigerINDX-*.ini GENERATED  one bundle per nozzle size
printer/*.ini              GENERATED  flattened printer presets
personal/*.ini             FOREIGN    exports from the Filament DB app
personal/README.md         handwritten  why they don't import as a bundle
tools/nozzles.py           handwritten  per-nozzle config table — start here
tools/build_print_profiles.py  GENERATOR  vendor bundle (HF sizes, --std 0.4)
tools/build_printer_preset.py  GENERATOR  printer presets (HF sizes, --std)
tools/derive_filaments.py      GENERATOR  high-flow filament bundles
tools/derive_std_filaments.py  GENERATOR  standard-nozzle filament bundles
LICENSE                    AGPL-3.0, this repo's own work only
```

`personal/*.ini` are **not** hand-made and not derived from `PrusaResearch.ini`:
each one is an export from the user's own Filament DB app, as its first line
says. Non-negotiable 5 still applies, but the generator is that app — a fix
belongs in its exporter, never in the committed file. They also carry two keys
PrusaSlicer does not define, so they cannot be imported as a config bundle; see
`personal/README.md`.

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

The committed artifacts were generated from PrusaResearch **2.5.12**. PrusaSlicer
auto-updates that file in place, so the path above may now hold a newer release:
check `grep -m1 ^config_version "$PR"` before regenerating. Running the recipe on
a newer file silently re-pins every artifact to it — that is a deliberate,
reviewable change, not a regeneration. PrusaSlicer snapshots the old bundle
before each upgrade (`<datadir>/snapshots/<timestamp>/vendor/PrusaResearch.ini`,
`reason = upgrade`), so point `PR` there to reproduce the committed artifacts.
Line numbers cited in this file and the README are 2.5.12's. A release does not
shift them uniformly — 2.5.11 → 2.5.12 moved the printer and print drafts by 10
and the `*C1INDX_*_PA*` sections by anything from 32 to 125 — so re-grep the
section name rather than applying an offset.

When re-pinning, diff the old and new `PrusaResearch.ini`, not just the
artifacts. An upstream change the generators do not read leaves every artifact
unchanged: 2.5.12's `*C1INDX_06_common*` changed nothing until
`derive_filaments.py` was taught to apply it. Grep for new INDX filaments and
print profiles, new commented drafts (`^; \[`), changes to `*C1INDX_*_PA*`, and
changes to the INDX `compatible_printers_condition` lines. Run the tools without
`python3 -I`: they import each other from `tools/`.

After any change to the generators, confirm the committed bundle is still
reproduced exactly:

```python
import sys; sys.path.insert(0, 'tools')
from build_print_profiles import load, resolve
a, b = load('/tmp/new.ini'), load('vendor/hyigerINDX.ini')
names = sorted({k for k in list(a) + list(b)
                if k.startswith('print:') and not k.startswith('print:*')})
assert all(dict(resolve(a, k)) == dict(resolve(b, k)) for k in names)
```

Both details matter. `resolve()` returns an `OrderedDict`, whose `__eq__` is
order sensitive, so comparing them directly fails on exactly the common-vs-tier
shift the next paragraph calls legitimate — hence `dict()`. And taking `names`
from both files, not just the new one, is what catches a **dropped** profile:
with `names` from `a` alone, forgetting `--std 0.4` drops four profiles and the
assert still passes. An added or dropped profile surfaces as
`KeyError: <preset name>` from `resolve()` rather than as a failed assert.

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
  ` @Template` to filament preset names in a templates bundle, and
  `Preset.cpp:435` hides them under the `no_templates` preference. Print presets
  are exempt from **those two** checks — both are guarded on
  `type == TYPE_FILAMENT`. They are *not* exempt from the third gate:
  `PresetComboBoxes.cpp` only pushes a templates-vendor preset into a combo box
  `if (allow_templates)` (323/335, 1138, 1419), with no type test at all, so
  setting the `no_templates` preference hides this bundle's print profiles from
  the sidebar and the Print Settings tab. It is off by default. Any claim that
  print presets are simply exempt from `no_templates` is wrong.
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
  `; key = value` blocks in PrusaResearch.ini. `load_drafts()` reads them. They
  are Prusa's own intent, so they count as sourced. At 2.5.12 (unchanged from
  2.5.11) there are more than the 0.25 pair this file used to name:
  - **6 INDX printers** — 8T and 4T at `0.25`, `HF0.6`, `HF0.8`
    (`56634-56710`). Used, two ways. The four HF drafts: `build()` applies the
    CORE One delta, compares the result against the draft, adopts the keys in
    `DRAFT_ADOPT` and refuses on any other disagreement. The two `0.25` drafts:
    `build_std()` re-resolves the parent the draft names and applies every draft
    key over it, with no `DRAFT_ADOPT` gate and no comparison — at that size
    there is no CORE One delta, so the draft is the only INDX-specific source. The 4T `HF0.6`/`HF0.8` drafts are upstream-buggy
    (`inherits = *C1_INDX_8T_common*`, 8-wide `nozzle_diameter` on a 4-tool
    machine), which is why only uniform scalar values are taken and re-widened.
  - **2 INDX 0.25 filaments** — `Prusament PLA` / `PETG`. Used as written.
  - **10 INDX print profiles** at `HF0.5`/`HF0.6`/`HF0.8`, four / four / two
    (`57206-57299`). Not used: the HF0.5 and HF0.6 drafts only restate the
    unreachable 250/200 they inherit; the two HF0.8 drafts set their own
    200 / 160-120 / 160-120 / 200-120 but leave infill at the inherited 300 (see
    "Data model"); and the HF0.6 ladder/tier naming is taken from CORE One HF0.6
    instead. The HF0.5 drafts' first three rungs are the 0.5 ladder `nozzles.py`
    uses.
  - **416 INDX filament drafts** at `HF0.5`/`HF0.6`/`HF0.8` — 135 / 144 / 137
    sections, 144 distinct filaments (the 0.5 and 0.8 name sets are subsets of
    0.6's). Pressure advance is taken from them where they set one; MVS is not —
    see "Things that look wrong but aren't".

  A new release can add more. Grep `^; \[` before assuming a size has no Prusa
  source.
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

Only `*INDX_025_common*` has a real speed pass. "No pass upstream" is a claim
about the **commons**, not about Prusa's profiles: the commented `HF0.8` print
drafts do set profile-level speeds (perimeter 200, external 160/120, small
160/120, solid 200/120), which at that common's 0.9 mm widths, each draft at its
own layer height, is 39-65 mm3/s, and they leave infill at the inherited 300,
which is 75-98 mm3/s. No HF0.8 filament Prusa ships allows more than 39, and
Prusa's own commented `Prusament PLA @COREONEINDX HF0.8` draft resolves to 36, so
the drafted perimeter and the inherited infill are unusable. The rest inherit
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

Pressure advance is the one value that is never scaled or inherited across
sizes, because Prusa publishes it per nozzle: `*C1INDX_<FAM>_<NN>_PA*` for
PLA/PET/ABS/PC at `04`/`05`/`06`/`08`, plus the nozzle-independent
`*C1INDX_FLEX_PA*`. Prusa's own structure gives the mapping —
`*PLA06HFC1INDX*` inherits `*C1INDX_PLA_06_PA*` — so `derive_filaments.py` reads
the family section out of the HF0.4 chain and swaps the nozzle token, preferring
a figure Prusa typed into its commented `<mat> @COREONEINDX HF<dia>` draft where
there is one. Prusa's INDX PA **falls** as the nozzle grows (PLA 0.031 → 0.02,
PET 0.048 → 0.031, ABS 0.02 → 0.015, PC 0.05 → 0.025), which is the opposite of
what a CHT's longer melt path would suggest, so do not "correct" it upward.

Since 2.5.12 Prusa also publishes the INDX toolchanger common per nozzle:
`*C1INDX_06_common*` and `*C1INDX_08_common*` inherit `*C1INDX_common*` and
change two keys (wipe-tower minimal purge 10 → 14 / 20,
`filament_retract_restart_extra_toolchange` unset → 0.04 / 0.05), and the 0.6
and 0.8 family sections inherit them in its place. Prusa's sized chains swap the
whole family section, not just the common: `Prusament PLA @COREONEINDX HF0.4`
inherits `*PLAHFC1INDX*`, its commented HF0.6 draft `*PLA06HFC1INDX*`. (Most
drafts do; the BVOH drafts carry no INDX family and PC Blend CF's takes
`*PC06PGC1INDX*`, which stands on the same common.) So
`derive_filaments.py` works per base:
- the 0.4 family is the one section of the base's chain that inherits
  `*C1INDX_common*` directly (structure);
- its sized counterpart is named by the same token swap PA uses
  (`*PLAHFC1INDX*` → `*PLA06HFC1INDX*`, `*FLEX04PGC1INDX*` → `*FLEX06PGC1INDX*`),
  and a missing one refuses;
- the per-nozzle common is whichever parent of that counterpart reaches
  `*C1INDX_common*`, under any name (structure again), so a rename or an
  intermediate section is followed, not silently dropped;
- nothing after that common in the counterpart (its own body, later parents)
  may set a toolchanger key, or the build refuses: such a value would override
  the common and be misattributed to it;
- the base is re-resolved with the family swapped, and each `COMMON_ADOPT` key
  takes the value from that chain.

The swap makes the 0.4 family's body and anything inherited before it give way,
as in Prusa's chain. A value the 0.4 preset sets in its own body survives as an
own override, whether or not it agreed with anything; that is this repo's choice,
not Prusa's (Prusa's HF0.6 drafts for FLEX and TPU 95A resolve to purge 14; ours
keep their 0.4 15). Do not reduce this to a
value comparison against `*C1INDX_common*`: a key it leaves unset can arrive from a
generic CORE One or MK4 ancestor, and an equality test would mistake that for an
INDX choice. Only keys in `COMMON_ADOPT` (key → reason, like `DRAFT_ADOPT`) are
taken. The tool refuses on any other changed key, on a per-nozzle common that drops
a shared key, and on a missing or ambiguous family, so a re-pin cannot slip a
toolchanger change in unreviewed. There is no `04` or `025` common, so the
standard bundles are untouched.

Filament binding: every generated filament keeps its HF0.4 base's
`printer_model=~/(...)/` clause (`printer_models()` in `build_print_profiles.py`)
and appends its own nozzle test. Prusa scopes the model list per family — since
2.5.12 ABS, PC and PA leave out the CORE One L INDX, which gets its own
`*C1LINDX_CH_*` chamber values — so a fixed list would silently diverge.

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
- **`derive_filaments.py` refuses 0.25 and 0.3.** Prusa publishes standard
  filament variants at 0.6 and 0.8 and high-flow ones at HF0.5, HF0.6 and HF0.8;
  at 0.25 and 0.3 there is nothing in either family to scale against. (The
  non-HF fallback is load-bearing, not a corner case: 9 of the 19 committed 0.6
  presets come from an `@COREONE` -> `@COREONE 0.6` pair. At 0.5 there is no
  plain `@COREONE 0.5`, so `-n 0.5` covers only 8 of the 20 materials.)
- **…but `derive_std_filaments.py` builds 0.25.** It scales nothing: a
  standard 0.25 is built from Prusa's INDX 0.25 bases and drafts. The two tools
  answer different questions.
- **Generic PVA is in no bundle.** Prusa added it in 2.5.12 as an INDX-only
  preset with no CORE One PVA. `derive_filaments.py` prints it as
  `NO REFERENCE - skipped`; `derive_std_filaments.py` skips it through
  `STD_SKIP`, a reviewed, named list, and refuses if a CORE One STD PVA ever
  appears so the entry gets reviewed again. Any other material without a CORE
  One STD counterpart still refuses. Adding to `STD_SKIP` is a human decision.
- **The standard ABS presets bind to `COREONE_INDX4T` although Prusa's
  `*ABSPGC1INDX*` does not.** At 2.5.12 that base reads
  `printer_model=~/(COREONE_INDX8T|COREONE_INDX4)/`, which under full-string
  `regex_match` never matches `COREONE_INDX4T`. The clause is taken from the
  HF0.4 base (`*ABSHFC1INDX*`, which spells both models), never from the
  swapped-in STD base, so the upstream typo does not reach the bundle.
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
- **HF0.6 pressure advance is *lower* than HF0.4** (Prusament PLA 0.02 vs
  0.038). Prusa's own per-nozzle figures go that way. See "Data model".
- **The HF0.6 printer preset's `retract_length` is 0.7, not the 0.8 its chain
  resolves.** Prusa's commented INDX HF0.6 printer draft says 0.7, and a draft
  written for this nozzle on this toolchanger outranks a value inherited from the
  HF0.4 chain. `DRAFT_ADOPT` in `build_printer_preset.py` records the decision;
  any *unlisted* draft disagreement refuses instead.
- **`build_printer_preset.py -n 0.8` works, but `--list` still calls 0.8
  unvalidated.** The printer preset is fully sourced from Prusa's HF0.8 draft.
  The *flow targets* in `nozzles.py` are still extrapolated, and neither has been
  printed. Two different claims, both true.
- **`min_bead_width = 90%` on the HF0.6 Draft tier** where every `@COREONE
  HF0.6` profile says 85%. It is a deliberate transfer of Prusa's own Draft-tier
  choice (`0.25mm Draft @COREONEINDX HF0.4`), with the reason recorded in
  `Nozzle.extra`. HF0.6 is test printed with it.
- **Prusa's commented HF0.6 filament drafts set an MVS that is not used.**
  Prusament PLA drafts 30 where the ratio rule gives 35. All three divergent MVS
  figures are typed in the draft's own body — `load_drafts()` reads nothing else,
  so nothing inherited can reach the report — but each restates the value its
  CORE One parent already supplies (FLEX 3.5, PLA 30, TPU 4, against INDX HF0.4
  baselines of 2 / 28 / 2). Adopting one would swap the INDX flow baseline for the
  CORE One one, and 35 is the test-printed value, so the ratio rule stands. (Three
  further drafts — Prusament ASA, PC Blend CF, Generic PETG — differ only through
  an MVS they inherit and never type, which is why the report cannot see them.) — but `derive_filaments.py` prints every divergence rather than hiding
  it. Pressure advance is the exception: drafts win there.
- **Binding includes `nozzle_high_flow[0]`** where upstream commons check
  diameter only. Intentional, harmless, documented in the README.
