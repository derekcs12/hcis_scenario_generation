# topo.py
#!/usr/bin/env python

# Copyright (c) 2019 Marc G Puig. All rights reserved.
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# import glob
# import os
# import sys
# import numpy as np
import yaml

# try:
#     sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
#         sys.version_info.major,
#         sys.version_info.minor,
#         'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
# except IndexError:
#     print('carla not found')
#     pass

# import carla
import argparse
# from random import sample 
# from copy import copy
# from pprint import pprint


# import matplotlib.pyplot as plt

# from dicent_utils import *
# from init_scenario import ScenarioCategory
# from xosc_t4way import generate_4way
# from xosc_striaght_cutin import generate_straight_cutin
# from xosc_striaght import generate_straight
# from xosc_striaght_obstacle import generate_straight_obstacle


from generate import generate


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
        default='config_example.yaml',
        help='Config file path')
    args = argparser.parse_args()

    with open(args.config,'r') as f:
        config = yaml.safe_load(f)

    """ 
    Build xosc 
    """
    sce = generate(config)
    sce.write_xml(f"/home/hcis-s05/Downloads/esmini-demo/resources/xosc/{config['Scenario_name']}.xosc")

    sce = generate(config,company="ITRI")
    sce.write_xml(f"./xosc_itri/{config['Scenario_name']}.xosc")
    
    # if sc.topo == '4way':
    #     sce = generate_4way(Map, sc)
    # # if sc.topo == 'straight_cutin':
    # #     sce = generate_straight_cutin(Map, sc)
    # # if sc.topo == 'straight':
    # #     sce = generate_straight(Map, sc)
    # # if sc.topo == 'straight_static':
    # #     sce = generate_straight_obstacle(Map, sc)
    #     # sce.write_xml(f"../../esmini-demo/resources/xosc/{scenario_name}TEST.xosc")
    #     sce.write_xml(f"/home/hcis-s05/Downloads/esmini-demo/resources/xosc/{scenario_name}_TEST.xosc")

    # if sc.topo == '4way':
    #     sce = generate_4way(Map, sc, company="ITRI")
    # # if sc.topo == 'straight_cutin':
    # #     sce = generate_straight_cutin(Map, sc, company="ITRI")
    # # if sc.topo == 'straight':
    # #     sce = generate_straight(Map, sc, company="ITRI")
    # # if sc.topo == 'straight_static':
    # #     sce = generate_straight_obstacle(Map, sc, company="ITRI")
    #     # sce.write_xml(f"../xosc/0722/{scenario_name}.xosc")
    #     sce.write_xml(f"./xosc_itri/{scenario_name}.xosc")
    """
    """
    # prettyprint(sce.get_element())



def get_waypoint(location, lanetype=' driving'):
    carla_lane_type = carla.LaneType.Driving
    if lanetype == 'parking':
        carla_lane_type = carla.LaneType.Parking
    elif lanetype == 'road_shoulder':
        carla_lane_type = carla.LaneType.RoadShoulder
    elif lanetype == 'Sidewalk':
        carla_lane_type = carla.LaneType.Sidewalk
    elif lanetype == 'any':
        carla_lane_type = carla.LaneType.Any

    return carla_map.get_waypoint(location, project_to_road=True, lane_type=carla_lane_type)




if __name__ == '__main__':
    try:
        main()
    finally:
        print('Done.')