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
    """验证路径是否有效"""
    if path == 'all' or path == 'sind':
        return path
    if not os.path.exists(path):
        raise argparse.ArgumentTypeError(f"路径无效: {path}")
    return path

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-s', '--sc',
        metavar='S',
        default='',
        nargs="+",
        help='Scenario category (default: all)')
    # config path
    argparser.add_argument(
        '-c', '--config',
        metavar='C',
        type=valid_path,
        default='config_example.yaml',
        help='Config file path')
    argparser.add_argument(
        '-d', '--deactivate',
        action='store_true',
        help='Whether to deactivate the controller')
    
    argcomplete.autocomplete(argparser)
    args = argparser.parse_args()
    
    configFile = []
    if args.config == 'all':
        for root, dirs, files in os.walk('./scenario_config'):
            for file in files:
                # # Downsampling
                # if 1.2 < random.randint(0, 10):
                #     continue
                if file.endswith('.yaml'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        config = yaml.safe_load(f)
                    configFile.append(config)
                    print('find config file: ', len(configFile),end='\r')
        for root, dirs, files in os.walk('./scenario_config_combined'):
            for file in files:
                if file.endswith('.yaml'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        config = yaml.safe_load(f)
                    configFile.append(config)
                    print('find config file: ', len(configFile),end='\r')

    elif args.config.endswith('.yaml'):
        with open(args.config,'r') as f:
            config = yaml.safe_load(f)
        configFile.append(config)
        
    elif os.path.isdir(args.config): 
        for root, dirs, files in os.walk(args.config):
            for file in files:
                if file.endswith('.yaml'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        config = yaml.safe_load(f)
                    configFile.append(config)
    else:
        raise ValueError("Invalid config file path.")
        
    print()
    from datetime import date
    folder = date.today().strftime("%m%d")
    # folder = "0729"
    
    for config in configFile:

        """ 
        Build xosc 
        """
        # config['DeactivateControl'] = args.deactivate
        sce = generate(config)
        # sce.write_xml(f"/home/hcis-s05/Downloads/esmini-demo/resources/xosc/{config['Scenario_name']}.xosc")
        sce.write_xml(f"/home/hcis-s05/ysws/esmini/resources/xosc/tmp/tmp.xosc")
        sce.write_xml(f"./test/{config['Scenario_name']}.xosc")
        
        # sce.write_xml(f"/home/hcis-s19/Documents/ChengYu/esmini-demo/resources/xosc/built_from_conf/{folder}/{config['Scenario_name']}.xosc")
        # sce.write_xml(f"/home/hcis-s19/Documents/ChengYu/ITRI/xosc/lin/{config['Scenario_name']}.xosc")
        
        # continue
        config['Control'] = True
        sce = generate(config,company="ITRI")
        sce.write_xml(f"/home/hcis-s19/Documents/ChengYu/ITRI/xosc/{folder}/{config['Scenario_name']}.xosc")
        
    print("total config: ", len(configFile))
 

if __name__ == '__main__':
    try:
        main()
    finally:
        print('Done.')