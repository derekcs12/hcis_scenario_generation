import os
import yaml
import argparse
from generate import generate
import argcomplete

def valid_path(path):
    """验证路径是否有效"""
    if path == 'all':
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
    
    argcomplete.autocomplete(argparser)
    args = argparser.parse_args()
    
    
    configFile = []
    if args.config == 'all':
        for root, dirs, files in os.walk('./scenario_config'):
            for file in files:
                if file.endswith('.yaml'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r') as f:
                        config = yaml.safe_load(f)
                    configFile.append(config)
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
        

    print("total config: ", len(configFile))
    for config in configFile:
        """ 
        Build xosc 
        """
        sce = generate(config)
        sce.write_xml(f"/home/hcis-s05/Downloads/esmini-demo/resources/xosc/{config['Scenario_name']}.xosc")
        sce.write_xml(f"/home/hcis-s05/Downloads/esmini-demo/resources/xosc/tmp.xosc")
        # sce.write_xml(f"/home/hcis-s19/Documents/ChengYu/esmini-demo/resources/xosc/built_from_conf/keeping/{config['Scenario_name']}.xosc")

        sce = generate(config,company="ITRI")
        sce.write_xml(f"./xosc_itri/{config['Scenario_name']}.xosc")
        # sce.write_xml(f"/home/hcis-s19/Documents/ChengYu/ITRI/xosc/0722/{config['Scenario_name']}.xosc")
        print(f"Scenario {config['Scenario_name']} is built.")
 

if __name__ == '__main__':
    try:
        main()
    finally:
        print('Done.')