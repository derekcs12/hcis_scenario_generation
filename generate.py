import os
from time import time
import numpy as np
from scenariogeneration import xosc, prettyprint
from utils.position import create_LanePosition_from_config
from utils.trigger import create_StopTrigger
from utils.condition import (
    create_collision_condition,
    create_ego_stroll_condition,
    create_ego_tle_condition,
    create_invalid_area_condition,
    create_reach_target_condition,
    create_right_start_speed_condition,
    create_stand_still_conditions,
    create_timeout_condition,
    create_wrong_start_speed_condition,
)

from utils.event import (
    create_Dummy_Event,
    generate_Agent_Start_Event,
    generate_Speed_Event,
    generate_Cut_Event,
    generate_Offset_Event,
    generate_Position_Event,
    generate_Zigzag_Event
)

def generate(config, company='HCISLab'):
    
    # === 基本參數與 Actor 數量 ===
    Actors = config['Actors']
    EgoConfig = config['Ego']
    MapConfig = config['Map']
    ScenarioName = config['Scenario_name']
    xodrPath = './hct_6.xodr'
    agentCount = len(Actors.get('Agents', []))
    pedCount = len(Actors.get('Pedestrians', []))


    # === 1. 宣告參數與 Catalogs ===
    paramdec = parameter_Declaration(Actors, EgoConfig)

    # CatalogLocations & RoadNetwork (document:xosc.utiles)
    catalog = xosc.Catalog()
    if company == 'HCISLab':
        catalog.add_catalog("VehicleCatalog", "./Catalogs/Vehicles")
        catalog.add_catalog("ControllerCatalog", "./Catalogs/Controllers")
        if 'Pedestrians' in Actors:
            catalog.add_catalog("PedestrianCatalog", "./Catalogs/Pedestrians")
        road = xosc.RoadNetwork(roadfile=xodrPath)
        controllerName = "ACCController"
        # controllerName = "interactiveDriver"
        
    else: # ITRI
        catalog.add_catalog("VehicleCatalog", "../Catalogs/Vehicles")
        catalog.add_catalog("ControllerCatalog", "../Catalogs/Controllers")
        if 'Pedestrians' in Actors:
            catalog.add_catalog("PedestrianCatalog", "../Catalogs/Pedestrians")
        road = xosc.RoadNetwork(roadfile="../../xodr/itri/hct_6.xodr")
        controllerName = "ROSController"


    # === 2. 建立 Ego Controller 實體 ===
    egoControllerProperties = xosc.Properties()
    egoControllerProperties.add_property(name="timeGap", value="1.0")
    egoControllerProperties.add_property(name="mode", value="override")
    egoControllerProperties.add_property(name="setSpeed", value="${$Ego_Speed / 3.6}")
    egoController = xosc.Controller(name=controllerName, properties=egoControllerProperties)
    # egoController = xosc.CatalogReference(catalogname="ControllerCatalog", entryname=controllerName)


    # === 3. 建立 Entities (Ego + Agents + Pedestrians)(document:xosc.Entities) ===
    agentController = xosc.Controller(name="ALKSController", properties=xosc.Properties())
    entities = create_Entity(egoController, agentCount, pedCount, agentController=agentController)


    # --- 4. Storyboard ---
    # === 4.1 建立 Init 動作 ===
    step_time = xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0)
    init = xosc.Init()

    # Ego 初始位置、控制器啟動與終點位置
    egoStartPos = create_LanePosition_from_config(MapConfig, EgoConfig['Start_pos'])
    egoEndPos = create_LanePosition_from_config(MapConfig, EgoConfig['End_pos'])
    egoController = True

    init.add_init_action('Ego', xosc.TeleportAction(egoStartPos))
    init.add_init_action('Ego', xosc.ActivateControllerAction(lateral=egoController, longitudinal=egoController))
    init.add_init_action('Ego', xosc.AcquirePositionAction(egoEndPos))
    # init.add_init_action('Ego', xosc.AbsoluteSpeedAction("${$Ego_Speed / 3.6}", step_time))
    

    # Agents / Pedestrians 初始位置
    for cata in Actors:
        for idx, actor in enumerate(Actors[cata], start=1):
            actorName = f"{cata[:-1]}{idx}"
            startPos = create_LanePosition_from_config(MapConfig, actor['Start_pos'], s=f"${actorName}_S", offset=f"${actorName}_Offset")
            init.add_init_action(actorName, xosc.TeleportAction(startPos))

    # === 4.2 產生 Maneuvers 與 Events ===
    # invalid condition flags
    egoParamManeuver = generate_Parameter_Maneuver(config, actors=Actors)
    
    # Activate Agents Controllers
    activateControllerManeuver = generate_Activate_Controller_Action(Actors)
    
    allManeuvers = {}
    allStartEvent = []

    for cata in Actors:
        for idx, actor in enumerate(Actors[cata], start=1):
            actorName = f"{cata[:-1]}{idx}"
            maneuvers, previousEventNames = generate_Adv_Maneuver(actorName, actor, MapConfig)
            if maneuvers:
                allManeuvers[actorName] = maneuvers
                allStartEvent.append(previousEventNames[0])

    # === 4.3 建立 StopTrigger 終止條件 ===
    sb_stoptrigger = create_StopTrigger(
        Map=MapConfig,
        egoName='Ego',
        eventStartPoint=Actors['Agents'][0]['Start_trigger'],
        eventStartSpeed=float(EgoConfig['Start_speed']),
        egoTargetPoint=EgoConfig['End_pos'],
        xodrPath=xodrPath
    )

    # === 4.4 Storyboard 組裝 ===
    sb = xosc.StoryBoard(init, sb_stoptrigger)
    sb.add_story(activateControllerManeuver)

    for name, maneuver in allManeuvers.items():
        sb.add_maneuver(maneuver, name)

    sb.add_maneuver(egoParamManeuver, "Ego")



    # === 5. 組裝 Scenario 實體並回傳 ===
    scenario = xosc.Scenario(
        name="hct_" + ScenarioName,
        author="HCIS_ChengYuSheng",
        parameters=paramdec,
        entities=entities,
        storyboard=sb,
        roadnetwork=road,
        catalog=catalog,
        osc_minor_version=0
    )

    return scenario


