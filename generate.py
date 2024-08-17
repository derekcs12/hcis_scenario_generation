import os
from scenariogeneration import xosc, prettyprint
from dicent_utils import *

def generate(config, company='HCISLab'):

    paramdec = parameter_Declaration(config)

    ### CatalogLocations & RoadNetwork (document:xosc.utiles)
    catalog = xosc.Catalog()
    if company == 'HCISLab':
        catalog.add_catalog("VehicleCatalog", "./Catalogs/Vehicles")
        road = xosc.RoadNetwork(roadfile="hct_6.xodr")

        # ACC controller
        egoControllerProperties = xosc.Properties()
        egoControllerProperties.add_property(name="timeGap", value="1.0")
        egoControllerProperties.add_property(name="mode", value="override")
        egoControllerProperties.add_property(name="setSpeed", value="${$Ego_Speed / 3.6}")
        egoController = xosc.Controller(name="ACCController", properties=egoControllerProperties)


    else: # ITRI
        # CatalogLocations
        catalog.add_catalog("VehicleCatalog", "../Catalogs/Vehicles")

        # RoadNetwork
        road = xosc.RoadNetwork(roadfile="../../xodr/itri/hct_6.xodr")

        #construct ego controller - ROS
        egoControllerProperties = xosc.Properties()
        egoControllerProperties.add_property(name="timeGap", value="1.0")
        egoControllerProperties.add_property(name="mode", value="override")
        egoControllerProperties.add_property(name="setSpeed", value="${$Ego_Speed / 3.6}")
        egoController = xosc.Controller(name="ROSController", properties=egoControllerProperties)



    ### Entities (document:xosc.Entities)
    entities = create_Entity(egoController, len(config['Agents']))

    step_time = xosc.TransitionDynamics(xosc.DynamicsShapes.step, xosc.DynamicsDimension.time, 0)

    ### Storyboard - Init 初始設定
    # Ego 初始化
    init = xosc.Init()
    # egoInitS = config['Ego']['Start_pos'][-1]
    egostart = xosc.TeleportAction(create_LanePosition_from_config(config['Map'],config['Ego']['Start_pos']))
    egospeed = xosc.AbsoluteSpeedAction("${$Ego_Speed / 3.6}", step_time)
    egocontl = xosc.ActivateControllerAction(lateral = "true", longitudinal = "true")
    egofinal = xosc.AcquirePositionAction(create_LanePosition_from_config(config['Map'],config['Ego']['End_pos'])) #Ego終點
    init.add_init_action('Ego', egostart)
    init.add_init_action('Ego', egospeed)
    init.add_init_action('Ego', egocontl)
    init.add_init_action('Ego', egofinal)

    # Agents 初始化
    for agentIndex, agent in enumerate(config['Agents'], start=1):
        agentStart = xosc.TeleportAction(create_LanePosition_from_config(config['Map'],agent['Start_pos'],s=f"$Agent{agentIndex}_S"))
        init.add_init_action(f"Agent{agentIndex}", agentStart)
    
    

    ### Storyboard - Event
    allEvent = []
    allManeuver = []
    for agentIndex, agent in enumerate(config['Agents'],start=1):
        agentManeuver, previousEventNames = generate_Adv_Maneuver(agentIndex, agent, config['Map'])
        allEvent.extend(previousEventNames)
        allManeuver.append(agentManeuver)
        # sb.add_maneuver(agentManeuver, f"Agent{agentIndex}")
        
    sb = xosc.StoryBoard(init, create_StopTrigger('Ego',distance=500,allEventName=allEvent))
    for man in allManeuver:
        sb.add_maneuver(man, f"Agent{allManeuver.index(i)+1}")

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

