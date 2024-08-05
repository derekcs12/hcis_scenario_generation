# topo.py
#!/usr/bin/env python

# Copyright (c) 2019 Marc G Puig. All rights reserved.
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import glob
import os
import sys
import numpy as np

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    print('carla not found')
    pass

import carla
import argparse
from random import sample 
from copy import copy
from pprint import pprint
# from scenariogeneration import xosc, prettyprint


import matplotlib.pyplot as plt

from dicent_utils import *
from init_scenario import ScenarioCategory
from xosc_t4way import generate_4way
# from xosc_striaght_cutin import generate_straight_cutin
# from xosc_striaght import generate_straight
# from xosc_striaght_obstacle import generate_straight_obstacle

hct_topo_list = {}
hct_topo_list['4way'] = [(449,184)]   # intersection center
hct_topo_list['4way'] = [(256,-30)]   # intersection center
hct_topo_list['4way'] = [(46,-115)]   # intersection center
# hct_topo_list['straight'] = [(325,80)]   # intersection center


"""
"""
class MapAlignment():
    def __init__(self, topo, topo_center):
        self.topo = topo
        self.topo_center = topo_center
        self.topo_center_wp = None
        self.zones = {}
        # self.uplt = copy(mplot)
        self._selfdefine_juction_zone()
        # if self.topo == '4way':
        #     self._define_junction_zone()
        # elif self.topo =='straight' or self.topo =='straight_cutin' or self.topo =='straight_static':
        #     self._define_straight_zone()
        
        # print("topo_center", self.topo_center)
    
    def _selfdefine_juction_zone(self):
        rid, lid, s = 121, 1, 5
        self.zones['sl1'] = carla_map.get_waypoint_xodr(rid, lid, s)
        self.zones['sl2'] = carla_map.get_waypoint_xodr(rid, lid, s+10)
        self.zones['sl3'] = carla_map.get_waypoint_xodr(rid, lid, s+20)
        self.zones['sr1'] = carla_map.get_waypoint_xodr(rid, lid*2, s)
        self.zones['sr2'] = carla_map.get_waypoint_xodr(rid, lid*2, s+10)
        self.zones['sr3'] = carla_map.get_waypoint_xodr(rid, lid*2, s+20)
        rid, lid, s = 17, 1, 0
        self.zones['wl-1'] = carla_map.get_waypoint_xodr(rid, lid*-1, s)
        self.zones['wl-2'] = carla_map.get_waypoint_xodr(rid, lid*-1, s+10)
        self.zones['wl-3'] = carla_map.get_waypoint_xodr(rid, lid*-1, s+20)
        rid, lid, s = 16, 1, 0
        self.zones['el-1'] = carla_map.get_waypoint_xodr(rid, lid*-1, s)
        self.zones['el-2'] = carla_map.get_waypoint_xodr(rid, lid*-1, s+10)
        self.zones['el-3'] = carla_map.get_waypoint_xodr(rid, lid*-1, s+20)
        rid, lid, s = 144, 1, 0
        self.zones['nl-1'] = carla_map.get_waypoint_xodr(rid, lid*-1, s)
        self.zones['nl-2'] = carla_map.get_waypoint_xodr(rid, lid*-1, s+10)
        self.zones['nl-3'] = carla_map.get_waypoint_xodr(rid, lid*-1, s+20)
        self.zones['nr-1'] = carla_map.get_waypoint_xodr(rid, lid*-1*2, s)
        self.zones['nr-2'] = carla_map.get_waypoint_xodr(rid, lid*-1*2, s+10)
        self.zones['nr-3'] = carla_map.get_waypoint_xodr(rid, lid*-1*2, s+20)

        junction_x, junction_y = 685, -132  # Replace with actual coordinates
        # junction_center = carla.Location(junction_x, junction_y, 0)

        # # 校正地圖中心
        # waypoint = get_waypoint(junction_center)
        # if waypoint is None:
        #     print("====Waypoint not found at the given location====")
        #     return

        # junction = waypoint.get_junction() # 抓所屬的junction
        # if junction is None:
        #     print("====No junction found at the waypoint====")
        #     return
        
        self.topo_center = (junction_x, junction_y)
        # self.topo_center_wp = waypoint

    def _define_junction_zone(self):
        # ------
        # Define the junction center coordinates
        # junction_x, junction_y = 7.0, 23.0  # Replace with actual coordinates
        # junction_x, junction_y = 450.0, 180.0  # Replace with actual coordinates
        # junction_x, junction_y = 47, 113  # Replace with actual coordinates
        junction_x, junction_y = self.topo_center  # Replace with actual coordinates
        junction_center = carla.Location(junction_x, junction_y, 0)

        # 校正地圖中心
        waypoint = get_waypoint(junction_center)
        if waypoint is None:
            print("====Waypoint not found at the given location====")
            return

        junction = waypoint.get_junction() # 抓所屬的junction
        if junction is None:
            print("====No junction found at the waypoint====")
            return
        
        self.topo_center_wp = waypoint


        # Get the bounding box of the junction
        bbox = junction.bounding_box
        junction_center = bbox.location
        junction_rotate = bbox.rotation
        junction_wp = get_waypoint(junction_center)
        print(f"Junction center: ({junction_center.x:.1f},{junction_center.y:.1f})")

        sortbyradians = {}
        begin = carla.Vector3D(0,-1,0) #direction 從下開始,逆時針定義z1,z2, ....
        jlane = junction.get_waypoints(carla.LaneType.Driving)
        for pair in jlane:
            wp = pair[1] #right lane
            n = begin.cross(wp.transform.location-junction_center)
            rad = begin.get_vector_angle(wp.transform.location-junction_center) * (n.z/abs(n.z))
            sortbyradians[round(rad,4)] = wp

        sortbyradians = sorted(sortbyradians.items(), key=lambda x: x[0] if x[0] > 0 else 6.28+x[0], reverse=True)

        uni_wplist = []
        for _, wp in sortbyradians:

            right_lane = wp.next(1)[-1]
            left_lane = right_lane.get_left_lane()

            if right_lane in uni_wplist:
                continue
            uni_wplist.append(right_lane)

        # uplt = copy(mplot)
        # uplt.add_carla_points(uni_wplist, color='red')
        # uplt.show(self.topo_center)
        # exit()

        #########################################
        
        # Calculate the z4_anchor
        # z1 下面
        # z2 右邊
        # z3 上面
        # z4 左邊      
        compass = ['s','e','n','w'] # 南東北西
        # # Generate gradient
        gradient = generate_gradient(n=4) 
        for i, wp in enumerate(uni_wplist):
            direction = compass[i]
            self.zones.update({direction + 'l1': carla_map.get_waypoint_xodr(wp.road_id, -wp.lane_id, wp.s)})
            self.zones.update({direction + 'l2': carla_map.get_waypoint_xodr(wp.road_id, -wp.lane_id, wp.s+7)})
            self.zones.update({direction + 'l3': carla_map.get_waypoint_xodr(wp.road_id, -wp.lane_id, wp.s+14)})
            self.zones.update({direction + 'r1': carla_map.get_waypoint_xodr(wp.road_id, -wp.lane_id, wp.s)})
            self.zones.update({direction + 'r2': carla_map.get_waypoint_xodr(wp.road_id, -wp.lane_id, wp.s+7)})
            self.zones.update({direction + 'r3': carla_map.get_waypoint_xodr(wp.road_id, -wp.lane_id, wp.s+14)})
            self.zones.update({direction + 'l-1': carla_map.get_waypoint_xodr(wp.road_id, wp.lane_id, wp.s)})
            self.zones.update({direction + 'l-2': carla_map.get_waypoint_xodr(wp.road_id, wp.lane_id, wp.s+7)})
            self.zones.update({direction + 'l-3': carla_map.get_waypoint_xodr(wp.road_id, wp.lane_id, wp.s+14)})
            self.zones.update({direction + 'r-1': carla_map.get_waypoint_xodr(wp.road_id, wp.lane_id, wp.s)})
            self.zones.update({direction + 'r-2': carla_map.get_waypoint_xodr(wp.road_id, wp.lane_id, wp.s+7)})
            self.zones.update({direction + 'r-3': carla_map.get_waypoint_xodr(wp.road_id, wp.lane_id, wp.s+14)})

            # print(zone, wp.road_id, wp.lane_id)
            # print(zone, ori_wp.road_id, ori_wp.lane_id)
            # pprint(self.zones[zone])
            
            # uplt.add_carla_points(wp, color=gradient[i])

            # continue
        # uplt.show(self.topo_center)
        # exit()

    def _define_straight_zone(self):
        lead_distance = 30
        
        # self.topo_center = (325, -72)
        # self.topo_center = (248, 249)
        # self.topo_center = (213, 146) #9
        # 獲取地圖資訊
        wp = get_waypoint(carla.Location(self.topo_center[0], self.topo_center[1], 0))
        if wp is None:
            print("Waypoint not found at the given location")
            return
        self.topo_center_wp = wp

        print(wp.lane_id, wp.road_id, wp.s)

        left_wp = wp.get_left_lane()
        right_wp = wp.get_right_lane()
   
        
        wp_forward, wp_backward = get_road_info(wp, lead_distance)
        left_wp_forward, left_wp_backward = get_road_info(left_wp, lead_distance)
        right_wp_forward, right_wp_backward = get_road_info(right_wp, lead_distance)
        
        # self.uplt.add_carla_points(waypoint, color='red', marker='x')
        # self.uplt.add_carla_points(wp_forward, color='green', marker='s')
        # self.uplt.add_carla_points(wp_backward, color='orange', marker='s')
        # self.uplt.show(self.topo_center)
        # # exit()
        # print("Left lane: {} | {} | {}, Right lane: {} | {} | {}".format(left_wp.road_id, left_wp.lane_id, left_wp.s, right_wp.road_id, right_wp.lane_id, right_wp.s))
        # print("Forward lane: {} | {} | {}, Back lane: {} | {} | {}".format(wp_forward.road_id, wp_forward.lane_id, wp_forward.s, wp_backward.lane_id, wp_backward.road_id, wp_backward.s))
        # self.uplt.add_carla_points(waypoint, color='red', marker='x')
        # if left_wp is not None: self.uplt.add_carla_points(left_wp, color='green', marker='s')
        # if right_wp is not None: self.uplt.add_carla_points(right_wp, color='yellow', marker='*')
        # self.uplt.show(self.topo_center)
        # exit()

        # 假設ego都在右邊車道
        """
        ┌───────┬───────┬───────┐
        │ R3    │ R2    │ R1    │
        ├───────┼───────┼───────┤
        │ R6    │ R5▭➞ │ R4    │
        ├───────┼───────┼───────┤
        │ R9    │ R8    │ R7    │
        └───────┴───────┴───────┘
        """
        
        if wp_backward is None: print("Cannot find backward point!")
        if wp_forward is None: print("Cannot find forward point!")
        if left_wp is None: print("No left lane!")
        if right_wp is None: print("No right lane!")
        

        self.zones['r1'] = left_wp_forward
        self.zones['r2'] = left_wp
        self.zones['r3'] = left_wp_backward
        self.zones['r4'] = wp_forward
        self.zones['r5'] = wp
        self.zones['r6'] = wp_backward
        self.zones['r7'] = right_wp_forward
        self.zones['r8'] = right_wp
        self.zones['r9'] = right_wp_backward




    def sample(self, zone):
        return sample(self.zones[zone]['points'], k=1)[0]

