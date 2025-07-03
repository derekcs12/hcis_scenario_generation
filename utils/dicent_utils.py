import csv
from scenariogeneration import xosc, prettyprint
import json
from collections import OrderedDict
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import glob
import pandas as pd
from pyxodr.road_objects.network import RoadNetwork



from config import RELATIVE_TRIGGER_POSITIONS

sys.path.append('../')
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass


# import carla
# # from agents.navigation.global_route_planner import GlobalRoutePlanner

# global carla_map
# with open('hct_6.xodr', 'r') as fp:
#     carla_map = carla.Map('hct_6', fp.read())

# class MapPlot():
#     def __init__(self) -> None:
#         self.plt = plt
#         self.plt.subplot()
#         # Invert the y axis since we follow UE4 coordinates
#         self.plt.gca().invert_yaxis()
#         self.plt.margins(x=0.0, y=0)

#     def add_carla_points(self, points, color='blue', marker='o', markersize=5, linestyle=''):
#         if not isinstance(points, list):
#             points = [points]

#         Xs = [waypoint.transform.location.x for waypoint in points]
#         Ys = [waypoint.transform.location.y for waypoint in points]
#         self.plt.plot(Xs,
#                       Ys,
#                       color=color, marker=marker, markersize=markersize , linestyle=linestyle)

#     def add_points(self, points, color='blue', marker='o', markersize=5, linestyle=''):
#         if not isinstance(points, list):
#             points = [points]

#         Xs = [waypoint[0] for waypoint in points]
#         Ys = [waypoint[1] for waypoint in points]
#         self.plt.plot(Xs,
#                       Ys,
#                       color=color, marker=marker, markersize=markersize , linestyle=linestyle)

#     def show(self, center=(50,50), zoom=50):
#         self.plt.xlim(center[0] - zoom, center[0] + zoom)
#         self.plt.ylim(center[1] - zoom, center[1] + zoom)
#         self.plt.show()


def sort_event(event):
    d = OrderedDict([
        ('Type', event['Type']),
        ('Dynamic_delay', event['Dynamic_delay']),
        ('Dynamic_duration', event['Dynamic_duration']),
        ('Dynamic_shape', event['Dynamic_shape']),
        ('End', event['End']),
        ('Use_route', event['Use_route'])
    ])
    return d


def sort_act(act):
    d = OrderedDict([
        ('Type', act['Type']),
        ('Delay', act['Delay']),
        ('Events', [sort_event(e) for e in act['Events']])
    ])
    return d


def sort_agent_dict(agent):
    d = OrderedDict([
        ('Type', agent['Type']),
        ('Start_pos', agent['Start_pos']),
        ('Start_speed', agent['Start_speed']),
        ('Start_trigger', OrderedDict([
            ('lane', agent['Start_trigger']['lane']),
            ('road', agent['Start_trigger']['road']),
            ('s', agent['Start_trigger']['s']),
            ('offset', agent['Start_trigger']['offset']),
            ('type', agent['Start_trigger']['type'])
        ])),
        ('Acts', [sort_act(act) for act in agent['Acts']])
    ])
    return d


def sort_config_dict(data):
    d = OrderedDict([
        ('Scenario_name', data['Scenario_name']),
        ('Ego', OrderedDict([
            ('Start_pos', data['Ego']['Start_pos']),
            ('Start_speed', data['Ego']['Start_speed']),
            ('End_pos', data['Ego']['End_pos'])
        ])),
        ('Map', data['Map']),
        ('Actors', OrderedDict([
            ('Agents', [sort_agent_dict(ag)
                        for ag in data['Actors']['Agents']])
        ]))
    ])

    return json.loads(json.dumps(d))


def generate_gradient(color1=np.array([0, 1, 0]), color2=np.array([1, 0, 0]), n=5):
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
    wp_forward = waypoint.next(distance)[0] if len(
        waypoint.next(distance)) > 0 else None
    wp_backward = waypoint.previous(distance)[0] if len(
        waypoint.previous(distance)) > 0 else None

    return wp_forward, wp_backward


def create_LanePosition_from_wp(waypoint, s=None, s_offset=0, lane_offset=0, orientation=False):
    sign = np.sign(waypoint.lane_id)
    final_s = waypoint.s - s_offset * sign if s is None else s
    # print("s_offset * sign", s_offset * sign)
    # print("final_s", final_s)
    # print("waypoint.s", waypoint.s)
    # print(orientation)

    return xosc.LanePosition(
        s=final_s,
        offset=lane_offset,
        lane_id=waypoint.lane_id,
        road_id=waypoint.road_id,
        orientation=xosc.Orientation(
            h=3.14159, reference='relative') if orientation else xosc.Orientation()
    )


def create_LanePosition_from_config(Map, position, orientation=False, s=None, offset=0):
    if s == None:
        # index, lane_id , s = map(int,position.split(' '))
        index, lane_id, s, offset, orientation = position
    else:
        # index, lane_id , _ = map(int,position.split(' '))
        index, lane_id, _, offset, orientation = position

    orientation = True if orientation == -1 else False
    # print("index, lane_id , s", index, lane_id , s)
    road = int(Map[index]) # if index < 4 else index #derek: SinD地圖太亂，traj直接給road比較快
    return xosc.LanePosition(
        s=s,
        offset=offset*np.sign(lane_id),
        lane_id=lane_id,
        road_id=road,
        orientation=xosc.Orientation(
            h=3.14159, reference='relative') if orientation else xosc.Orientation()
    )


def get_entity_position(entityName):
    return xosc.RelativeLanePosition(lane_id=0, entity=entityName, dsLane=0)


def create_TransitionDynamics_from_sc(agent_sc):
    dynamic_shape = getattr(xosc.DynamicsShapes, agent_sc.dynamic_shape)
    return xosc.TransitionDynamics(dynamic_shape, xosc.DynamicsDimension.time, agent_sc.dynamic_duration)


