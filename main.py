import os
import yaml
import argparse
from generate import generate
import argcomplete
import random

"""
 Usage:
    python main.py -c all
"""

def valid_path(path):
    """驗證路徑是否有效"""
    if path == 'all' or path == 'sind':
        return path
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"invalid path: {path}")
    return path

def parse_args():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '-s', '--sc',
        metavar='S',
        default='',
        nargs="+",
        help='Scenario category')
    argparser.add_argument(
        '-b', '--base-config',
        type=valid_path,
        default='config/base/hcis_base.yaml',
        help='Base Config file path')
    # config path
    argparser.add_argument(
        '-c', '--config',
        required=True,
        metavar='C',
        type=valid_path,
        help='Config file path')
    argparser.add_argument(
        '-d', '--deactivate',
        action='store_true',
        help='Whether to deactivate the controller')
    argparser.add_argument(
        '--controller',
        metavar='CONTROLLER',
        default='',
        help='Controller name (default: None)')
    
    argcomplete.autocomplete(argparser)
    return argparser.parse_args()

def collect_scenarios(path):
    collection = []
    for root, dirs, files in os.walk(path):
        for file in files:
            # # Downsampling
            # if 1.2 < random.randint(0, 10):
            #     continue
            if file.endswith('.yaml'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    scenario_config = yaml.safe_load(f)
                collection.append(scenario_config)
                print('find config file: ', len(collection),end='\r')
    return collection

def main():
    args = parse_args()

    # === Load Base Config === 
    with open(args.base_config,'r') as f:
        base_config = yaml.safe_load(f)

    # === Load Scenario Configs ===
    scenario_configs = []
    if args.config == 'all':
        # collect all files in the folder
        scenario_configs.extend(collect_scenarios('./scenario_config'))
        scenario_configs.extend(collect_scenarios('./scenario_config_additional'))
    elif args.config.endswith('.yaml'):
        # collect single file
        with open(args.config,'r') as f:
            scenario_config = yaml.safe_load(f)
        scenario_configs.append(scenario_config)
    elif os.path.isdir(args.config): 
        # collect all files in the folder
        scenario_configs = collect_scenarios(args.config)
    else:
        raise ValueError("Invalid config file path.")

    # === Generate & Save xosc ===
    for scenario_config in scenario_configs:
        scenario_config['Controller'] = args.controller

        # Generate xosc 
        sce = generate(base_config, scenario_config)

        # Save xosc
        for path in base_config['save_paths']:
            if path.endswith('.xosc'):
                dir_path = os.path.dirname(path)
                file_path = path
            elif os.path.isdir(path) or path.endswith('/'):
                dir_path = path
                file_path = os.path.join(dir_path, f"{scenario_config['Scenario_name']}.xosc")
            else:
                raise ValueError(f"Invalid save path: {path}")
            
            os.makedirs(dir_path, exist_ok=True)
            sce.write_xml(file_path)


    print("total config: ", len(scenario_configs))

if __name__ == '__main__':
    try:
        main()
    finally:
        print('Done.')