# class 


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
    args = argparser.parse_args()

    # Approximate distance between the waypoints
    WAYPOINT_DISTANCE = 2.0 # in meters

    try:
        if 'init':

            global carla_map
            with open('hct_6.xodr', 'r') as fp:
                carla_map = carla.Map('hct_6', fp.read())

            global mplot
            mplot = MapPlot()

            """
            # GET WAYPOINTS IN THE MAP 
            waypoint_list = carla_map.generate_waypoints(WAYPOINT_DISTANCE)
            junction_list = [(wp.transform.location.x,wp.transform.location.y) for wp in waypoint_list if wp.is_junction]


            mplot.add_carla_points(waypoint_list, linestyle='', markersize=3, color='blue', marker='o')
            mplot.show()
            """
            
            # print(plan_path(carla_map, method='global_planner'))
            # exit("ETESTSTT")


        # get logical sc
        # scenario_category = ['31-1']
        # scenario_category = ['99']

        scenario_category_all = [args.sc]
        # scenario_category_all = [['left_turn'+str(i)] for i in range(1,16)]
        # scenario_category_all = [['left_turn1']]

        # scenario_category = ['15']
        for scenario_category in scenario_category_all:
            scenario_name = "_".join(scenario_category)
            # sc = ScenarioCategory(['31-1'])
            print("scenario_name: ",scenario_name)
            sc = ScenarioCategory(scenario_category)
            # print((sc.adv))
            # continue
            
            if sc.topo_center is not None: 
                topo_center = (sc.topo_center[0], -sc.topo_center[1])
            else:
                topo_center = sample(hct_topo_list[sc.topo], k=1)[0]
            # print(topo_center)
            # print(SC)
            # mplot.show(topo_center)
            # exit()

            # align init position
            Map = MapAlignment(sc.topo, topo_center)
            # pprint(Map.zones)
            # dir(Map);exit()
            # print(Map.topo_center);exit()

            """ 
            Build xosc 
            """
            if sc.topo == '4way':
                sce = generate_4way(Map, sc)
            # if sc.topo == 'straight_cutin':
            #     sce = generate_straight_cutin(Map, sc)
            # if sc.topo == 'straight':
            #     sce = generate_straight(Map, sc)
            # if sc.topo == 'straight_static':
            #     sce = generate_straight_obstacle(Map, sc)
                # sce.write_xml(f"../../esmini-demo/resources/xosc/{scenario_name}TEST.xosc")
                sce.write_xml(f"/home/hcis-s05/Downloads/esmini-demo/resources/xosc/{scenario_name}_TEST.xosc")

            if sc.topo == '4way':
                sce = generate_4way(Map, sc, company="ITRI")
            # if sc.topo == 'straight_cutin':
            #     sce = generate_straight_cutin(Map, sc, company="ITRI")
            # if sc.topo == 'straight':
            #     sce = generate_straight(Map, sc, company="ITRI")
            # if sc.topo == 'straight_static':
            #     sce = generate_straight_obstacle(Map, sc, company="ITRI")
                # sce.write_xml(f"../xosc/0722/{scenario_name}.xosc")
                sce.write_xml(f"./xosc_itri/{scenario_name}.xosc")
            """
            """
        # prettyprint(sce.get_element())


    finally:
        pass



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