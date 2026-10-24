# CLAUDE.md

Context for AI assistants working in this repo. `README.md` is the user guide
(install, verify, calibrate, known gaps); `docs/PROVENANCE.md` is where every
value comes from and why, for readers who want the detail; this file is for
whoever edits the code. Keep the README short: derivation detail belongs in
`docs/PROVENANCE.md`.

## What this is

PrusaSlicer profiles for Prusa CORE One INDX toolheads at nozzle sizes Prusa
ships no INDX printer for (its only variant is `HF0.4`): high-flow HF0.6, HF0.8
and HF1.0, and standard, non-high-flow 0.4 and 0.25. Since bundle 0.7.0 it also
carries one **mixed tool layout**, `0.25+HF0.4`: different nozzles on different
tools of one toolchanger, which is Prusa's own experimental workflow
(help.prusa3d.com article 821176) worked through for the INDX. A layout is
composed from the single-nozzle presets here, not derived; see "Mixed tool
layouts" below. HF0.6, HF0.8, HF1.0 and
standard 0.4 print profiles install as read-only **system presets** via a vendor bundle.
HF1.0 is the one size Prusa publishes nothing for; it is 0.8 scaled up, under
the exception to non-negotiable 1. At 0.25 the print
profiles are Prusa's own `@COREONEINDX 0.25`, so only the printer and filaments
come from here. Filament presets ship as one importable config bundle per size;
printer presets ship as flattened user presets.

Nearly everything is **generated** from Prusa's own `PrusaResearch.ini`. The
value of this repo is its provenance discipline, not its cleverness. Preserve
that.

## Non-negotiables

