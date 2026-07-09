import os
import math
from pprint import pprint
from time import time
import numpy as np
from scenariogeneration import xosc, prettyprint, esmini
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
    generate_Zigzag_Event,
    generate_FollowTrajectory_Event,  # <-- add this import
)

from utils.utils_config import (
    DEFAULT_AGENT_CONTROLLER,
    agent_type_map,
    set_flag_action,
    agent_controller,
)
import config


def generate(base_config, scenario_config):
    
    # === 基本參數與 Actor 數量 ===
    EgoName = base_config['ego'].get('name', 'Ego')

    Actors = scenario_config['Actors']
    EgoConfig = scenario_config['Ego']
    MapConfig = scenario_config['Map']
    ScenarioName = scenario_config['Scenario_name']
    # print(f"Generating scenario: {ScenarioName} ", end=' | ')
    agentCount = len(Actors.get('Agents', []))
    pedCount = len(Actors.get('Pedestrians', []))


    # === 1. 宣告參數與 Catalogs ===
    vardec, variable_dict = variable_Declaration(base_config.get('variables', []))
    paramdec = parameter_Declaration(Actors, EgoConfig, base_config.get('variables', []))

    # CatalogLocations & RoadNetwork (document:xosc.utiles)
    catalog = xosc.Catalog()
    for cata in base_config['catalogs']:
        catalog.add_catalog(cata['name'], cata['path'])

    road = xosc.RoadNetwork(roadfile=base_config['xodr_path'])

    # === 2. 建立 Ego Controller 實體 ===
    egoController = get_Ego_Controller(base_config['ego'].get('controller', None))


    # === 3. 建立 Entities (Ego + Agents + Pedestrians)(document:xosc.Entities) ===
    entities = create_Entity(egoController, Actors)

    # --- 4. Storyboard ---
    # === 4.1 建立 Init 動作 ===
    step_time = xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0)
    init = xosc.Init()
    

    # 天氣
    if config.SIMULATION_FOR == "CARLA":
        if config.OPENSCENARIO_VERSION != 1.0:
            raise NotImplementedError("Only OpenSCENARIO 1.0 is supported in the current implementation.")
        
        tod = xosc.TimeOfDay(True, 2026, 4, 21, 12, 00, 00)
        weather = xosc.Weather(
            cloudstate="free",
            # cloudstate="zeroOktas", # osc 1.2
            precipitation=xosc.Precipitation(xosc.PrecipitationType.dry, 0),
            fog=xosc.Fog(100000.0),
            sun=xosc.Sun(100000, 0.0, 1.31),
        )
        rc = xosc.RoadCondition(1)
        env = xosc.Environment("Environment1", tod, weather, rc)
        ea = xosc.EnvironmentAction(env)
        init.add_global_action(ea)

    # Ego 初始位置、控制器啟動與終點位置
    egoStartPos = create_LanePosition_from_config(MapConfig, EgoConfig['Start_pos'])
    # eventStart_road = MapConfig[Actors['Agents'][0]['Start_trigger']['road']]
    # eventStart_lane = Actors['Agents'][0]['Start_trigger']['lane']
    # eventStart_s = Actors['Agents'][0]['Start_trigger']['s']
    # eventStart_offset = Actors['Agents'][0]['Start_trigger']['offset']
    # egoStartPos = xosc.LanePosition(
    #     s=eventStart_s,
    #     offset=eventStart_offset,
    #     lane_id=eventStart_lane,
    #     road_id=eventStart_road)
    egoEndPos = create_LanePosition_from_config(MapConfig, EgoConfig['End_pos'])
    egoController = agent_controller.get('car_white', False)


    init.add_init_action(EgoName, xosc.TeleportAction(egoStartPos))
    # init.add_init_action(EgoName, xosc.ActivateControllerAction(lateral=egoController, longitudinal=egoController))
    # init.add_init_action(EgoName, xosc.AcquirePositionAction(egoEndPos)) # Scenario runner 目前不支援在 Init 使用 AcquirePositionAction，改放在 Storyboard 的第一個 Event 裡面
    init.add_init_action(EgoName, xosc.AbsoluteSpeedAction("${$Ego_Speed / 3.6}", step_time))

    # Add ControllerAction for Ego
    if egoController:
        # 舊版
        # controller_action = xosc.ControllerAction()
        # controller_action.add_assign_controller_action(egoController)
        # controller_action.add_override_controller_value_action(lateral=True, longitudinal=True)
        # init.add_init_action(EgoName, controller_action)

        override_action = xosc.OverrideControllerValueAction()
        override_action.set_throttle(active=False, value=0)
        override_action.set_brake(active=False, value=0)
        override_action.set_clutch(active=False, value=0)
        override_action.set_parkingbrake(active=False, value=0)
        override_action.set_steeringwheel(active=False, value=0)
        override_action.set_gear(active=False, value=0)

        # 2. 建立 AssignControllerAction (依 agent type 對應到 utils_config.agent_controller)
        catalog_ref = xosc.CatalogReference("ControllerCatalog", egoController)
        assign_action = xosc.AssignControllerAction(catalog_ref)

        # 3. 【最終修正】在同一個 ControllerAction 中傳入兩者
        # 這樣能同時滿足：
        # - 兩者都被標記為 _used_by_parent (解決 VersionError)
        # - 兩者都存在 (解決 NotEnoughInputArguments)
        controller_action = xosc.ControllerAction(
            assignControllerAction=assign_action,
            overrideControllerValueAction=override_action
        )

        # 4. 只加入這一個 Action
        init.add_init_action(EgoName, controller_action)


    # Agents / Pedestrians 初始位置
    for cata in Actors:
        # continue #改在story
        for idx, actor in enumerate(Actors[cata], start=1):

            actorName = f"{cata[:-1]}{idx}"
            # for HetroD nps model
            
            """ esmini """
            # # esmini
            # startPos = xosc.WorldPosition(0, 1, -100, 0, 0, 0)
            # if actor['Acts'][0]['Type'] == 'replay':
            #     first_point = actor['Acts'][0]['Events'][0]['Trajectories'][0]
            #     startPos = xosc.WorldPosition(first_point[1], -100, math.radians(first_point[2]), 0, 0)
            # init.add_init_action(actorName, xosc.TeleportAction(startPos))


            # # Add ControllerAction for Agents
            # agentController = xosc.Controller(name="ACCController", properties=xosc.Properties())
            # controller_action = xosc.ControllerAction()
            # controller_action.add_assign_controller_action(agentController)
            # controller_action.add_override_controller_value_action(lateral=True, longitudinal=True)
            # init.add_init_action(actorName, controller_action)

            """ carla """
            if config.OPENSCENARIO_VERSION == 1.0:
                init.add_init_action(actorName, xosc.TeleportAction(create_LanePosition_from_config(MapConfig, actor['Start_pos'])))
                
                override_action = xosc.OverrideControllerValueAction()
                override_action.set_throttle(active=False, value=0)
                override_action.set_brake(active=False, value=0)
                override_action.set_clutch(active=False, value=0)
                override_action.set_parkingbrake(active=False, value=0)
                override_action.set_steeringwheel(active=False, value=0)
                override_action.set_gear(active=False, value=0)

                # 2. 建立 AssignControllerAction (依 agent type 對應到 utils_config.agent_controller)
                controller_name = agent_controller.get(actor.get('Type'), DEFAULT_AGENT_CONTROLLER)
                catalog_ref = xosc.CatalogReference("ControllerCatalog", controller_name)
                assign_action = xosc.AssignControllerAction(catalog_ref)

                # 3. 【最終修正】在同一個 ControllerAction 中傳入兩者
                # 這樣能同時滿足：
                # - 兩者都被標記為 _used_by_parent (解決 VersionError)
                # - 兩者都存在 (解決 NotEnoughInputArguments)
                controller_action = xosc.ControllerAction(
                    assignControllerAction=assign_action,
                    overrideControllerValueAction=override_action
                )

                # 4. 只加入這一個 Action
                init.add_init_action(actorName, controller_action)
            else:
                NotImplementedError("Only OpenSCENARIO 1.0 is supported in the current implementation.")


    # === 4.2 產生 Maneuvers 與 Events ===
    # invalid condition flags
    egoParamManeuver = generate_Variable_Maneuver(EgoName, variable_dict, scenario_config, actors=Actors)


    allManeuvers = {}
    allStartEvent = []

    if config.DEBUG: #平常不加避免autowawre Actor not found in blackboard的問題
        egoManeuver = xosc.Maneuver(f"Ego_Maneuver")
        egoEndPos = create_LanePosition_from_config(MapConfig, EgoConfig['End_pos'])
        
        # Create Ego Acquire Position Event
        egoAcquirePosEvent = xosc.Event("Ego_GoalEvent", xosc.Priority.parallel)
        egoAcquirePosEvent.add_action("Ego_EndPosAction", xosc.AcquirePositionAction(egoEndPos))
        egoAcquirePosEvent.add_action("Ego_ActivateController", xosc.ActivateControllerAction(longitudinal=True, lateral=True)) #for default demo
        condition = xosc.SimulationTimeCondition(0, xosc.Rule.greaterThan)
        egoAcquirePosTrigger = xosc.ValueTrigger(
            name="EgoAcquirePosTrigger",
            delay=0,
            conditionedge=xosc.ConditionEdge.none,
            valuecondition=condition,
        )
        egoAcquirePosEvent.add_trigger(egoAcquirePosTrigger)
        

    
        
        egoManeuver.add_event(egoAcquirePosEvent)
        allManeuvers['Ego'] = egoManeuver

    for cata in Actors:
        for idx, actor in enumerate(Actors[cata], start=1):
            actorName = f"{cata[:-1]}{idx}"
            maneuvers, previousEventNames = generate_Adv_Maneuver(actorName, actor, MapConfig)
            from rich import console
            console = console.Console()
            # console.log(dir(maneuvers))
            # console.log(previousEventNames)
            # exit()
            if maneuvers:
                allManeuvers[actorName] = maneuvers
                allStartEvent.append(previousEventNames[0])

    # === 4.3 建立 StopTrigger 終止條件 ===
    sb_stoptrigger = create_StopTrigger(base_config['stop_conditions'], variable_dict)

    # === 4.4 Storyboard 組裝 ===
    sb = xosc.StoryBoard(init, sb_stoptrigger)
    for name, maneuver in allManeuvers.items():
        mangr = xosc.ManeuverGroup("maneuvergroup_" + maneuver.name)
        mangr.add_actor(name)
        mangr.add_maneuver(maneuver)
        act = xosc.Act(name, stoptrigger=sb_stoptrigger)
        act.add_maneuver_group(mangr)
        sb.add_act(act)

    sb.add_maneuver(egoParamManeuver, "Ego")

    # from rich import inspect
    # inspect(sb);exit()
    class HackyInt(int):
        def __gt__(self, other):
            # 欺騙邏輯：當程式問「2 是否大於 1」時，回傳 False
            if other == 1:
                return False
            return super().__gt__(other)
        
        def __lt__(self, other):
            # 欺騙邏輯：當程式問「2 是否小於 2」時，回傳 False
            if other == 2:
                return False
            return super().__lt__(other)

    # === 5. 組裝 Scenario 實體並回傳 ===
    scenario = xosc.Scenario(
        name="hct_" + ScenarioName,
        author="HCIS_ChengYu-Wu",
        parameters=paramdec,
        entities=entities,
        storyboard=sb,
        roadnetwork=road,
        catalog=catalog,
        osc_minor_version=0,
        # variable_declaration=vardec
    )

    return scenario