def parameter_Declaration(Actors, Ego):
    paramdec = xosc.ParameterDeclarations()
    paraList = []

    egoConnectedFlag = xosc.Parameter(
        name="AV_CONNECTED", parameter_type="boolean", value="false")
    paraList.append(egoConnectedFlag)

    eventStartFlag = xosc.Parameter(
        name="EVENT_START", parameter_type="boolean", value="false")
    paraList.append(eventStartFlag)

    invalidFlag = xosc.Parameter(
        name="IS_VALID", parameter_type="boolean", value="false")
    paraList.append(invalidFlag)

    avConnectionTimeoutFlag = xosc.Parameter(
        name="AV_CONNECTION_TIMEOUT", parameter_type="boolean", value="false")
    paraList.append(avConnectionTimeoutFlag)

    wrongStartSpeedFlag = xosc.Parameter(
        name="WRONG_START_SPEED", parameter_type="boolean", value="false")
    paraList.append(wrongStartSpeedFlag)

    egoreachedEndFlag = xosc.Parameter(
        name="EGO_REACHED_END", parameter_type="boolean", value="false")
    paraList.append(egoreachedEndFlag)

    egoTLEFlag = xosc.Parameter(
        name="EGO_TLE", parameter_type="boolean", value="false")
    paraList.append(egoTLEFlag)

    egoCollisionFlag = xosc.Parameter(
        name="EGO_COLLISION", parameter_type="boolean", value="false")
    paraList.append(egoCollisionFlag)

    egoStrollFlag = xosc.Parameter(
        name="EGO_STROLL", parameter_type="boolean", value="false")
    paraList.append(egoStrollFlag)

    # ParameterDeclarations
    egoInit = xosc.Parameter(
        name="Ego_Vehicle", parameter_type="string", value="car_white")
    egoSpeed = xosc.Parameter(
        name="Ego_Speed", parameter_type="double", value=Ego['Start_speed'])
    egoS = xosc.Parameter(
        name="Ego_S", parameter_type="double", value=Ego['Start_pos'][2])
    paraList.extend([egoInit, egoSpeed, egoS])

    # catas = ['Agents', 'Pedestrians']
    for cata in Actors:
        for actorIndex, actor in enumerate(Actors[cata], start=1):
            actorName = f"{cata[:-1]}{actorIndex}"
            # actor's Init parameter
            actorType = xosc.Parameter(
                name=f"{actorName}_Type", parameter_type="string", value=actor['Type'])
            actorInitSpeed = xosc.Parameter(
                name=f"{actorName}_Speed", parameter_type="double", value=str(actor['Start_speed']))
            actorInitS = xosc.Parameter(
                name=f"{actorName}_S", parameter_type="double", value=str(actor['Start_pos'][2]))
            actorInitOffset = xosc.Parameter(
                name=f"{actorName}_Offset", parameter_type="double", value=str(actor['Start_pos'][3]))
            paraList.extend([actorType, actorInitSpeed, actorInitS, actorInitOffset])

            # check if actor has 'Acts'
            if 'Acts' not in actor:
                print(f"{actorName} has no 'Acts'")
                continue

            # actor's Event parameter
            for actIndex, act in enumerate(actor['Acts'], start=1):
                if act['Type'] == 'zigzag':
                    for eventIndex, event in enumerate(act['Events'], start=1):
                        if event['Type'] == 'offset':
                            delay = xosc.Parameter(
                                name=f"{actorName}_{actIndex}_Delay", parameter_type="double", value=str(event['Dynamic_delay']))
                            offset = xosc.Parameter(
                                name=f"{actorName}_{actIndex}_TA_Offset", parameter_type="double", value=str(event['Dynamic_shape']))
                            period = xosc.Parameter(name=f"{actorName}_{actIndex}_TA_Period", parameter_type="double", value=str(
                                event['Dynamic_duration']))
                            times = xosc.Parameter(
                                name=f"{actorName}_{actIndex}_TA_Times", parameter_type="double", value=str(event['Use_route']))
                            paraList.extend([delay, offset, period, times])
                        if event['Type'] == 'speed':
                            dynamicDelay = xosc.Parameter(
                                name=f"{actorName}_{actIndex}_SA_DynamicDelay", parameter_type="double", value=str(event['Dynamic_delay']))
                            dynamicDuration = xosc.Parameter(
                                name=f"{actorName}_{actIndex}_SA_DynamicDuration", parameter_type="double", value=str(event['Dynamic_duration']))
                            dynamicShape = xosc.Parameter(
                                name=f"{actorName}_{actIndex}_SA_DynamicShape", parameter_type="double", value=str(event['Dynamic_shape']))
                            endSpeed = xosc.Parameter(
                                name=f"{actorName}_{actIndex}_SA_EndSpeed", parameter_type="double", value=str(event['End']))
                            paraList.extend(
                                [dynamicDelay, dynamicShape, dynamicDuration, endSpeed])
                else:
                    delay = xosc.Parameter(
                        name=f"{actorName}_{actIndex}_Delay", parameter_type="double", value=str(act['Delay']))
                    paraList.append(delay)
                    for eventIndex, event in enumerate(act['Events'], start=1):
                        actionName = 'TA'
                        if event['Type'] == 'speed':
                            actionName = 'SA'
                            endSpeed = xosc.Parameter(
                                name=f"{actorName}_{actIndex}_{actionName}_EndSpeed", parameter_type="double", value=str(event['End']))
                            paraList.append(endSpeed)
                        dynamicDelay = xosc.Parameter(
                            name=f"{actorName}_{actIndex}_{actionName}_DynamicDelay", parameter_type="double", value=str(event['Dynamic_delay']))
                        dynamicDuration = xosc.Parameter(
                            name=f"{actorName}_{actIndex}_{actionName}_DynamicDuration", parameter_type="double", value=str(event['Dynamic_duration']))
                        dynamicShape = xosc.Parameter(
                            name=f"{actorName}_{actIndex}_{actionName}_DynamicShape", parameter_type="string", value=event['Dynamic_shape'])
                        
                        if event['Type'] == 'cut' :
                            dynamicOffset = xosc.Parameter(
                                name=f"{actorName}_{actIndex}_{actionName}_Offset", parameter_type="double", value=str(event['End'][1]))
                            paraList.append(dynamicOffset)
                            
                        elif event['Type'] == 'position' and len(event['End']) >= 4:
                            dynamicOffset = xosc.Parameter(
                                name=f"{actorName}_{actIndex}_{actionName}_Offset", parameter_type="double", value=str(event['End'][3]))
                            paraList.append(dynamicOffset)

                        

                        paraList.extend(
                            [dynamicDelay, dynamicDuration, dynamicShape])

    for i in paraList:
        paramdec.add_parameter(i)

    return paramdec


