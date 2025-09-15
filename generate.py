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
    # create_invalid_area_condition,
    create_reach_target_condition,
    # create_right_start_speed_condition,
    # create_stand_still_conditions,
    create_timeout_condition,
    # create_wrong_start_speed_condition,
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



def generate(base_config, scenario_config, company='HCISLab'):
    
    # === 基本參數與 Actor 數量 ===
    EgoName = base_config['ego'].get('name', 'Ego')

    Actors = scenario_config['Actors']
    EgoConfig = scenario_config['Ego']
    MapConfig = scenario_config['Map']
    ScenarioName = scenario_config['Scenario_name']
    agentCount = len(Actors.get('Agents', []))
    pedCount = len(Actors.get('Pedestrians', []))


    # === 1. 宣告參數與 Catalogs ===
    vardec, variable_dict = variable_Declaration(base_config.get('variables', []))
    paramdec = parameter_Declaration(Actors, EgoConfig)

    # CatalogLocations & RoadNetwork (document:xosc.utiles)
    catalog = xosc.Catalog()
    for cata in base_config['catalogs']:
        catalog.add_catalog(cata['name'], cata['path'])

    road = xosc.RoadNetwork(roadfile=base_config['xodr_path'])

    # === 2. 建立 Ego Controller 實體 ===
    egoController = get_Ego_Controller(base_config['ego'].get('controller', None))


    # === 3. 建立 Entities (Ego + Agents + Pedestrians)(document:xosc.Entities) ===
    agentController = xosc.Controller(name="ALKSController", properties=xosc.Properties())
    entities = create_Entity(egoController, agentCount, pedCount, agentController=agentController)


    # --- 4. Storyboard ---
    # === 4.1 建立 Init 動作 ===
    step_time = xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0)
    init = xosc.Init()

    # Ego 初始位置、控制器啟動與終點位置
    # egoStartPos = create_LanePosition_from_config(MapConfig, EgoConfig['Start_pos'])
    eventStart_road = MapConfig[Actors['Agents'][0]['Start_trigger']['road']]
    eventStart_lane = Actors['Agents'][0]['Start_trigger']['lane']
    eventStart_s = Actors['Agents'][0]['Start_trigger']['s']
    eventStart_offset = Actors['Agents'][0]['Start_trigger']['offset']
    egoStartPos = xosc.LanePosition(
        s=eventStart_s,
        offset=eventStart_offset,
        lane_id=eventStart_lane,
        road_id=eventStart_road)
    egoEndPos = create_LanePosition_from_config(MapConfig, EgoConfig['End_pos'])
    egoController = True

    init.add_init_action(EgoName, xosc.TeleportAction(egoStartPos))
    init.add_init_action(EgoName, xosc.ActivateControllerAction(lateral=egoController, longitudinal=egoController))
    init.add_init_action(EgoName, xosc.AcquirePositionAction(egoEndPos))
    init.add_init_action(EgoName, xosc.AbsoluteSpeedAction("${$Ego_Speed / 3.6}", step_time))


    # Agents / Pedestrians 初始位置
    for cata in Actors:
        for idx, actor in enumerate(Actors[cata], start=1):
            actorName = f"{cata[:-1]}{idx}"
            startPos = create_LanePosition_from_config(MapConfig, actor['Start_pos'], s=f"${actorName}_S", offset=f"${actorName}_Offset")
            init.add_init_action(actorName, xosc.TeleportAction(startPos))

    # === 4.2 產生 Maneuvers 與 Events ===
    # invalid condition flags
    egoParamManeuver = generate_Variable_Maneuver(EgoName, variable_dict, scenario_config, actors=Actors)


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
    sb_stoptrigger = create_StopTrigger(base_config['stop_conditions'], variable_dict)

    # === 4.4 Storyboard 組裝 ===
    sb = xosc.StoryBoard(init, sb_stoptrigger)
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
        osc_minor_version=2,
        variable_declaration=vardec
    )

    return scenario