def variable_Declaration(variable_list):
    # vardec = xosc.VariableDeclarations()
    # variable_dict = {}
    # for var in variable_list:
    #     vardec.add_variable(xosc.Variable(
    #         name=var['name'], variable_type=var['type'], value=str(var['value'])))
    #     variable_dict[var['name']] = var['value']

    # scenario_runner 目前不支援 VariableDeclarations，先把變數用Declarations處理
    vardec = xosc.ParameterDeclarations()
    variable_dict = {}
    for var in variable_list:
        vardec.add_parameter(xosc.Parameter(
            name=var['name'], parameter_type=var['type'], value=str(var['value'])))
        variable_dict[var['name']] = var['value']

    return vardec, variable_dict

def parameter_Declaration(Actors, Ego, Variables=None):
    paramdec = xosc.ParameterDeclarations()
    paraList = []

    # for common use
    ego_type = agent_type_map.get("car_white", "vehicle.tesla.model3")


    # ParameterDeclarations
    egoInit = xosc.Parameter(
        name="Ego_Vehicle", parameter_type="string", value=ego_type)
    egoSpeed = xosc.Parameter(
        name="Ego_Speed", parameter_type="double", value=Ego['Start_speed'])
    egoS = xosc.Parameter(
        name="Ego_S", parameter_type="double", value=Ego['Start_pos'][2])
    paraList.extend([egoInit, egoSpeed, egoS])

    # catas = ['Agents', 'Pedestrians']
    for cata in Actors:
        for actorIndex, actor in enumerate(Actors[cata], start=1):
            agent_type = agent_type_map.get(actor['Type'], "vehicle.tesla.model3")
            actorName = f"{cata[:-1]}{actorIndex}"
            # actor's Init parameter
            actorType = xosc.Parameter(
                name=f"{actorName}_Type", parameter_type="string", value=agent_type)
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
                elif act['Type'] == 'replay':
                    for eventIndex, event in enumerate(act['Events'], start=1):
                        if event['Type'] == 'follow_trajectory':
                            spawn_delay = xosc.Parameter(
                                name=f"{actorName}_Delay", parameter_type="double", value=str(act['Delay'])) #Spawn event
                            delay = xosc.Parameter(
                                name=f"{actorName}_{actIndex}_Delay", parameter_type="double", value=str(0.0)) #Dummy event
                            loop = xosc.Parameter(
                                name=f"{actorName}_Loop_Times", parameter_type="double", value=str(event['Loop']))
                            paraList.extend([loop, delay, spawn_delay])
                else:
                    spawn_delay = xosc.Parameter(
                        name=f"{actorName}_Delay", parameter_type="double", value=str(act['Delay'])) #Spawn event
                    delay = xosc.Parameter(
                        name=f"{actorName}_{actIndex}_Delay", parameter_type="double", value=str(0.0))
                    paraList.extend([spawn_delay, delay])
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

    # Add Agent1_1_TA_Times parameter if any act of type follow_trajectory with Loop: true is found
    for cata in Actors:
        for actorIndex, actor in enumerate(Actors[cata], start=1):
            actorName = f"{cata[:-1]}{actorIndex}"
            # check if actor has 'Acts'
            if 'Acts' not in actor:
                print(f"{actorName} has no 'Acts'")
                continue
            for actIndex, act in enumerate(actor['Acts'], start=1):
                # print(f"Processing {actorName} Act {actIndex}: {act['Type']}"   )
                if act['Type'] == 'follow_trajectory':
                    for eventIndex, event in enumerate(act['Events'], start=1):
                        if event.get('Loop', False):
                            ta_times_name = f"{actorName}_{actIndex}_TA_Times"
                            ta_times_param = xosc.Parameter(
                                name=ta_times_name, parameter_type="double", value="5"
                            )
                            paraList.append(ta_times_param)
    if Variables:
        for var in Variables:
            param = xosc.Parameter(name=var['name'], parameter_type=var['type'], value=str(var['value']))
            paraList.append(param)

    # for dummy action: ParameterAction
    dummy_parameter = xosc.Parameter(name="Dummy_Parameter", parameter_type="double", value=1)
    paraList.append(dummy_parameter)

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
    elif controller_name == "IgnoreEgoACCController" or controller_name == "IgnoreEgoACC":
        egoControllerProperties = xosc.Properties()
        egoControllerProperties.add_property(name="timeGap", value="1.0")
        egoControllerProperties.add_property(name="mode", value="override")
        egoControllerProperties.add_property(name="setSpeed", value="${$Ego_Speed / 3.6}")
        return xosc.Controller(name="IgnoreEgoACCController", properties=egoControllerProperties)
    elif controller_name == "interactiveDriver":
        print("Ego Controller: interactiveDriver")
        return xosc.CatalogReference(catalogname="ControllerCatalog", entryname="interactiveDriver")
    elif controller_name == "ROSController" or controller_name == "ROS":
        print("Ego Controller: ROSController")
        return xosc.CatalogReference(catalogname="ControllerCatalog", entryname="ROSController")

    print("Controller not found")
    return None