def create_TransitionDynamics_from_config(event, actorName, actIndex, eventType, type='other'):
    dynamic_shape = getattr(xosc.DynamicsShapes, event['Dynamic_shape'])
    # if type == 'other':
    #     transition_dynamics = xosc.TransitionDynamics(dynamic_shape, xosc.DynamicsDimension.time, f"${actorName}_{actIndex}_{eventIndex}_DynamicDuration")
    # elif type == 'zigzag':
    #     transition_dynamics = xosc.TransitionDynamics(dynamic_shape, xosc.DynamicsDimension.time, f"${actorName}_{actIndex}_DynamicDuration")
    # transition_dynamics = xosc.TransitionDynamics(dynamic_shape, xosc.DynamicsDimension.time, f"${actorName}_{actIndex}_{eventType}_DynamicDuration")
    transition_dynamics = xosc.TransitionDynamics(
        f"${actorName}_{actIndex}_{eventType}_DynamicShape", xosc.DynamicsDimension.time, f"${actorName}_{actIndex}_{eventType}_DynamicDuration")

    return transition_dynamics


def create_ValueTrigger_from_sc(agent_sc=None, agent_name=None, ego_name=None):
    if agent_sc == None:
        return xosc.ValueTrigger(
            name="start_triggerSimulationTime",
            delay=0.3,
            conditionedge=xosc.ConditionEdge.none,
            valuecondition=xosc.SimulationTimeCondition(
                0, xosc.Rule.greaterThan)
        )
    if agent_sc.trigger == 'sim_time':
        print("USE", agent_sc.trigger)
        return xosc.ValueTrigger(
            name="start_triggerSimulationTime",
            delay=0,
            conditionedge=xosc.ConditionEdge.none,
            valuecondition=xosc.SimulationTimeCondition(
                agent_sc.dyn_start, xosc.Rule.greaterThan)
        )
    elif agent_sc.trigger == 'sim_step':
        return xosc.EntityTrigger(
            name="EgoCloseToAgent",
            delay=0,
            conditionedge=xosc.ConditionEdge.rising,
            entitycondition=xosc.TimeHeadwayCondition(
                entity=agent_name,
                value=agent_sc.dyn_start,
                rule=xosc.Rule.lessThan if agent_sc.from_opposite else xosc.Rule.greaterThan),
            triggerentity=ego_name,
            triggeringrule="any"
        )

# def create_EntityTrigger_from_sc(egoName, agent_sc=None,):
#     return xosc.EntityTrigger(
#                 name = "EgoCloseToAgent",
#                 delay = 0,
#                 conditionedge = xosc.ConditionEdge.rising,
#                 entitycondition = xosc.TimeHeadwayCondition(
#                                     entity=agent_name,
#                                     value=agent_sc.dyn_start,
#                                     rule=xosc.Rule.lessThan if agent_sc.from_opposite else xosc.Rule.greaterThan),
#                 triggerentity = egoName,
#                 triggeringrule = "any"
#             )


def create_EntityTrigger_at_egoInitWp(egoName, ego_wp, s="$Ego_S", tolerance=1):
    sign = -np.sign(ego_wp.lane_id)
    s = ego_wp.s - sign*27
    # if s != "$Ego_S":
    #     s *= sign
    reachPosCondition = xosc.ReachPositionCondition(xosc.LanePosition(s=s,
                                                                      offset=0,
                                                                      lane_id=ego_wp.lane_id,
                                                                      road_id=ego_wp.road_id),
                                                    tolerance=tolerance)
    return xosc.EntityTrigger(name="EgoApproachInitWp",
                              delay=0,
                              conditionedge=xosc.ConditionEdge.rising,
                              entitycondition=reachPosCondition,
                              triggerentity=egoName, triggeringrule="any")


def create_EntityTrigger_at_absolutePos(Map, Trigger, EntityName, tolerance=2, delay = 0, triggerName="EgoApproachInitWp"):
    
    road_index, lane_id, s, offset = Trigger['road'], Trigger['lane'], Trigger['s'], Trigger['offset']
    road = int(Map[road_index]) # if road_index < 4 else road_index #derek: SinD地圖太亂，traj直接給road比較快
    return xosc.EntityTrigger(name=triggerName,
                              delay=delay,
                              conditionedge=xosc.ConditionEdge.rising,
                              entitycondition=xosc.ReachPositionCondition(xosc.LanePosition(s=s,
                                                                                            offset=offset,
                                                                                            lane_id=lane_id,
                                                                                            road_id=road),
                                                                          tolerance=tolerance),
                              triggerentity=EntityName, triggeringrule="any")

    # road_index , lane_id , s , offset= Trigger['road'], Trigger['lane'], Trigger['s'], Trigger['offset']
    # # road = int(Map[road_index])
    # road = road_index #derek: 地圖太亂，traj直接給road比較快
    # return xosc.EntityTrigger(name = "EgoApproachInitWp", 
    #                           delay = 0,
    #                           conditionedge = xosc.ConditionEdge.rising,
    #                           entitycondition = xosc.ReachPositionCondition(xosc.LanePosition(s = s,
    #                                                                                       offset = offset,  
    #                                                                                       lane_id = lane_id, 
    #                                                                                       road_id = road),
    #                                                                     tolerance = 2), 
    #                           triggerentity = EntityName, triggeringrule = "any")

