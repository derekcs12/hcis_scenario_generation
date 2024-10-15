import os
from scenariogeneration import xosc, prettyprint
from dicent_utils import *

def generate(config, company='HCISLab'):

    Actors = config['Actors']
    paramdec = parameter_Declaration(Actors, config['Ego'])

    ### CatalogLocations & RoadNetwork (document:xosc.utiles)
    catalog = xosc.Catalog()
    if company == 'HCISLab':
        catalog.add_catalog("VehicleCatalog", "./Catalogs/Vehicles")
        if 'Pedestrians' in Actors:
            catalog.add_catalog("PedestrianCatalog", "./Catalogs/Pedestrians")
        road = xosc.RoadNetwork(roadfile="hct_6.xodr")

        # ACC controller
        controllerName = "ACCController"

    else: # ITRI
        # CatalogLocations
        catalog.add_catalog("VehicleCatalog", "../Catalogs/Vehicles")
        if 'Pedestrians' in Actors:
            catalog.add_catalog("PedestrianCatalog", "../Catalogs/Pedestrians")

        # RoadNetwork
        road = xosc.RoadNetwork(roadfile="../../xodr/itri/hct_6.xodr")

        # construct ego controller - ROS
        controllerName = "ROSController"
    
    egoControllerProperties = xosc.Properties()
    egoControllerProperties.add_property(name="timeGap", value="1.0")
    egoControllerProperties.add_property(name="mode", value="override")
    egoControllerProperties.add_property(name="setSpeed", value="${$Ego_Speed / 3.6}")
    egoController = xosc.Controller(name=controllerName, properties=egoControllerProperties)


    ### Entities (document:xosc.Entities)
    agentCount = len(Actors['Agents']) if 'Agents' in Actors else 0
    pedCount = len(Actors['Pedestrians']) if 'Pedestrians' in Actors else 0
    entities = create_Entity(egoController, agentCount, pedCount)

    step_time = xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0)

    ### Storyboard - Init 初始設定
    # Ego 初始化
    init = xosc.Init()
    egostart = xosc.TeleportAction(create_LanePosition_from_config(config['Map'],config['Ego']['Start_pos']))
    egospeed = xosc.AbsoluteSpeedAction("${$Ego_Speed / 3.6}", step_time)
    # activate_controller = 'false' if config['DeactivateControl'] else 'true'
    activate_controller = 'true'
    egocontl = xosc.ActivateControllerAction(lateral = activate_controller, longitudinal = activate_controller)
    egofinal = xosc.AcquirePositionAction(create_LanePosition_from_config(config['Map'],config['Ego']['End_pos'])) #Ego終點
    init.add_init_action('Ego', egostart)
    init.add_init_action('Ego', egospeed)
    init.add_init_action('Ego', egocontl)
    init.add_init_action('Ego', egofinal)

    # Actor 初始化
    for cata in Actors:
        for actorIndex, actor in enumerate(Actors[cata], start=1):
            actorStart = xosc.TeleportAction(create_LanePosition_from_config(config['Map'],actor['Start_pos'],s=f"${cata[:-1]}{actorIndex}_S"))
            init.add_init_action(f"{cata[:-1]}{actorIndex}", actorStart)

    ### Storyboard - Event
    allEvent = []
    allManeuver = {}
    for actors in Actors:
        for actorIndex, actor in enumerate(Actors[actors],start=1):
            actorName = f"{actors[:-1]}{actorIndex}"
            agentManeuver, previousEventNames = generate_Adv_Maneuver(actorName, actor, config['Map'])
            if agentManeuver is not None:
                allEvent.extend(previousEventNames)
                allManeuver[actorName] = agentManeuver
    

    sb = xosc.StoryBoard(init, create_StopTrigger('Ego',distance=500, allEventName=allEvent))
    for man in allManeuver:
        sb.add_maneuver(allManeuver[man], man)

    ### Create Scenario
    sce = xosc.Scenario( 
        name="hct_"+config['Scenario_name'],
        author="HCIS_ChengYuSheng",
        parameters = paramdec,
        entities=entities,
        storyboard=sb,
        roadnetwork=road,
        catalog=catalog,
        osc_minor_version=0
    )

    return sce