def variable_Declaration(variable_list):
    vardec = xosc.VariableDeclarations()
    variable_dict = {}
    for var in variable_list:
        vardec.add_variable(xosc.Variable(
            name=var['name'], variable_type=var['type'], value=str(var['value'])))
        variable_dict[var['name']] = var['value']

    return vardec, variable_dict

def parameter_Declaration(Actors, Ego):
    paramdec = xosc.ParameterDeclarations()
    paraList = []

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


def get_Ego_Controller(controller_name):
    if controller_name == "ACCController" or controller_name == "ACC":
        print("Ego Controller: ACCController")
        egoControllerProperties = xosc.Properties()
        egoControllerProperties.add_property(name="timeGap", value="1.0")
        egoControllerProperties.add_property(name="mode", value="override")
        egoControllerProperties.add_property(name="setSpeed", value="${$Ego_Speed / 3.6}")
        return xosc.Controller(name="ACCController", properties=egoControllerProperties)
    elif controller_name == "interactiveDriver":
        print("Ego Controller: interactiveDriver")
        return xosc.CatalogReference(catalogname="ControllerCatalog", entryname="interactiveDriver")
    elif controller_name == "ROSController" or controller_name == "ROS":
        print("Ego Controller: ROSController")
        return xosc.CatalogReference(catalogname="ControllerCatalog", entryname="ROSController")

    print("Controller not found")
    return None

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