def create_Catalog_and_RoadNetwork():
    ...


def create_Entity(egoController, agentCount, pedCount, agentController):
    # construct CatalogReference
    egoObject = xosc.CatalogReference(
        catalogname="VehicleCatalog", entryname="$Ego_Vehicle")  # xosc.utils

    # Create agent object
    agentObjectList = []
    for i in range(agentCount):
        agentObject = xosc.CatalogReference(
            catalogname="VehicleCatalog", entryname=f"$Agent{i+1}_Type")
        agentObjectList.append(agentObject)

    # Create Pedestrian object
    pedObjectList = []
    for i in range(pedCount):
        pedObject = xosc.CatalogReference(
            catalogname="PedestrianCatalog", entryname=f"$Pedestrian{i+1}_Type")
        pedObjectList.append(pedObject)

    # create entity
    entities = xosc.Entities()

    # ego
    entities.add_scenario_object(
        name="Ego", entityobject=egoObject, controller=egoController)
    

    # agents
    for i in range(agentCount):
        entities.add_scenario_object(
            name=f"Agent{i+1}", entityobject=agentObjectList[i], controller=agentController)

    # pedestrians
    for i in range(pedCount):
        entities.add_scenario_object(
            name=f"Pedestrian{i+1}", entityobject=pedObjectList[i])

    return entities


