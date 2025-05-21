import os
import argparse
import subprocess

import yaml
from generate import generate

ESMINI_HOME = '/home/hcis-s05/Downloads/esmini-demo'

def check_collision_between_agents(sc_path):
    command = f'{ESMINI_HOME}/bin/esmini --osc {sc_path} --collision --fixed_timestep 0.01 --headless --disable_controllers'
    # command = f'{ESMINI_HOME}/bin/esmini --osc {sc_path} --collision --fixed_timestep 0.05 --window 60 60 1920 1080 --disable_controllers'
    result = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    collision = False
    try:
        # 使用 communicate 讀取所有輸出，避免卡住
        stdout, stderr = result.communicate(timeout=5)  # 設置一個超時，防止永遠等待
        for line in stdout.splitlines():
            if 'Collision' in line:
                print(line)
                if line.count('Agent') > 1:
                    collision = True
                    print(f'Collision detected')
                    break
    except subprocess.TimeoutExpired:
        print('Timeout')
        result.kill()  # 超時後殺掉子進程
        stdout, stderr = result.communicate()  # 確保捕獲已輸出的內容
    finally:
        result.stdout.close()
        result.stderr.close()
    
    return collision



def build_xosc(yaml_path):
    print("Building scenario... ", end='')
    with open(yaml_path,'r') as f:
        config = yaml.safe_load(f)
    sce = generate(config)
    yaml_path = f"{ESMINI_HOME}/resources/xosc/tmp.xosc"
    sce.write_xml(yaml_path)
    command = f'python main.py -c {yaml_path}'
    result = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        # print(f"Building {yaml_path}")
        for line in result.stdout:
            print(line, end='')
    finally:
        result.stdout.close()
        result.stderr.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', type=str,default='scenario_config_combined/test')
    parser.add_argument('--rb', type=str,default='scenario_config_combined/test/filtered')
    args = parser.parse_args()

    # create the directory if it does not exist
    if not os.path.exists(args.rb):
        os.makedirs(args.rb)

    # get all the files in the directory
    files = os.listdir(args.dir)
    for file in files:
        if file.endswith('.yaml'):
            print(f'--------Checking {args.dir}{file}----------')
            build_xosc(os.path.abspath(f'{args.dir}/{file}'))
            if check_collision_between_agents(f'{ESMINI_HOME}/resources/xosc/tmp.xosc'):
                # copy the yaml file to the filtered folder
                print(f'Collision detected')
                with open(f'{args.dir}/{file}', 'r') as f:
                    data = f.readlines()
                    with open(f'{args.rb}/{file}', 'w') as f:
                        f.writelines(data)
            else:
                print(f'No collision detected')
                    
    # check_collision_between_agents('/home/hcis-s05/Downloads/esmini-demo/resources/xosc/tmp.xosc')