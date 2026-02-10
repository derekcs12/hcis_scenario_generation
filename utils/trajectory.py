import scenariogeneration.xosc as xosc

def create_NURBSTrajectoryAction(trajectory_names, loop=False):
    """
    Create a TrajectoryAction using NURBS for the given trajectory names.
    """
    # Create a TrajectoryRefAction for each trajectory and chain them
    # For simplicity, assume all trajectories are defined in a catalog
    traj_actions = []
    for traj_name in trajectory_names:
        traj_ref = xosc.CatalogReference(catalogname="TrajectoryCatalog", entryname=traj_name)
        traj_action = xosc.FollowTrajectoryAction(traj_ref, loop=loop)
        traj_actions.append(traj_action)
    # If multiple trajectories, wrap in a CompositeAction (if supported)
    if len(traj_actions) == 1:
        return traj_actions[0]
    else:
        # If OpenSCENARIO supports composite actions, use it; otherwise, return the first
        # TODO: Implement proper chaining if needed
        return traj_actions[0]