def generate_Adv_Maneuver(actorName, agent, Map):
    # check if actor has 'Acts'
    if 'Acts' not in agent:
        print(f"{actorName} has no 'Acts'")
        return None, None

    advManeuver = xosc.Maneuver(f"{actorName}_Maneuver")
    agentStartEvent = generate_Agent_Start_Event(actorName, agent, Map)
    advManeuver.add_event(agentStartEvent)
    previousEventName = [agentStartEvent.name]
    currentPosition = agent['Start_pos'].copy()
    # currentPosition[3] *= np.sign(currentPosition[2])
    currentPosition[3] = currentPosition[3] * np.sign(currentPosition[1])
    for actIndex, act in enumerate(agent['Acts'], start=1):
        # Add dummy event first to avoid the action disappear and support overall delay
        dummyEvent = create_Dummy_Event(
            actorName, actIndex, f"{actorName}_{actIndex}_Delay", previousEventName)
        advManeuver.add_event(dummyEvent)
        previousEventName = [dummyEvent.name]

        currentEventName = []
        if act['Type'] == 'zigzag':
            for eventIndex, event in enumerate(act['Events'], start=1):
                if event['Type'] == 'speed':
                    currentEvent = generate_Speed_Event(
                        actorName, actIndex, 'SA', event, previousEventName, type='zigzag')
                    currentEventName.append(currentEvent.name)
                    advManeuver.add_event(currentEvent)
                elif event['Type'] == 'offset':
                    zigzagEvent, currentPosition = generate_Zigzag_Event(
                        actorName, actIndex, event, Map, previousEventName, currentPosition)
                    for currentEvent in zigzagEvent:
                        currentEventName.append(currentEvent.name)
                        advManeuver.add_event(currentEvent)
                else:
                    print('Event Type Error')
                    break

            previousEventName = currentEventName
        else:
            for eventIndex, event in enumerate(act['Events'], start=1):
                if event['Type'] == 'speed':
                    currentEvent = generate_Speed_Event(
                        actorName, actIndex, 'SA', event, previousEventName)
                elif event['Type'] == 'offset':
                    currentEvent, currentPosition = generate_Offset_Event(
                        actorName, actIndex, 'TA', event, previousEventName, currentPosition)
                elif event['Type'] == 'cut':
                    currentEvent, currentPosition = generate_Cut_Event(
                        actorName, actIndex, 'TA', event, previousEventName, currentPosition)
                elif event['Type'] == 'position':
                    currentEvent, _ = generate_Position_Event(
                        actorName, actIndex, event, Map, previousEventName, currentPosition)
                else:
                    print('Event Type Error')
                    break

                currentEventName.append(currentEvent.name)
                advManeuver.add_event(currentEvent)
            previousEventName = currentEventName

    return advManeuver, previousEventName


