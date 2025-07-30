import numpy as np
from scenariogeneration import xosc

from utils.trigger import *
from utils.position import *


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


def create_ego_tle_condition(Map, eventStartPoint, egoName, time=30):
    """
    End Condition (2-b) - Ego TLE
    Test Result: Valid/Success
    """
    group = xosc.ConditionGroup()
    trigger = create_EntityTrigger_at_absolutePos(Map, eventStartPoint, egoName, delay=time, triggerName="EgoTLE")
    group.add_condition(trigger)
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

    
def create_timeout_condition(egoName, time=60):
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


def create_wrong_start_speed_condition(Map, egoName, eventStartPoint, eventStartSpeed, tolerance=5):
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
