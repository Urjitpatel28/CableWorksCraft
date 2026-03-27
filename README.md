# CableWorksCraft

CableWorksCraft is a Windows desktop application for configuring and auto-generating 3D cable cross-section models in FreeCAD. Engineers input detailed cable layer parameters through an intuitive WPF interface; the application serialises the configuration to JSON and drives FreeCAD's embedded Python interpreter to produce a parametric `.fcstd` solid model, ready for further engineering work or technical drawings.

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Getting Started](#getting-started)
- [Workflow](#workflow)
- [Cable Parameter Reference](#cable-parameter-reference)
- [Python Scripts](#python-scripts)
- [NuGet Dependencies](#nuget-dependencies)
- [Unit Tests](#unit-tests)
- [Troubleshooting](#troubleshooting)

---

## Features

- **Project management** — create and organise named cable projects under a configurable root folder.
- **Dual core types** — supports **Circular** and **Shaped (Sectoral)** conductor cross-sections.
- **Full layer configurator** — conductor, insulation, screen layers, sheaths, armor, fillers, and more, each with material and colour settings.
- **Live validation** — every numeric field validates in real time; the Generate button stays disabled until all required values are positive.
- **FreeCAD integration** — serialises the complete configuration to `projectDetail.json` and invokes FreeCAD's bundled Python executable to build the `.fcstd` 3D model.
- **Calculated outer radius read-back** — after generation, the script writes the computed outer radius back into the JSON; the application reads it and populates the *Layyd Diameter* field automatically.
- **Layer-arrangement lookup** — reads a provided Excel file (`CoreInLayerArrangement.xlsx`) that maps the number of cores per layer to the individual concentric layer counts.
- **Colour dictionary** — loads cable colour-to-RGB mappings from a dedicated Excel workbook for consistent material appearance in the 3D model.
- **One-click folder navigation** — prompts to open the output folder in Windows Explorer after successful generation.

---

## Architecture Overview

The application follows the **MVVM** (Model–View–ViewModel) pattern:

```
┌─────────────────────────────────────────────────────────┐
│                         WpfUI                           │
│                                                         │
│  Views ──binds──► ViewModels ──uses──► Commands         │
│     │                  │                   │            │
│     │               Models             Services         │
│     │            (CableParameters,    (FileWriter)      │
│     │             ProjectDetails)         │             │
│     └──────────────────────────────►  Helpers           │
│                                    (ExcelReader,        │
│                                     ExcelHelper,        │
│                                     Converters)         │
└─────────────────────────────────────────────────────────┘
              │  JSON  │
              ▼        ▼
     Helpers/PythonScripts/
       CircularCore_V1.1.py
       SectoralCore_V1.1.py
              │
              ▼
     FreeCAD Python Engine
              │
              ▼
     Outputs/<ProjectName>/<ProjectName>_<CoreType>.fcstd
```

---

## Project Structure

```
CableWorksCraft/
├── CableWorksCraft.sln
├── WpfUI/                              # Main WPF application
│   ├── App.xaml / App.xaml.cs
│   ├── App.config                      # Runtime configuration (paths, etc.)
│   ├── packages.config
│   │
│   ├── Views/
│   │   ├── MainWindow.xaml             # Shell window
│   │   ├── MainWindow.xaml.cs
│   │   ├── CableDetailUC.xaml          # Cable parameter user control
│   │   └── CableDetailUC.xaml.cs
│   │
│   ├── ViewModels/
│   │   └── MainViewModel.cs            # Central ViewModel; owns all UI state & lists
│   │
│   ├── Models/
│   │   ├── CableParameters.cs          # Full cable geometry & material model
│   │   └── ProjectDetails.cs           # Project metadata wrapper
│   │
│   ├── Command/
│   │   ├── BaseCommand.cs              # Abstract ICommand base
│   │   ├── RelayCommand.cs             # Generic relay command
│   │   ├── CreateProjectCommand.cs     # Creates output folder structure
│   │   ├── GenerateCommand.cs          # Orchestrates JSON export + script execution
│   │   ├── ExecuteCommand.cs           # Runs shell commands as administrator
│   │   └── OpenProjectFolder.cs        # Opens output folder in Explorer
│   │
│   ├── Services/
│   │   └── FileWriter.cs               # JSON serialise / deserialise helpers
│   │
│   ├── Helpers/
│   │   ├── ExcelReader.cs              # Reads CoreInLayerArrangement.xlsx
│   │   ├── ExcelHelper.cs              # Reads colour dictionary Excel
│   │   ├── CoreInLayerArrangement.xlsx # Layer-count lookup table
│   │   ├── BoolNegationConverter.cs
│   │   ├── CeilingGreaterOrEqualConverter.cs
│   │   ├── CoreTypeToVisibilityConverter.cs
│   │   ├── DecimalValueConverter.cs
│   │   ├── EnabledToTextConverter.cs
│   │   ├── FillingMethodToBoolConverter.cs
│   │   ├── LayerVisibilityConverter.cs
│   │   └── PythonScripts/
│   │       ├── CircularCore_V1.1.py    # FreeCAD script — circular cross-section
│   │       ├── SectoralCore_V1.1.py    # FreeCAD script — sectoral cross-section
│   │       ├── CreateDrawing.py        # Technical drawing helper
│   │       ├── BaloonHelper.py         # Balloon annotation helper
│   │       └── conductorlayercalculator.py
│   │
│   └── Resources/
│       └── (icons, styles, resource dictionaries)
│
└── UnitTest/
    └── UnitTest1.cs                    # MSTest unit tests
```

---

## Prerequisites

| Requirement | Version / Notes |
|---|---|
| **Windows** | 10 / 11 |
| **.NET Framework** | 4.7.2 |
| **Visual Studio** | 2019 or later (WPF workload) |
| **FreeCAD** | 1.0 — provides the Python 3 interpreter used to run generation scripts |
| **Python** | Bundled with FreeCAD at `C:\Program Files\FreeCAD 1.0\bin\python.exe` |

> FreeCAD must be installed before running the application because the generation step calls FreeCAD's embedded Python directly.

---

## Configuration

All external paths are stored in `WpfUI/App.config` under `<appSettings>`. Edit these to match your environment:

```xml
<appSettings>
  <!-- Root folder where all cable projects are saved -->
  <add key="ProjectRootPath"          value="C:\ProjectRoot" />

  <!-- Excel file mapping core counts to per-layer arrangements -->
  <add key="CoreInLayersExcelPath"    value="...\WpfUI\Helpers\CoreInLayerArrangement.xlsx" />

  <!-- FreeCAD's bundled Python executable -->
  <add key="PythonExePath"            value="C:\Program Files\FreeCAD 1.0\bin\python.exe" />

  <!-- Python generation scripts -->
  <add key="CircularCoreScriptPath"   value="...\WpfUI\Helpers\PythonScripts\CircularCore_V1.1.py" />
  <add key="SectoralCoreScriptPath"   value="...\WpfUI\Helpers\PythonScripts\SectoralCore_V1.1.py" />
</appSettings>
```

---

## Getting Started

1. **Clone the repository**

   ```bash
   git clone https://github.com/Urjitpatel28/CableWorksCraft.git
   cd CableWorksCraft
   ```

2. **Restore NuGet packages**

   Open `CableWorksCraft.sln` in Visual Studio. NuGet packages restore automatically on build, or run:

   ```bash
   nuget restore CableWorksCraft.sln
   ```

3. **Update `App.config`** with the correct paths for your machine (see [Configuration](#configuration)).

4. **Build** the solution in Visual Studio (`Ctrl+Shift+B`).

5. **Run** the `WpfUI` project (`F5`).

---

## Workflow

```
1. Enter a Project Name
2. Select Core Type  ──►  Circular  or  Shaped (Sectoral)
3. Click  [Create Project]
        └─► Creates  <ProjectRootPath>/<ProjectName>/Outputs/  on disk
            and enables the Cable Info panel.

4. Fill in all cable layer parameters (see reference below).

5. Click  [Generate]
        └─► Validates inputs
        └─► Serialises ProjectDetails → projectDetail.json
        └─► Calls:  python.exe  <script>.py  --jsonFile  projectDetail.json
        └─► FreeCAD script builds the 3D model  →  <ProjectName>_<CoreType>.fcstd
        └─► Reads back  "Calculated outer radius"  from JSON
        └─► Populates  Layyd Diameter  field
        └─► Offers to open the output folder
```

---

## Cable Parameter Reference

`CableParameters` holds the complete geometry and material specification for one cable design:

### Conductor

| Property | Description |
|---|---|
| `ConductorDia` | Overall conductor outer diameter (mm) |
| `conductorMaterial` | `Copper`, `Tinned`, or `Aluminum` |
| `wire_dia` / `wire_radius` | Individual wire strand diameter / radius |
| `numCylindersPerLayer` | Number of concentric core layers (looked up in `CoreInLayerArrangement.xlsx`) |
| `num_concentric_cylinders` | Total concentric layer count (default 7) |

### Layer Spacing (Circular Core)

| Property | Description |
|---|---|
| `spacing_1` – `spacing_7` | Radial spacing for each concentric build-up layer |
| `layyd_dia` / `layyd_rad` | Laid-up diameter; back-calculates `spacing_1` automatically |

### Sectoral / Shaped Conductor

| Property | Description |
|---|---|
| `conductor_radius` | Equivalent full radius (= spacing_1 + spacing_2 + spacing_3) |
| `offset_radius1` | Inner offset (= spacing_1) |
| `offset_radius2` | Outer offset (= spacing_1 + spacing_2) |
| `fillet_radius` | Corner fillet radius (default 1 mm) |
| `halfcore_dia` / `halfcore_radius` | Half-core reference dimension for fractional layers |

### Insulation & Screens

| Property | Description |
|---|---|
| `insulationMaterial` | Insulation compound (e.g., XLPE, PVC) |
| `insulationColor` | Display colour |
| `conductorScreenColor` | Conductor screen layer colour |
| `insulationScreenMaterial` | Non-metallic screen material |
| `nometallicScreenColor` | Non-metallic screen colour |
| `metallicScreenColor` | Metallic screen colour |
| `idTapeColor` | ID tape layer colour |
| `lappingColor` | Lapping tape colour |
| `condscreencolor1`–`condscreencolor5` | Individual conductor screen colours (multi-core) |
| `halfcondscreencolor` | Half-layer conductor screen colour |

### Sheath Layers

| Property | Description |
|---|---|
| `preinnersheaththickness` / `preinnersheathcolor` | Pre-inner sheath thickness and colour |
| `innersheaththickness` / `innersheathcolor` | Inner sheath thickness and colour |
| `innerSheathMaterial` | Inner sheath compound |
| `overinnersheaththickness` / `overinnersheathcolor` | Over-inner sheath thickness and colour |
| `outersheaththickness` / `outersheathcolor` | Outer sheath thickness and colour |
| `outerSheathMaterial` | Outer sheath compound |
| `outersheathLineRequired` | Whether a longitudinal stripe line is present |
| `outercolor1` / `outercolor2` | Base colour and stripe colour for outer sheath |
| `printingMatter` | Text printed on the outer sheath |

### Armor

| Property | Description |
|---|---|
| `armor_choice` | `Wire` (round wire armor) or `Strip` (flat strip / cubical armor) |
| `armor_Size` | Armor wire diameter (Wire) or strip side length (Strip) |
| `cylinder_dia` / `cylinder_radius` | Armor wire cross-section dimensions (Wire armor) |
| `side_length` / `side_thickness` | Strip dimensions (Strip armor) |
| `armortapingthickness` / `armortapingcolor` | Armor taping layer properties |
| `armorcolor` | Armor material colour (default: Gray) |

### Filling

| Property | Description |
|---|---|
| `FillingMethod` | `Auto` (script calculates) or `Manual` (user-specified filler diameters) |
| `SelectedNumberOfFillers` | Number of filler diameters to specify (1–3) |
| `Filler1`, `Filler2`, `Filler3` | Individual filler outer diameters |
| `FillerMaterial` | Filler compound |
| `leftoverDia` | Calculated remaining inner cavity diameter (written back by Python script) |

---

## Python Scripts

The scripts are invoked by FreeCAD's embedded Python and receive a single `--jsonFile` argument pointing to the serialised `projectDetail.json`.

| Script | Purpose |
|---|---|
| `CircularCore_V1.1.py` | Builds a parametric 3D model for cables with a **circular** stranded conductor |
| `SectoralCore_V1.1.py` | Builds a parametric 3D model for cables with a **shaped (sectoral)** conductor |
| `CreateDrawing.py` | Generates a FreeCAD technical drawing sheet from an existing model |
| `BaloonHelper.py` | Adds balloon annotations to technical drawings |
| `conductorlayercalculator.py` | Utility for conductor layer arrangement calculations |

The scripts write `"Calculated outer radius"` back to the same JSON file so the application can read it after generation completes.

---

## NuGet Dependencies

| Package | Version | Purpose |
|---|---|---|
| `ClosedXML` | 0.104.2 | Read/write Excel files (layer lookup, colour data) |
| `DocumentFormat.OpenXml` | 3.1.1 | Low-level Open XML support (required by ClosedXML) |
| `Newtonsoft.Json` | 13.0.3 | JSON serialisation of `ProjectDetails` → `projectDetail.json` |
| `FontAwesome.WPF` | 4.7.0.9 | Icon font for UI buttons and indicators |
| `RBush` | 4.0.0 | Spatial indexing (used internally by ClosedXML) |
| `SixLabors.Fonts` | 1.0.0 | Font handling support library |
| `System.Memory` | 4.5.4 | Memory-span primitives backport for .NET 4.7.2 |

---

## Unit Tests

Tests are in the `UnitTest` project and use the **MSTest** framework.

| Test | Description |
|---|---|
| `TestMethod1` | Runs `ExecuteCommand.RunCommandAsAdmin` end-to-end against a sample JSON and FreeCAD Python |
| `Readxml` | Reads `CoreInLayerArrangement.xlsx` via `ExcelReader.ReadExcel` and prints the parsed dictionary |
| `ExcelWriter` | Exercises `ExcelHelper.ReadColorDataFromExcel` against a sample workbook |

Run tests via **Test Explorer** in Visual Studio or:

```bash
vstest.console.exe UnitTest\bin\Debug\UnitTest.dll
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| *"Unable to load CoreInLayers.xlsx"* on startup | `CoreInLayersExcelPath` in `App.config` is wrong or file is missing | Verify the path and that the file exists |
| *"Unable to find script for Circular/Shaped"* | `CircularCoreScriptPath` or `SectoralCoreScriptPath` not set | Update `App.config` with correct script paths |
| *"Fail to Create FreeCAD model"* | FreeCAD Python not found, script error, or output path issue | Check `PythonExePath`, run the script manually with `python.exe <script> --jsonFile <path>` and inspect the `.log` file in the project folder |
| Generate button stays disabled | `spacing_1` or `wire_dia` is zero | Fill in all required conductor parameters before generating |
| Output `.fcstd` file opens blank in FreeCAD | FreeCAD version mismatch | Ensure FreeCAD 1.0 is installed; scripts target FreeCAD 1.0 API |
| Admin prompt not appearing | UAC disabled or running as administrator already | `ExecuteCommand` uses `runas` verb; ensure UAC is enabled or run Visual Studio as administrator |
