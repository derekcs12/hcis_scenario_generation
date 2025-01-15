import argparse
import glob

from tqdm import tqdm
import combine
import os
import datetime
import itertools

def combine_all_scenarios(basic_scenarios_folder):
    # Get all folder in ./scenario_config
    all_basis = os.listdir(basic_scenarios_folder)
    print(f"Total {len(all_basis)} folder found.")

    # Define save folder
    # save_root = f'scenario_config_combined/{datetime.datetime.now()}'
    # save_root = f'scenario_config_combined/{datetime.datetime.date(datetime.datetime.now())}'
    save_root = f'scenario_config_combined'

    # Create save folder
    if not os.path.exists(save_root):
        os.makedirs(save_root)

    # Combine all yaml and csv files
    cata_combinations = list(itertools.combinations(all_basis, 2))
    print("Total combinations: ", len(cata_combinations))

    counter = 0
    for cata1, cata2 in tqdm(cata_combinations):
        success = True
        # get the number of scenarios in each folder
        cata_1s = len(glob.glob(os.path.join(f'./scenario_config/{cata1}', '*.yaml'), recursive=False))
        cata_2s = len(glob.glob(os.path.join(f'./scenario_config/{cata2}', '*.yaml'), recursive=False))

        # get all combinations of scenarios (scenario's index starts from 1)
        sce_combinations = list(itertools.product(range(1,cata_1s+1), range(1,cata_2s+1)))

        sc_folder_name = combine.combine_scenario_name(cata1, cata2) 
        print(f"Combining {cata1.ljust(9)} and {cata2.ljust(9)} with {str(len(sce_combinations)).ljust(5)}scenarios. Output folder: {sc_folder_name.ljust(25)}")
        for sce1, sce2 in sce_combinations:
            # get the current scenario number in the folder
            scenario_number = len(glob.glob(os.path.join(f'{save_root}/{sc_folder_name}', '*.yaml'), recursive=False))+1
            combined_scenario_name = f'{sc_folder_name}_{scenario_number}'
            
            yaml1 = f'{basic_scenarios_folder}/{cata1}/{sce1}.yaml'
            yaml2 = f'{basic_scenarios_folder}/{cata2}/{sce2}.yaml'
            combined_yaml, msg= combine.combine_yaml(yaml1, yaml2, combined_scenario_name, mode='agent')
            if combined_yaml is None:
                print(f'Fail: {msg}')
                # counter -= len(sce_combinations)
                success = False
                break

            csv1 = f'{basic_scenarios_folder}/{cata1}/{sce1}.csv'
            csv2 = f'{basic_scenarios_folder}/{cata2}/{sce2}.csv'
            combined_csv = combine.combine_csv(csv1, csv2, combined_scenario_name, mode='agent')

            # save the combined data
            if not os.path.exists(f'{save_root}/{sc_folder_name}'):
                os.makedirs(f'{save_root}/{sc_folder_name}')
            save_path = f'{save_root}/{sc_folder_name}/{scenario_number}'
            combine.save_yaml(combined_yaml, f'{save_path}.yaml')
            combine.save_csv(combined_csv, f'{save_path}.csv')
            counter +=1
        # if success:
        #     counter += len(sce_combinations)
        print('-----------------------------------')

    print(f"{counter} scenarios combined.")


def show_statistics(basic_scenarios_folder):
    # Get all folder in ./scenario_config
    all_basis = os.listdir(basic_scenarios_folder)
    print(f"Total {len(all_basis)} folder found.")

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
        print(f"[ {cata1} ] x [ {cata2} ] =  {cata_1s} x {cata_2s}  = {len(sce_combinations)} SCs")
        counter += len(sce_combinations)
        
    print(f"Total {counter} scenarios.")



if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '-m', '--mode',
        metavar='MODE',
        default='combine',
        type=str,
        help='statistic/s or combine/c')
    argparser.add_argument(
        '-f', '--folder',
        metavar='FOLDER',
        default='scenario_config',
        type=str,
        help='basic scenario folder')
    
    args = argparser.parse_args()

    if args.mode == 'combine' or args.mode == 'c':
        combine_all_scenarios(args.folder)
    elif args.mode == 'statistic' or args.mode == 's':
        show_statistics(args.folder)