def parameter_Declaration(config):
    paramdec = xosc.ParameterDeclarations()

    ### ParameterDeclarations (document:xosc.utiles)
    egoInit  = xosc.Parameter(name="Ego_Vehicle",parameter_type="string",value="car_white")
    egoSpeed = xosc.Parameter(name="Ego_Speed",parameter_type="double",value=config['Ego']['Start_speed'])
    egoS     = xosc.Parameter(name="Ego_S",parameter_type="double",value=config['Ego']['Start_pos'][-1])
    paraList = [egoInit, egoSpeed, egoS]

    Agents = config['Agents']
    for agentIndex, agent in enumerate(Agents, start=1):

        # agent's Init parameter
        agentVehicle  = xosc.Parameter(name=f"Agent{agentIndex}_Vehicle",parameter_type="string",value="car_red")
        agentInitSpeed = xosc.Parameter(name=f"Agent{agentIndex}_Speed",parameter_type="double",value=str(agent['Start_speed']))
        agentInitS     = xosc.Parameter(name=f"Agent{agentIndex}_S",parameter_type="double",value=str(agent['Start_pos'][-1]))
        paraList.extend([agentVehicle, agentInitSpeed, agentInitS])

        # agent's Event parameter
        for actIndex, act in enumerate(agent['Acts'], start=1):
            if act['Type'] == 'zigzag':
                for eventIndex, event in enumerate(act['Events'], start=1):
                    if event['Type'] == 'offset':
                        delay = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_Deley",parameter_type="double",value=str(event['Dynamic_delay']))
                        offset = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_Offset",parameter_type="double",value=str(event['Dynamic_shape']))
                        period = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_Period",parameter_type="double",value=str(event['Dynamic_duration']))
                        times = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_Times",parameter_type="double",value=str(event['End']))
                        paraList.extend([delay, offset, period, times])
                    if event['Type'] == 'speed':
                        dynamicDelay = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_DynamicDelay",parameter_type="double",value=str(event['Dynamic_delay']))
                        dynamicDuration = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_DynamicDuration",parameter_type="double",value=str(event['Dynamic_duration']))
                        dynamicShape = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_DynamicShape",parameter_type="double",value=str(event['Dynamic_shape']))
                        endSpeed = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_EndSpeed",parameter_type="double",value=str(event['End']))
                        paraList.extend([dynamicDelay, dynamicShape, dynamicDuration, endSpeed])
            else:
                for eventIndex, event in enumerate(act['Events'], start=1):
                    if event['Type'] == 'speed':
                        endSpeed = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_{eventIndex}_EndSpeed",parameter_type="double",value=str(event['End']))
                        paraList.append(endSpeed)
                    dynamicDelay = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_{eventIndex}_DynamicDelay",parameter_type="double",value=str(event['Dynamic_delay']))
                    dynamicDuration = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_{eventIndex}_DynamicDuration",parameter_type="double",value=str(event['Dynamic_duration']))
                    dynamicShape = xosc.Parameter(name=f"Agent{agentIndex}_{actIndex}_{eventIndex}_DynamicShape",parameter_type="string",value=event['Dynamic_shape'])
                    paraList.extend([dynamicDelay, dynamicDuration, dynamicShape])

    for i in paraList:
        paramdec.add_parameter(i)
        # print(i.name, i.value)
    
    return paramdec


def create_Catalog_and_RoadNetwork():
    ...


def create_Entity(egoController, agentCount):
    # construct CatalogReference
    egoObject = xosc.CatalogReference(catalogname="VehicleCatalog", entryname="$Ego_Vehicle") #xosc.utils
    
    # Create agent object
    agentObjectList = []
    for i in range(agentCount):
        agentObject = xosc.CatalogReference(catalogname="VehicleCatalog", entryname=f"$Agent{i+1}_Vehicle")
        agentObjectList.append(agentObject)


    # create entity
    entities = xosc.Entities()
    egoName = "Ego"
    entities.add_scenario_object(name = egoName, entityobject = egoObject, controller = egoController)
    for i in range(agentCount):
        entities.add_scenario_object(name = f"Agent{i+1}", entityobject = agentObjectList[i])

    return entities


def generate_Adv_Maneuver(agentIndex, agent, Map):
    advManeuver = xosc.Maneuver(f"Adv{agentIndex}_Maneuver")
    agentStartEvent = generate_Agent_Start_Event(agentIndex, agent, Map)
    advManeuver.add_event(agentStartEvent)
    previousEventName = [agentStartEvent.name]
    currentPosition = agent['Start_pos']


    for actIndex, act in enumerate(agent['Acts'], start=1):
        currentEventName = []
        if act['Type'] == 'zigzag':
            ...
        else:
            for eventIndex, event in enumerate(act['Events'], start=1):
                if event['Type'] == 'speed':
                    currentEvent = generate_Speed_Event(agentIndex, actIndex, eventIndex, event, previousEventName)
                elif event['Type'] == 'offset':
                    currentEvent, currentPosition = generate_Offset_Event(agentIndex, actIndex, eventIndex, event, previousEventName, currentPosition)
                elif event['Type'] == 'cut':
                    currentEvent, currentPosition = generate_Cut_Event(agentIndex, actIndex, eventIndex, event, previousEventName, currentPosition)
                elif event['Type'] == 'position':
                    currentEvent , currentPosition = generate_Position_Event(agentIndex, actIndex, event, Map, previousEventName ,currentPosition)
                else:
                    print('Event Type Error')
                    break
                # previousEventName = currentEvent.name
                currentEventName.append(currentEvent.name)
                advManeuver.add_event(currentEvent)
            previousEventName = currentEventName


    return advManeuver, previousEventName
