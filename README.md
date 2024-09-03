# hcis_scenario_generation
- Config File Format: [link](https://lopsided-soursop-bec.notion.site/Scenario-Configuration-File-Format-5d423c6aab1740a2b53e7444fa2dad31?pvs=4)
- Parameter Naming Rule: [link](https://lopsided-soursop-bec.notion.site/Scenario-Parameter-Naming-642563ce89f74de195116291d153c4ef?pvs=4)

## Usage
`python main.py -c [CONFIG_PATH]`

Note: If CONFIG_PATH == 'all', it will generate all config file in './scenario_config'

### Code
- main.py : main program, read config file and write Openscenario file.
- dicent_utils.py : some useful function.
- generate.py : all generation pipeline, include parameter setting, create entity, event generation, and so on.
- scenario_upload.py : upload scenario to MongoDB
- upload_utils.py : build tag tree, tags and corresponding params for scenarios