def generate_Parameter_Maneuver(config, actors):
    param_maneuver = xosc.Maneuver("ParameterManeuver")
    ego_name = 'Ego'
    ego_speed = float(config['Ego']['Start_speed'])
    agent = actors['Agents'][0]
    agent_count = len(actors['Agents'])
    MapConfig = config['Map']

    # === Detect Ego Has Moved Event ===
    event = xosc.Event("DetectEgoHasMovedEvent", xosc.Priority.parallel)
    event.add_action("Set EgoHasMoved Flag", xosc.ParameterSetAction("AV_CONNECTED", "true"))
    event.add_trigger(xosc.EntityTrigger("EgoHasMoved", 0, xosc.ConditionEdge.rising,
                      xosc.SpeedCondition(0, xosc.Rule.greaterThan), ego_name))
    param_maneuver.add_event(event)

    # === Init Valid Flag ===
    event = xosc.Event("ValidManeuverEvent", xosc.Priority.parallel)
    event.add_action("Set Valid Flag", xosc.ParameterSetAction("IS_VALID", "true"))
    valid_trigger = create_right_start_speed_condition(MapConfig, ego_name, agent['Start_trigger'], ego_speed)
    event.add_trigger(valid_trigger)
    param_maneuver.add_event(event)

    # === Detect AV Connection Timeout Event(30) ===
    event = xosc.Event("DetectAVConnectionTimeoutEvent", xosc.Priority.parallel)
    event.add_action("Set AV Connection Timeout Flag", xosc.ParameterSetAction("AV_CONNECTION_TIMEOUT", "true"))
    event.add_trigger(create_timeout_condition(ego_name, time=30))
    param_maneuver.add_event(event)

    # === Detect Wrong Start Speed Event - above tolerance ===
    low_group, high_group = create_wrong_start_speed_condition(
        MapConfig, ego_name, agent['Start_trigger'], ego_speed, tolerance=2)

    event = xosc.Event("DetectHighStartSpeedEvent", xosc.Priority.parallel)
    event.add_action("Set High Start Speed Flag", xosc.ParameterSetAction("WRONG_START_SPEED", "true"))
    event.add_trigger(high_group)
    param_maneuver.add_event(event)

    # === Detect Wrong Start Speed Event - below tolerance ===
    event = xosc.Event("DetectLowStartSpeedEvent", xosc.Priority.parallel)
    event.add_action("Set Low Start Speed Flag", xosc.ParameterSetAction("WRONG_START_SPEED", "true"))
    event.add_trigger(low_group)
    param_maneuver.add_event(event)

    # === Detect Ego Reached End Event ===
    event = xosc.Event("DetectEgoReachedEndEvent", xosc.Priority.parallel)
    event.add_action("Set Ego Reached End Flag", xosc.ParameterSetAction("EGO_REACHED_END", "true"))
    event.add_trigger(create_reach_target_condition(MapConfig, ego_name, config['Ego']['End_pos']))
    param_maneuver.add_event(event)

    # === Detect Ego TLE Event ===
    event = xosc.Event("DetectEgoTLEEvent", xosc.Priority.parallel)
    event.add_action("Set Ego TLE Flag", xosc.ParameterSetAction("EGO_TLE", "true"))
    event.add_trigger(create_ego_tle_condition(MapConfig, agent['Start_trigger'], ego_name, time=20))
    param_maneuver.add_event(event)

    # === Detect Ego Collision Event ===
    event = xosc.Event("DetectEgoCollisionEvent", xosc.Priority.parallel)
    event.add_action("Set Ego Collision Flag", xosc.ParameterSetAction("EGO_COLLISION", "true"))
    event.add_trigger(create_collision_condition(ego_name, agentCount=agent_count))
    param_maneuver.add_event(event)

    # === Create Ego Stroll Event ===
    event = xosc.Event("EgoStrollEvent", xosc.Priority.parallel)
    event.add_action("Set Ego Stroll Flag", xosc.ParameterSetAction("EGO_STROLL", "true"))
    event.add_trigger(create_ego_stroll_condition(time=20))
    param_maneuver.add_event(event)

    return param_maneuver


def generate_Activate_Controller_Action(Actors):
    """
    Generate ActivateControllerAction for the actor.
    """

    def create_maneuver_group(agent_name, delay_time):
        
        mg = xosc.ManeuverGroup(name=f"{agent_name}", maxexecution=1)
        mg.add_actor(agent_name)

        maneuver = xosc.Maneuver(name=f"{agent_name}")
        
        # action = xosc.PrivateAction()
        # action.add_controller_action(xosc.ActivateControllerAction(longitudinal=True, lateral=True))
        name = f"Activate_{agent_name}Controller"
        event = xosc.Event(name, priority="overwrite", maxexecution=1)
        event.add_action(f"Activate{agent_name}", xosc.ActivateControllerAction(longitudinal=True, lateral=True))
        


        trigger = xosc.ValueTrigger(
                name=f"activate_{agent_name}_controller",
                delay=delay_time,
                conditionedge=xosc.ConditionEdge.none,
                valuecondition=xosc.SimulationTimeCondition(0, xosc.Rule.greaterThan)
            )
        group = xosc.ConditionGroup()
        group.add_condition(trigger)
        event.add_trigger(group)
        maneuver.add_event(event)
        mg.add_maneuver(maneuver)
        return mg

    # 建立 Act 並加入兩個 agent 的 ManeuverGroup
    delay_time = 0.0
    act = xosc.Act(name="act_activate_controllers")
    for cata in Actors:
        for idx, actor in enumerate(Actors[cata], start=1):
            actorName = f"{cata[:-1]}{idx}"
            act.add_maneuver_group(create_maneuver_group(actorName, delay_time=delay_time))
            delay_time += 0.1

    
    # 包成 Story
    story = xosc.Story(name="story_activate_controllers")
    story.add_act(act)
    
    return story
    