import glob
import combine
import os
import datetime
import itertools

# basic scenarios folder
basic_scenarios_folder = 'scenario_config'

# Get all folder in ./scenario_config
all_folders = os.listdir(basic_scenarios_folder)
print("all_folders: ", all_folders)

# Define save folder
# save_folder = f'scenario_config_combined/{datetime.datetime.now()}'
save_folder = f'scenario_config_combined/{datetime.datetime.date(datetime.datetime.now())}'

# Create save folder
if not os.path.exists(save_folder):
    os.makedirs(save_folder)

# Combine all yaml and csv files
cata_combinations = list(itertools.combinations(all_folders, 2))
print("combinations: ", cata_combinations)
counter = 0
for i, j in cata_combinations:
    cata_1s = len(glob.glob(os.path.join(f'./scenario_config/{i}', '*.yaml'), recursive=True))
    cata_2s = len(glob.glob(os.path.join(f'./scenario_config/{j}', '*.yaml'), recursive=True))

    sce_combinations = list(itertools.product(range(1,cata_1s+1), range(1,cata_2s+1)))
    counter += len(sce_combinations)
    for sce1, sce2 in sce_combinations:
        yaml1 = f'{basic_scenarios_folder}/{i}/{sce1}.yaml'
        yaml2 = f'{basic_scenarios_folder}/{j}/{sce2}.yaml'
        combined_yaml, sc_folder_name = combine.combine_yaml(yaml1, yaml2, mode='agent')

        csv1 = f'{basic_scenarios_folder}/{i}/{sce1}.csv'
        csv2 = f'{basic_scenarios_folder}/{j}/{sce2}.csv'
        combined_csv = combine.combine_csv(csv1, csv2, mode='agent')

        # get the current scenario number in the folder
        if not os.path.exists(f'{save_folder}/{sc_folder_name}'):
            os.makedirs(f'{save_folder}/{sc_folder_name}')
        scenario_number = len(glob.glob(os.path.join(f'{save_folder}/{sc_folder_name}', '*.yaml'), recursive=True))+1
                
        # save the combined data
        save_path = f'{save_folder}/{sc_folder_name}/{scenario_number}'
        print('saving to:',save_path)
        combine.save_yaml(combined_yaml, f'{save_path}.yaml')
        combine.save_csv(combined_csv, f'{save_path}.csv')

print(f"{counter} scenarios combined.")