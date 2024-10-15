# 共用變數

RELATIVE_TRIGGER_POSITIONS = { 
    # Given ego (trigger) position, return agent start positions relative to the trigger position.
    # Lat: L/S/R, Long: F/S/B | (Type, lane, road, s(road_offs), lane_offset)
    "FL-1": ("relative", -1,  0,  15,  0),
    "FS-2": ("relative",  0,  0,  15,  0),
    "FR-3": ("relative",  1,  0,  15,  0),
    "SL-4": ("relative", -1,  0,   0,  0),
    "SR-5": ("relative",  1,  0,   0,  0),
    "BL-6": ("relative", -1,  0, -15,  0),
    "BS-7": ("relative",  0,  0, -15,  0),
    "BR-8": ("relative",  1,  0, -15,  0),
    
    # Motor/Bike
    "FL-M1": ("relative",  0,  0, 15, -1.5),
    "FL-M2": ("relative", -1,  0, 15,  1.5),
    "FL-M3": ("relative", -1,  0, 15, -1.5),
    "FR-M1": ("relative",  0,  0, 15,  1.5),
    "FR-M2": ("relative",  1,  0, 15, -1.5),
    "FR-M3": ("relative",  1,  0, 15,  1.5),
    "SL-M1": ("relative",  0,  0,  0, -1.5),
    "SL-M2": ("relative", -1,  0,  0,  1.5),
    "SL-M3": ("relative", -1,  0,  0, -1.5),
    "SR-M1": ("relative",  0,  0,  0,  1.5),
    "SR-M2": ("relative",  1,  0,  0, -1.5),
    "SR-M3": ("relative",  1,  0,  0,  1.5),
    "BL-M1": ("relative",  0,  0, -15, -1.5),
    "BL-M2": ("relative", -1,  0, -15,  1.5),
    "BL-M3": ("relative", -1,  0, -15, -1.5),
    "BR-M1": ("relative",  0,  0, -15,  1.5),
    "BR-M2": ("relative",  1,  0, -15, -1.5),
    "BR-M3": ("relative",  1,  0, -15,  1.5),
}


