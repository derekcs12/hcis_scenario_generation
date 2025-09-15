import numpy as np
from scenariogeneration import xosc

from utils.trigger import *
from utils.position import *


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


def generate_Agent_Start_Event(actorName, agent, Map):
    agentInitSpeed = xosc.AbsoluteSpeedAction(
        f'${{${actorName}_Speed / 3.6}}', xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0))
    # if agent['Start_trigger']['type'] == 'relative':
    #     agentStartTrigger = create_EntityTrigger_at_relativePos(
    #         Map, agent, 'Ego')
    # else:  # absolute
    #     agentStartTrigger = create_EntityTrigger_at_absolutePos(
    #         Map, agent['Start_trigger'], 'Ego')
    
    # agentStartTrigger = create_flag_trigger('IS_VALID', 'true', delay=0, conditionedge=xosc.ConditionEdge.rising)
    agentStartTrigger = create_flag_trigger('FLAG-AV_CONNECTED', 'true', delay=0, conditionedge=xosc.ConditionEdge.rising)

    advStartSpeedEvent = xosc.Event(
        f"{actorName}_StartSpeedEvent", xosc.Priority.overwrite)
    advStartSpeedEvent.add_action(
        f"{actorName}_StartSpeedAction", agentInitSpeed)
    advStartSpeedEvent.add_action(
        f"{actorName}_ActivateController", xosc.ActivateControllerAction(longitudinal=True, lateral=True))
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


def generate_Cut_Event(actorName, actIndex, eventIndex, event, previousEventName, currentPosition):
    targetLane = event['End'][0]
    # offset = event['End'][1]
    # if isinstance(offset, str) and np.sign(targetLane) == -1:
    #     target_offset = f'${{{offset}}}'
    # elif isinstance(offset, (int, float)):
    #     target_offset = target_offset * np.sign(targetLane)
    target_offset = f'${actorName}_{actIndex}_{eventIndex}_Offset'

    if np.sign(targetLane) == -1:
        target_offset = f'${{-{target_offset}}}'

    advgoal = xosc.AbsoluteLaneChangeAction(targetLane, create_TransitionDynamics_from_config(
        event, actorName, actIndex, eventIndex), target_lane_offset=target_offset)

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


def generate_Position_Event(actorName, actIndex, event, Map, previousEventName, currentPosition):
    if len(event['End']) == 2:
        targetPoint = xosc.WorldPosition(event['End'][0], event['End'][1])
    else:
        target = event['End']
        target[3] = f'${actorName}_{actIndex}_TA_Offset'
        targetPoint = create_LanePosition_from_config(Map, target)

    currentPosition[2] = f'${actorName}_{actIndex-1}_S' if actIndex > 1 else f'${actorName}_S'
    currentPosition[3] = f'${actorName}_{actIndex-1}_TA_Offset' if actIndex > 1 else f'${actorName}_Offset'

    # targetPoint = xosc.WorldPosition(event['End'][0], event['End'][1]) if len(
    #     event['End']) == 2 else create_LanePosition_from_config(Map, event['End'])
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

