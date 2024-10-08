import glob
import combine
import os
import datetime
import itertools

# basic scenarios folder
basic_scenarios_folder = 'scenario_config'

# Get all folder in ./scenario_config
all_basis = os.listdir(basic_scenarios_folder)
print(f"Total {len(all_basis)} folder found.")

# Define save folder
# save_root = f'scenario_config_combined/{datetime.datetime.now()}'
save_root = f'scenario_config_combined/{datetime.datetime.date(datetime.datetime.now())}'

# Create save folder
if not os.path.exists(save_root):
    os.makedirs(save_root)

# Combine all yaml and csv files
cata_combinations = list(itertools.combinations(all_basis, 2))
print("Total combinations: ", len(cata_combinations))

counter = 0
for cata1, cata2 in cata_combinations:
    # get the number of scenarios in each folder
    cata_1s = len(glob.glob(os.path.join(f'./scenario_config/{cata1}', '*.yaml'), recursive=False))
    cata_2s = len(glob.glob(os.path.join(f'./scenario_config/{cata2}', '*.yaml'), recursive=False))

    # get all combinations of scenarios (scenario's index starts from 1)
    sce_combinations = list(itertools.product(range(1,cata_1s+1), range(1,cata_2s+1)))
    print(f"Combining {cata1} and {cata2} with {len(sce_combinations)} scenarios.")
    counter += len(sce_combinations)
    
    sc_folder_name = combine.combine_scenario_name(cata1, cata2) 
    print(f"Combined folder name: {sc_folder_name}")
    print('-----------------------------------')
    for sce1, sce2 in sce_combinations:
        # get the current scenario number in the folder
        if not os.path.exists(f'{save_root}/{sc_folder_name}'):
            os.makedirs(f'{save_root}/{sc_folder_name}')
        scenario_number = len(glob.glob(os.path.join(f'{save_root}/{sc_folder_name}', '*.yaml'), recursive=False))+1
        combined_scenario_name = f'{sc_folder_name}_{scenario_number}'
        
        yaml1 = f'{basic_scenarios_folder}/{cata1}/{sce1}.yaml'
        yaml2 = f'{basic_scenarios_folder}/{cata2}/{sce2}.yaml'
        combined_yaml= combine.combine_yaml(yaml1, yaml2, combined_scenario_name, mode='agent')

        csv1 = f'{basic_scenarios_folder}/{cata1}/{sce1}.csv'
        csv2 = f'{basic_scenarios_folder}/{cata2}/{sce2}.csv'
        combined_csv = combine.combine_csv(csv1, csv2, combined_scenario_name, mode='agent')

        # save the combined data
        save_path = f'{save_root}/{sc_folder_name}/{scenario_number}'
        combine.save_yaml(combined_yaml, f'{save_path}.yaml')
        combine.save_csv(combined_csv, f'{save_path}.csv')

print(f"{counter} scenarios combined.")