def create_EntityTrigger_at_relativePos(Map, Agent, EntityName):
    Trigger = Agent['Start_trigger']
    longitude, lateral, s, offset = Trigger['road'], Trigger['lane'], Trigger['s'], Trigger['offset']

    # ego_wp = Agent['Start_pos'].split(' ')
    # ego_road = int(Map[int(ego_wp[0])])
    # ego_lane = int(ego_wp[1])
    # ego_s = int(ego_wp[2])

    ego_road, ego_lane, ego_s, ego_offset, _ = Agent['Start_pos']
    ego_road = int(Map[ego_road])

    if lateral == 0:
        lane_id = ego_lane
    # elif lateral > 0:
    #     lane_id = ego_lane + np.sign(ego_lane) * lateral
    else:
        lane_id = ego_lane + np.sign(ego_lane) * lateral

    if longitude == 0:
        s = ego_s
    else:
        s = ego_s - np.sign(ego_lane) * s * longitude

    position = xosc.LanePosition(
        s=s, lane_id=lane_id, road_id=ego_road, offset=ego_offset)
    return xosc.EntityTrigger(name="EgoApproachInitWp",
                              delay=0,
                              conditionedge=xosc.ConditionEdge.rising,
                              entitycondition=xosc.ReachPositionCondition(
                                  position, tolerance=2),
                              triggerentity=EntityName, triggeringrule="any")


def create_timeout_condition(egoName, time=300):
    """
    End Condition (1-a) - Timeout Condition
    Description: If the simulation time exceeds the specified time, and the AV system has not connected, the scenario is considered invalid.
    Test Result: Invalid
    """
    group = xosc.ConditionGroup()
    condition = xosc.SimulationTimeCondition(time, xosc.Rule.greaterThan)
    simtime_trigger = xosc.ValueTrigger(
        name="EgoTimeout",
        delay=0,
        conditionedge=xosc.ConditionEdge.none,
        valuecondition=condition,
    )

    has_moved = xosc.ParameterCondition("AV_CONNECTED", "false", xosc.Rule.equalTo)
    has_moved_trigger = xosc.ValueTrigger(
        name="EgoHasNotMoved",
        delay=0,
        conditionedge=xosc.ConditionEdge.none,
        valuecondition=has_moved
    )

    group.add_condition(simtime_trigger)
    group.add_condition(has_moved_trigger)
    return group


def create_stand_still_conditions(egoName,time=10):
    """
    End Condition (1-b) - Ego Get Stuck Condition
    Test Result: Invalid
    """
    group = xosc.ConditionGroup()
    stand_still = xosc.StandStillCondition(time)
    stand_trigger = xosc.EntityTrigger(
        name="EgoStandStill",
        delay=0,
        conditionedge=xosc.ConditionEdge.none,
        entitycondition=stand_still,
        triggerentity=egoName
    )
    has_moved = xosc.ParameterCondition("AV_CONNECTED", "true", xosc.Rule.equalTo)
    has_moved_trigger = xosc.ValueTrigger(
        name="egoHasMoved",
        delay=0,
        conditionedge=xosc.ConditionEdge.none,
        valuecondition=has_moved
    )
    event_started = xosc.ParameterCondition("IS_VALID", "false", xosc.Rule.equalTo)
    event_started_trigger = xosc.ValueTrigger(
        name="EventStarted",
        delay=0,
        conditionedge=xosc.ConditionEdge.none,
        valuecondition=event_started
    )
    group.add_condition(stand_trigger)
    group.add_condition(has_moved_trigger)
    group.add_condition(event_started_trigger)
    return group

def create_invalid_area_condition(Map, egoName, eventStartPoint, xodrPath, distance=2):
    """
    End Condition (1-c) - Invalid Area Condition
    Test Result: Invalid
    """
    group = xosc.ConditionGroup()
    roadnetwork = RoadNetwork(xodrPath)
    roadnetwork.get_roads()
    # roadobj = roadnetwork.road_ids_to_object.get(str(Map[eventStartPoint['road']]))
    # print("roadobj", roadobj)
    exit()
    position = xosc.WorldPosition(eventStartPoint[0], eventStartPoint[1])
    condition = xosc.ReachPositionCondition(position, tolerance=distance)
    trigger = xosc.EntityTrigger(
        name="EgoInvalidArea",
        delay=0,
        conditionedge=xosc.ConditionEdge.falling,
        entitycondition=condition,
        triggerentity=egoName,
        triggeringrule="any"
    )
    group.add_condition(trigger)
    return group
    

def create_right_start_speed_condition(Map, egoName, eventStartPoint, eventStartSpeed, tolerance=5):
    """
    End Condition (1-d) - Right Start Speed Condition
    Test Result: Valid/Success
    """
    group = xosc.ConditionGroup()
    # Position Condition
    startpoint_trigger = create_EntityTrigger_at_absolutePos(Map, eventStartPoint, egoName)

    # Speed Condition 
    lowspeed_condition = xosc.SpeedCondition(f'${{$Ego_Speed/3.6-{tolerance/3.6}}}', xosc.Rule.greaterThan)
    highspeed_condition = xosc.SpeedCondition(f'${{$Ego_Speed/3.6+{tolerance/3.6}}}', xosc.Rule.lessThan)
    lowspeed_trigger = xosc.EntityTrigger(
        name="EgoRightStartSpeed",
        delay=0,
        conditionedge=xosc.ConditionEdge.none,
        entitycondition=lowspeed_condition,
        triggerentity=egoName,
        triggeringrule="any"
    )
    highspeed_trigger = xosc.EntityTrigger(
        name="EgoRightStartSpeed",
        delay=0,
        conditionedge=xosc.ConditionEdge.none,
        entitycondition=highspeed_condition,
        triggerentity=egoName,
        triggeringrule="any"
    )
    group.add_condition(startpoint_trigger)
    group.add_condition(lowspeed_trigger)
    group.add_condition(highspeed_trigger)
    return group

