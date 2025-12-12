# HCIS Scenario Generation

An OpenSCENARIO generator for creating **diverse and interactive traffic scenarios**.

This project provides a complete pipeline to:

- Generate structured scenario configuration files
- Combine traffic agents across scenarios
- Convert configurations into OpenSCENARIO (`.xosc`) files

## Environment Setup

Install all required dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

### Generate Scenario Configurations and OpenSCENARIO Files

This command runs the full pipeline:

- Generates scenario configuration files
- Converts them into OpenSCENARIO (`.xosc`) files

You can customize global settings (directories, variables, controllers, conditions, etc.) by editing: `./config/base/example.yaml`

Run the pipeline:

```bash
sh run.sh
```

## Output Structure

By default, generated files are organized as follows:

### Scenario Configuration Files

- `./config/scenario_config/`
- `./config/scenario_config_combined/`

### OpenSCENARIO Files

- `./results/`

---

## Scenario Combination

### Combine Two Scenarios

You can merge agents from two different scenarios into a new combined scenario:

```bash
python combine.py --s1 [SCENARIO_PATH_1] --s2 [SCENARIO_PATH_2]
```

Example:

```bash
python combine.py --s1 scenario_config/01BL-KEEP/1 --s2 scenario_config/01FS-CO/4
```

> **Note:** Do **not** include file extensions (`.yaml`, `.csv`) when specifying scenario paths.

---

### Combine All Scenarios in a Folder

To automatically combine all scenarios across different categories under `scenario_config`:

```bash
python combine_all.py
```

This generates cross-category combined scenarios and stores them under:

```
./config/scenario_config_combined/
```

---

## OpenSCENARIO Generator

This module converts a scenario configuration file into an OpenSCENARIO (`.xosc`) file.

```bash
python main.py -b [BASE_CONFIG_PATH] -c [SCENARIO_CONFIG_PATH]
```

### Arguments

- **Base Config (`-b`)**  
  Defines global settings such as directories, variables, controllers, and conditions.

- **Scenario Config (`-c`)**  
  Uses HCIS Lab’s custom simplified scenario configuration format.

  Please refer to the documentation here:  
  https://lopsided-soursop-bec.notion.site/Scenario-Configuration-File-Format-5d423c6aab1740a2b53e7444fa2dad31

### Generate All Scenarios

If `CONFIG_PATH == "all"`, the generator will automatically convert **all** scenario configurations located in:`./config/scenario_config/`

---

## References & Documentation

- **Scenariogeneration (pyoscx)**  
  https://github.com/pyoscx/scenariogeneration

- **Scenario Configuration File Format**  
  https://lopsided-soursop-bec.notion.site/Scenario-Configuration-File-Format-5d423c6aab1740a2b53e7444fa2dad31

- **Parameter Naming Rules**  
  https://lopsided-soursop-bec.notion.site/Scenario-Parameter-Naming-642563ce89f74de195116291d153c4ef
