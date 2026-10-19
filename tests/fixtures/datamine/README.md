# Datamine Source Fixtures

These minimal offline fixtures contain extracts from Genshin Impact client configuration files (ExcelBinOutput), sourced from public datamine archives (`Dimbreath/AnimeGameData` / `Sycamore0/GenshinData`).

## Fixture Inventory

1. `ReliquaryAffix_depot501.json`
   - **Upstream Source**: `ExcelBinOutput/ReliquaryAffixExcelConfigData.json`
   - **Filter**: `depotId == 501`
   - **Records**: Exactly 40 objects (10 canonical substats $\times$ 4 enhancement roll quality tiers).
   - **Purpose**: Offline validation of 5★ substat roll values and tier ratios ($0.70 / 0.80 / 0.90 / 1.00$).

2. `ReliquaryLevel_rank5.json`
   - **Upstream Source**: `ExcelBinOutput/ReliquaryLevelExcelConfigData.json`
   - **Filter**: `rank == 5`
   - **Records**: Exactly 21 objects (`level: 1` through `level: 21`, mapping to domain enhancement levels 0 through 20).
   - **Purpose**: Offline extraction of complete main-stat scaling progression across all 21 levels for the 18 valid 5★ main stats.

3. `ReliquaryMainProp_depots.json`
   - **Upstream Source**: `ExcelBinOutput/ReliquaryMainPropExcelConfigData.json`
   - **Records**: 66 objects covering all main property depots (Flower: 4000, Plume: 2000, Sands: 1000/1095-1099, Goblet: 5000/5088-5099, Circlet: 3000/3093-3099).
   - **Purpose**: Cross-verifies the 18 valid 5★ main stats and proves `FLAT_DEF` is never a valid main stat on any artifact slot.

## Extraction Instructions
To update or reproduce these fixtures from upstream repositories:
```bash
python tools/import_artifact_datamine.py --input-dir tests/fixtures/datamine --check
```
All data extraction in production tools and test suites runs strictly offline using these fixtures, with no network access required.