1. **Never invent a slicer value.** Every number is resolved from
   `PrusaResearch.ini`, derived by a documented, reproducible rule, or is one of
   the few chosen inputs whose basis is recorded beside it: the `flow` targets
   in `nozzles.py` (every derived speed is solved from them) and the
   `COMMON_EDITS` `bridge_speed = 30` and `interlocking_beam_width` (2 ×
   nozzle). A new chosen input needs a defensible basis, a reason string and
   `validated=False` until printed. Where none of this is possible, the tool
   must **refuse** — see `derive_filaments.py` refusing 0.25 (no CORE One 0.25
   filament pair to scale MVS against) and `derive_std_filaments.py` refusing a
   material with no CORE One STD counterpart. A loud failure beats a plausible
   fabrication. (`flow=None` in `nozzles.py` is not a refusal: it passes
   Prusa's own speeds through untouched.) `personal/*.ini` are outside this
   rule.

   **One exception, approved by the repo owner on 2026-10-21: HF1.0, scaled
   from 0.8 by 1.0/0.8.** Prusa publishes nothing at 1.0 (no INDX common, no
   print, printer or filament profile, no draft, no PA section), so nothing can
   be resolved. It is built from 0.8 by one rule, `SCALED SIZES` in
   `nozzles.py`: only lengths proportional to the nozzle (the line widths, the
   layer ladder, the printer's layer-height limits) are scaled by 1.25, rounded
   half-up to 0.01; values that merely name the size are moved; **everything
   else is held** at 0.8, apart from the per-size `COMMON_EDITS`, which apply as
   at every size (`interlocking_beam_width` 2 × nozzle). The premise is checked,
   not assumed: `assert_unsourced()` in `build_print_profiles.py` makes all
   three generators refuse if the PrusaResearch.ini they read publishes
   anything at 1.0. The rule may not be extended to other value types, applied
   to any other size, or used for a size Prusa has *any* source for, without a
   new approval from the owner; the code is general, the approval is not.
   HF1.0 is always `validated=False`, and every scaled or moved key carries a
   reason in the emitted file.
2. **Record provenance for anything changed.** `COMMON_EDITS` and `Nozzle.extra`
   in `nozzles.py`, `STD_EDITS` in `build_print_profiles.py`, `TRANSFER` /
   `DRAFT_ADOPT` / `DOCK_FAN` in `build_printer_preset.py`, `COMMON_ADOPT` in
   `derive_filaments.py` and `STD_SKIP` (per material) in
   `derive_std_filaments.py` carry a reason string per entry, as do
   `SIZE_LABELS` in `nozzles.py` and `SCALED_PRINTER` in
   `build_printer_preset.py` for HF1.0, and, for a mixed layout,
   `Layout.extra` in `nozzles.py`, `LAYOUT_BASE` / `ROLE_ANCHOR` /
   `ROLE_WHY` / `RENAME_WHY` in `build_print_profiles.py` and `MIXED_SCALAR`
   in `build_printer_preset.py` (`EXTRUDER_KEYS`, `ROLE_KEYS` and
   `ROLE_SPEED_WIDTH` are copied out of PrusaSlicer and cite their source
   lines instead of carrying a reason); `scale_common()` and `build_scaled()`
   write a generated reason for every scaled key. `RETARGET`
   (printer pointer templates) and `derive_filaments.py`'s `TRANSFER` (a bare
   key list) are each covered by one rule stated in their comment instead.
   Where the reasons surface varies. The printer presets list every changed key
   in their header, with the `DRAFT_ADOPT` / `DOCK_FAN` reason or a generic line
   (`TRANSFER`, `RETARGET`, the 0.25 draft). Each filament preset records its
   MVS, PA and per-nozzle-common provenance in `filament_notes`, and a filament
   bundle's header prints the `COMMON_ADOPT` reasons for any per-nozzle common
   it uses (at 2.5.12 only the high-flow bundle uses one). `STD_SKIP` reasons
   and `derive_filaments.py`'s `TRANSFER` moves go to stdout only. The print
   bundle's header lists, per size, every `COMMON_EDITS`, `Nozzle.extra` and
   `STD_EDITS` key whose value it changes, with its reason (`why_lines()`), and
   the flow targets the speeds are solved from. Keep the reason strings: a new
   override channel without one is the failure mode to watch for.
3. **Mark unvalidated output as unvalidated.** `Nozzle.validated` drives a
   warning banner in stdout and a comment in the emitted file, in the print
   bundle, the printer presets and the high-flow filament bundles alike;
   `STD_VALIDATED` does the same for every standard-nozzle output: `--std` on
   the two build tools, and both `derive_std_filaments.py` bundles; and
   `Layout.validated` does it for a mixed layout's print profiles and printer
   preset. A layout composed entirely from printed sizes is still unprinted as
   a layout: `0.25+HF0.4` is built from two test-printed setups and is
   `validated=False`. Don't
   quietly promote extrapolated numbers, and don't treat sourced as validated:
   validated means test printed.
4. **Byline is `hyiger`.** Never use a real name in profiles, commits, README
   or generated file headers. Commit as
   `hyiger <43388146+hyiger@users.noreply.github.com>` — never a personal mail
   address. (`0370c2f` predates this rule and still carries one; rewriting it
   would need a force-push, so it is left alone deliberately.)
5. **Regenerate, don't hand-edit.** `vendor/hyigerINDX.ini`, `printer/*.ini`
   and `filaments/*.ini` are build artifacts. Editing them directly
   desynchronises them from the tools.

## Layout

```
vendor/hyigerINDX.ini      GENERATED  print profiles: HF0.6, HF0.8, HF1.0, standard 0.4, mixed 0.25+HF0.4 (plain 0.25 uses Prusa's)
vendor/hyigerINDX.idx      handwritten  version index
filaments/hyigerINDX-*.ini GENERATED  one bundle per nozzle size
printer/*.ini              GENERATED  flattened printer presets, one per size plus one per mixed layout
personal/*.ini             FOREIGN    exports from the Filament DB app
personal/README.md         handwritten  why they don't import as a bundle
docs/PROVENANCE.md         handwritten  provenance and design deep-dive
tools/nozzles.py           handwritten  per-nozzle and per-layout config table — start here
tools/build_print_profiles.py  GENERATOR  vendor bundle (HF sizes, --std 0.4)
tools/build_printer_preset.py  GENERATOR  printer presets (HF sizes, --std)
tools/derive_filaments.py      GENERATOR  high-flow filament bundles
tools/derive_std_filaments.py  GENERATOR  standard-nozzle filament bundles
tests/test_generators.py   handwritten  synthetic-INI tests of refusals and guards
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
python3 tools/build_print_profiles.py "$PR" vendor/hyigerINDX.ini -n 0.6 -n 0.8 -n 1.0 --std 0.4 --layout 0.25+HF0.4
python3 tools/build_printer_preset.py "$PR" printer -n 0.6 -n 0.8 -n 1.0
python3 tools/build_printer_preset.py "$PR" printer -n 0.4 -n 0.25 --std
python3 tools/build_printer_preset.py "$PR" printer --layout 0.25+HF0.4
python3 tools/derive_filaments.py "$PR" filaments/hyigerINDX-0.6-filaments.ini -n 0.6
python3 tools/derive_filaments.py "$PR" filaments/hyigerINDX-0.8-filaments.ini -n 0.8
python3 tools/derive_filaments.py "$PR" filaments/hyigerINDX-1.0-filaments.ini -n 1.0
python3 tools/derive_std_filaments.py "$PR" filaments/hyigerINDX-0.4-filaments.ini -n 0.4
python3 tools/derive_std_filaments.py "$PR" filaments/hyigerINDX-0.25-filaments.ini -n 0.25
```

The committed artifacts were generated from PrusaResearch **2.5.12**. PrusaSlicer
auto-updates that file in place, so the path above may now hold a newer release:
check `grep -m1 ^config_version "$PR"` before regenerating. Running the recipe on
a newer file silently re-pins every artifact to it — that is a deliberate,
reviewable change, not a regeneration. PrusaSlicer snapshots the old bundle
before each upgrade (`<datadir>/snapshots/<timestamp>/vendor/PrusaResearch.ini`,
`reason = upgrade`), so to reproduce the committed artifacts point `PR` at the
snapshot whose copy reports `config_version = 2.5.12`: the one taken when 2.5.12
was replaced, not necessarily the newest. `PrusaResearch.ini` line numbers cited
in this file and docs/PROVENANCE.md are 2.5.12's; PrusaSlicer source line numbers are
`version_2.9.6`'s. A release does not shift INI lines uniformly — 2.5.11 →
2.5.12 moved the printer and print drafts by 10 and the `*C1INDX_*_PA*` sections
by anything from 32 to 125 — so re-grep the section name rather than applying an
offset.

When re-pinning, diff the old and new `PrusaResearch.ini`, not just the
artifacts. An upstream change the generators do not read leaves every artifact
unchanged: 2.5.12's `*C1INDX_06_common*` changed nothing until
`derive_filaments.py` was taught to apply it. Grep for new INDX filaments and
print profiles, new commented drafts (`^; \[`), changes to `*C1INDX_*_PA*`, and
changes to the INDX `compatible_printers_condition` lines. Run the tools without
`python3 -I`: they import each other from `tools/`.

After any change to the generators, run the synthetic-INI tests, which need no
`PrusaResearch.ini`:

```bash
python3 -m unittest discover -s tests -v
```

A new refusal gets a test there that shows it fires and writes no output file.
Then rebuild every artifact from the pinned
2.5.12 `PrusaResearch.ini` into a scratch directory with the recipe above, and
check all three outputs. `diff -r` against `printer/` and `filaments/` must be
empty: those files are fully flattened with sorted keys, so text equality is
exact. The print bundle is compared resolved instead. With the scratch build at
`/tmp/new.ini`, from the repo root:

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

## PrusaSlicer behaviors that dictate the design

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
  are exempt from **those two** checks: the suffix is added only in the
  `filament:` branch of `load_configbundle` (`PresetBundle.cpp:1529-1533`), and
  `Preset.cpp:435` tests `type == TYPE_FILAMENT`. They are *not* exempt from two
  type-agnostic gates. `PresetComboBoxes.cpp` only pushes a templates-vendor
  preset into a combo box `if (allow_templates)` (323/335, 1138, 1419), so the
  `no_templates` preference (off by default) hides this bundle's print profiles
  from the sidebar and the Print Settings tab. And
  `PresetCollection::update_compatible_internal` (`Preset.cpp:1387-1398`) marks
  a templates-vendor preset incompatible whenever a compatible non-templates
  preset has the same alias (the name before `@`, trimmed). The `--std 0.4`
  copies share all four aliases with Prusa's HF0.4 prints. The filter never
  fires only because the two sets bind on opposite `nozzle_high_flow[0]`
  clauses, so no printer accepts both. Any claim that print presets are simply
  exempt from template handling is wrong.
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
  drops inherited ones the same way, and every generator also pops the base's
  own, since each emits new presets, not renames: `build_nozzle()`, the `--std`
  print path, `build_printer_preset.py` (the base, the 0.25 draft and its
  parent, and both sides of the CORE One delta, where it would otherwise read
  as an unreviewed key) and both filament generators. Prusa's INDX sections
  carry none at 2.5.12, so this changes no artifact.
- **Prusa keeps unreleased profiles as comments.** `; [printer:...]` /
  `; key = value` blocks in PrusaResearch.ini. `load_drafts()` reads them. They
  are Prusa's own intent, so they count as sourced. At 2.5.12 (unchanged from
  2.5.11) there are:
  - **6 INDX printers** — 8T and 4T at `0.25`, `HF0.6`, `HF0.8`
    (`56634-56710`). Used, two ways. The four HF drafts: `build()` applies the
    CORE One delta, compares the result against the draft, adopts the keys in
    `DRAFT_ADOPT` and refuses on any other disagreement. The two `0.25` drafts:
    `build_std()` re-resolves the parent the draft names and applies every draft
    key over it, with no `DRAFT_ADOPT` gate. The CORE One HF0.4 → 0.25 delta
    (`Prusa CORE One 0.25 nozzle`, `STD_CHECK`) is not applied, only compared
    with the result: `cross_check()` prints each delta key where the draft-built
    preset ends up elsewhere, to stdout only. The owner chose that over adopting
    it. At 2.5.12 it prints jerk, 8,8 where the draft leaves INDX's 10,8, and
    `retract_length`, CORE One 0.8 against the draft's 0.7. Applying the delta
    could not work as written: jerk is not in `TRANSFER`, and a machine limit is
    a (normal, stealth) pair that `uniform()` reads as non-uniform per-tool
    values. Both 4T HF drafts say `inherits = *C1_INDX_8T_common*`, and the 4T
    `HF0.6` one also has an 8-wide `nozzle_diameter`; the 4T `HF0.8` one is
    4-wide throughout. Neither bug reaches the output. `inherits` is in
    `DRAFT_SKIP`, the base is always the shipping 4T HF0.4 preset, and every
    draft value must be uniform across tools or the tool refuses. Each value is
    compared as one scalar and written back widened to the base's arity.
  - **2 INDX 0.25 filaments** — `Prusament PLA` / `PETG`. Used as written.
  - **13 INDX print profiles.** Three at `HF0.4` (`0.20mm Balanced Strength`,
    `Soluble Full`, `Soluble Interface`; `57113-57138`): not used, since
    `--std 0.4` copies only the four released HF0.4 prints. Ten at
    `HF0.5`/`HF0.6`/`HF0.8`, four / four / two (`57206-57299`): not used either.
    The HF0.5 and HF0.6 drafts' speeds restate the 250/200 the commons carry
    (past every Prusa HF0.6 filament from the 0.25 mm layer up, though not at
    HF0.5's 0.15 / 0.20). Their other keys are per-layer: HF0.6 sets support and raft
    contact distance to the layer height (the common has 0.3 / 0.25) and top
    solid 5 at 0.20; HF0.5 sets 6/4 solid layers at 0.15 and top 5 at 0.20. The
    HF0.6 profiles here keep the common's 0.3 / 0.25 at every tier. The two HF0.8
    drafts set their own speeds but every one overruns the filaments (see "Data
    model"). The HF0.6 ladder (0.20 / 0.25 / 0.32) is taken from CORE One HF0.6
    instead; the tier names are this repo's own `TIERS` (Detail / Balanced ★ /
    Draft), not CORE One's SPEED / BALANCED / STRUCTURAL. The HF0.5 drafts'
    first three rungs are the 0.5 ladder `nozzles.py` uses.
  - **1042 INDX filament drafts.** 416 at `HF0.5`/`HF0.6`/`HF0.8` (135 / 144 /
    137 sections, 144 distinct filaments; the 0.5 and 0.8 name sets are subsets
    of 0.6's): pressure advance is taken from these where they set one; MVS is
    not (see "Things that look wrong but aren't"). The 2 at `0.25` are above. No
    generator reads the rest: 137 at `HF0.4`; 244 unsized `<mat> @COREONEINDX`
    drafts for the standard nozzle (26 do not resolve; of the other 218, 81
    bind `nozzle_diameter[0]==0.4 and ! nozzle_high_flow[0]` like
    `Prusament PLA @COREONEINDX`, 40 add `! nozzle_high_flow[0]` to an
    exclusion test, and the rest bind by exclusion or on diameter alone); 125 standard `0.6` and 113 standard `0.8`; 5 hidden `*INDX_PA_*`.
    `derive_std_filaments.py` reads drafts only at 0.25, so Prusa's standard-0.4
    drafts are unreviewed and disagree with the 0.4 bundle (Prusament PETG PA
    0.048 vs 0.058, bed 85 vs 90).

  A new release can add more. Grep `^; \[` before assuming a size has no Prusa
  source.
- **A role's flow uses that role's extruder's nozzle.** `PrintRegion::flow`
  (`PrintRegion.cpp:63`) reads `nozzle_diameter` at `this->extruder(role) - 1`,
  where `extruder(role)` is `perimeter_extruder` / `infill_extruder` /
  `solid_infill_extruder` (`PrintRegion.cpp:22-35`). Pin a role to one tool and
  every per-role width and speed key belongs to exactly one nozzle — which is
  what lets a mixed layout keep explicit widths where Prusa's article says to
  zero them (auto would be 1.125 × nozzle, `Flow::auto_extrusion_width`,
  `Flow.cpp:33`). A role left at `0` has no knowable nozzle.
- **Filament compatibility is evaluated per extruder, print compatibility is
  not.** `ExtruderFilaments::update_compatible_internal` (`Preset.cpp:2404-2415`)
  copies every per-extruder key's value at tool N into index 0 before evaluating
  a filament's `compatible_printers_condition`, whenever
  `single_extruder_multi_material` is 0 — which the INDX sets. So
  `nozzle_diameter[0]==0.4 and nozzle_high_flow[0]` tests *that tool's* nozzle,
  and the filament bundles here need no change for a mixed printer.
  `default_filament_profile` is the one per-extruder key the shift skips.
  `PresetCollection::update_compatible_internal` (`Preset.cpp:1352-1368`) does no
  such shift, so **print** presets always see tool 1.
- **An out-of-range vector index reads element 0; it does not throw.**
  `PlaceholderParser.cpp:1074` clamps to 0 when reading
  (`vector_element_to_expr`); only *assignment* throws (1152). So
  `nozzle_diameter[1]` in a `compatible_printers_condition` is safe on any
  printer, including a single-extruder one, where it compares tool 1 with
  itself. This matters because `is_compatible_with_printer` returns **true** on
  a parse error (`Preset.cpp:402-405`): a condition that threw would make the
  preset compatible with everything.
- **Mixed nozzle diameters are legal; two warnings and one hard rule.** With a
  wipe tower, differing diameters raise `_WIPE_TOWER_NOZZLE_DIAMETER_DIFFER`
  (`Print.cpp:567`), a warning, not an error; a support extruder left at `0`
  while diameters differ raises `_SUPPORT_NOZZLE_DIAMETER_DIFFER`
  (`Print.cpp:675-679`). The hard rule: with a wipe tower and non-soluble
  supports, `Print::validate` **rejects** the slice unless both support
  extruders are `0` — except when `support_material_style` is organic, which
  skips that branch entirely (`Print.cpp:685-692`). Pinning supports therefore
  forces organic supports. Layer height must also be ≤ the smallest *used*
  nozzle, and `first_layer_height` likewise (`Print.cpp:735-741`).
- **Per-extruder layer-height limits do not constrain a profile's layer
  height.** `SlicingParameters::create_from_config` widens them to include it
  (`Slicing.cpp:120-121`); they bound variable layer height and support layers
  only. PrusaSlicer's default ceiling, when `max_layer_height` is 0, is
  0.75 × nozzle (`Slicing.cpp:48`).
- **Infill combining is capped by the smaller of two nozzles.**
  `PrintObject::combine_infill` (`PrintObject.cpp:3126-3132`) caps the combined
  height at `min(nozzle[infill_extruder], nozzle[solid_infill_extruder])`, so
  keeping solid infill on a small nozzle caps combining at that nozzle however
  big the infill one is. `automatic_infill_combination` (2.9.6) caps at
  `min(automatic_infill_combination_max_layer_height, nozzle)`, defaulting to
  100% of the nozzle, so it is no more permissive — and its per-region layer
  count is not knowable in advance, which is why layouts set
  `infill_every_layers` instead.
- **PrusaSlicer only unifies nozzles on a single-extruder multimaterial
  printer.** Both "all extruders must have the same nozzle diameter" dialogs
  (`Tab.cpp:2742-2756` and `3252-3280`) are gated on
  `single_extruder_multi_material`, which the INDX sets to 0, so per-tool
  diameters are freely editable and stay as written.
- **The INDX start G-code already checks each tool's own nozzle.** Prusa emits
  `M862.1 T<n> P{nozzle_diameter[n]} A{filament_abrasive[n]} F{nozzle_high_flow[n]}`
  per used tool, so the firmware verifies a mixed layout without any change
  here. `assert_per_tool_nozzle_check()` refuses to write a layout preset if a
  re-pin ever collapses that to one tool.
- **`printer_variant` constrains nothing for a user preset.** A variant is
  validated only when loading a vendor bundle's `[printer:]` sections against
  the model's declared `variants` (`PresetBundle.cpp:1642-1659`), and
  `Preset::set_visible_from_appconfig` returns early when the preset has no
  vendor of its own (`Preset.cpp:425`), which every preset in `printer/` does.
  That is why `0.25`, `0.4` and `0.25+HF0.4` work as variant tags although Prusa
  declares only `HF0.4`.
- **An unknown key in a bundle section is silently dropped, not an error.**
  `load_configbundle` does not wrap `set_deserialize` per key, and
  `UnknownOptionException` derives from `ConfigurationError`, so a throw there
  would abort the whole bundle (`PresetBundle.cpp:1609, 1623-1624`). It never
  gets that far: `PrintConfigDef::handle_legacy` clears any key the config
  definition does not have (`PrintConfig.cpp:5383-5386`) and `set_deserialize`
  returns early on an empty key. That is why Prusa's own misspelled
  `top solid_infill_speed` in `*INDX_025_common*` is harmless, and why copying
  it verbatim into a layout's profiles is too.
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

`PrusaResearch.ini` contains per-nozzle INDX print commons for 0.25 / 0.3 / 0.5
/ 0.6 / 0.8 (the high-flow ones named `*INDX_05hf_common*` and so on since
2.5.11). All define complete geometry. Prusa ships print profiles on the 0.25
and 0.3 commons, but its only released INDX printers are HF0.4. The 0.25
printer is a commented draft (this repo's `printer/` 0.25 preset is built from
it). There is no 0.2 or 0.3 mm INDX nozzle, so `*INDX_03_common*` and its three
`@COREONEINDX 0.3` profiles are scaffolding no printer can select, as the
HF0.5/0.6/0.8 commons are upstream.

Only `*INDX_025_common*` has a real speed pass. "No pass upstream" is a claim
about the **commons**, not about Prusa's profiles: the commented `HF0.8` print
drafts do set profile-level speeds (perimeter 200, external 160/120, small
160/120, solid 200/120), which at that common's 0.9 mm widths, each draft at its
own layer height, is 39-65 mm3/s, and they leave infill at the inherited 300,
which is 75-98 mm3/s. No HF0.8 filament Prusa ships allows more than 39, and
Prusa's own commented `Prusament PLA @COREONEINDX HF0.8` draft resolves to 36,
so every drafted speed (39.1 mm³/s at the lowest) and the inherited infill
overrun it. None is used: the 0.8 speeds are solved from `nozzles.py` targets.
The 0.5, 0.6 and 0.8 commons (and `*INDX_03_common*`) inherit
`perimeter_speed = 250` / `infill_speed = 300` from `*INDX_common*`. At HF0.6's
0.68 mm width and a 0.25 mm layer that is 39–47 mm³/s, past every
`@COREONE HF0.6` filament Prusa ships (max 34). So:

- **geometry** → the common's, verbatim, except keys changed with a recorded
  reason: `interlocking_beam_width` (2× nozzle, `COMMON_EDITS`) and the HF0.6
  per-tier overrides in `Nozzle.extra` (Draft `min_bead_width` 90%, Detail 5/4
  solid layers). At a scaled size (1.0) the common is the source size's
  (`*INDX_08hf_common*`) with its eight line widths scaled ×1.25 and its two
  size labels moved (`scale_common()`); every other key is the 0.8 common's
- **speeds** → the six main speeds solved from `nozzles.py` flow targets, only
  where upstream has no pass and targets exist; `bridge_speed = 30` is a
  `COMMON_EDITS` value, not solved

Speeds are solved backward from volumetric targets using PrusaSlicer's own
extrusion geometry, `A = w·h − h²(1 − π/4)` (`Flow::mm3_per_mm`). Keep that
formula exact; approximating it produces speeds that miss the target rate.

Filament MVS is ratio-scaled off the INDX HF0.4 value using Prusa's CORE One
`HF0.4` → `HF<dia>` pair, or the non-HF `@COREONE` → `@COREONE <dia>` pair where
Prusa has no high-flow profile (9 of the 19 at 0.6). A material with neither is
skipped. Of the other keys, only `TRANSFER` (11 cooling and speed-limit keys)
takes the CORE One `<dia>` value, and only where INDX agreed with CORE One at
0.4 — where INDX differs it made a deliberate toolchanger choice that must
survive. Any other key keeps the INDX 0.4 value even where it agreed (Prusament
PLA Blend `temperature` stays 225, not CORE One 0.6's 215). PA and
`COMMON_ADOPT` keys follow their own rules below.

Pressure advance is never scaled: Prusa publishes it per nozzle, in
`*C1INDX_<FAM>_<NN>_PA*` for PLA/PET/ABS/PC/PA (polyamide)/PP at
`04`/`05`/`06`/`08` (PP is 0 throughout), PLA and PET also at `025` (0.1 / 0.15,
which `derive_std_filaments.py` uses), plus the nozzle-independent
`*C1INDX_FLEX_PA*`. A section counts as PA only if its name matches and its own
body types an M572: the polyamide chamber section `*C1INDX_CH_PA*` matches the
nozzle-independent name, and taken for PA it would keep a polyamide base's 0.4
figure. A chain with two PA sections refuses. Prusa's own structure gives the
mapping — `*PLA06HFC1INDX*` inherits `*C1INDX_PLA_06_PA*` — so
`derive_filaments.py` reads the PA section out of the HF0.4 chain
(`*C1INDX_PLA_04_PA*`) and swaps its nozzle token (`*C1INDX_PLA_06_PA*`),
preferring a figure Prusa typed into its
commented `<mat> @COREONEINDX HF<dia>` draft where there is one. Where Prusa has
no sized figure the tool keeps the 0.4 value, noted in the report and
`filament_notes` but not refused: by design for FLEX/TPU (`*C1INDX_FLEX_PA*` is
nozzle independent), and as a fallback for any family missing its `<NN>`
section (none today). Prusa's INDX PA **falls** as the nozzle grows (PLA 0.031 →
0.02, PET 0.048 → 0.031, ABS 0.02 → 0.015, PC 0.05 → 0.025), which is the
opposite of what a CHT's longer melt path would suggest, so do not "correct" it
upward.

Since 2.5.12 Prusa also publishes the INDX toolchanger common per nozzle:
`*C1INDX_06_common*` and `*C1INDX_08_common*` inherit `*C1INDX_common*` and
change two keys (wipe-tower minimal purge 10 → 14 / 20,
`filament_retract_restart_extra_toolchange` unset → 0.04 / 0.05). The 0.6 and
0.8 family sections stand on them: the HF ones and the ABS/PC/PA/FLEX/PP ones in
place of `*C1INDX_common*`; the standard PLA/PET ones (`*PLA06PGC1INDX*`,
`*PET06PGC1INDX*`, likewise 08) on top of their 0.4 family, which still brings
`*C1INDX_common*`. No HF0.4 base maps to those four, and `sized_common()` would
refuse them (two parents reach `*C1INDX_common*`). Prusa's sized chains swap
the whole family section, not just the common: `Prusament PLA @COREONEINDX
HF0.4` inherits `*PLAHFC1INDX*`, its commented HF0.6 draft `*PLA06HFC1INDX*`.
(Most drafts do; the BVOH drafts carry no INDX family and PC Blend CF's takes
`*PC06PGC1INDX*`, which stands on the same common.) So `derive_filaments.py`
works per base:
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
own override, whether or not it agreed with anything; that is this repo's
choice, not Prusa's (Prusa's HF0.6 drafts for FLEX and TPU 95A resolve to purge
14; ours keep their 0.4 15). Do not reduce this to a value comparison against
`*C1INDX_common*`: a key it leaves unset can arrive from a generic CORE One or
MK4 ancestor, and an equality test would mistake that for an INDX choice. Only
keys in `COMMON_ADOPT` (key → reason, like `DRAFT_ADOPT`) are taken. The tool
refuses on any other changed key, on a per-nozzle common that drops a shared
key, and on a missing or ambiguous family, so a re-pin cannot slip in an
unreviewed toolchanger *key*. The gate is per key, not per value: a new value
for an adopted key passes with exit 0 (the reasons quote 2.5.12 figures, so
update them).

There is no `*C1INDX_04_common*` or `*C1INDX_025_common*` (filament; the print
`*INDX_025_common*` is unrelated), so the standard bundles carry none.
`derive_std_filaments.py` swaps in Prusa's STD and 0.25 family sections whole
(`BASE_SWAP`), so the toolchanger keys arrive with them. It applies the same
gate, through the same `sized_common()` / `common_delta()` and the same
`COMMON_ADOPT`. Each preset must reach `*C1INDX_common*` through exactly one
`BASE_SWAP` target and by no other route (`std_base()`); that refuses a new HF
family `BASE_SWAP` has no STD base for, which would otherwise be kept, high-flow
values and all. Nothing that overrides that base may set a toolchanger key
either (`after_base()`): on every level of the path from the preset down to
the base, neither a parent listed after the step toward the base nor the own
body of a wrapper section the path passes through. The last parent wins in
PrusaSlicer's chain and a body beats its parents, so such a value would replace
the common's while reaching no common and sitting outside the base's chain,
and be credited as the preset's own. The preset's own body is exempt, as is
the body of a preset generated earlier in the run (Fiberlogy BVOH on Verbatim
BVOH), which holds an INDX HF0.4 preset's own overrides in Prusa's own chain. The common under that base is found by structure, and the same
refusals apply. An adopted key comes in with the base: it is recorded in the
header, `filament_notes` and stdout, and a preset's own value is kept over it.

Filament binding: every generated filament keeps its HF0.4 base's
`printer_model=~/(...)/` clause (`printer_models()` in `build_print_profiles.py`)
and appends its nozzle test: HF `nozzle_diameter[0]==<dia> and
nozzle_high_flow[0]`; standard 0.4 `nozzle_diameter[0]==0.4 and !
nozzle_high_flow[0]`; 0.25 `nozzle_diameter[0]==0.25` alone. Prusa scopes the
model list per family — since 2.5.12 the ABS, PC and PA (polyamide) families
leave out the CORE One L INDX, for which Prusa has staged `*C1LINDX_CH_*`
chamber values (60/50 °C) that no preset uses yet; 2.5.12 has no L INDX printer
— so a fixed list would silently diverge. Here that drops `COREONEL_INDX*` from
Generic ABS, Prusament ASA, both BVOHs and both PC Blends.

### Mixed tool layouts

`LAYOUTS` in `nozzles.py` holds one entry, `0.25+HF0.4`: a standard 0.25 on tool
1, Prusa's HF0.4 on tools 2-8. A layout is **composed**, never derived. Its two
halves work differently:

- **Printer preset** (`build_mixed()`): each tool's nozzle already has a preset
  here, so the layout interleaves them tool by tool. Only PrusaSlicer's own
  per-extruder keys may vary that way — `EXTRUDER_KEYS` is
  `PrintConfigDef::init_extruder_option_keys` (`PrintConfig.cpp:4124-4131`)
  copied out. At 2.5.12 six keys differ: `nozzle_diameter`, `nozzle_high_flow`,
  `min_layer_height`, `max_layer_height`, `retract_length`, `retract_lift`. Any
  other key the two nozzles' presets disagree on describes the machine, and the
  build refuses unless `MIXED_SCALAR` (key → reason) says what to do with it, so
  a re-pin cannot absorb an unreviewed disagreement. A source preset whose
  per-extruder vector is non-uniform, or that leaves a key another tool sets,
  also refuses: there would be no single value to fit that tool.
- **Print profiles** (`build_layout()`): **Prusa's own profiles for the tool that
  prints perimeters**, one per tier, not the bare common. Prusa tunes the 0.25
  profiles per tier (11/9 solid layers at 0.07, 9/7 at 0.10, 6/5 at 0.15, which
  also widens the perimeters to 0.27), so the common flattened over every tier
  would put the finest tier's shell on the coarsest. The ladder is therefore
  Prusa's own 0.07 / 0.10 / 0.15, not the `NOZZLES['0.25'].layers` ladder, and
  `LAYOUT_BASE` names the profile suffix per base tool. Prusa shipping a
  different number of those profiles than there are `TIERS` refuses: which map
  to Detail / Balanced / Draft is a human decision.

Roles are pinned from `Layout.roles` (every one, never left at Prusa's `0`), and
a role on a tool other than the base tool takes:

- its **widths** verbatim from `ROLE_ANCHOR[tag]`, a Prusa profile that ships at
  that nozzle — at 2.5.12 `0.20mm Balanced ★ @COREONEINDX HF0.4`, the same
  starred profile `FLOW_06` is anchored against;
- its **speeds** re-solved so the volumetric rate equals the rate that anchor
  runs the same role at (0.45 × 0.20 at 300 mm/s = 24.4 mm³/s), at the layout's
  own geometry and never past the anchor's own speed. `ROLE_KEYS` says which keys
  follow which role (from `PrintRegion::flow`); `ROLE_SPEED_WIDTH` says which
  width each speed is solved against, and deliberately omits `bridge_speed`, so
  moving solid infill refuses until someone works through `Flow::bridging_flow`.

`infill_every_layers` is per tier, set to the most PrusaSlicer will combine
(`combine_cap()`; 3 / 2 / 1 here). `interlocking_beam_width` is **not** set — 2 ×
nozzle has no meaning with two nozzles fitted — and `COMMON_EDITS` otherwise
applies. The binding tests only the tools the layout prints with, by index, and
keeps Prusa's own `printer_model` clause.

## Conventions

- Profile names: `<layer>mm <Tier> @COREONEINDX HF<dia>`, layer height to two
  decimals (`0.20mm`, not `0.2mm`). Prusa's format. Standard nozzles drop the
  `HF`: prints `@COREONEINDX 0.4`, printer `Prusa CORE One INDX 8T 0.4 nozzle`,
  as Prusa names its CORE One STD prints (`@COREONE 0.4`) and printers.
  Filaments differ at 0.4: ours are `<mat> @COREONEINDX 0.4`, where Prusa names
  STD 0.4 filaments with no size (`@COREONE`; its commented INDX drafts
  `<mat> @COREONEINDX`). At 0.25 Prusa's drafts are sized, `@COREONEINDX 0.25`,
  as ours are.
- A mixed layout is named by its tools, not by one nozzle: prints
  `<layer>mm <Tier> @COREONEINDX 0.25+HF0.4`, printer
  `Prusa CORE One INDX 8T 0.25+HF0.4 nozzles` (plural), hidden parent
  `*COREONEINDX 0.25+HF0.4*`, G-code `_0.25+HF0.4n_`. The tier labels are this
  repo's `TIERS` over Prusa's own layer heights, which is forced rather than
  stylistic: see the alias-filter entry under "Things that look wrong but
  aren't".
- The star `★` marks the **recommended default only** — one per nozzle size and
  one per layout, on Balanced. It is not a decoration for every profile.
- Hidden parents use asterisks: `*COREONEINDX HF0.6*`. PrusaSlicer strips these
  during flattening and never shows them.
- Commit messages explain *why* a value changed, with the number that motivated
  it. The git log is part of the provenance record.

## Adding a nozzle size

1. `NOZZLES` in `tools/nozzles.py` already has a `Nozzle` for every non-0.4 INDX
   print common Prusa defines (0.25, 0.3, 0.5, 0.6, 0.8), so building 0.5 or 0.8
   needs no new entry. A new high-flow size needs a new Prusa common first:
   `Nozzle.common` must name one. The one exception is HF1.0, built with
   `scaled_nozzle()` from 0.8 under the owner's approval (non-negotiable 1);
   its ladder is 0.8's, scaled, not read out. No other size may use
   `scaled_nozzle()` without a new approval. Check that the nozzle physically exists for
   the INDX before building anything (there is no 0.2 or 0.3 INDX nozzle). Layer
   ladders come from Prusa's CORE One profiles for the same nozzle — read them
   out, do not invent them. `Nozzle` is high-flow only (`tag` is always
   `HF<dia>`); a standard size goes through `STD_SOURCE`, `STD_PAIR`/`STD_DRAFT`,
   `BIND`/`BASE_SWAP` and `STD_VALIDATED` instead.
2. Supply `flow` targets only with a defensible basis, and set
   `validated=False` until printed.
3. Rebuild the vendor bundle with every size it carries (`-n 0.6 -n 0.8 -n 1.0
   -n <dia> --std 0.4`, i.e. every size in the recipe above plus the new one: one bundle
   holds all sizes, so `-n <dia>` alone drops the rest), then
   the printer preset (`build_printer_preset.py "$PR" printer -n <dia>`) and the
   filament bundle (`derive_filaments.py ... -n <dia>`). Commit all three.
4. Bump `BUNDLE_VERSION` in `build_print_profiles.py`, add the matching line to
   the `.idx`, and update every per-nozzle table and list in `README.md` (What
   you get; under Install the `cp` list, the by-hand table and the bundle names;
   Verify; the pressure-advance list under Calibrate; Known gaps) and in
   `docs/PROVENANCE.md` (What the bundles contain, Setting a printer up by hand,
   Adding a nozzle size, Pressure advance by size).

## Adding a mixed tool layout

A layout is an entry in `LAYOUTS`, not a `Nozzle`. It needs: the perimeter tool
listed in `LAYOUT_BASE`; a `ROLE_ANCHOR` entry for every tool a role is moved
**onto**; a printer preset buildable here for each tool's nozzle (the layout's
is composed from them); `validated=False`; and a reason on every `extra` entry.
No filament work — each tool is already offered the filaments for its own
nozzle. Rebuild the bundle with every size *and* layout it carries, bump
`BUNDLE_VERSION`, add the `.idx` line, and update the per-layout rows in
`README.md` (What you get, the `cp` list, Mixed nozzles, Verify, Known gaps) and
`docs/PROVENANCE.md` (Mixed tool layouts, Adding a mixed tool layout).

Bindings test tools by index, so swapping which dock holds which nozzle is a
different layout, not the same one.

## Things that look wrong but aren't

- **An HF1.0 printer is also offered nine of Prusa's own `@COREONEINDX HF0.4`
  filaments** (Prusament ASA, PETG, PETG V0, PETG CF, Generic ABS, PETG, PVA,
  both BVOHs). `*PETHFC1INDX*`, `*ABSHFC1INDX*` and `*ABSHFC1LINDX*` bind by
  `nozzle_diameter[0]!=0.8 and !=0.6 and !=0.5 and nozzle_high_flow[0]`, and
  that list does not name 1.0. Not fixable here: they are Prusa's presets.
  `derive_filaments.py -n 1.0` lists them (`foreign_at()`), and the README's
  Verify section warns users off them.
- **HF1.0 layer heights are 0.38 / 0.50 / 0.69.** Untidy, and deliberate: they
  are 0.8's 0.30 / 0.40 / 0.55 × 1.25, half-up to 0.01, by the same rule as the
  widths. Rounding them to tidier numbers would be a second, undocumented rule.
- **HF1.0 `first_layer_height` (0.2) is below its printer's `min_layer_height`
  (0.25).** The first is held at 0.8's, the second is scaled. PrusaSlicer 2.9.6
  does not object: `Print::validate` only rejects a first layer taller than the
  nozzle, and `Slicing.cpp` uses `first_layer_height` as-is, not clamped to
  `min_layer_height`. Scaling it would extend the rule past what was approved.
- **HF1.0 speeds are lower than HF0.8's** (Balanced perimeter 65 against 100).
  The flow targets are held at 0.8's, so the same mm³/s on a wider, taller line
  is a slower one. The 5 mm/s rounding leaves a feature's rate between about 6%
  below and 12% above 0.8's; the held filament MVS caps both alike.
- **HF1.0 filaments are byte-for-byte the HF0.8 ones** apart from the binding
  and `filament_notes`, including MVS (Prusament PLA 42, this repo's HF0.8
  derivation, not CORE One HF0.8's 36) and pressure advance (Prusa's
  `*C1INDX_*_08_PA*`). Held, not forgotten.
- **The HF1.0 vendor section's `output_filename_format` and binding differ
  from Prusa's `*INDX_08hf_common*`.** They name the size, so `SIZE_LABELS`
  moves them to 1.0; held, they would bind 1.0 profiles to a 0.8 nozzle and
  name its G-code `_0.8n_`.

- **A mixed printer is offered Prusa's own three `@COREONEINDX 0.25` prints as
  well as the three `0.25+HF0.4` ones.** Prusa's bind on
  `nozzle_diameter[0]==0.25`, which a layout with 0.25 on tool 1 satisfies.
  They are valid — they just print everything with tool 1 and ignore the CHT.
  Not fixable here: they are Prusa's presets. The README's Mixed nozzles section
  warns about it.
- **A layout's tiers are renamed instead of keeping Prusa's names.** Because of
  the entry above, Prusa's 0.25 profiles are *compatible* on a mixed printer,
  and `PresetCollection::update_compatible_internal` (`Preset.cpp:1388-1401`)
  marks a templates-vendor preset incompatible whenever a compatible
  non-templates preset shares its alias — the name before `@`. Keeping
  `0.10mm Fine ★` would hide this layout's whole tier behind Prusa's. This is the
  same filter the `--std 0.4` copies dodge only because no printer accepts both
  of those bindings; a mixed printer does accept both of these. `RENAME_WHY`
  records it.
- **Infill combining on `0.25+HF0.4` is capped by the 0.25 nozzle, not the
  0.4.** `PrintObject::combine_infill` caps the combined height at the smaller of
  the infill and **solid-infill** extruders' nozzles
  (`PrintObject.cpp:3126-3132`), and the layout keeps solid infill and top
  surfaces on the 0.25 tool for surface quality. So the cap is 0.25 mm: 3 layers
  at 0.07, 2 at 0.10, 1 — no combining at all — at 0.15. Putting solid infill on
  the 0.4 tool would raise the cap and lower the top-surface quality; that was
  the choice, not an oversight.
- **A layout's `infill_speed` is capped at 300 mm/s and so misses its target at
  the coarsest tier.** The solved speed for 24.4 mm³/s at 0.45 × 0.15 mm is
  390 mm/s; the cap is Prusa's own `infill_speed` in the anchor profile, because
  nothing here should ask more of a nozzle than Prusa does. The 0.15 tier
  therefore runs 18.8 mm³/s, reported in the header and on stdout.
- **The `0.25+HF0.4` print profiles carry Prusa's `top solid_infill_speed`
  typo.** `*INDX_025_common*` writes it with a space, so PrusaSlicer ignores the
  key and top solid infill runs at the inherited 100 mm/s rather than the 60
  Prusa evidently meant. It is copied as written: the plain 0.25 setup was test
  printed that way, and silently changing a speed is not the same kind of fix as
  `DOCK_FAN`, which restores a behaviour the typo disables outright. Documented
  as a gap in both the README and docs/PROVENANCE.md.
- **A layout's printer preset writes one `default_filament_profile`, not one per
  tool.** It is a per-extruder key, but
  `ExtruderFilaments::update_compatible_internal` skips exactly this key when it
  shifts a tool's values into index 0 (`Preset.cpp:2407-2409`), so entries past
  the first would be written and never read. `MIXED_SCALAR` records that.
- **Tools 2-8 of the mixed layout get Prusa's own HF0.4 filaments, and that is
  the intended outcome.** HF0.4 is the one INDX nozzle Prusa ships filaments
  for, so there is nothing to derive; `filaments/hyigerINDX-0.25-filaments.ini`
  covers tool 1 and nothing new is emitted. The per-tool filtering that makes
  this work is `Preset.cpp:2404-2415`.
- **`interlocking_beam_width` is unset on a layout.** `COMMON_EDITS` sets it to
  2 × nozzle everywhere else; with two nozzles fitted there is no single nozzle
  to double. It is inert unless interlocking beams are switched on, exactly as
  on the `--std` path.

- **`0.2` is rejected.** There is no 0.2 mm INDX nozzle, and Prusa defines no
  INDX common below `*INDX_025_common*`. Not a bug.
- **0.3 has no flow targets, and needs none.** There is no 0.3 mm INDX nozzle.
  `*INDX_03_common*` and Prusa's three `@COREONEINDX 0.3` prints are scaffolding
  (no INDX 0.3 printer, released or drafted), and `build_print_profiles.py`
  refuses the size as `shipped` before flow would matter. For the record,
  extrapolating the 0.4/0.6 anchors to 0.3 predicts ~18 mm³/s, where Prusa's
  tuned `0.10mm Fine ★ @COREONEINDX 0.25` runs 3.4 (perimeter): the curve
  collapses below 0.4.
- **`derive_filaments.py` refuses 0.25.** Prusa publishes standard filament
  variants at 0.6 and 0.8 and high-flow ones at HF0.5, HF0.6 and HF0.8; at 0.25
  there is nothing in either family to scale against. (It refuses 0.3 the same
  way.) The non-HF fallback is load-bearing, not a corner case: 9 of the 19
  committed 0.6 presets come from an `@COREONE` -> `@COREONE 0.6` pair. At 0.5
  Prusa ships no `<mat> @COREONE 0.5` filament (only `@COREONE 0.5` prints,
  whose ladder `nozzles.py` uses), so `-n 0.5` covers only 8 of the 20
  materials.
- **…but `derive_std_filaments.py` builds 0.25.** It scales nothing: each
  standard 0.25 preset is Prusa's 0.25 draft (Prusament PLA, PETG) or its CORE
  One STD parent plus an INDX base — the 0.25 base for PLA and PET, the INDX
  STD base (`*ABSPGC1INDX*`, `*PCPGC1INDX*`) for ABS, PC and both BVOHs, whose
  PA then comes from the CORE One 0.25 value. The two tools answer different
  questions.
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
  Prusa's. Only 0.25 is a real nozzle: the 0.3 set is Prusa scaffolding, with
  no INDX 0.3 nozzle and no INDX 0.3 printer, released or drafted.
- **Each print size binds on its own diameter; only standard 0.4 also tests the
  high-flow flag.** Standard 0.4 prints: `nozzle_diameter[0]==0.4 and !
  nozzle_high_flow[0]` — Prusa's HF0.4 originals require `nozzle_high_flow[0]`,
  and `STD_BIND` inverts it. HF0.6 prints: `nozzle_diameter[0]==0.6` alone,
  verbatim from `*INDX_06hf_common*` (the HF0.6 *filaments* add
  `nozzle_high_flow[0]`; see the last entry). The 0.4 test is needed because
  Prusa's HF0.4 printer is also 0.4 mm: without the `!` the copies would be
  compatible there, and the alias filter (`Preset.cpp:1387-1398`) would hide
  them behind Prusa's identically aliased prints. The flag states the intent
  instead of leaning on that name collision. No standard 0.6 INDX printer
  exists (released, drafted or built here), so diameter alone is unambiguous at
  0.6.
- **Printer layer G-code differs from Prusa's in one place.** The PET-family
  dock-fan check is `=~/(PET|CPE|PCTG).*/`, because Prusa's `/(PET|CPE|PCTG)/`
  never matches `PETG` (full-string `regex_match`). Reported upstream as
  prusa3d/PrusaSlicer-settings-prusa-fff#50; `DOCK_FAN` in
  `build_printer_preset.py`, which goes quiet once Prusa changes the pattern.
- **Filament notes are appended to, never replaced.** The INDX start G-code
  reads `MBL160` / `HT_MBL10` out of `filament_notes`.
- **`@COREONE 0.8` MVS is lower than `HF0.6`** (Prusament PLA 19 vs 30). That is
  a standard brass nozzle, not high-flow. Do not use it as an absolute CHT 0.8
  flow anchor (`nozzles.py` extrapolates instead). `derive_filaments.py -n 0.8`
  does still fall back to the standard `@COREONE` → `@COREONE 0.8` *ratio* for
  the 11 of 19 materials with no HF0.8 pair (Prusament PVB 6 → 19), one more
  reason 0.8 stays unvalidated.
- **The 0.25 printer keeps jerk 10,8 where `Prusa CORE One 0.25 nozzle` has
  8,8, and `retract_length` 0.7 where it has 0.8.** The 0.25 preset is Prusa's
  INDX 0.25 draft, which sets `retract_length` 0.7 and leaves jerk at the INDX
  HF0.4 value. The CORE One delta is reported (`STD_CHECK`), not applied. Under
  the agreed-at-0.4 rule `retract_length` would not move anyway: INDX HF0.4 has
  0.8 where CORE One HF0.4 has 0.7.
- **HF0.6 pressure advance is *lower* than HF0.4** (Prusament PLA 0.02 vs
  0.038). Prusa's own per-nozzle figures go that way. See "Data model".
- **The HF0.6 printer preset's `retract_length` is 0.7, not the 0.8 its chain
  resolves.** Prusa's commented INDX HF0.6 printer draft says 0.7, and a draft
  written for this nozzle on this toolchanger outranks a value inherited from the
  HF0.4 chain. `DRAFT_ADOPT` in `build_printer_preset.py` records the decision;
  any *unlisted* draft disagreement refuses instead.
- **`build_printer_preset.py -n 0.8` works, but 0.8 is still unvalidated.** The
  printer preset is fully sourced: Prusa's INDX HF0.4 chain plus the CORE One
  HF0.4 → HF0.8 delta, with the five retraction keys Prusa's HF0.8 draft types
  adopted through `DRAFT_ADOPT`. It matches the resolved draft on every key
  except `default_print_profile` (ours `0.40mm Balanced ★`, the draft's
  `0.40mm Extra Coarse ★`) and the dock-fan fix. The *flow targets* in
  `nozzles.py` are still extrapolated (`validated=False`), so
  `build_print_profiles.py --list` and the printer tool's own banner and header
  both say UNVALIDATED, and nothing at 0.8 has been printed. HF0.8 is committed
  since bundle 0.6.0 (print profiles, printer preset and filament bundle), so
  the recipe builds it.
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
  CORE One one, and 35 is the test-printed value, so the ratio rule stands.
  (Further drafts differ only through values they inherit and never type, which
  is why the report cannot see them: Prusament ASA MVS 34 against our 39, PC
  Blend CF 13 against 19, Generic PETG 27 against 22. Generic PLA's would
  resolve to MVS 28 against 23 and `slowdown_below_layer_time` 15 against 9, but
  it names a parent, `*PA_GenericPLAINDX*`, that PrusaResearch does not define.)
  What the drafts do type, `derive_filaments.py` prints rather than hides: every
  `DRAFT_WATCH` divergence (MVS and `slowdown_below_layer_time`, four rows at
  0.6). Pressure advance is the exception: where a draft types an M572, it wins.
- **HF0.6 filaments test `nozzle_high_flow[0]`; HF0.6 prints do not.**
  `derive_filaments.py` binds every preset on `nozzle_diameter[0]==0.6 and
  nozzle_high_flow[0]` (`BIND_TMPL`), the test Prusa's own sized HF families
  already use (`*PLA06HFC1INDX*`, `*PET06HFC1INDX*`, `*ABS06HFC1INDX*`,
  `*PC06HFC1INDX*`). It adds the flag only for Generic FLEX and Prusament TPU
  95A, whose `*FLEX06PGC1INDX*` binds on diameter alone. The prints keep
  `*INDX_06hf_common*`'s diameter-only test (see above). Intentional and
  harmless: nothing here builds a standard 0.6 printer.