def create_agent_controller(agent_type):
    name = agent_controller.get(agent_type, DEFAULT_AGENT_CONTROLLER)
    return xosc.Controller(name=name, properties=xosc.Properties())

def create_Entity(egoController, Actors):
    # construct CatalogReference
    egoObject = xosc.CatalogReference(
        catalogname="VehicleCatalog", entryname="$Ego_Vehicle")  # xosc.utils

    agents = Actors.get('Agents', [])
    pedestrians = Actors.get('Pedestrians', [])

    # create entity
    entities = xosc.Entities()

    # ego
    entities.add_scenario_object(
        name="Ego", entityobject=egoObject) #, controller=egoController) # Scenario Runner 目前不支援在 Entity 定義 Controller

    # Scenario Runner 目前不支援在 Entity 定義 Controller，所以改在 Init 裡面用 ControllerAction 指定控制器與 OverrideControllerValueAction 的初始值
    # agents — controller chosen per actor type via utils_config.agent_controller
    for i, actor in enumerate(agents):
        agentObject = xosc.CatalogReference(
            catalogname="VehicleCatalog", entryname=f"$Agent{i+1}_Type")
        entities.add_scenario_object(
            name=f"Agent{i+1}", entityobject=agentObject)

    # pedestrians — controller chosen per actor type via utils_config.agent_controller
    for i, actor in enumerate(pedestrians):
        pedObject = xosc.CatalogReference(
            catalogname="PedestrianCatalog", entryname=f"$Pedestrian{i+1}_Type")
        entities.add_scenario_object(
            name=f"Pedestrian{i+1}", entityobject=pedObject)

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
                        actorName, actIndex, event, Map, previousEventNames, currentPosition)
                    for currentEvent in zigzagEvent:
                        currentEventName.append(currentEvent.name)
                        advManeuver.add_event(currentEvent)
                else:
                    print('Event Type Error')
                    break

            previousEventName = currentEventName
        elif act['Type'] == 'replay':
            for eventIndex, event in enumerate(act['Events'], start=1):
                if event['Type'] == 'follow_trajectory':
                    currentEvent = generate_FollowTrajectory_Event(
                        actorName, actIndex, event, previousEventName
                    )
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
    setFlagAction = set_flag_action['ParameterSetAction']

    param_maneuver = xosc.Maneuver("ParameterManeuver")
    # ego_speed = float(scenario_config['Ego']['Start_speed'])
    # try:
    #     agent = actors['generate_Agent_Start_Event'][0]
    # except (KeyError, IndexError):
    #     agent = actors['Agents'][0]
    agent_count = 1
    try:
        agent_count = len(actors['Agents']) + len(actors['Pedestrians'])
    except (KeyError, IndexError):
        pass
    MapConfig = scenario_config['Map']

    # === Detect Ego Has Moved Event ===
    if 'FLAG-AV_CONNECTED' in variable_dict:
        event = xosc.Event("DetectEgoHasMovedEvent", xosc.Priority.parallel)
        event.add_action("Set EgoHasMoved Flag", setFlagAction("FLAG-AV_CONNECTED", "true"))
        event.add_trigger(xosc.EntityTrigger("EgoHasMoved", 0, xosc.ConditionEdge.none,
                        xosc.SpeedCondition(0, xosc.Rule.greaterThan), ego_name))
        param_maneuver.add_event(event)

    # === Init Valid Flag ===
    if 'FLAG-IS_VALID' in variable_dict:
        event = xosc.Event("ValidManeuverEvent", xosc.Priority.parallel)
        event.add_action("Set Valid Flag", setFlagAction("FLAG-IS_VALID", "true"))
        
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
        event.add_action("Set AV Connection Timeout Flag", setFlagAction("FLAG-AV_CONNECTION_TIMEOUT", "true"))
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
    # event.add_action("Set High Start Speed Flag", setFlagAction("FLAG-WRONG_START_SPEED", "true"))
    # event.add_trigger(high_group)
    # param_maneuver.add_event(event)

    # # === Detect Wrong Start Speed Event - below tolerance ===
    # event = xosc.Event("DetectLowStartSpeedEvent", xosc.Priority.parallel)
    # event.add_action("Set Low Start Speed Flag", setFlagAction("FLAG-WRONG_START_SPEED", "true"))
    # event.add_trigger(low_group)
    # param_maneuver.add_event(event)

    # === Detect Ego Reached End Event ===
    if 'FLAG-EGO_REACHED_END' in variable_dict:
        event = xosc.Event("DetectEgoReachedEndEvent", xosc.Priority.parallel)
        event.add_action("Set Ego Reached End Flag", setFlagAction("FLAG-EGO_REACHED_END", "true"))
        event.add_trigger(create_reach_target_condition(MapConfig, ego_name, scenario_config['Ego']['End_pos']))
        param_maneuver.add_event(event)

    # === Detect Ego TLE Event ===
    if 'FLAG-EGO_TLE' in variable_dict:
        event = xosc.Event("DetectEgoTLEEvent", xosc.Priority.parallel)
        event.add_action("Set Ego TLE Flag", setFlagAction("FLAG-EGO_TLE", "true"))
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
        event.add_action("Set Ego Collision Flag", setFlagAction("FLAG-EGO_COLLISION", "true"))
        event.add_trigger(create_collision_condition(ego_name, agentCount=agent_count))
        param_maneuver.add_event(event)

    # === Create Ego Stroll Event ===
    if 'FLAG-EGO_STROLL' in variable_dict:
        event = xosc.Event("EgoStrollEvent", xosc.Priority.parallel)
        event.add_action("Set Ego Stroll Flag", setFlagAction("FLAG-EGO_STROLL", "true"))
        if 'VAL-EGO_STROLL' in variable_dict:
            time = float(variable_dict['VAL-EGO_STROLL'])
        else:
            print("No VAL-EGO_STROLL variable, use default 20s")
            time = 20.0
        event.add_trigger(create_ego_stroll_condition(time=time))
        param_maneuver.add_event(event)

    return param_maneuver