def create_wrong_start_speed_condition(Map, egoName, eventStartPoint, eventStartSpeed, tolerance=2):
    """
    End Condition (1-d) - Wrong Start Speed Condition
    Test Result: Invalid
    """
    lowgroup = xosc.ConditionGroup()
    highgroup = xosc.ConditionGroup()
    # Position Condition
    startpoint_trigger = create_EntityTrigger_at_absolutePos(Map, eventStartPoint, egoName)


    # Speed Condition 
    low_speed_condition = xosc.SpeedCondition(f'${{$Ego_Speed/3.6-{tolerance/3.6}}}', xosc.Rule.lessThan)
    high_speed_condition = xosc.SpeedCondition(f'${{$Ego_Speed/3.6+{tolerance/3.6}}}', xosc.Rule.greaterThan)
    low_speed_trigger = xosc.EntityTrigger(
        name="EgoWrongStartSpeed_low",
        delay=0,
        conditionedge=xosc.ConditionEdge.none,
        entitycondition=low_speed_condition,
        triggerentity=egoName,
        triggeringrule="any"
    )
    high_speed_trigger = xosc.EntityTrigger(
        name="EgoWrongStartSpeed_high",
        delay=0,
        conditionedge=xosc.ConditionEdge.none,
        entitycondition=high_speed_condition,
        triggerentity=egoName,
        triggeringrule="any"
    )

    lowgroup.add_condition(startpoint_trigger)
    lowgroup.add_condition(low_speed_trigger)
    highgroup.add_condition(startpoint_trigger)
    highgroup.add_condition(high_speed_trigger)


    return lowgroup, highgroup

def create_reach_target_condition(Map, egoName, targetPoint):
    """ 
    End Condition (2-a) - Ego reaches the target point
    Test Result: Valid/Success
    """
    group = xosc.ConditionGroup()
    position = create_LanePosition_from_config(Map, targetPoint)
    condition = xosc.ReachPositionCondition(position, tolerance=2)
    trigger = xosc.EntityTrigger(
        name="EgoApproachEndWp",
        delay=0,
        conditionedge=xosc.ConditionEdge.rising,
        entitycondition=condition,
        triggerentity=egoName,
        triggeringrule="any"
    )
    group.add_condition(trigger)
    return group

def create_ego_tle_condition(Map, eventStartPoint, egoName, time=30):
    """
    End Condition (2-b) - Ego TLE
    Test Result: Valid/Success
    """
    group = xosc.ConditionGroup()
    trigger = create_EntityTrigger_at_absolutePos(Map, eventStartPoint, egoName, delay=time, triggerName="EgoTLE")
    group.add_condition(trigger)
    return group


def create_collision_condition(egoName, agentCount=1):
    """
    End Condition (2-c) - Collision
    Test Result: Valid/Success
    """
    group = xosc.ConditionGroup()
    condition = xosc.CollisionCondition('Agent1')
    trigger = xosc.EntityTrigger(
        name="EgoCollision",
        delay=0,
        conditionedge=xosc.ConditionEdge.rising,
        entitycondition=condition,
        triggerentity=egoName,
        triggeringrule="any"
    )
    group.add_condition(trigger)
    return group    

def create_ego_stroll_condition(time=30):
    """
    Replace (1-c) and (2-d): Ego enters invalid area => check if the ego is connected and does not arrive the trigger point in x seconds
    Test Result: invalid
    """
    group = xosc.ConditionGroup()
    connected_condition = xosc.ParameterCondition("AV_CONNECTED", "true", xosc.Rule.equalTo)
    connected_trigger = xosc.ValueTrigger(
        name="EgoStroll",
        delay=time,
        conditionedge=xosc.ConditionEdge.none,
        valuecondition=connected_condition
    )
    event_started = xosc.ParameterCondition("IS_VALID", "false", xosc.Rule.equalTo)
    event_started_trigger = xosc.ValueTrigger(
        name="EventStarted",
        delay=0,
        conditionedge=xosc.ConditionEdge.none,
        valuecondition=event_started
    )
    group.add_condition(connected_trigger)
    group.add_condition(event_started_trigger)
    return group
    
def create_flag_trigger(parameter_name, value='true', delay=0, conditionedge=xosc.ConditionEdge.rising):
    group = xosc.ConditionGroup()
    condition = xosc.ParameterCondition(parameter_name, value, xosc.Rule.equalTo)
    trigger = xosc.ValueTrigger(
        name=f"{parameter_name}_Trigger",
        delay=delay,
        conditionedge=conditionedge,
        valuecondition=condition
    )
    group.add_condition(trigger)
    return group
    
    
def create_StopTrigger(Map, egoName, eventStartPoint, eventStartSpeed, egoTargetPoint, xodrPath):
    stopTrigger = xosc.Trigger('stop')
    
    """NEW END CONDITIONS"""
    # Condition 1 - AV Connection timeout => Invalid
    stopTrigger.add_conditiongroup(create_flag_trigger('AV_CONNECTION_TIMEOUT', 'true'))
    # Condition 2 - Wrong Start Speed => Invalid
    stopTrigger.add_conditiongroup(create_flag_trigger('WRONG_START_SPEED', 'true'))
    # Condition 3 - Ego reaches the target point => Valid/Success
    stopTrigger.add_conditiongroup(create_flag_trigger('EGO_REACHED_END', 'true'))
    # Condition 4 - Ego TLE => Valid/Fail
    stopTrigger.add_conditiongroup(create_flag_trigger('EGO_TLE', 'true'))
    # Condition 5 - Collision => Valid/Fail
    stopTrigger.add_conditiongroup(create_flag_trigger('EGO_COLLISION', 'true'))
    # Condition 6 - Ego Stroll => Invalid
    stopTrigger.add_conditiongroup(create_flag_trigger('EGO_STROLL', 'true'))
    

    return stopTrigger




