import os
from scenariogeneration import xosc, prettyprint
from utils.dicent_utils import *


def generate(config, company='HCISLab'):

    Actors = config['Actors']
    paramdec = parameter_Declaration(Actors, config['Ego'])
    xodrPath = './hct_6.xodr'
    # CatalogLocations & RoadNetwork (document:xosc.utiles)
    catalog = xosc.Catalog()
    if company == 'HCISLab':
        catalog.add_catalog("VehicleCatalog", "./Catalogs/Vehicles")
        catalog.add_catalog("ControllerCatalog", "./Catalogs/Controllers")
        # catalog.add_catalog("VehicleCatalog", "/home/hcis-s19/Documents/ChengYu/esmini-demo/resources/xosc/Catalogs/Vehicles")
        if 'Pedestrians' in Actors:
            catalog.add_catalog("PedestrianCatalog", "./Catalogs/Pedestrians")
        road = xosc.RoadNetwork(roadfile="../hct_6.xodr")
        # road = xosc.RoadNetwork(roadfile="/home/hcis-s19/Documents/ChengYu/retrive_scene_nps/tianjin.xodr")
        # road = xosc.RoadNetwork(roadfile="/home/hcis-s19/Documents/ChengYu/retrive_scene_nps/cr_file.xodr")

        # ACC controller
        # controllerName = "ACCController"
        controllerName = "interactiveDriver"

    else:  # ITRI
        # CatalogLocations
        catalog.add_catalog("VehicleCatalog", "../Catalogs/Vehicles")
        catalog.add_catalog("ControllerCatalog", "../Catalogs/Controllers")

        if 'Pedestrians' in Actors:
            catalog.add_catalog("PedestrianCatalog", "../Catalogs/Pedestrians")

        # RoadNetwork
        road = xosc.RoadNetwork(roadfile="../../xodr/itri/hct_6.xodr")

        # construct ego controller - ROS
        controllerName = "ROSController"

    egoControllerProperties = xosc.Properties()
    egoControllerProperties.add_property(name="timeGap", value="1.0")
    egoControllerProperties.add_property(name="mode", value="override")
    egoControllerProperties.add_property(
        name="setSpeed", value="${$Ego_Speed / 3.6}")
    egoController = xosc.Controller(
        name=controllerName, properties=egoControllerProperties)
    # egoController = xosc.CatalogReference(
    #     catalogname="ControllerCatalog", entryname=controllerName)
    # Entities (document:xosc.Entities)
    agentCount = len(Actors['Agents']) if 'Agents' in Actors else 0
    pedCount = len(Actors['Pedestrians']) if 'Pedestrians' in Actors else 0
    entities = create_Entity(egoController, agentCount, pedCount)

    step_time = xosc.TransitionDynamics(
        xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0)

    # Storyboard - Init 初始設定
    # Ego 初始化
    init = xosc.Init()
    egostart = xosc.TeleportAction(create_LanePosition_from_config(
        config['Map'], config['Ego']['Start_pos']))
    egospeed = xosc.AbsoluteSpeedAction("${$Ego_Speed / 3.6}", step_time)
    # egospeed = xosc.AbsoluteSpeedAction(30/3.6, step_time)
    # activate_controller = 'false' if config['DeactivateControl'] else 'true'
    activate_controller = 'true'
    egocontl = xosc.ActivateControllerAction(
        lateral=activate_controller, longitudinal=activate_controller)
    egoEndPosition = create_LanePosition_from_config(
        config['Map'], config['Ego']['End_pos'])
    egofinal = xosc.AcquirePositionAction(egoEndPosition)  # Ego終點
    init.add_init_action('Ego', egostart)
    # init.add_init_action('Ego', egospeed)
    init.add_init_action('Ego', egocontl)
    init.add_init_action('Ego', egofinal)

    # Actor 初始化
    for cata in Actors:
        for actorIndex, actor in enumerate(Actors[cata], start=1):
            actorStart = xosc.TeleportAction(create_LanePosition_from_config(
                config['Map'], actor['Start_pos'], s=f"${cata[:-1]}{actorIndex}_S"))
            init.add_init_action(f"{cata[:-1]}{actorIndex}", actorStart)

    # Storyboard - boolean condition
    paraManeuver = generate_Parameter_Maneuver(config, actors=Actors)

    # Storyboard - Event
    allEvent = []
    allManeuver = {}
    allStartEvent = []
    for actors in Actors:
        for actorIndex, actor in enumerate(Actors[actors], start=1):
            actorName = f"{actors[:-1]}{actorIndex}"
            agentManeuver, previousEventNames = generate_Adv_Maneuver(
                actorName, actor, config['Map'])
            if agentManeuver is not None:
                allStartEvent.append(previousEventNames[0])
                allEvent.extend(previousEventNames)
                allManeuver[actorName] = agentManeuver

    sb_stoptrigger = create_StopTrigger(
        Map=config['Map'],
        egoName='Ego',
        eventStartPoint=Actors['Agents'][0]['Start_trigger'],
        eventStartSpeed=float(config['Ego']['Start_speed']),
        egoTargetPoint=config['Ego']['End_pos'],
        xodrPath=xodrPath)

    sb = xosc.StoryBoard(init, sb_stoptrigger)
    for man in allManeuver:
        sb.add_maneuver(allManeuver[man], man)

    # sb.add_maneuver(status_maneuver, "Ego")
    # sb.add_maneuver(approach_init_wp_maneuver, "Ego")
    sb.add_maneuver(paraManeuver, "Ego")

    # Create Scenario
    sce = xosc.Scenario(
        name="hct_"+config['Scenario_name'],
        author="HCIS_ChengYuSheng",
        parameters=paramdec,
        entities=entities,
        storyboard=sb,
        roadnetwork=road,
        catalog=catalog,
        osc_minor_version=0
    )

    return sce


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
            paraList.extend([actorType, actorInitSpeed, actorInitS])

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
                        paraList.extend(
                            [dynamicDelay, dynamicDuration, dynamicShape])

    for i in paraList:
        paramdec.add_parameter(i)

    return paramdec


