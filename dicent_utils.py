import matplotlib.pyplot as plt
import numpy as np
import sys
import os

import glob

sys.path.append('../')
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass


import carla
from agents.navigation.global_route_planner import GlobalRoutePlanner

global carla_map
with open('hct_6.xodr', 'r') as fp:
    carla_map = carla.Map('hct_6', fp.read())

class MapPlot():
    def __init__(self) -> None:
        self.plt = plt
        self.plt.subplot()
        # Invert the y axis since we follow UE4 coordinates
        self.plt.gca().invert_yaxis()
        self.plt.margins(x=0.0, y=0)

    def add_carla_points(self, points, color='blue', marker='o', markersize=5, linestyle=''):
        if not isinstance(points, list):
            points = [points]

        Xs = [waypoint.transform.location.x for waypoint in points]
        Ys = [waypoint.transform.location.y for waypoint in points]
        self.plt.plot(Xs, 
                      Ys,
                      color=color, marker=marker, markersize=markersize , linestyle=linestyle)
        
    def add_points(self, points, color='blue', marker='o', markersize=5, linestyle=''):
        if not isinstance(points, list):
            points = [points]

        Xs = [waypoint[0] for waypoint in points]
        Ys = [waypoint[1] for waypoint in points]
        self.plt.plot(Xs, 
                      Ys,
                      color=color, marker=marker, markersize=markersize , linestyle=linestyle)

    def show(self, center=(50,50), zoom=50):
        self.plt.xlim(center[0] - zoom, center[0] + zoom)
        self.plt.ylim(center[1] - zoom, center[1] + zoom)
        self.plt.show()



def generate_gradient(color1=np.array([0, 1, 0]), color2=np.array([1, 0, 0]), n = 5):
    # rgb_space = ['#'+str(c) for c in np.linspace(color1, color2, n)]
    rgb_space = np.linspace(color1, color2, n)
    return rgb_space



def get_road_info(waypoint, distance=20):
    """
    給定一個點，返回前後指定距離的道路信息。
    
    :param waypoint: carla.Waypoint 對象
    :param distance: 要查找的距離（默認20m）
    :return: 前後waypoint
    """

    # 獲取給定點的s偏移量
    s = waypoint.s
    # global carla_map
    # 獲取前後路徑點
    wp_forward = waypoint.next(distance)[0] if len(waypoint.next(distance)) > 0 else None
    wp_backward = waypoint.previous(distance)[0] if len(waypoint.previous(distance)) > 0 else None

    return wp_forward , wp_backward


from scenariogeneration import xosc, prettyprint
def create_LanePosition_from_wp(waypoint, s=None, s_offset=0, lane_offset=0, orientation=False):
    sign = np.sign(waypoint.lane_id)
    final_s = waypoint.s - s_offset * sign if s is None else s
    # print("s_offset * sign", s_offset * sign)
    # print("final_s", final_s)
    # print("waypoint.s", waypoint.s)
    # print(orientation)

    return xosc.LanePosition(
        s=final_s,
        offset= lane_offset,
        lane_id=waypoint.lane_id,
        road_id=waypoint.road_id,
        orientation= xosc.Orientation(h=3.14159, reference='relative') if orientation else xosc.Orientation()
    )


def create_TransitionDynamics_from_sc(agent_sc):
    dynamic_shape = getattr(xosc.DynamicsShapes, agent_sc.dynamic_shape)
    return xosc.TransitionDynamics(dynamic_shape, xosc.DynamicsDimension.time, agent_sc.dynamic_duration)


def create_ValueTrigger_from_sc(agent_sc=None, agent_name=None, ego_name=None):
    if agent_sc == None:
        return xosc.ValueTrigger(
            name = "start_triggerSimulationTime",
            delay = 0.3,
            conditionedge = xosc.ConditionEdge.none,
            valuecondition = xosc.SimulationTimeCondition(0, xosc.Rule.greaterThan)
        )
    if agent_sc.trigger =='sim_time':
        print("USE", agent_sc.trigger)
        return xosc.ValueTrigger(
                name = "start_triggerSimulationTime",
                delay = 0,
                conditionedge = xosc.ConditionEdge.none,
                valuecondition = xosc.SimulationTimeCondition(agent_sc.dyn_start, xosc.Rule.greaterThan)
            )
    elif agent_sc.trigger =='sim_step':
        return xosc.EntityTrigger(
                name = "EgoCloseToAgent",  
                delay = 0,
                conditionedge = xosc.ConditionEdge.rising,
                entitycondition = xosc.TimeHeadwayCondition(
                                    entity=agent_name, 
                                    value=agent_sc.dyn_start, 
                                    rule=xosc.Rule.lessThan if agent_sc.from_opposite else xosc.Rule.greaterThan),
                triggerentity = ego_name, 
                triggeringrule = "any" 
            )
    