def parameter_Declaration(Actors, Ego):
    paramdec = xosc.ParameterDeclarations()

    ### ParameterDeclarations (document:xosc.utiles)
    egoInit  = xosc.Parameter(name="Ego_Vehicle",parameter_type="string",value="car_white")
    egoSpeed = xosc.Parameter(name="Ego_Speed",parameter_type="double",value=Ego['Start_speed'])
    egoS     = xosc.Parameter(name="Ego_S",parameter_type="double",value=Ego['Start_pos'][2])
    paraList = [egoInit, egoSpeed, egoS]

    # catas = ['Agents', 'Pedestrians']
    for cata in Actors:
        for actorIndex, actor in enumerate(Actors[cata], start=1):
            actorName = f"{cata[:-1]}{actorIndex}"
            # actor's Init parameter
            actorType  = xosc.Parameter(name=f"{actorName}_Type",parameter_type="string",value=actor['Type'])
            actorInitSpeed = xosc.Parameter(name=f"{actorName}_Speed",parameter_type="double",value=str(actor['Start_speed']))
            actorInitS     = xosc.Parameter(name=f"{actorName}_S",parameter_type="double",value=str(actor['Start_pos'][2]))
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
                            delay = xosc.Parameter(name=f"{actorName}_{actIndex}_Delay",parameter_type="double",value=str(event['Dynamic_delay']))
                            offset = xosc.Parameter(name=f"{actorName}_{actIndex}_TA_Offset",parameter_type="double",value=str(event['Dynamic_shape']))
                            period = xosc.Parameter(name=f"{actorName}_{actIndex}_TA_Period",parameter_type="double",value=str(event['Dynamic_duration']))
                            times = xosc.Parameter(name=f"{actorName}_{actIndex}_TA_Times",parameter_type="double",value=str(event['Use_route']))
                            paraList.extend([delay, offset, period, times])
                        if event['Type'] == 'speed':
                            dynamicDelay = xosc.Parameter(name=f"{actorName}_{actIndex}_SA_DynamicDelay",parameter_type="double",value=str(event['Dynamic_delay']))
                            dynamicDuration = xosc.Parameter(name=f"{actorName}_{actIndex}_SA_DynamicDuration",parameter_type="double",value=str(event['Dynamic_duration']))
                            dynamicShape = xosc.Parameter(name=f"{actorName}_{actIndex}_SA_DynamicShape",parameter_type="double",value=str(event['Dynamic_shape']))
                            endSpeed = xosc.Parameter(name=f"{actorName}_{actIndex}_SA_EndSpeed",parameter_type="double",value=str(event['End']))
                            paraList.extend([dynamicDelay, dynamicShape, dynamicDuration, endSpeed])
                else:
                    for eventIndex, event in enumerate(act['Events'], start=1):
                        actionName = 'TA'
                        if event['Type'] == 'speed':
                            actionName = 'SA'
                            endSpeed = xosc.Parameter(name=f"{actorName}_{actIndex}_{actionName}_EndSpeed",parameter_type="double",value=str(event['End']))
                            paraList.append(endSpeed)
                        dynamicDelay = xosc.Parameter(name=f"{actorName}_{actIndex}_{actionName}_DynamicDelay",parameter_type="double",value=str(event['Dynamic_delay']))
                        dynamicDuration = xosc.Parameter(name=f"{actorName}_{actIndex}_{actionName}_DynamicDuration",parameter_type="double",value=str(event['Dynamic_duration']))
                        dynamicShape = xosc.Parameter(name=f"{actorName}_{actIndex}_{actionName}_DynamicShape",parameter_type="string",value=event['Dynamic_shape'])
                        paraList.extend([dynamicDelay, dynamicDuration, dynamicShape])

    for i in paraList:
        paramdec.add_parameter(i)
    
    return paramdec


def create_Catalog_and_RoadNetwork():
    ...


def create_Entity(egoController, agentCount, pedCount):
    # construct CatalogReference
    egoObject = xosc.CatalogReference(catalogname="VehicleCatalog", entryname="$Ego_Vehicle") #xosc.utils
    
    # Create agent object
    agentObjectList = []
    for i in range(agentCount):
        agentObject = xosc.CatalogReference(catalogname="VehicleCatalog", entryname=f"$Agent{i+1}_Type")
        agentObjectList.append(agentObject)

    # Create Pedestrian object
    pedObjectList = []
    for i in range(pedCount):
        pedObject = xosc.CatalogReference(catalogname="PedestrianCatalog", entryname=f"$Pedestrian{i+1}_Type")
        pedObjectList.append(pedObject)


    # create entity
    entities = xosc.Entities()

    # ego
    entities.add_scenario_object(name = "Ego", entityobject = egoObject, controller = egoController)

    # agents
    for i in range(agentCount):
        entities.add_scenario_object(name = f"Agent{i+1}", entityobject = agentObjectList[i])
        
    # pedestrians
    for i in range(pedCount):
        entities.add_scenario_object(name = f"Pedestrian{i+1}", entityobject = pedObjectList[i])

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
        dummyEvent = create_Dummy_Event(actorName ,actIndex,act['Delay'],previousEventName)
        advManeuver.add_event(dummyEvent)
        previousEventName = [dummyEvent.name]

        currentEventName = []
        if act['Type'] == 'zigzag':
            for eventIndex, event in enumerate(act['Events'], start=1):
                if event['Type'] == 'speed':
                    currentEvent = generate_Speed_Event(actorName, actIndex, 'SA', event, previousEventName,type='zigzag')
                    currentEventName.append(currentEvent.name)
                    advManeuver.add_event(currentEvent)

                elif event['Type'] == 'offset':
                    zigzagEvent, currentPosition = generate_Zigzag_Event(actorName, actIndex, event, Map,previousEventName, currentPosition) 
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
                    currentEvent = generate_Speed_Event(actorName, actIndex, 'SA', event, previousEventName)
                elif event['Type'] == 'offset':
                    currentEvent, currentPosition = generate_Offset_Event(actorName, actIndex, 'TA', event, previousEventName, currentPosition)
                elif event['Type'] == 'cut':
                    currentEvent, currentPosition = generate_Cut_Event(actorName, actIndex, 'TA', event, previousEventName, currentPosition)
                elif event['Type'] == 'position':
                    currentEvent , _ = generate_Position_Event(actorName, actIndex, event, Map, previousEventName ,currentPosition)
                else:
                    print('Event Type Error')
                    break

                currentEventName.append(currentEvent.name)
                advManeuver.add_event(currentEvent)
            previousEventName = currentEventName

    return advManeuver, previousEventName
