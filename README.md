# hcis_scenario_generation
- Config File Format: [link](https://lopsided-soursop-bec.notion.site/Scenario-Configuration-File-Format-5d423c6aab1740a2b53e7444fa2dad31?pvs=4)
- Parameter Naming Rule: [link](https://lopsided-soursop-bec.notion.site/Scenario-Parameter-Naming-642563ce89f74de195116291d153c4ef?pvs=4)

## Usage
### OpenScenario Config File(.yaml) Generator
Runs all necessary functions to generate config files and .xosc. 
Uncomment the upload section to upload scenarios & parameters to the payload (VPN connection required).
```
sh run.sh
```

### Combine scenarios
You can combine two scenario's agents as a new scenario.

`python combine.py --s1 [1st scenario_path] --s2 [2nd scenario_path]`

e.g. python combine.py --s1 scenario_config/01BL-KEEP/1 --s2 scenario_config/01FS-CO/4

**Note: you don't need to add the file extension (.yaml, .csv) in command.**

### Combine all scenarios in a folder
`python combine_all.py`

- This command will combine all scenarios cross different catagories in `scenario_config` folder.
- In default, they will be saved in `scenario_config_conbined/[date]` folder.

### OpenScenario Generator
`python main.py -c [CONFIG_PATH]`

Note: If CONFIG_PATH == 'all', it will generate all config file in './scenario_config'

### Code
- main.py : main program, read config file and write OpenScenario file.
- generate.py : all generation pipeline, include parameter setting, create entity, event generation, and so on.
- scenario_upload.py : upload scenario to MongoDB

- combine.py : combine two scenario.
- combine_all.py : combine all scenarios in `./scenario_config`
- scripts/
  - config_generator_4way.py : generate 4way scenarios, e.g. left turn, U turn, ...
  - config_generator_straight.py : generate straight scenarios, e.g. cut-in/out, zigzag
  - config_generator_straight_at4way.py : generate straight scenarios over 4way topology, e.g. cut-in/out, zigzag at crossroad
  - combine_csv_files.py : output scenarios list

- utils/
  - upload.py : build tag tree, tags and corresponding params for scenarios