def create_Catalog_and_RoadNetwork():
    ...


def create_Entity(egoController, agentCount, pedCount):
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
            name=f"Agent{i+1}", entityobject=agentObjectList[i])

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
                    if event['End'] == 0:
                        terminateEvent = create_Terminate_Event(
                            actorName, actIndex, currentEvent)
                        advManeuver.add_event(terminateEvent)
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
                    if event['End'] == 0:
                        terminateEvent = create_Terminate_Event(
                            actorName, actIndex, currentEvent)
                        advManeuver.add_event(terminateEvent)
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

    # Detect Ego Has Moved Event
    status_event = xosc.Event("DetectEgoHasMovedEvent", xosc.Priority.parallel)
    status_event.add_action("Set EgoHasMoved Flag",
                            xosc.ParameterSetAction("AV_CONNECTED", "true"))
    status_event.add_trigger(xosc.EntityTrigger(
        "EgoHasMoved", 0, xosc.ConditionEdge.rising, xosc.SpeedCondition(0, xosc.Rule.greaterThan), "Ego"))
    param_maneuver.add_event(status_event)

    # Valid Maneuver Event
    valid_event = xosc.Event("ValidManeuverEvent", xosc.Priority.parallel)
    valid_event.add_action(
        "Set Valid Flag",
        xosc.ParameterSetAction("IS_VALID", "true"))
    # invalid_event.add_trigger(create_timeout_condition('Ego', time=300))
    valid_trigger = create_right_start_speed_condition(
        config['Map'], 'Ego', actors['Agents'][0]['Start_trigger'], float(config['Ego']['Start_speed']))
    valid_event.add_trigger(valid_trigger)
    param_maneuver.add_event(valid_event)

    # Detect AV Connection Timeout Event
    av_connection_timeout_event = xosc.Event(
        "DetectAVConnectionTimeoutEvent", xosc.Priority.parallel)
    av_connection_timeout_event.add_action(
        "Set AV Connection Timeout Flag",
        xosc.ParameterSetAction("AV_CONNECTION_TIMEOUT", "true"))
    av_connection_timeout_event.add_trigger(
        create_timeout_condition('Ego', time=300))
    param_maneuver.add_event(av_connection_timeout_event)

    # Detect Wrong Start Speed Event - high
    wrong_start_speed_event = xosc.Event(
        "DetectHighStartSpeedEvent", xosc.Priority.parallel)
    wrong_start_speed_event.add_action(
        "Set High Start Speed Flag",
        xosc.ParameterSetAction("WRONG_START_SPEED", "true"))
    low_group, high_group = create_wrong_start_speed_condition(
        config['Map'], 'Ego', actors['Agents'][0]['Start_trigger'], float(config['Ego']['Start_speed']), tolerance=2)
    wrong_start_speed_event.add_trigger(high_group)
    param_maneuver.add_event(wrong_start_speed_event)

    # Detect Wrong Start Speed Event - low
    wrong_start_speed_event = xosc.Event(
        "DetectLowStartSpeedEvent", xosc.Priority.parallel)
    wrong_start_speed_event.add_action(
        "Set Low Start Speed Flag",
        xosc.ParameterSetAction("WRONG_START_SPEED", "true"))
    low_group, high_group = create_wrong_start_speed_condition(
        config['Map'], 'Ego', actors['Agents'][0]['Start_trigger'], float(config['Ego']['Start_speed']), tolerance=2)
    wrong_start_speed_event.add_trigger(low_group)
    param_maneuver.add_event(wrong_start_speed_event)

    # Detect Ego Reached End Event
    ego_reached_end_event = xosc.Event(
        "DetectEgoReachedEndEvent", xosc.Priority.parallel)
    ego_reached_end_event.add_action(
        "Set Ego Reached End Flag",
        xosc.ParameterSetAction("EGO_REACHED_END", "true"))
    ego_reached_end_event.add_trigger(create_reach_target_condition(
        config['Map'], 'Ego', config['Ego']['End_pos']))
    param_maneuver.add_event(ego_reached_end_event)

    #  Detect Ego TLE Event
    ego_tle_event = xosc.Event("DetectEgoTLEEvent", xosc.Priority.parallel)
    ego_tle_event.add_action(
        "Set Ego TLE Flag",
        xosc.ParameterSetAction("EGO_TLE", "true"))
    ego_tle_event.add_trigger(create_ego_tle_condition(
        config['Map'], actors['Agents'][0]['Start_trigger'], 'Ego', time=30))
    param_maneuver.add_event(ego_tle_event)

    # Detect Ego Collision Event
    ego_collision_event = xosc.Event(
        "DetectEgoCollisionEvent", xosc.Priority.parallel)
    ego_collision_event.add_action(
        "Set Ego Collision Flag",
        xosc.ParameterSetAction("EGO_COLLISION", "true"))
    ego_collision_event.add_trigger(
        create_collision_condition('Ego', agentCount=1))
    param_maneuver.add_event(ego_collision_event)

    # Create Ego Stroll Event
    ego_stroll_event = xosc.Event("EgoStrollEvent", xosc.Priority.parallel)
    ego_stroll_event.add_action(
        "Set Ego Stroll Flag",
        xosc.ParameterSetAction("EGO_STROLL", "true"))
    ego_stroll_event.add_trigger(create_ego_stroll_condition(time=30))
    param_maneuver.add_event(ego_stroll_event)

    return param_maneuver
