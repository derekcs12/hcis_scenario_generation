import numpy as np
from scenariogeneration import xosc


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
    

def create_flag_trigger(variable_name, value='true', delay=0, conditionedge=xosc.ConditionEdge.rising):
    group = xosc.ConditionGroup()
    condition = xosc.VariableCondition(variable_name, value, xosc.Rule.equalTo)
    trigger = xosc.ValueTrigger(
        name=f"{variable_name}_Trigger",
        delay=delay,
        conditionedge=conditionedge,
        valuecondition=condition
    )
    group.add_condition(trigger)
    return group


def has_name(variable_list, name):
    for var in variable_list:
        if var['name'] == name:
            return True
    return False

def av_connection_timeout_trigger(variable_dict): # 0
    assert 'FLAG-AV_CONNECTION_TIMEOUT' in variable_dict and 'FLAG-AV_CONNECTED' in variable_dict, "Variable FLAG-AV_CONNECTION_TIMEOUT or FLAG-AV_CONNECTED not defined."
    return create_flag_trigger('FLAG-AV_CONNECTION_TIMEOUT', 'true')

def wrong_start_speed_trigger(variable_dict): # 1
    assert 'FLAG-WRONG_START_SPEED' in variable_dict, "Variable FLAG-WRONG_START_SPEED not defined."
    return create_flag_trigger('FLAG-WRONG_START_SPEED', 'true')

def ego_reached_end_trigger(variable_dict): # 2
    assert 'FLAG-EGO_REACHED_END' in variable_dict, "Variable FLAG-EGO_REACHED_END not defined."
    return create_flag_trigger('FLAG-EGO_REACHED_END', 'true')

def ego_tle_trigger(variable_dict): # 3
    assert 'FLAG-EGO_TLE' in variable_dict, "Variable FLAG-EGO_TLE not defined."
    return create_flag_trigger('FLAG-EGO_TLE', 'true')

def ego_collision_trigger(variable_dict): # 4
    assert 'FLAG-EGO_COLLISION' in variable_dict, "Variable FLAG-EGO_COLLISION not defined."
    return create_flag_trigger('FLAG-EGO_COLLISION', 'true')

def ego_stroll_trigger(variable_dict): # 5
    assert 'FLAG-EGO_STROLL' in variable_dict, "Variable FLAG-EGO_STROLL not defined."
    return create_flag_trigger('FLAG-EGO_STROLL', 'true')   

end_condition_triggers = [av_connection_timeout_trigger,
                          wrong_start_speed_trigger,
                          ego_reached_end_trigger,
                          ego_tle_trigger,
                          ego_collision_trigger,
                            ego_stroll_trigger]



def create_StopTrigger(end_condition_indices, variable_dict):
    stopTrigger = xosc.Trigger('stop')

    for idx in end_condition_indices:
        if idx < 0 or idx >= len(end_condition_triggers):
            print(f"Invalid end condition index: {idx}")
            continue
        stopTrigger.add_conditiongroup(end_condition_triggers[idx](variable_dict))

    # """NEW END CONDITIONS"""
    # # Condition 1 - AV Connection timeout => Invalid
    # stopTrigger.add_conditiongroup(create_flag_trigger('FLAG-AV_CONNECTION_TIMEOUT', 'true'))
    # # Condition 2 - Wrong Start Speed => Invalid
    # stopTrigger.add_conditiongroup(create_flag_trigger('FLAG-WRONG_START_SPEED', 'true'))
    # # Condition 3 - Ego reaches the target point => Valid/Success
    # stopTrigger.add_conditiongroup(create_flag_trigger('FLAG-EGO_REACHED_END', 'true'))
    # # Condition 4 - Ego TLE => Valid/Fail
    # stopTrigger.add_conditiongroup(create_flag_trigger('FLAG-EGO_TLE', 'true'))
    # # Condition 5 - Collision => Valid/Fail
    # stopTrigger.add_conditiongroup(create_flag_trigger('FLAG-EGO_COLLISION', 'true'))
    # # Condition 6 - Ego Stroll => Invalid
    # stopTrigger.add_conditiongroup(create_flag_trigger('FLAG-EGO_STROLL', 'true'))


    

    return stopTrigger


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


