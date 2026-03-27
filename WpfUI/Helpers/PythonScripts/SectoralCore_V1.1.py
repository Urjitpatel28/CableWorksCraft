import FreeCAD as App
import FreeCADGui as Gui
import Part
import math
from math import pi, radians, cos, sin, floor

import argparse
import json
import sys
import logging
import os
import random
from PySide2.QtWidgets import QMessageBox

# Try to import a Qt binding (prefer PySide; if not available, use PyQt5)
try:
    from PySide2 import QtCore
except ImportError:
    from PySide2 import QtCore
##############################################################################
# LOGGING SETUP
##############################################################################
def setup_logger(log_file_path):
    """
    Configures the logger to write to the file specified by log_file_path.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers (if rerunning in the same session)
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create file handler
    fh = logging.FileHandler(log_file_path, mode='w')
    fh.setLevel(logging.DEBUG)
    
    # Create console handler (optional, can set a different level)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Create a common format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

##############################################################################
# 1) CREATE HOLLOW CONDUCTOR MODEL
##############################################################################
def create_hollow_conductor_model(wireColor,conductor_radius, small_cylinder_radius, cylinder_height, num_levels):
    """
    Creates a hollow conductor model by placing small cylinders in a circular
    pattern from the center out to the specified conductor radius.
    """
    doc = App.newDocument("SECTORAL SHAPED CABLE")
    
    cylinders = []  # To keep track of created cylinders for interference checks
    for level in range(num_levels + 1):
        level_radius = level * 2 * small_cylinder_radius
        if level_radius < conductor_radius - small_cylinder_radius:
            if level == 0:
                num_cylinders_in_level = 1
            else:
                num_cylinders_in_level = int(2 * math.pi * level_radius / (2 * small_cylinder_radius))

            if num_cylinders_in_level > 0:
                angle_step = 2 * math.pi / num_cylinders_in_level
                for i in range(num_cylinders_in_level):
                    angle = i * angle_step
                    x = level_radius * math.cos(angle)
                    y = level_radius * math.sin(angle)
                    small_cylinder = Part.makeCylinder(small_cylinder_radius, cylinder_height, App.Vector(x, y, 0))
                    cylinder_obj = doc.addObject("Part::Feature", f"Wires_{i+1}")
                    cylinder_obj.Shape = small_cylinder
                    cylinder_obj.ViewObject.ShapeColor = tuple(wireColor)
                    cylinders.append(cylinder_obj)
    
    doc.recompute()
    return doc, cylinders

def create_dual_outersheath(
    doc,
    outercolor1,
    outercolor2,
    outer_diameter,
    inner_diameter,
    h,
    strip_start_angle=150,   # degrees CCW from +X
    strip_end_angle=210,     # e.g., 150..210 puts it on the LEFT side
    strip_z_offset=0,
    name="Outersheath"
):
    import FreeCAD as App
    import Part

    R_out = outer_diameter / 2.0
    R_in  = inner_diameter / 2.0

    # Full hollow cylinder (the main outer sheath base)
    outer_full = Part.makeCylinder(R_out, h)
    inner_full = Part.makeCylinder(R_in,  h)
    hollow_full = outer_full.cut(inner_full)

    # Normalize angle width (supports wrap-around, e.g. 330..30)
    ang_width = (strip_end_angle - strip_start_angle) % 360
    if ang_width == 0:
        raise ValueError("strip_start_angle and strip_end_angle define 0° width.")

    # Build an annular sector for the strip:
    # 1) make outer sector and inner sector with ang_width
    outer_sector = Part.makeCylinder(R_out, h, App.Vector(0,0,0), App.Vector(0,0,1), ang_width)
    inner_sector = Part.makeCylinder(R_in,  h, App.Vector(0,0,0), App.Vector(0,0,1), ang_width)

    # 2) rotate both by strip_start_angle so the sector begins there
    for s in (outer_sector, inner_sector):
        s.rotate(App.Vector(0,0,0), App.Vector(0,0,1), float(strip_start_angle))

    # 3) annular sector (the colored strip body)
    strip_sleeve = outer_sector.cut(inner_sector)

    # Optional vertical shift
    if strip_z_offset:
        strip_sleeve.translate(App.Vector(0,0,strip_z_offset))

    # Remaining main body = hollow sheath MINUS strip
    main_body = hollow_full.cut(strip_sleeve)

    # Add to document
    strip_obj = doc.addObject("Part::Feature", "_Outersheathstrip")
    strip_obj.Shape = strip_sleeve
    strip_obj.ViewObject.ShapeColor = tuple(outercolor1)

    main_obj = doc.addObject("Part::Feature", name)
    main_obj.Shape = main_body
    main_obj.ViewObject.ShapeColor = tuple(outercolor2)

    doc.recompute()
    return strip_obj, main_obj

##############################################################################
# Function to apply fillets to vertical edges
##############################################################################
def add_fillets_to_cylinder(cylinder, fillet_radius):
    """
    Apply fillets to vertical edges of a cylinder. Checks edge suitability more thoroughly.
    """
    vertical_edges = []
    for edge in cylinder.Edges:
        # Ensure the edge is linear and vertical
        if edge.Curve.TypeId == 'Part::GeomLine':
            v1, v2 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
            if v1.x == v2.x and v1.y == v2.y:  # Confirm edge is vertical
                if abs(v1.z - v2.z) > 0.1:  # Check if the edge has a minimal length for filleting
                    vertical_edges.append(edge)
    
    if vertical_edges:
        try:
            modified_cylinder = cylinder.makeFillet(fillet_radius, vertical_edges)
            logging.info("Fillet applied successfully.")
            return modified_cylinder
        except Part.OCCError as e:
            logging.error(f"Failed to apply fillet: {e}")
            return cylinder
    else:
        logging.warning("No suitable vertical edges found for filleting.")
        return cylinder

##############################################################################
# Function to delete cylinders that interfere with any other objects
##############################################################################
def delete_interfering_cylinders(doc, cylinders, threshold_distance=0.1):
    to_delete = []

    for i, cylinder in enumerate(cylinders):
        for other_obj in doc.Objects:
            if other_obj is not cylinder:
                # If there's a common volume, they intersect
                if cylinder.Shape.common(other_obj.Shape).Area > 0:
                    to_delete.append(cylinder)
                    break
    
    for obj in to_delete:
        doc.removeObject(obj.Name)

    doc.recompute()


def delete_interfering_cylinders_na(doc, cylinders, threshold_distance=0.1):
    to_delete = []

    # Precompute bounding boxes for all document objects with a valid shape.
    bbox_cache = {}
    for obj in doc.Objects:
        if hasattr(obj, "Shape") and not obj.Shape.isNull():
            bbox_cache[obj.Name] = obj.Shape.BoundBox

    # Helper function to check if two bounding boxes intersect.
    def bbox_intersect(b1, b2):
        return not (
            b1.XMax < b2.XMin or b1.XMin > b2.XMax or
            b1.YMax < b2.YMin or b1.YMin > b2.YMax or
            b1.ZMax < b2.ZMin or b1.ZMin > b2.ZMax
        )

    for cylinder in cylinders:
        cyl_shape = cylinder.Shape
        cyl_bbox = bbox_cache.get(cylinder.Name, cyl_shape.BoundBox)
        for other_obj in doc.Objects:
            if other_obj is cylinder:
                continue
            if not (hasattr(other_obj, "Shape") and not other_obj.Shape.isNull()):
                continue

            # Retrieve the other object's bounding box from cache.
            other_bbox = bbox_cache.get(other_obj.Name)
            if other_bbox is None:
                other_bbox = other_obj.Shape.BoundBox
                bbox_cache[other_obj.Name] = other_bbox

            # Quick bounding box check: if they do not intersect, skip.
            if not bbox_intersect(cyl_bbox, other_bbox):
                continue

            # Only if bounding boxes intersect, compute the common shape.
            common_shape = cyl_shape.common(other_obj.Shape)
            # If the common shape's area exceeds the threshold, mark the cylinder for deletion.
            if common_shape.Area > threshold_distance:
                to_delete.append(cylinder)
                break

    for obj in to_delete:
        doc.removeObject(obj.Name)

    doc.recompute()

##############################################################################
# 2) PLACE CIRCLES OF A FIXED DIAMETER
##############################################################################
def place_circles_of_fixed_diameter(
    doc,
    existing_circles,
    boundary_radius,
    circle_diameter,
    tries=80000,
    filler_height=50.0
):
    """
    Try to place as many circles of 'circle_diameter' in leftover space
    within boundary_radius, by random sampling for center positions.

    existing_circles: list of (x_center, y_center, radius)
    boundary_radius:  bounding circle radius
    tries: number of random attempts
    """
    import math

    r_fixed = circle_diameter / 2.0
    all_circles = list(existing_circles)
    placed_count = 0

    for _ in range(tries):
        angle = 2 * math.pi * random.random()
        rr = boundary_radius * math.sqrt(random.random())  # uniform area
        x_new = rr * math.cos(angle)
        y_new = rr * math.sin(angle)

        # boundary check
        dist_center = math.hypot(x_new, y_new)
        if dist_center + r_fixed > boundary_radius:
            continue

        # overlap check
        overlap = False
        for (cx, cy, cr) in all_circles:
            dist_ij = math.hypot(cx - x_new, cy - y_new)
            if dist_ij < (cr + r_fixed):
                overlap = True
                break

        if not overlap:
            # place
            pos = App.Vector(x_new, y_new, 0)
            cobj = Part.makeCylinder(r_fixed, filler_height, pos)
            doc_obj = doc.addObject("Part::Feature", f"Filler_{circle_diameter:.1f}_{placed_count+1}")
            doc_obj.Shape = cobj
            doc.recompute()

            all_circles.append((x_new, y_new, r_fixed))
            placed_count += 1

    print(f"[place_circles_of_fixed_diameter] Placed {placed_count} of diameter {circle_diameter}")
    return all_circles

##############################################################################
# 3) MULTI-SWEEP: FILL WITH DISCRETE DIAMETERS FROM LARGEST TO SMALLEST
##############################################################################
def fill_with_discrete_sweeps(
    doc,
    existing_circles,
    boundary_radius,
    diameters_desc=[30, 20, 10, 5, 0.1],
    tries_per_size=80000,
    filler_height=50.0
):
    """
    For each diameter in diameters_desc, place as many circles of that diameter
    as possible. Then return the final circle list.
    """
    all_circles = list(existing_circles)
    for d in diameters_desc:
        print(f"\n===== FILLING with diameter={d} =====")
        all_circles = place_circles_of_fixed_diameter(
            doc=doc,
            existing_circles=all_circles,
            boundary_radius=boundary_radius,
            circle_diameter=d,
            tries=tries_per_size,
            filler_height=filler_height
        )
    return all_circles

##############################################################################
# 4) BUBBLE PACK (MOVE ONLY), DOES NOT GROW (unused in main but retained)
##############################################################################
def bubble_pack_circles_no_grow(
    circles,
    boundary_radius,
    max_passes=50,
    step_size=0.001
):
    """
    Moves circles to reduce overlaps & boundary breach,
    but does not allow any radius growth => keeps discrete diameters.
    """
    import math

    cdata = list(circles)
    for pass_i in range(max_passes):
        changed = False
        new_data = []
        for i, (x_i, y_i, r_i) in enumerate(cdata):
            net_dx = 0.0
            net_dy = 0.0

            dist_center = math.hypot(x_i, y_i)
            if dist_center + r_i > boundary_radius:
                overlap = (dist_center + r_i) - boundary_radius
                nx = x_i / (dist_center + 1e-9)
                ny = y_i / (dist_center + 1e-9)
                net_dx -= nx * overlap
                net_dy -= ny * overlap

            for j, (x_j, y_j, r_j) in enumerate(cdata):
                if i == j:
                    continue
                dx = x_i - x_j
                dy = y_i - y_j
                dist_ij = math.hypot(dx, dy)
                if dist_ij < 1e-9:
                    continue
                ideal_dist = r_i + r_j
                if dist_ij < ideal_dist:
                    overlap = ideal_dist - dist_ij
                    nx = dx / dist_ij
                    ny = dy / dist_ij
                    net_dx += nx * overlap * 0.5
                    net_dy += ny * overlap * 0.5

            if abs(net_dx) > 1e-12 or abs(net_dy) > 1e-12:
                x_new = x_i + net_dx * step_size
                y_new = y_i + net_dy * step_size
                changed = True
            else:
                x_new = x_i
                y_new = y_i

            new_data.append((x_new, y_new, r_i))

        cdata = new_data
        if not changed:
            print(f"[bubble_pack_circles_no_grow] pass={pass_i}, no changes => done")
            break
        elif pass_i % 10 == 0:
            print(f"[bubble_pack_circles_no_grow] pass={pass_i} in progress...")

    return cdata

##############################################################################
# Helper to recreate discrete cylinders after bubble-pack (unused in main)
##############################################################################
def recreate_discrete_cylinders(doc, circle_data, height=50.0, prefix="DiscreteMoved_"):
    to_remove = []
    for obj in doc.Objects:
        if obj.Name.startswith("Filler_") or obj.Name.startswith("DiscreteMoved_"):
            to_remove.append(obj.Name)

    for nm in to_remove:
        doc.removeObject(nm)

    for idx, (cx, cy, rr) in enumerate(circle_data):
        pos = App.Vector(cx, cy, 0)
        cobj = Part.makeCylinder(rr, height, pos)
        new_obj = doc.addObject("Part::Feature", f"{prefix}{idx+1}")
        new_obj.Shape = cobj

    doc.recompute()
##############################################################################
# Load JSON
##############################################################################
def load_json_data(json_file):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not parse JSON file: {e}")
        sys.exit(1)
    return data

def parse_color(color_str):
    # Remove any parentheses and whitespace, then split by comma
    s = color_str.strip().strip("()")
    return tuple(float(x.strip()) for x in s.split(','))
##############################################################################
# Extract parameters
##############################################################################
def get_parameters_from_json(data):
    """
    Adjusted to allow "outputFile" and "logFile" to be specified outside the 
    "parameters" object. The expected JSON structure is:

    {
      "parameters": {
         "conductor_radius": 7,
         "wire_radius": 0.5,
         "full_radius": 7,
         "numCylindersPerLayer": 3.0,
         "fillet_radius": 2,
         "offset_radius1": 5,
         "offset_radius2": 6,
         "preinnersheaththickness": 1.0,
         "innersheaththickness": 2.0,
         "overinnersheaththickness": 3.0,
         "armor_choice": "1",
         "cylinder_radius": 0.3,
         "side_length": 0.7,
         "side_thickness": 0.05,
         "armortapingthickness": 0.5,
         "outersheaththickness": 1.0     
      },
      "outputFile": "C:/Temp/CableConfigurator/myCable.FCStd",
      "logFile": "C:/Temp/CableConfigurator/myCable.log"
    }
    """
    if "parameters" not in data:
        print("ERROR: JSON must contain a top-level 'parameters' key.")
        sys.exit(1)
    
    params = data["parameters"]

    # List the keys required in the "parameters" section.
    required_keys = [
        "conductor_radius",
        "wire_radius",
        "full_radius",
        "offset_radius1",
        "offset_radius2",
        "numCylindersPerLayer",
        "fillet_radius",
        "preinnersheaththickness",
        "innersheaththickness",
        "overinnersheaththickness",
        "cylinder_radius",
        "side_length",
        "side_thickness",
        "armortapingthickness",
        "outersheaththickness",
    ]

    for key in required_keys:
        if key not in params:
            print(f"ERROR: JSON 'parameters' object must contain the key '{key}'.")
            sys.exit(1)

    # For outputFile and logFile, try first from the parameters object,
    # then fall back to the top-level JSON.
    output_file = params.get("outputFile", data.get("outputFile"))
    log_file = params.get("logFile", data.get("logFile"))

    if output_file is None:
        print("ERROR: JSON must contain an 'outputFile' key either in 'parameters' or at the top level.")
        sys.exit(1)
    if log_file is None:
        print("ERROR: JSON must contain a 'logFile' key either in 'parameters' or at the top level.")
        sys.exit(1)

    return {
        "conductor_radius":          float(params["conductor_radius"]),
        "wire_radius":               float(params["wire_radius"]),
        "offset_radius1":            float(params["offset_radius1"]),
        "offset_radius2":            float(params["offset_radius2"]),
        "full_radius":               float(params["full_radius"]),
        "numCylindersPerLayer":      float(params["numCylindersPerLayer"]),
        "fillet_radius":             float(params["fillet_radius"]),
        "preinnersheaththickness":   float(params["preinnersheaththickness"]),
        "innersheaththickness":      float(params["innersheaththickness"]),
        "overinnersheaththickness":  float(params["overinnersheaththickness"]),
        "armor_choice":              str(params.get("armor_choice", "0")), 
        "cylinder_radius":           float(params.get("cylinder_radius", 0)),
        "side_length":               float(params["side_length"]),
        "side_thickness":            float(params["side_thickness"]),
        "armortapingthickness":      float(params["armortapingthickness"]),
        "outersheaththickness":      float(params["outersheaththickness"]),
        "outputFile":                str(output_file),
        "logFile":                   str(log_file),
        "conductorScreenColor":     parse_color(params.get("conductorScreenColor", "(0.8, 0.8, 0.8)")),
        "insulationColor":          parse_color(params.get("insulationColor", "(0.8, 0.8, 0.8)")),
        "nometallicScreenColor":    parse_color(params.get("nometallicScreenColor", "(0.8, 0.8, 0.8)")),
        "wireColor":                parse_color(params.get("wireColor", "(0.8, 0.8, 0.8)")),
        "preinnersheathcolor":      parse_color(params.get("preinnersheathcolor", "(0.8, 0.8, 0.8)")),
        "innersheathcolor":         parse_color(params.get("innersheathcolor", "(0.8, 0.8, 0.8)")),
        "overinnersheathcolor":     parse_color(params.get("overinnersheathcolor", "(0.8, 0.8, 0.8)")),
        "armorcolor":               parse_color(params.get("armorcolor", "(0.8, 0.8, 0.8)")),
        "armortapingcolor":         parse_color(params.get("armortapingcolor", "(0.8, 0.8, 0.8)")),
        "outersheathcolor":         parse_color(params.get("outersheathcolor", "(0.8, 0.8, 0.8)")),
        "printingMatter":           params.get("printingMatter", ""),
        "condscreencolor1":parse_color(params.get("condscreencolor1", "(0.8, 0.8, 0.8)")), 
        "condscreencolor2":parse_color(params.get("condscreencolor2", "(0.8, 0.8, 0.8)")), 
        "condscreencolor3":parse_color(params.get("condscreencolor3", "(0.8, 0.8, 0.8)")), 
        "condscreencolor4":parse_color(params.get("condscreencolor4", "(0.8, 0.8, 0.8)")), 
        "condscreencolor5":parse_color(params.get("condscreencolor5", "(0.8, 0.8, 0.8)")), 
        # "insscreencolor1":parse_color(params.get("insscreencolor1", "(0.8, 0.8, 0.8)")), 
        # "insscreencolor2":parse_color(params.get("insscreencolor2", "(0.8, 0.8, 0.8)")), 
        # "insscreencolor3":parse_color(params.get("insscreencolor3", "(0.8, 0.8, 0.8)")), 
        # "insscreencolor4":parse_color(params.get("insscreencolor4", "(0.8, 0.8, 0.8)")), 
        # "insscreencolor5":parse_color(params.get("insscreencolor5", "(0.8, 0.8, 0.8)")), 
        "fraccondscreencolor":parse_color(params.get("fraccondscreencolor", "(0.8, 0.8, 0.8)")), 
        #"fracinsscreencolor":parse_color(params.get("fracinsscreencolor", "(0.8, 0.8, 0.8)")), 
        "outercolorchoice" : float(params["outercolorchoice"]),
        "oangle" : float(params["oangle"]),
        "outercolor1": parse_color(params.get("outercolor1", "(0.8, 0.8, 0.8)")),
        "outercolor2" : parse_color(params.get("outercolor2", "(0.0, 0.0, 0.0)")),
    }

##############################################################################
# MAIN FUNCTION
##############################################################################
def main():
    # 1) Parse command-line argument for JSON file
    parser = argparse.ArgumentParser(description="Cable configuration script")
    parser.add_argument('--jsonFile', required=True, help="Path to input JSON")
    args = parser.parse_args()

    # 2) Load JSON data
    json_file_path = args.jsonFile
    if not os.path.isfile(json_file_path):
        print(f"ERROR: JSON file does not exist at {json_file_path}")
        sys.exit(1)

    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not parse JSON file: {e}")
        sys.exit(1)

    # 3) Extract parameters using our helper function.
    params = get_parameters_from_json(data)

    # 4) Setup logger using the logFile (from either parameters or top-level).
    logger = setup_logger(params["logFile"])
    logger.info("Starting Cable Configuration Script...")

    try:
        # --------------------------------------------------------------------
        # Retrieve parameters from JSON (values already converted)
        # --------------------------------------------------------------------
        conductor_radius       = params["conductor_radius"]
        small_cylinder_radius  = params["wire_radius"]

        # Hard-coded values you do not want to change:
        cylinder_height = 50
        num_levels      = int(conductor_radius/small_cylinder_radius)

        full_radius     = params["full_radius"]
        sectors         = params["numCylindersPerLayer"]
        fillet_radius   = 0.2
        offset_radius1  = params["offset_radius1"]
        offset_radius2  = params["offset_radius2"]
        thk1 =full_radius-offset_radius2
        thk2 = offset_radius2-offset_radius1 

        # Another hard-coded factor used in your original code:
        height_factor   = 40
        height          = full_radius * height_factor
        increment =2*  full_radius

        preinnersheaththickness  = params["preinnersheaththickness"]
        innersheaththickness     = params["innersheaththickness"]
        overinnersheaththickness = params["overinnersheaththickness"]
        armor_choice             = params.get("armor_choice", 1)

        circular_armor_params = params.get("cylinder_radius",0)  # for circular armor
        cubical_armor_params  = params["side_length"]        # for cubical armor

        armortapingthickness  = params["armortapingthickness"]
        outersheaththickness  = params["outersheaththickness"]

        conductorScreenColor=params.get("conductorScreenColor", (0.8,0.8,0.8))
        insulationColor=params.get("insulationColor", (0.8,0.8,0.8))
        wireColor=params.get("wireColor", (0.8,0.8,0.8))
        preinnersheathcolor=params.get("preinnersheathcolor", (0.8,0.8,0.8))
        innersheathcolor=params.get("innersheathcolor", (0.8,0.8,0.8))
        overinnersheathcolor=params.get("overinnersheathcolor", (0.8,0.8,0.8))
        armorcolor=params.get("armorcolor", (0.8,0.8,0.8))
        armortapingcolor=params.get("armortapingcolor", (0.8,0.8,0.8))
        outersheathcolor=params.get("outersheathcolor", (0.0,0.0,0.0))    
        condscreencolor1=params.get("condscreencolor1", (0.8,0.8,0.8)) 
        condscreencolor2 =  params.get("condscreencolor2", (0.8,0.8,0.8))
        condscreencolor3 =  params.get("condscreencolor3", (0.8,0.8,0.8))
        condscreencolor4 =  params.get("condscreencolor4", (0.8,0.8,0.8))
        condscreencolor5 =  params.get("condscreencolor5", (0.8,0.8,0.8))
        # insscreencolor1 =  params.get("insscreencolor1", (0.8,0.8,0.8))
        # insscreencolor2 =  params.get("insscreencolor2", (0.8,0.8,0.8))
        # insscreencolor3 =  params.get("insscreencolor3", (0.8,0.8,0.8))
        # insscreencolor4 =  params.get("insscreencolor4", (0.8,0.8,0.8))
        # insscreencolor5 =  params.get("insscreencolor5", (0.8,0.8,0.8)) 
        fraccondscreencolor =  params.get("fraccondscreencolor", (0.8,0.8,0.8))
        #fracinsscreencolor =  params.get("fracinsscreencolor", (0.8,0.8,0.8))
        printingMatter  = params.get("printingMatter", "")
        # Hard-coded value you do not want to change:
        tries_per_size = 80000

        # Optional keys, retrieved with .get() if needed:
        save_file_path = params["outputFile"]

        logger.info("All parameters successfully read from JSON.")

        # --------------------------------------------------------------------
        # 1) CREATE THE WIRES (CONDUCTOR MODEL)
        # --------------------------------------------------------------------
        doc, cylinders = create_hollow_conductor_model(wireColor,
            conductor_radius=conductor_radius,
            small_cylinder_radius=small_cylinder_radius,
            cylinder_height=height,
            num_levels=num_levels
        )

        # Define parameters for sectors
        int_sectors = floor(sectors) 
        sector_angle = 360 / sectors
        fractional_sector_angle = (sectors - int_sectors) * sector_angle
        main_cores_info = []
        tempheight = height
        # Create the full cylinder and apply fillets
        full_cylinder = Part.makeCylinder(full_radius, height)
        full_cylinder = add_fillets_to_cylinder(full_cylinder, fillet_radius)

        QtCore.QCoreApplication.processEvents()
        # Build sectors
        for i in range(int_sectors):
            height = tempheight
            import FreeCAD
            sector = Part.makeCylinder(full_radius, height-2*increment,
                                       FreeCAD.Vector(0, 0, 0),
                                       FreeCAD.Vector(0, 0, 1),
                                       360 / sectors)
            sector = add_fillets_to_cylinder(sector, fillet_radius)
            rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), (360 / sectors) * i)
            sector.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), rotation)
            
            x_offset1 = 0  # or some appropriate default
            y_offset1 = 0
            if thk2!=0:
                height = height - increment
                offset_cylinder2 = Part.makeCylinder(offset_radius2, height,
                                                     FreeCAD.Vector(0, 0, 0),
                                                     FreeCAD.Vector(0, 0, 1),
                                                     360 / sectors)
                offset_cylinder2 = add_fillets_to_cylinder(offset_cylinder2, fillet_radius)
                angle_offset2 = (360 / sectors * i) + (360 / sectors / 2)
                x_offset2 = ((full_radius - offset_radius2) / 2) * cos(radians(angle_offset2))
                y_offset2 = ((full_radius - offset_radius2) / 2) * sin(radians(angle_offset2))
                offset_position2 = FreeCAD.Vector(x_offset2, y_offset2, 0)
                offset_cylinder2.Placement = FreeCAD.Placement(offset_position2, rotation)
                offset_cylinder1 = Part.makeCylinder(offset_radius1, height+1,
                                                     FreeCAD.Vector(0, 0, 0),
                                                     FreeCAD.Vector(0, 0, 1),
                                                     360 / sectors)
                offset_cylinder1 = add_fillets_to_cylinder(offset_cylinder1, fillet_radius)
                angle_offset1 = (360 / sectors * i) + (360 / sectors / 2)
                x_offset1 = ((full_radius - offset_radius1) / 2) * cos(radians(angle_offset1))
                y_offset1 = ((full_radius - offset_radius1) / 2) * sin(radians(angle_offset1))
                offset_position1 = FreeCAD.Vector(x_offset1, y_offset1, 0)
                offset_cylinder1.Placement = FreeCAD.Placement(offset_position1, rotation)
                offcylinder1 = offset_cylinder2.cut(offset_cylinder1)
                cylinder_obj = doc.addObject("Part::Feature", f"Conductor Screen_{i+1}")
                cylinder_obj.Shape = offcylinder1
                if int_sectors >= 6:
                    cylinder_obj.ViewObject.ShapeColor = tuple(conductorScreenColor)
                elif i == 0:
                    cylinder_obj.ViewObject.ShapeColor = tuple(condscreencolor1)
                elif i == 1:
                    cylinder_obj.ViewObject.ShapeColor = tuple(condscreencolor2)
                elif i == 2:
                    cylinder_obj.ViewObject.ShapeColor = tuple(condscreencolor3)
                elif i == 3:
                    cylinder_obj.ViewObject.ShapeColor = tuple(condscreencolor4)
                elif i == 4:
                    cylinder_obj.ViewObject.ShapeColor = tuple(condscreencolor5)

            if 'x_offset2' not in locals() or x_offset2 is None:
                x_offset2 = 0
            if 'y_offset2' not in locals() or y_offset2 is None:
                y_offset2 = 0
            if thk1!=0:
                height = height - increment
                offset_cylinder2 = Part.makeCylinder(offset_radius2, height+increment,
                                                     FreeCAD.Vector(0, 0, 0),
                                                     FreeCAD.Vector(0, 0, 1),
                                                     360 / sectors)
                offset_cylinder2 = add_fillets_to_cylinder(offset_cylinder2, fillet_radius)
                angle_offset2 = (360 / sectors * i) + (360 / sectors / 2)
                x_offset2 = ((full_radius - offset_radius2) / 2) * cos(radians(angle_offset2))
                y_offset2 = ((full_radius - offset_radius2) / 2) * sin(radians(angle_offset2))
                offset_position2 = FreeCAD.Vector(x_offset2, y_offset2, 0)
                offset_cylinder2.Placement = FreeCAD.Placement(offset_position2, rotation)
                offcylinder2 = sector.cut(offset_cylinder2)
                cylinder_obj = doc.addObject("Part::Feature", f"Insulation Screen_{i+1}")
                cylinder_obj.Shape = offcylinder2
                #if int_sectors >= 6:
                cylinder_obj.ViewObject.ShapeColor = tuple(insulationColor)
                #height = height - increment
                # elif i == 0:
                #     cylinder_obj.ViewObject.ShapeColor = tuple(insscreencolor1)
                # elif i == 1:
                #     cylinder_obj.ViewObject.ShapeColor = tuple(insscreencolor2)
                # elif i == 2:
                #     cylinder_obj.ViewObject.ShapeColor = tuple(insscreencolor3)
                # elif i == 3:
                #     cylinder_obj.ViewObject.ShapeColor = tuple(insscreencolor4)
                # elif i == 4:
                #     cylinder_obj.ViewObject.ShapeColor = tuple(insscreencolor5)
                
            # if thk1!=0:
            #     sector = sector.cut(offset_cylinder1)                
            # if thk2!=0:
            #     sector = sector.cut(offset_cylinder2)
            #     sector_obj = doc.addObject("Part::Feature", f"Insulation Screen_{i+1}")
            #     sector_obj.Shape = sector

            # sector_obj = doc.addObject("Part::Feature", f"Insulation Screen_{i+1}")
            # sector_obj.Shape = sector
            main_cores_info.append((x_offset2, y_offset2, offset_radius2))
            QtCore.QCoreApplication.processEvents()
        # Create fractional sector if applicable
        if fractional_sector_angle > 0:
            import FreeCAD
            fractional_sector = Part.makeCylinder(full_radius, tempheight-2*increment,
                                                  FreeCAD.Vector(0, 0, 0),
                                                  FreeCAD.Vector(0, 0, 1),
                                                  fractional_sector_angle)
            fractional_sector = add_fillets_to_cylinder(fractional_sector, fillet_radius)
            fractional_rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), sector_angle * int_sectors)
            fractional_sector.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), fractional_rotation)

            if thk2!=0:
                tempheight = tempheight -increment
                offset_cylinder2 = Part.makeCylinder(offset_radius2, tempheight,
                                                     FreeCAD.Vector(0, 0, 0),
                                                     FreeCAD.Vector(0, 0, 1),
                                                     fractional_sector_angle)
                offset_cylinder2 = add_fillets_to_cylinder(offset_cylinder2, fillet_radius)
                angle_offset2 = (sector_angle * int_sectors) + (fractional_sector_angle / 2)
                x_offset2 = ((full_radius - offset_radius2) / 2) * cos(radians(angle_offset2))
                y_offset2 = ((full_radius - offset_radius2) / 2) * sin(radians(angle_offset2))
                offset_position2 = FreeCAD.Vector(x_offset2, y_offset2, 0)
                offset_cylinder2.Placement = FreeCAD.Placement(offset_position2, fractional_rotation)
                offset_cylinder1 = Part.makeCylinder(offset_radius1, tempheight+1,
                                                     FreeCAD.Vector(0, 0, 0),
                                                     FreeCAD.Vector(0, 0, 1),
                                                     fractional_sector_angle)
                offset_cylinder1 = add_fillets_to_cylinder(offset_cylinder1, fillet_radius)
                angle_offset1 = (sector_angle * int_sectors) + (fractional_sector_angle / 2)
                x_offset1 = ((full_radius - offset_radius1) / 2) * cos(radians(angle_offset1))
                y_offset1 = ((full_radius - offset_radius1) / 2) * sin(radians(angle_offset1))
                offset_position1 = FreeCAD.Vector(x_offset1, y_offset1, 0)
                offset_cylinder1.Placement = FreeCAD.Placement(offset_position1, fractional_rotation)
                offcylinder1 = offset_cylinder2.cut(offset_cylinder1)
                cylinder_obj = doc.addObject("Part::Feature", f"Conductor Screen_{i+1}")
                cylinder_obj.Shape = offcylinder1
                if int_sectors >= 6:
                    cylinder_obj.ViewObject.ShapeColor = tuple(conductorScreenColor)
                else:
                    cylinder_obj.ViewObject.ShapeColor = tuple(fraccondscreencolor)
            
            if 'x_offset2' not in locals() or x_offset2 is None:
                x_offset2 = 0
            if 'y_offset2' not in locals() or y_offset2 is None:
                y_offset2 = 0
            if thk1!=0:
                tempheight= tempheight-increment
                offset_cylinder2 = Part.makeCylinder(offset_radius2, tempheight+increment,
                                                     FreeCAD.Vector(0, 0, 0),
                                                     FreeCAD.Vector(0, 0, 1),
                                                     fractional_sector_angle)
                offset_cylinder2 = add_fillets_to_cylinder(offset_cylinder2, fillet_radius)
                angle_offset2 = (sector_angle * int_sectors) + (fractional_sector_angle / 2)
                x_offset2 = ((full_radius - offset_radius2) / 2) * cos(radians(angle_offset2))
                y_offset2 = ((full_radius - offset_radius2) / 2) * sin(radians(angle_offset2))
                offset_position2 = FreeCAD.Vector(x_offset2, y_offset2, 0)
                offset_cylinder2.Placement = FreeCAD.Placement(offset_position2, fractional_rotation)
                offcylinder2 = fractional_sector.cut(offset_cylinder2)
                cylinder_obj = doc.addObject("Part::Feature", f"Insulation Screen_{i+1}")
                cylinder_obj.Shape = offcylinder2
                #if int_sectors >= 6:
                cylinder_obj.ViewObject.ShapeColor = tuple(insulationColor)
                # else:
                #     cylinder_obj.ViewObject.ShapeColor = tuple(fracinsscreencolor)

            # if thk1!=0:
            #     fractional_sector = fractional_sector.cut(offset_cylinder1)                
            # if thk2!=0:
            #     fractional_sector = fractional_sector.cut(offset_cylinder2)
            #     fractional_sector_obj = doc.addObject("Part::Feature", f"Fractional Sector_Insulation Screen")
            #     fractional_sector_obj.Shape = fractional_sector

            # fractional_sector_obj = doc.addObject("Part::Feature", f"Fractional Sector_Insulation Screen")
            # fractional_sector_obj.Shape = fractional_sector
            main_cores_info.append((x_offset2, y_offset2, offset_radius2))

        doc.recompute()
        QtCore.QCoreApplication.processEvents()
        # Delete interfering wires
        delete_interfering_cylinders(doc, cylinders)

        doc.recompute()

        # --------------------------------------------------------------------
        # PROMPTS replaced with JSON values
        # --------------------------------------------------------------------
        # Pre-Inner sheath insulation parameters
        innersheathinsuradii = full_radius + preinnersheaththickness
        if preinnersheaththickness!=0:
            core = Part.makeCylinder(full_radius, height)
            height = height - increment
            innersheathinsu_cylinder = Part.makeCylinder(innersheathinsuradii, height)
            innersheathinsu = innersheathinsu_cylinder.cut(core)
            part = doc.addObject("Part::Feature", "Pre-innersheath insulation")
            part.Shape = innersheathinsu
            part.ViewObject.ShapeColor = tuple(preinnersheathcolor)

        # Inner sheath parameters
        innersheathradii = innersheathinsuradii + innersheaththickness
        if innersheaththickness!=0:
            core = Part.makeCylinder(innersheathinsuradii, height)
            height = height - increment
            innersheath_cylinder = Part.makeCylinder(innersheathradii, height )
            innersheath = innersheath_cylinder.cut(core)
            part = doc.addObject("Part::Feature", "innersheath")
            part.Shape = innersheath
            part.ViewObject.ShapeColor = tuple(innersheathcolor)

        # Insulation over Inner sheath parameters
        overinnersheathradii = innersheathradii + overinnersheaththickness
        if overinnersheaththickness!=0:
            core = Part.makeCylinder(innersheathradii, height)
            height = height-increment
            overinnersheath_cylinder = Part.makeCylinder(overinnersheathradii, height)
            overinnersheath = overinnersheath_cylinder.cut(core)
            part = doc.addObject("Part::Feature", "Insulation over innersheath")
            part.Shape = overinnersheath
            part.ViewObject.ShapeColor = tuple(overinnersheathcolor)

        # Armor sheath parameters
        cylinder_radius = 0  	
        r = overinnersheathradii																						  
        if armor_choice == "1":
            # Circular cylinders
            cylinder_radius = circular_armor_params
            r = overinnersheathradii + cylinder_radius
            cylinder_height_armor = height - (increment)
           

            if cylinder_radius!=0:
                height=height-increment
                num_cylinders = int(math.floor((2 * math.pi * r) / (2 * cylinder_radius)))
                angle_step = 2 * math.pi / num_cylinders

                for i in range(num_cylinders):
                    x = r * math.cos(i * angle_step)
                    y = r * math.sin(i * angle_step)
                    position = App.Vector(x, y, 0)
                    cylinder_obj = Part.makeCylinder(cylinder_radius, cylinder_height_armor, position)
                    part = doc.addObject("Part::Feature", f"Armor wires_{i+1}")
                    part.Shape = cylinder_obj
                    part.ViewObject.ShapeColor = tuple(armorcolor)


        elif armor_choice == "2":
            # Cubical
            side_length = cubical_armor_params
            side_thickness = 0.5 #float(cubical_armor_params["side_thickness"])
            cylinder_radius = side_thickness  # to reuse same var for subsequent calcs
            r = overinnersheathradii
            cylinder_height_armor = height - (increment)
            height=height-increment
            if cylinder_radius!=0:
                create_armorstrips(doc, outer_diameter=2*(overinnersheathradii+side_thickness), inner_diameter=2*overinnersheathradii, ht=height, arc_length=side_length)

            # num_cylinders = int(math.floor((2 * math.pi * r) / side_length))
            # angle_step = 360 / num_cylinders

            # for i in range(num_cylinders):
            #     angle = math.radians(i * angle_step)
            #     x = r * math.cos(angle)
            #     y = r * math.sin(angle)

            #     cube = Part.makeBox(side_thickness, side_length, cylinder_height_armor)
            #     rotation_angle = (i + 0.5) * angle_step
            #     cube.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), rotation_angle)
            #     cube.translate(App.Vector(x, y, 0))

            #     obj = doc.addObject("Part::Feature", f"Armor strips_{i+1}")
            #     obj.Shape = cube
            #     obj.ViewObject.ShapeColor = tuple(armorcolor)

        doc.recompute()
        QtCore.QCoreApplication.processEvents()
        # armor taping
        armortapingradii = cylinder_radius + r + armortapingthickness
        if armortapingthickness!=0:
            cylinder_height_armor = height - (increment)
            armoursheath = Part.makeCylinder(cylinder_radius + r, cylinder_height_armor)
            height=height-increment
            armorsheath_cylinder = Part.makeCylinder(armortapingradii, height)
            armourtaping = armorsheath_cylinder.cut(armoursheath)
            part = doc.addObject("Part::Feature", "armor taping")
            part.Shape = armourtaping
            part.ViewObject.ShapeColor = tuple(armortapingcolor)

        # Outer sheath        
        outercolorchoice = params["outercolorchoice"]
        oangle = params["oangle"]
        outercolor1 =params.get("outercolor1", (0.0,0.0,0.0))
        outercolor2 =params.get("outercolor2", (0.0,0.0,0.0))
        outersheathradii = armortapingradii + outersheaththickness       
        with open(json_file_path, "r") as file:
            params = json.load(file)
        params["Calculated outer radius"] = outersheathradii
        with open(json_file_path, "w") as f:
            json.dump(params, f, indent=4)
        if outersheaththickness!=0:
            if outercolorchoice == 1:
                cylinder_height_armor = height
                armoursheath = Part.makeCylinder(armortapingradii, cylinder_height_armor)
                height=height-increment
                outersheath_cylinder = Part.makeCylinder(outersheathradii, height)
                outersheath = outersheath_cylinder.cut(armoursheath)
                part = doc.addObject("Part::Feature", "Outersheath")
                part.Shape = outersheath
                part.ViewObject.ShapeColor = tuple(outersheathcolor)
            if outercolorchoice == 2:  
                height=height-increment         
                create_dual_outersheath(
                    doc,
                    outercolor1,
                    outercolor2,
                    outer_diameter=outersheathradii*2, 
                    inner_diameter=armortapingradii*2,
                    h=height,
                    strip_start_angle=150,
                    strip_end_angle=180,
                    strip_z_offset=0
                )   

        doc.recompute()
        QtCore.QCoreApplication.processEvents()
        doc.saveAs(save_file_path)                       
        doc.recompute()        
              
        printingMatterText = printingMatter.strip()

        if printingMatterText:
            create_text_on_outersheath(doc,outersheathcolor,outercolor2,logger,printingMatter, r"C:\Windows\Fonts\times.ttf", outersheathradii * 0.6)
        else:
            logger.info("No printing matter specified; skipping text creation.")
        
        #create_text_on_outersheath(doc,outersheathcolor,outercolor2,logger,printingMatter, r"C:\Windows\Fonts\times.ttf", outersheathradii * 0.6)

        QtCore.QCoreApplication.processEvents()
        doc.saveAs(save_file_path)                       
        doc.recompute()

        create_images(params["outputFile"])
        doc.recompute()

        import CreateDrawing
        CreateDrawing.CreateDrawingSectoral(doc)
        doc.recompute()
        # --------------------------------------------------------------------
        # 5) MAIN LOGIC: MULTI-SWEEP FILL
        # --------------------------------------------------------------------
        all_existing_circles = list(main_cores_info)
        # leftover region
        outer_sheath_radius = innersheathinsuradii - preinnersheaththickness

        # logger.info(f"Starting multi-sweep fill with diameters: {fill_diameters_desc}")
        # filled_circles = fill_with_discrete_sweeps(
        #     doc=doc,
        #     existing_circles=all_existing_circles,
        #     boundary_radius=outer_sheath_radius,
        #     diameters_desc=fill_diameters_desc,
        #     tries_per_size=tries_per_size,
        #     filler_height=height + 1
        # )

        # --------------------------------------------------------------------
        # 6) Save the File
        # --------------------------------------------------------------------
        doc.saveAs(save_file_path)
        logger.info(f"File saved to: {save_file_path}")
        QMessageBox.information(None, "Operation Complete", "Done Generating! Please Check FreeCad for adjustments!")
        logger.info("CableConfig script completed successfully.")
    except KeyError as ke:
        logger.error(f"Missing key in JSON data: {ke}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Script execution finished.")

def create_text_on_outersheath(doc,ocolor,ocolor1, logger, text, font_path=r"C:\Windows\Fonts\times.ttf", text_size=20):
    """
    Creates a text label on the 'Outersheath' object.

    The text is created using Draft.makeShapeString, positioned at a point on the front face 
    of the Outersheath (using its bounding box), rotated so that it aligns with the front view, 
    and justified to the middle-center.

    Parameters:
      text (str): The text to display.
      font_path (str): Path to the TrueType font file.
      text_size (float): The size of the text.

    Returns:
      The created ShapeString object.
    """
    if not doc:
        logger.error("No active document found!\n")
        return None

   
    
    # Retrieve a suitable object from the candidate list for text placement.
    candidate_names = ["Outersheath", "Armor_strips", "Insulation_over_innersheath", "Insulation"]
    cylinder_obj = None
    for name in candidate_names:
        cylinder_obj = doc.getObject(name)
        if cylinder_obj:
            break
    if not cylinder_obj:
        logger.error("No suitable object found from candidate list: {}.\n".format(candidate_names))
        return None

    # Get the bounding box of the cylinder object
    bbox = cylinder_obj.Shape.BoundBox
    FreeCADGui.updateGui()

    # Calculate the height of the bounding box
    height = (bbox.ZMax - bbox.ZMin)

    # Estimate width of text in 3D units: 
    # Assume each character is roughly 0.6 * text_size wide (typical for sans serif)
    #char_count = 100
    char_count = len(text)
    est_text_length = text_size * char_count * 1.5

    # Calculate scale factor to make text fit in height
    if height < est_text_length:
        scale_factor = height / est_text_length
        adjusted_text_size = text_size *scale_factor
    else:
        adjusted_text_size = text_size

    #tracking = (height - est_text_length)/(char_count-1)
    #tracking = max(tracking, 0)
    if char_count > 1:
        tracking = (height - est_text_length)/(char_count-1)
        tracking = max(tracking, 0)
    else:
        tracking = 0 

     # Create the 2D text using Draft.makeShapeString
    import Draft
    # if (char_count < 30):
    #     shape_str = Draft.makeShapeString(String=text, FontFile=font_path, Size=text_size, Tracking = text_size * 0.5)
    # elif (char_count > 30 and char_count < 50):
    #     hape_str = Draft.makeShapeString(String=text, FontFile=font_path, Size=text_size, Tracking = text_size * 0.4)
    # else:
    #     shape_str = Draft.makeShapeString(String=text, FontFile=font_path, Size=adjusted_text_size, Tracking = adjusted_text_size * 0.1)

    shape_str = Draft.makeShapeString(String=text, FontFile=font_path, Size=adjusted_text_size, Tracking = adjusted_text_size * 0.1)
    
    if (ocolor1 != tuple([0,0,0])) or (ocolor!=tuple([0,0,0])):
        shape_str.ViewObject.ShapeColor = tuple([0,0,0])
        # shape_str.ViewObject.LineColor = tuple([0,0,0])
    else:
        shape_str.ViewObject.ShapeColor = tuple([255,255,255])
        shape_str.ViewObject.LineColor = tuple([255,255,255])
    # Place the text at (0, -bbox.YMax, midZ)
    #text_position = App.Vector(0, -bbox.YMax, (bbox.ZMin + bbox.ZMax) / 2.0)
    text_position = App.Vector(0, math.floor(-bbox.YMax * 10) / 10.0, (bbox.ZMin + bbox.ZMax) / 2.0)
    shape_str.Placement.Base = text_position
    shape_str.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), 90)
    shape_str.Justification = u"Middle-Center"
    Draft.rotate(shape_str, 90.0, App.Vector(0, 0.0, (bbox.ZMin + bbox.ZMax) / 2.0), 
                 axis=App.Vector(0.0, -1.0, 0.0), copy=False)

    # Corrected mirrored text
    mirrored_text = Draft.makeShapeString(String=text, FontFile=font_path, 
                                         Size=adjusted_text_size, Tracking=adjusted_text_size * 0.1)
    
    # Set colors
    text_color = tuple([0,0,0]) if (ocolor1 != (0,0,0)) or (ocolor != (0,0,0)) else tuple([255,255,255])
    mirrored_text.ViewObject.ShapeColor = text_color
    mirrored_text.ViewObject.LineColor = text_color

    # CORRECTED POSITION: Place on opposite side with positive Y
    mirrored_position = App.Vector(0, math.floor(-bbox.YMax * 10) / 10.0, (bbox.ZMin + bbox.ZMax) / 2.0)
    mirrored_text.Placement.Base = mirrored_position
    
    # CORRECTED ROTATION: 
    # 1. Initial rotation same as front text
    mirrored_text.Placement.Rotation = App.Rotation(App.Vector(1, 0, 0), 90)
    mirrored_text.Justification = u"Middle-Center"
    
    # 2. Rotate for cylindrical surface (opposite direction)
    Draft.rotate(mirrored_text, -90.0,  # Note: Negative rotation for opposite side
                 App.Vector(0, 0.0, (bbox.ZMin + bbox.ZMax) / 2.0),
                 axis=App.Vector(0.0, 1.0, 0.0),  # Positive Y axis
                 copy=False)
    
    # 3. Additional 180° Z-rotation for correct orientation
    Draft.rotate(mirrored_text, 180.0,
                 App.Vector(0, 0.0, (bbox.ZMin + bbox.ZMax) / 2.0),
                 axis=App.Vector(0.0, 0.0, 1.0),  # Z-axis
                 copy=False)

    doc.recompute()
    Gui.Selection.clearSelection()
    return shape_str, mirrored_text

# Armor sheath parameters
def create_armorstrips(doc, outer_diameter, inner_diameter, ht, arc_length, name="Armor strips"):      
    outer_cylinder = Part.makeCylinder(outer_diameter / 2, ht)
    inner_cylinder = Part.makeCylinder(inner_diameter / 2, ht)
    
    hollow_cylinder = outer_cylinder.cut(inner_cylinder)
    #Part.show(hollow_cylinder)
    
    # Calculate the number of vertical sections based on arc length
    radius = outer_diameter / 2
    total_circumference = 2 * math.pi * radius
    num_sections = int(total_circumference / arc_length)
    angle_step = 360 / num_sections
    
    cut_pieces = []
    for i in range(num_sections):
        angle = i * angle_step
        
        # Create vertical cutting plane
        plane = Part.makeBox(2 * radius, 2*ht,2*ht)
        plane.translate(App.Vector(-radius, 0, -radius))
        plane.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), angle)
        
        # Perform intersection to get the section
        cut_piece = hollow_cylinder.common(plane)
        cut_pieces.append(cut_piece)
    
    for idx, piece in enumerate(cut_pieces):
        obj = doc.addObject("Part::Feature", f"{name}_{idx+1}")
        obj.Shape = piece
    
    doc.recompute()	

def create_armorstripswithgap(doc, outer_diameter, inner_diameter, ht, arc_length, name="Armor strips"):
    outer_cylinder = Part.makeCylinder(outer_diameter / 2, ht)
    inner_cylinder = Part.makeCylinder(inner_diameter / 2, ht)
    
    hollow_cylinder = outer_cylinder.cut(inner_cylinder)
    
    # Calculate number of sections
    radius = outer_diameter / 2
    total_circumference = 2 * math.pi * radius
    num_sections = int(total_circumference / arc_length)
    angle_step = 360 / num_sections

    gap = 0.1  # mm gap between segments
    adjusted_arc_length = arc_length - gap
    adjusted_angle_rad = adjusted_arc_length / radius  # angle in radians
    adjusted_angle_deg = math.degrees(adjusted_angle_rad)

    cut_pieces = []
    for i in range(num_sections):
        angle = i * angle_step

        # Calculate width of cutting box from adjusted angle
        slice_width = 2 * radius * math.tan(math.radians(adjusted_angle_deg / 2))
        
        # Make cutting box slightly narrower for gap
        plane = Part.makeBox(slice_width, 2 * ht, 2 * ht)
        plane.translate(App.Vector(-slice_width / 2, 0, -radius))
        plane.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), angle)

        # Cut the slice
        cut_piece = hollow_cylinder.common(plane)
        cut_pieces.append(cut_piece)

    for idx, piece in enumerate(cut_pieces):
        obj = doc.addObject("Part::Feature", f"{name}_{idx+1}")
        obj.Shape = piece

    doc.recompute()
def create_images(output_file):
    #from FreeCADGui import ActiveDocument, runCommand, SendMsgToActiveView
    out_dir = os.path.dirname(output_file)
    out_dir = os.path.join(out_dir, "Images")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    name = "Circular_Cable"
    view = Gui.ActiveDocument.ActiveView

    # Change draw style to Shaded (code 5)    
    import pivy.coin as coin

    view = Gui.ActiveDocument.ActiveView
    sg = view.getSceneGraph()

    # Create your own directional light
    my_light = coin.SoDirectionalLight()
    my_light.direction = coin.SbVec3f(-1, -1, 0)  # top-front light
    my_light.intensity = 0                     # reduce glare

    # Insert it into the scenegraph (top)
    sg.insertChild(my_light, 0)

    print("✅ Custom directional light added.") 

    # Change draw style to Shaded (code 5)
    #Gui.runCommand('Std_DrawStyle', 5)

    # Create images with different Views, Cameras and sizes
    for p in ["OrthographicCamera"]:
        Gui.SendMsgToActiveView(p)
        for f in ["ViewTop", "ViewAxo", "ViewLeft", "ViewFront"]:
            Gui.SendMsgToActiveView(f)
            App.ActiveDocument.recompute()

            if f == "ViewAxo":
                yaw_rotation = App.Rotation(App.Vector(0, 0, 1), -135)
                pitch_rotation = App.Rotation(App.Vector(1, 0, 0), 54.736)
                final_rotation = yaw_rotation.multiply(pitch_rotation)
                
                # Temporary trigger for update
                roll_rotation = App.Rotation(App.Vector(0, 0, 1), -30)
                final_rotation = roll_rotation.multiply(final_rotation)
                view.setCameraOrientation(final_rotation)
                view.fitAll() 

                Gui.updateGui()
                App.ActiveDocument.recompute()
                view.fitAll()

            elif f == "ViewTop":
                # 🔍 Zoom in by reducing orthographic camera height
                cam = view.getCameraNode()
                cam.height.setValue(cam.height.getValue() * 0.5)

            for width, height in [[5000, 5000]]:
                # ⬜ Save White background
                path_white = os.path.join(out_dir, f"{name}_{f}_{width}_{height}_White.png")
                view.saveImage(path_white, width, height, "White")

                # 🟦 Save Transparent background
                path_trans = os.path.join(out_dir, f"{name}_{f}_{width}_{height}_Transparent.png")
                view.saveImage(path_trans, width, height, "Transparent")

    # 🎯 Restore view style to AsIs (default)
    Gui.runCommand('Std_DrawStyle', 0)


def create_images_old():
            out_dir = "C:/temp/"
            name = "sectoral_cable"
            view = Gui.ActiveDocument.ActiveView

            # Create images with different Views, Cameras and sizes
            for p in ["OrthographicCamera"]:
                Gui.SendMsgToActiveView(p)
                for f in ["ViewAxo", "ViewTop", "ViewRight"]:  # Added "ViewRight"
                    Gui.SendMsgToActiveView(f)

                    # Zoom in only for Top View
                    if f == "ViewTop":
                        cam = view.getCameraNode()
                        cam_height = cam.height.getValue()  # Extract actual float value
                        cam.height.setValue(cam_height * 0.3)  # Reduce height to zoom in (adjust factor as needed)

                    for x, y in [[5000, 5000]]:
                        view.saveImage(out_dir + name + "_" + p + "_" + f + "_" + str(x) + "_" + str(y) + ".png", x, y, "Transparent")

# If this script is the main entry point, run main()
if __name__ == "__main__":
    # Launch the FreeCAD GUI main window
    Gui.showMainWindow()
    # Delay execution of the main function to ensure the GUI is visible.
    delay_ms = 1000  # delay in milliseconds; adjust if needed
    QtCore.QTimer.singleShot(delay_ms, main)
    # Start the FreeCAD GUI event loop (this call blocks until the GUI is closed)
    Gui.exec_loop()