def create_Trigger_following_previous(previousEventName, delay=0, state='init'):
    if state == 'init':
        state = xosc.StoryboardElementState.startTransition
    elif state == 'complete':
        state = xosc.StoryboardElementState.completeState
    elif state == 'standby':
        state = xosc.StoryboardElementState.standbyState
    else:
        print("state error")
        return None

    conditionGroup = xosc.ConditionGroup()
    for name in previousEventName:
        conditionGroup.add_condition(
            create_StoryBoardElement_Trigger(
                "FollowingPreviosTrigger", delay, xosc.ConditionEdge.rising, 'event', name, state)
        )
    trigger = xosc.Trigger()
    trigger.add_conditiongroup(conditionGroup)
    return trigger


def create_StoryBoardElement_Trigger(name, delay, conditionedge, element, reference, state):
    return xosc.ValueTrigger(
        name=name,
        delay=delay,
        conditionedge=conditionedge,
        valuecondition=xosc.StoryboardElementStateCondition(
            element=element,
            reference=reference,
            state=state)
    )


def create_agent_start_trigger(actorName):
    trigger = xosc.ValueTrigger(
        name=f"EventStartCondition",
        delay=0,
        conditionedge=xosc.ConditionEdge.rising,
        valuecondition=xosc.ParameterCondition(
            "IS_VALID", "true", xosc.Rule.equalTo)
    )
    return trigger

def generate_Agent_Start_Event(actorName, agent, Map):
    agentInitSpeed = xosc.AbsoluteSpeedAction(
        f'${{${actorName}_Speed / 3.6}}', xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0))
    # if agent['Start_trigger']['type'] == 'relative':
    #     agentStartTrigger = create_EntityTrigger_at_relativePos(
    #         Map, agent, 'Ego')
    # else:  # absolute
    #     agentStartTrigger = create_EntityTrigger_at_absolutePos(
    #         Map, agent['Start_trigger'], 'Ego')
    
    agentStartTrigger = create_flag_trigger('IS_VALID', 'true', delay=0, conditionedge=xosc.ConditionEdge.rising)

    advStartSpeedEvent = xosc.Event(
        f"{actorName}_StartSpeedEvent", xosc.Priority.overwrite)
    advStartSpeedEvent.add_action(
        f"{actorName}_StartSpeedAction", agentInitSpeed)
    advStartSpeedEvent.add_trigger(agentStartTrigger)

    return advStartSpeedEvent


def generate_Speed_Event(actorName, actIndex, eventType, event, previousEventName, type='other'):
    transitionDynamic = create_TransitionDynamics_from_config(
        event, actorName, actIndex, eventType, type)
    # if type == 'other':
    #     advEndSpeed = xosc.AbsoluteSpeedAction(f'${{${actorName}_{actIndex}_{eventIndex}_EndSpeed/3.6}}',transitionDynamic)
    #     trigger = create_Trigger_following_previous(previousEventName, f'${actorName}_{actIndex}_{eventIndex}_DynamicDelay', state='complete')
    # elif type == 'zigzag':
    #     advEndSpeed = xosc.AbsoluteSpeedAction(f'${{${actorName}_{actIndex}_{eventIndex}_EndSpeed/3.6}}',transitionDynamic)
    #     trigger = create_Trigger_following_previous(previousEventName, f'${actorName}_{actIndex}_{eventIndex}_DynamicDelay', state='complete')
    advEndSpeed = xosc.AbsoluteSpeedAction(
        f'${{${actorName}_{actIndex}_{eventType}_EndSpeed/3.6}}', transitionDynamic)
    trigger = create_Trigger_following_previous(
        previousEventName, f'${actorName}_{actIndex}_{eventType}_DynamicDelay', state='complete')

    advSpeedEvent = xosc.Event(
        f"{actorName}_SpeedEvent", xosc.Priority.parallel)
    advSpeedEvent.add_action(f"{actorName}_SpeedAction", advEndSpeed)
    advSpeedEvent.add_trigger(trigger)

    return advSpeedEvent


def create_Terminate_Event(actorName, actIndex, currentEvent):
    trigger = create_Trigger_following_previous(
        [currentEvent.name], delay=0, state='complete')
    TerminateEvent = xosc.Event(
        f"{actorName}_Event{actIndex}_TerminateEvent", xosc.Priority.overwrite)
    TerminateEvent.add_action(
        f"{actorName}_Event{actIndex}_TerminateAction", xosc.VisibilityAction(True, True, True))
    TerminateEvent.add_trigger(trigger)

    return TerminateEvent


def generate_Offset_Event(actorName, actIndex, eventType, event, previousEventName, currentPosition):
    displacement = abs(event['End'] - currentPosition[3])
    advgoal = xosc.AbsoluteLaneOffsetAction(event['End'], f"${actorName}_{actIndex}_{eventType}_DynamicShape",
                                            maxlatacc=f"${{{displacement}/{actorName}_{actIndex}_{eventType}_DynamicDuration}}")

    trigger = create_Trigger_following_previous(
        previousEventName, delay=f'${actorName}_{actIndex}_TA_DynamicDelay', state='complete')

    advgoalEvent = xosc.Event(
        f"{actorName}_Event{actIndex}_TrajectoryEvent", xosc.Priority.parallel)
    advgoalEvent.add_action(
        f"{actorName}_Event{actIndex}_TrajectoryAction", advgoal)
    advgoalEvent.add_trigger(trigger)
    currentPosition[3] = event['End']

    return advgoalEvent, currentPosition


