import os
import yaml
import argparse
import concurrent.futures
from generate import generate, esmini
import random
import glob

"""
 Usage:
    python main.py -b config/base/hcis_no_runup.yaml -c all
    python main.py -b config/base/hcis_no_runup.yaml -c all --esmini-path /home/hcis-s19/Documents/ChengYu/esmini  #(跑完自動開啟esmini)
    python main.py -b config/base/HetroD_no_runup.yaml -c /home/hcis-s19/Documents/ChengYu/retrive_scene_nps/yaml/config_dynamic.yaml
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
        # type=valid_path,
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
    argparser.add_argument(
        '--esmini-path',
        type=valid_path,
        default=None,
        help='Esmini path')
    argparser.add_argument(
        '--yaml-workers',
        type=int,
        default=0,
        help='Number of worker threads for loading yaml files (0: auto)')
    
    return argparser.parse_args()


YAML_LOADER = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)


def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.load(f, Loader=YAML_LOADER)


def iter_yaml_files(path):
    stack = [path]
    while stack:
        current = stack.pop()
        with os.scandir(current) as it:
            for entry in it:
                if entry.is_dir(follow_symlinks=False):
                    stack.append(entry.path)
                elif entry.is_file() and entry.name.endswith('.yaml'):
                    yield entry.path


def resolve_yaml_workers(configured_workers):
    if configured_workers is None or configured_workers <= 0:
        cpu_count = os.cpu_count() or 4
        return max(1, min(32, cpu_count * 4))
    return max(1, configured_workers)


def collect_scenarios(path, yaml_workers=0):
    collection = []
    file_paths = list(iter_yaml_files(path))
    total = len(file_paths)
    if total == 0:
        return collection

    workers = resolve_yaml_workers(yaml_workers)

    # Small set: avoid thread-pool overhead
    if workers == 1 or total < 64:
        append = collection.append
        for idx, file_path in enumerate(file_paths, start=1):
            # # Downsampling
            # if 1.2 < random.randint(0, 10):
            #     continue
            append(load_yaml(file_path))
            if idx == 1 or idx % 10 == 0:
                print('find config file: ', idx, end='\r')
        print('find config file: ', len(collection))
        return collection

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for idx, scenario_config in enumerate(executor.map(load_yaml, file_paths), start=1):
        # # Downsampling
        # if 1.2 < random.randint(0, 10):
        #     continue
            collection.append(scenario_config)
            if idx == 1 or idx % 10 == 0:
                print('find config file: ', idx, end='\r')

    print('find config file: ', len(collection))
    return collection

def main():
    args = parse_args()

    # === Load Base Config === 
    base_config = load_yaml(args.base_config)

    # === Load Scenario Configs ===
    scenario_configs = []
    if args.config == 'all':
        scenario_configs.extend(collect_scenarios('./config/scenario_config', yaml_workers=args.yaml_workers))
        scenario_configs.extend(collect_scenarios('./config/scenario_config_combined', yaml_workers=args.yaml_workers))
    elif args.config.endswith('.yaml'):
        scenario_configs.append(load_yaml(args.config))
    elif os.path.isdir(args.config): 
        scenario_configs = collect_scenarios(args.config, yaml_workers=args.yaml_workers)
    elif '*' in args.config or '?' in args.config or '[' in args.config:
        # Handle glob patterns
        for file_path in glob.glob(args.config):
            if file_path.endswith('.yaml'):
                scenario_configs.append(load_yaml(file_path))
    else:
        raise ValueError("Invalid config file path.")

    # === Generate & Save xosc ===
    for scenario_config in scenario_configs:
        scenario_config['Controller'] = args.controller

        # Generate xosc 
        sce = generate(base_config, scenario_config)
        
        if args.esmini_path is not None:
            esmini(sce, esminipath=args.esmini_path, window_size="60 60 1920 1080")

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