def create_EntityTrigger_from_sc(egoName, agent_sc=None,):
    return xosc.EntityTrigger(
                name = "EgoCloseToAgent",  
                delay = 0,
                conditionedge = xosc.ConditionEdge.rising,
                entitycondition = xosc.TimeHeadwayCondition(
                                    entity=agent_name, 
                                    value=agent_sc.dyn_start, 
                                    rule=xosc.Rule.lessThan if agent_sc.from_opposite else xosc.Rule.greaterThan),
                triggerentity = egoName, 
                triggeringrule = "any" 
            )

def create_EntityTrigger_at_egoInitWp(egoName, ego_wp,s="$Ego_S", tolerance=1):
    sign = -np.sign(ego_wp.lane_id)
    s = ego_wp.s - sign*27
    # if s != "$Ego_S":
    #     s *= sign
    reachPosCondition = xosc.ReachPositionCondition(xosc.LanePosition(s = s,
                                                                      offset = 0,  
                                                                      lane_id = ego_wp.lane_id, 
                                                                      road_id = ego_wp.road_id),
                                                    tolerance = tolerance)
    return xosc.EntityTrigger(name = "EgoApproachInitWp", 
                              delay = 0,
                              conditionedge = xosc.ConditionEdge.rising,
                              entitycondition = reachPosCondition, 
                              triggerentity = egoName, triggeringrule = "any")
    
def create_StopTrigger(egoName, distance=130, time=11,event_name='event'):

    stopdist_trigger = xosc.EntityTrigger(
            "stoptrigger", 0, xosc.ConditionEdge.none, xosc.TraveledDistanceCondition(value = distance), egoName
    )
    stoptime_trigger = xosc.ValueTrigger(
            # "stoptrigger", 0, xosc.ConditionEdge.none, xosc.SimulationTimeCondition(value = time, rule= xosc.Rule.greaterThan)
            "stoptrigger", 3, xosc.ConditionEdge.none, xosc.StoryboardElementStateCondition(element=xosc.StoryboardElementType.event, reference=event_name, state=xosc.StoryboardElementState.completeState)
    )
    stopdist_group = xosc.ConditionGroup()
    stopdist_group.add_condition(stopdist_trigger)
    stoptime_group = xosc.ConditionGroup()
    stoptime_group.add_condition(stoptime_trigger)

    # create trigger and add the two conditiongroups (or logic)
    stopTrigger = xosc.Trigger('stop')
    stopTrigger.add_conditiongroup(stopdist_group)
    stopTrigger.add_conditiongroup(stoptime_group)

    return stopTrigger

def create_Trigger_following_previous(previousEventName, delay):
    return xosc.ValueTrigger(
            name = "FollowingPreviosTrigger",
            delay = delay,
            conditionedge = xosc.ConditionEdge.none,
            valuecondition = xosc.StoryboardElementStateCondition(
                                element='event',
                                reference=previousEventName,
                                state='startTransition')
        )
    
    

def plan_path(start=None, end=None, WAYPOINT_DISTANCE=1.0, method='greedy'):
    if method == 'greedy':

        pass
    elif method=='global_planner':
        global_planner = GlobalRoutePlanner(carla_map, WAYPOINT_DISTANCE)
        start = start.transform.location
        end   = end.transform.location
        # s = carla_map.get_waypoint(carla.Location(440, 170, 0)).transform.location
        # e = carla_map.get_waypoint(carla.Location(450, 200, 0)).transform.location
        # start = s
        # end   = e

        # route = global_planner.trace_route(e,s)
        route1 = global_planner.trace_route(start,end)
        route2 = global_planner.trace_route(end,start)
        print(len(route1), len(route2))
        if len(route1) <= len(route2):
            route = route1
        else:
            route = route2

        route = [wp for wp,r in route]
        # print(route)
        return route