def generate_Cut_Event(actorName, actIndex, eventIndex, event, previousEventName, currentPosition):
    targetLane = event['End'][0]
    targetOffset = event['End'][1]
    targetOffset = targetOffset * np.sign(targetLane)
    advgoal = xosc.AbsoluteLaneChangeAction(targetLane, create_TransitionDynamics_from_config(
        event, actorName, actIndex, eventIndex), target_lane_offset=targetOffset)

    trigger = create_Trigger_following_previous(
        previousEventName, delay=f'${actorName}_{actIndex}_TA_DynamicDelay', state='complete')

    advgoalEvent = xosc.Event(
        f"{actorName}_Event{actIndex}_TrajectoryEvent", xosc.Priority.parallel)
    advgoalEvent.add_action(
        f"{actorName}_Event{actIndex}_TrajectoryAction", advgoal)
    advgoalEvent.add_trigger(trigger)
    currentPosition[1] = event['End'][0]
    currentPosition[3] = event['End'][1]

    return advgoalEvent, currentPosition


def generate_Position_Event(actorName, actIndex, event, Map, previousEventName, currentPosition):
    targetPoint = xosc.WorldPosition(event['End'][0], event['End'][1]) if len(
        event['End']) == 2 else create_LanePosition_from_config(Map, event['End'])
    if event['Dynamic_shape'] == 'Straight':
        trajectory = xosc.Trajectory('selfDefineTrajectory', False)
        nurbs = xosc.Nurbs(2)
        nurbs.add_control_point(xosc.ControlPoint(
            create_LanePosition_from_config(Map, currentPosition)))  # 出發點
        # nurbs.add_control_point(xosc.ControlPoint(get_entity_position(actorName))) #出發點
        nurbs.add_control_point(xosc.ControlPoint(targetPoint))  # 目的地
        nurbs.add_knots([0, 0, 1, 1])
        trajectory.add_shape(nurbs)

        # Create a FollowTrajectory action
        advgoal = xosc.FollowTrajectoryAction(
            trajectory, xosc.FollowingMode.position)
    elif event['Dynamic_shape'] == 'Curve':
        trajectory = xosc.Trajectory('selfDefineTrajectory', False)
        road_center = event['Use_route']
        nurbs = xosc.Nurbs(4)

        from rich import console
        console = console.Console()
        # console.log(currentPosition);exit()
        nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_config(Map,currentPosition))) #出發點
        # nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_config(Map,currentPosition, s = 0))) #與出發點同道之進入路口點，加這個點軌跡比較自然
        nurbs.add_control_point(xosc.ControlPoint(create_LanePosition_from_config(Map,currentPosition))) #與出發點同道之進入路口點，加這個點軌跡比較自然
        if event['Use_route'] != None:
            nurbs.add_control_point(xosc.ControlPoint(xosc.WorldPosition(
                road_center[0], road_center[1]), weight=0.5))  # 路口中心
        nurbs.add_control_point(xosc.ControlPoint(
            create_LanePosition_from_config(Map, event['End'], s=0)))  # 目的地
        nurbs.add_control_point(xosc.ControlPoint(targetPoint))  # 目的地
        if event['Use_route'] != None:
            nurbs.add_knots([0, 0, 0, 0, 1, 2, 2, 2, 2])
        else:
            nurbs.add_knots([0, 0, 0, 0, 2, 2, 2, 2])

        trajectory.add_shape(nurbs)

        # Create a FollowTrajectory action
        advgoal = xosc.FollowTrajectoryAction(
            trajectory, xosc.FollowingMode.position)
    else:
        advgoal = xosc.AcquirePositionAction(targetPoint)

    trigger = create_Trigger_following_previous(
        previousEventName, delay=f'${actorName}_{actIndex}_TA_DynamicDelay', state='complete')

    advgoalEvent = xosc.Event(
        f"{actorName}_Event{actIndex}_TrajectoryEvent", xosc.Priority.parallel)
    advgoalEvent.add_action(
        f"{actorName}_Event{actIndex}_TrajectoryAction", advgoal)
    advgoalEvent.add_trigger(trigger)
    currentPosition = event['End']

    return advgoalEvent, currentPosition