def generate_Variable_Maneuver(ego_name, variable_dict, scenario_config, actors):
    param_maneuver = xosc.Maneuver("ParameterManeuver")
    ego_speed = float(scenario_config['Ego']['Start_speed'])
    agent = actors['Agents'][0]
    agent_count = len(actors['Agents'])
    MapConfig = scenario_config['Map']

    # === Detect Ego Has Moved Event ===
    if 'FLAG-AV_CONNECTED' in variable_dict:
        event = xosc.Event("DetectEgoHasMovedEvent", xosc.Priority.parallel)
        event.add_action("Set EgoHasMoved Flag", xosc.VariableSetAction("FLAG-AV_CONNECTED", "true"))
        event.add_trigger(xosc.EntityTrigger("EgoHasMoved", 0, xosc.ConditionEdge.none,
                        xosc.SpeedCondition(0, xosc.Rule.greaterThan), ego_name))
        param_maneuver.add_event(event)

    # === Init Valid Flag ===
    if 'FLAG-IS_VALID' in variable_dict:
        event = xosc.Event("ValidManeuverEvent", xosc.Priority.parallel)
        event.add_action("Set Valid Flag", xosc.VariableSetAction("FLAG-IS_VALID", "true"))
        
        """ 舊的trigger(有助跑得狀況): 需要在觸發位置有正確的速度才算valid"""
        # valid_trigger = create_right_start_speed_condition(MapConfig, EGO_NAME, agent['Start_trigger'], ego_speed)
        
        """ 
        沒有助跑得情況下，直接用 Ego 有移動來當作 Valid 的條件
        TODO: 未來要檢查ego 是出生在適當位置(一開始不會離agent太近) 才算valid
        """
        valid_trigger = xosc.EntityTrigger("EgoHasMoved", 0, xosc.ConditionEdge.none,
                        xosc.SpeedCondition(0, xosc.Rule.greaterThan), ego_name)
        event.add_trigger(valid_trigger)
        param_maneuver.add_event(event)

    # === Detect AV Connection Timeout Event(30) ===
    if 'FLAG-AV_CONNECTION_TIMEOUT' in variable_dict:
        event = xosc.Event("DetectAVConnectionTimeoutEvent", xosc.Priority.parallel)
        event.add_action("Set AV Connection Timeout Flag", xosc.VariableSetAction("FLAG-AV_CONNECTION_TIMEOUT", "true"))
        if 'VAL-AV_CONNECTION_TIMEOUT' in variable_dict:
            time = float(variable_dict['VAL-AV_CONNECTION_TIMEOUT'])
        else:
            print("No VAL-AV_CONNECTION_TIMEOUT variable, use default 30s")
            time = 30.0
        event.add_trigger(create_timeout_condition(ego_name, time=time))
        param_maneuver.add_event(event)

    # # === Detect Wrong Start Speed Event - above tolerance ===
    # low_group, high_group = create_wrong_start_speed_condition(
    #     MapConfig, EGO_NAME, agent['Start_trigger'], ego_speed, tolerance=2)

    # event = xosc.Event("DetectHighStartSpeedEvent", xosc.Priority.parallel)
    # event.add_action("Set High Start Speed Flag", xosc.VariableSetAction("FLAG-WRONG_START_SPEED", "true"))
    # event.add_trigger(high_group)
    # param_maneuver.add_event(event)

    # # === Detect Wrong Start Speed Event - below tolerance ===
    # event = xosc.Event("DetectLowStartSpeedEvent", xosc.Priority.parallel)
    # event.add_action("Set Low Start Speed Flag", xosc.VariableSetAction("FLAG-WRONG_START_SPEED", "true"))
    # event.add_trigger(low_group)
    # param_maneuver.add_event(event)

    # === Detect Ego Reached End Event ===
    if 'FLAG-EGO_REACHED_END' in variable_dict:
        event = xosc.Event("DetectEgoReachedEndEvent", xosc.Priority.parallel)
        event.add_action("Set Ego Reached End Flag", xosc.VariableSetAction("FLAG-EGO_REACHED_END", "true"))
        event.add_trigger(create_reach_target_condition(MapConfig, ego_name, scenario_config['Ego']['End_pos']))
        param_maneuver.add_event(event)

    # === Detect Ego TLE Event ===
    if 'FLAG-EGO_TLE' in variable_dict:
        event = xosc.Event("DetectEgoTLEEvent", xosc.Priority.parallel)
        event.add_action("Set Ego TLE Flag", xosc.VariableSetAction("FLAG-EGO_TLE", "true"))
        if 'VAL-EGO_TLE' in variable_dict:
            time = float(variable_dict['VAL-EGO_TLE'])
        else:
            print("No VAL-EGO_TLE variable, use default 20s")
            time = 20.0

        # OLD: 有助跑版本
        # event.add_trigger(create_ego_tle_condition(MapConfig, agent['Start_trigger'], EGO_NAME, time=time))
       
        """ 無助跑: 從AV_CONNECTED開始計時 """
        tle_trigger = xosc.EntityTrigger("EgoHasMoved", time, xosc.ConditionEdge.none,
                        xosc.SpeedCondition(0, xosc.Rule.greaterThan), ego_name)
        event.add_trigger(tle_trigger)

        param_maneuver.add_event(event)

    # === Detect Ego Collision Event ===
    if 'FLAG-EGO_COLLISION' in variable_dict:
        event = xosc.Event("DetectEgoCollisionEvent", xosc.Priority.parallel)
        event.add_action("Set Ego Collision Flag", xosc.VariableSetAction("FLAG-EGO_COLLISION", "true"))
        event.add_trigger(create_collision_condition(ego_name, agentCount=agent_count))
        param_maneuver.add_event(event)

    # === Create Ego Stroll Event ===
    if 'FLAG-EGO_STROLL' in variable_dict:
        event = xosc.Event("EgoStrollEvent", xosc.Priority.parallel)
        event.add_action("Set Ego Stroll Flag", xosc.VariableSetAction("FLAG-EGO_STROLL", "true"))
        if 'VAL-EGO_STROLL' in variable_dict:
            time = float(variable_dict['VAL-EGO_STROLL'])
        else:
            print("No VAL-EGO_STROLL variable, use default 20s")
            time = 20.0
        event.add_trigger(create_ego_stroll_condition(time=time))
        param_maneuver.add_event(event)

    return param_maneuver


    