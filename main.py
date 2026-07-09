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
    argparser.add_argument(
        '--gen-workers',
        type=int,
        default=0,
        help='生成 xosc 的平行 worker 進程數 (0=自動: 核心數-2, 上限12)')

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

_WORKER_BASE = None
_WORKER_CTRL = None


def _save_xosc(sce, base_config, scenario_config):
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


def _gen_init(base_config, controller):
    """ProcessPoolExecutor 每個 worker 啟動一次, 存 base_config/controller 為全域, 避免每個 task 重複 pickle。"""
    global _WORKER_BASE, _WORKER_CTRL
    _WORKER_BASE = base_config
    _WORKER_CTRL = controller


def _gen_from_path(file_path):
    """Worker: 自行讀取 yaml → 生成 → 寫檔。只 pickle 檔案路徑, 避免傳輸大 config dict, 並平行化 yaml 讀取。"""
    scenario_config = load_yaml(file_path)
    scenario_config['Controller'] = _WORKER_CTRL
    sce = generate(_WORKER_BASE, scenario_config)
    _save_xosc(sce, _WORKER_BASE, scenario_config)
    return scenario_config.get('Scenario_name')


def main():
    args = parse_args()

    # === Load Base Config === 
    base_config = load_yaml(args.base_config)

    # === 收集 yaml 檔路徑 (不在主程序載入; 交給 worker 各自讀, 讀取也平行化) ===
    file_paths = []
    if args.config == 'all':
        for d in ('./config/scenario_config', './config/scenario_config_combined'):
            if os.path.isdir(d):
                file_paths.extend(iter_yaml_files(d))
    elif args.config.endswith('.yaml'):
        file_paths.append(args.config)
    elif os.path.isdir(args.config):
        file_paths.extend(iter_yaml_files(args.config))
    elif '*' in args.config or '?' in args.config or '[' in args.config:
        file_paths.extend(p for p in glob.glob(args.config) if p.endswith('.yaml'))
    else:
        raise ValueError("Invalid config file path.")
    print(f"找到 {len(file_paths)} 個 config 檔")

    # === Generate & Save xosc ===
    if args.esmini_path is not None:
        # 需開啟 esmini 視窗, 維持序列執行
        for fp in file_paths:
            scenario_config = load_yaml(fp)
            scenario_config['Controller'] = args.controller
            sce = generate(base_config, scenario_config)
            esmini(sce, esminipath=args.esmini_path, window_size="60 60 1920 1080")
            _save_xosc(sce, base_config, scenario_config)
            print(f"Saved scenario '{scenario_config['Scenario_name']}'")
    else:
        # 平行: 每個 worker 自行讀 yaml + 生成 + 寫檔 (讀取與生成皆平行, 不 pickle 大 config dict)
        if args.gen_workers and args.gen_workers > 0:
            gen_workers = args.gen_workers
        else:
            gen_workers = min(12, max(1, (os.cpu_count() or 4) - 2))
        gen_workers = max(1, min(gen_workers, len(file_paths) or 1))
        print(f"🧵 生成使用 {gen_workers} 個 worker 進程")
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=gen_workers,
                initializer=_gen_init,
                initargs=(base_config, args.controller)) as executor:
            done = 0
            for _ in executor.map(_gen_from_path, file_paths, chunksize=8):
                done += 1
                if done == 1 or done % 100 == 0:
                    print(f"generated: {done}/{len(file_paths)}", end='\r')
        print(f"generated: {len(file_paths)}/{len(file_paths)}")

    print("total config: ", len(file_paths))

if __name__ == '__main__':
    try:
        main()
    finally:
        print('Done.')