def generate_Zigzag_Event(actorName, actIndex, event, Map, previousEventName, currentPosition):
    allEvent = []
    init_offset = currentPosition[3]

    period = f'${actorName}_{actIndex}_TA_Period'
    amplidute = f'${actorName}_{actIndex}_TA_Offset'
    times = f'${actorName}_{actIndex}_TA_Times'

    """To prevent the agent randomly turn left or right, we need to assign the target position to the agent"""
    targetPoint = create_LanePosition_from_config(Map, event['End'])
    advgoal = xosc.AcquirePositionAction(targetPoint)
    trigger = create_Trigger_following_previous(
        previousEventName, delay=0, state='complete')
    advgoalEvent = xosc.Event(
        f"{actorName}_Event{actIndex}_TrajectoryEvent_0", xosc.Priority.parallel)
    advgoalEvent.add_action(
        f"{actorName}_Event{actIndex}_TrajectoryAction_0", advgoal)
    advgoalEvent.add_trigger(trigger)
    allEvent.append(advgoalEvent)

    """Left offset event: TrajectoryEvent_1"""
    advgoal = xosc.AbsoluteLaneOffsetAction(
        f'${{{amplidute} + {init_offset}}}', shape=xosc.DynamicsShapes.sinusoidal, maxlatacc=f'${{abs({amplidute}/{period})}}')
    advgoalEvent = xosc.Event(
        f"{actorName}_Event{actIndex}_TrajectoryEvent_1", xosc.Priority.parallel, maxexecution=times)
    advgoalEvent.add_action(
        f"{actorName}_Event{actIndex}_TrajectoryAction_1", advgoal)
    # Trigger 1. privious event complete
    condition1 = create_StoryBoardElement_Trigger(
        "FollowingPreviosTrigger", 0, xosc.ConditionEdge.rising, 'event', previousEventName[0], xosc.StoryboardElementState.completeState)
    # Trigger 2. Right offset event complete and execution times is smaller than the maxexecution times
    condition2 = create_StoryBoardElement_Trigger("FollowingPreviosTrigger2", 0, xosc.ConditionEdge.rising,
                                                  'event', f"{actorName}_Event{actIndex}_TrajectoryEvent_2", xosc.StoryboardElementState.endTransition)
    trigger = xosc.Trigger()
    condition_group1 = xosc.ConditionGroup()
    condition_group1.add_condition(condition1)
    condition_group2 = xosc.ConditionGroup()
    condition_group2.add_condition(condition2)
    trigger.add_conditiongroup(condition_group1)
    trigger.add_conditiongroup(condition_group2)
    advgoalEvent.add_trigger(trigger)
    allEvent.append(advgoalEvent)

    """Right offset event: TrajectoryEvent_2"""
    advgoal = xosc.AbsoluteLaneOffsetAction(
        f'${{-{amplidute} + {init_offset}}}', shape=xosc.DynamicsShapes.sinusoidal, maxlatacc=f'${{abs({amplidute}/{period})}}')
    trigger = xosc.Trigger()
    # Trigger: Left offset event complete and execution times is smaller than the maxexecution times
    condition3 = create_StoryBoardElement_Trigger("FollowingPreviosTrigger3", 0, xosc.ConditionEdge.rising,
                                                  'event', f"{actorName}_Event{actIndex}_TrajectoryEvent_1", xosc.StoryboardElementState.endTransition)
    condition_group1 = xosc.ConditionGroup()
    condition_group1.add_condition(condition3)
    trigger.add_conditiongroup(condition_group1)
    advgoalEvent = xosc.Event(
        f"{actorName}_Event{actIndex}_TrajectoryEvent_2", xosc.Priority.parallel, maxexecution=times)
    advgoalEvent.add_action(
        f"{actorName}_Event{actIndex}_TrajectoryAction_2", advgoal)
    advgoalEvent.add_trigger(trigger)
    allEvent.append(advgoalEvent)
    previousEventName = [advgoalEvent.name]

    """The last event: move back to the initial offset"""
    advgoal = xosc.AbsoluteLaneOffsetAction(
        init_offset, shape=xosc.DynamicsShapes.sinusoidal, maxlatacc=f'${{abs({amplidute}/{period})}}')
    trigger = create_Trigger_following_previous(
        previousEventName, delay=0, state='complete')
    advgoalEvent = xosc.Event(
        f"Adv{actorName}_Event{actIndex}_TrajectoryEvent_3", xosc.Priority.parallel)
    advgoalEvent.add_action(
        f"Adv{actorName}_Event{actIndex}_TrajectoryAction_3", advgoal)
    advgoalEvent.add_trigger(trigger)
    allEvent.append(advgoalEvent)

    return allEvent, currentPosition


def create_Dummy_Event(actorName, actIndex, delay, previousEventName):
    """Generate a dummy event to delay the next event"""
    trigger = create_Trigger_following_previous(
        previousEventName, delay=f'${actorName}_{actIndex}_Delay', state='complete')
    dummyEvent = xosc.Event(
        f"{actorName}_Event{actIndex}_DummyEvent", xosc.Priority.parallel)
    dummyEvent.add_action(f"{actorName}_Event{actIndex}_DummyAction",
                          xosc.VisibilityAction(True, True, True))
    dummyEvent.add_trigger(trigger)

    return dummyEvent


def set_agentpos_relative_to_egopos(egoPos, road_index=None, relative_lane=0, s_offset=0, lane_offset=0, orientation=1):
    agentPos = egoPos.copy()
    agentPos[0] = road_index if road_index != None else agentPos[0]
    agentPos[1] += relative_lane * int(np.sign(agentPos[1]))
    agentPos[2] += s_offset * -int(np.sign(agentPos[1]))
    agentPos[3] += lane_offset
    agentPos[4] = orientation
    # list(map(add, config['Ego']['Start_pos'], [0,0,20,0,0]))

    return agentPos


def set_trigger_dict_from_relative_pos(relative_pos):
    position_vals = RELATIVE_TRIGGER_POSITIONS[relative_pos]
    trigger_dict = dict.fromkeys(['type', 'lane', 'road', 's', 'offset'], '')
    trigger_dict.update(zip(trigger_dict, position_vals))

    return trigger_dict


def set_trigger_dict_from_absolute_pos(lane, road, s, offset, triggertype='absolute'):
    position_vals = [triggertype, lane, road, s, offset]
    trigger_dict = dict.fromkeys(['type', 'lane', 'road', 's', 'offset'], '')
    trigger_dict.update(zip(trigger_dict, position_vals))

    return trigger_dict


def set_agentStart_from_relative_triggerAt(egoTriggerAt, relative_pos):
    # + RELATIVE_TRIGGER_POSITIONS[relative_pos][2]
    road_index = egoTriggerAt[0]
    relative_lane = RELATIVE_TRIGGER_POSITIONS[relative_pos][1]
    s_offset = RELATIVE_TRIGGER_POSITIONS[relative_pos][3]
    lane_offset = egoTriggerAt[3] + RELATIVE_TRIGGER_POSITIONS[relative_pos][4]

    return set_agentpos_relative_to_egopos(egoTriggerAt, road_index=road_index, relative_lane=relative_lane, s_offset=s_offset, lane_offset=lane_offset)


def set_behavior_dict(behavior_type, behavior_mode):
    extracted_elements = [behavior_mode[5], behavior_mode[3],
                          behavior_mode[4], behavior_mode[2], behavior_mode[0], 'null']

    # behavior_dict = dict.fromkeys(['type','Start_speed', 'End_speed','Dynamic_duration','Dynamic_shape'],'')
    behavior_dict = dict.fromkeys(
        ['Type', 'Dynamic_delay', 'Dynamic_duration', 'Dynamic_shape', 'End', 'Use_route'], '')
    behavior_dict.update(
        zip(behavior_dict, [behavior_type] + extracted_elements))

    return behavior_dict


"""
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
"""


def remove_yaml_files(directory='./scenario_config'):
    # Construct the pattern for YAML files
    pattern = os.path.join(directory, '*.yaml')

    # Find all files matching the pattern
    yaml_files = glob.glob(pattern)

    # Remove each file
    for file in yaml_files:
        os.remove(file)
        print(f"Removed: {file}")

    try:
        os.remove('./HCIS_scenarios.csv')
        print(f"Removed: ./HCIS_scenarios.csv")
    except:
        pass


def get_behavior_mode(AgentSpeed=40, AgentEndSpeed=10, DynamicDuration=3, DynamicHaltDuration=1, DynamicDelay=1):
    BehaviorMode = {}
    BehaviorMode['keeping'] = (
        'Autocruise.', AgentSpeed, AgentSpeed, DynamicDuration, 'linear', DynamicDelay)  # 等速
    BehaviorMode['braking'] = (
        'braking.', AgentSpeed, AgentEndSpeed, DynamicDuration, 'linear', DynamicDelay)  # 減速
    BehaviorMode['braking_halt'] = (
        'Braking & Halted halfway.', AgentSpeed, 0, DynamicHaltDuration, 'linear', DynamicDelay)  # 減速|未完成
    BehaviorMode['sudden_braking_halt'] = (
        'Sudden braking & Halted halfway.', AgentSpeed, 0, DynamicHaltDuration, 'sinusoidal', DynamicDelay)  # 急煞|未完成
    BehaviorMode['speed_up'] = (
        'Speed up.', 0, AgentSpeed, DynamicDuration-1, 'linear', DynamicDelay-1)  # 加速

    return BehaviorMode

# def create_scenario_configs_by_behavior_mode(scenario_name, description, config, BehaviorMode):
#     # Multiple 待完成
#     car['Start_speed'] = behavior[1]
#     gostraightAct[1]['End'] = behavior[2]
#     gostraightAct[1]['Dynamic_duration'] = behavior[3]
#     gostraightAct[1]['Dynamic_shape'] = behavior[4]
#     gostraightAct[1]['Dynamic_delay'] = behavior[5]
#     car['Acts'] = [{'Type': 'gostraight','Delay':0, 'Events':gostraightAct}]

#     config['Actors'] = {'Agents':[car]}

#     scenario_config = {
#         'scenario_id': scenario_id,
#         'scenario_name': scenario_name,
#         'description': description,
#         'config': config
#     }

#     return scenario_config
#     # List all files in the directory
#     for filename in os.listdir(directory):
#         match = pattern.match(filename)
#         if match:
#             scenario_id = int(match.group(1))
#             if scenario_id > max_scenario_id:
#                 max_scenario_id = scenario_id

#     # Calculate the next scenario ID
#     next_scenario_id = max_scenario_id + 1

#     return next_scenario_id


def write_to_scenario_table(scenario_id, content, file_path='./HCIS_scenarios.csv'):
    """
    Writes the given content to a CSV file with the specified scenario_id.

    :param scenario_id: The scenario ID to be included in the CSV file.
    :param content: List of dictionaries or list of lists to write to the CSV file.
    :param file_path: Path to the CSV file. Default is 'scenario_table.csv'.

    # Example input
    content_dicts = [
        {'Name': 'Alice', 'Age': 30, 'City': 'New York'},
        {'Name': 'Bob', 'Age': 25, 'City': 'Los Angeles'},
        {'Name': 'Charlie', 'Age': 35, 'City': 'Chicago'}
    ]
    """
    print(f"write {scenario_id}, description: {content[0]['description']}.")

    file_exists = os.path.isfile(file_path)
    columns = ['scenario_id', 'scenario_name', 'description']
    # Check if content is a list of dictionaries
    if isinstance(content, list) and all(isinstance(row, dict) for row in content):
        # Add scenario_id to each dictionary
        for row in content:
            row['scenario_id'] = scenario_id

        with open(file_path, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            if not file_exists:
                writer.writeheader()
            writer.writerows(content)
    else:
        # Add scenario_id to each list
        content_with_id = [[scenario_id] + row for row in content]

        with open(file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                # Write header if file does not exist
                writer.writerow(columns)
            writer.writerows(content_with_id)


def remove_yaml_files(directory='./scenario_config'):
    # Construct the pattern for YAML files
    pattern = os.path.join(directory, '*.yaml')

    # Find all files matching the pattern
    yaml_files = glob.glob(pattern)

    # Remove each file
    for file in yaml_files:
        os.remove(file)
        print(f"Removed: {file}")

    try:
        os.remove('./HCIS_scenarios.csv')
        print(f"Removed: ./HCIS_scenarios.csv")
    except:
        pass


def get_behavior_mode(AgentSpeed=40, AgentEndSpeed=10, DynamicDuration=3, DynamicHaltDuration=1, DynamicDelay=1):
    BehaviorMode = {}
    BehaviorMode['keeping'] = (
        'Autocruise.', AgentSpeed, AgentSpeed, DynamicDuration, 'linear', DynamicDelay)  # 等速
    BehaviorMode['braking'] = (
        'braking.', AgentSpeed, AgentEndSpeed, DynamicDuration, 'linear', DynamicDelay)  # 減速
    BehaviorMode['braking_halt'] = (
        'Braking & Halted halfway.', AgentSpeed, 0, DynamicHaltDuration, 'linear', DynamicDelay)  # 減速|未完成
    BehaviorMode['sudden_braking_halt'] = (
        'Sudden braking & Halted halfway.', AgentSpeed, 0, DynamicHaltDuration, 'sinusoidal', DynamicDelay)  # 急煞|未完成
    BehaviorMode['speed_up'] = (
        'Speed up.', 0, AgentSpeed, DynamicDuration-1, 'linear', DynamicDelay-1)  # 加速

    return BehaviorMode
