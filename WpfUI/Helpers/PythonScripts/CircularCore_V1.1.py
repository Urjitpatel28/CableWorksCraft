#!/usr/bin/env python
"""
CableConfigCmd.py

This script builds a multi–layer cable configuration with the following features:
  • A core composed of concentric cylinders arranged in layers.
    – If a layer value is fractional (e.g. 5.5), an extra “half–core” is added.
  • Pre–Inner sheath insulation, inner sheath, and insulation over inner sheath.
  • Armor sheath (either circular or cubical as chosen) plus armor taping and an outer sheath.
  • Filler circles placed via multi–sweep (with optional bubble–packing functions included).

Parameters can be provided via a JSON file (using the --jsonFile option) or, if not provided,
the script will prompt interactively. (Any new variable is now represented as a JSON field.)

JSON example:
{
  "projectName": "Test1",
  "parameters": {
    "spacing_1": 15.0,
    "spacing_2": 2.0,
    "spacing_3": 2.0,
    "spacing_4": 2.0,
    "spacing_5": 0.0,
    "spacing_6": 0.0,
    "spacing_7": 0.0,
    "wire_radius": 1.0,
    "num_cylinders_per_layer": [1, 5.5],
    "halfcore_radius": 10.0,
    "preinnersheaththickness": 2.0,
    "innersheaththickness": 5.0,
    "overinnersheaththickness": 1.0,
    "armor_choice": "1",         // "1" for circular armor, "2" for cubical armor
    "cylinder_radius": 3.0,        // used when armor_choice=="1"
    "side_length": 0.0,            // used when armor_choice=="2"
    "side_thickness": 0.0,         // used when armor_choice=="2"
    "armortapingthickness": 2.0,
    "outersheaththickness": 5.0,
    "fillerDiameters": [13,12,11,10,9,8,7,6,5,4,3,2,1],
    "leftoverRadius": 0.0
  },
  "outputFile": "C:\\ProjectRoot\\Test1\\Outputs\\Test1.fcstd",
  "logFile": "C:\\ProjectRoot\\Test1\\Test1.log"
}

Usage:
    python CableConfigCmd.py --jsonFile "path/to/myCables.json"
    (or run interactively if no --jsonFile is provided)
"""

import sys, os, json, math, argparse, logging

try:
    import FreeCAD as App
    import FreeCADGui as Gui  # not required if running headless
    
    import Part
    import array
    import math
    import shutil
    from PySide2.QtWidgets import QMessageBox

    
except ImportError:
    print("Error: FreeCAD modules not found! Make sure you are running inside a FreeCAD environment.")
    sys.exit(1)

# Try to import a Qt binding (prefer PySide; if not available, use PyQt5)
try:
    from PySide2 import QtCore
except ImportError:
    from PySide2 import QtCore

# ------------------------------------------------------------------------------
# Helper: safe float input (for interactive mode)
# ------------------------------------------------------------------------------

factorforheight = 70

def get_float_input(prompt):
    while True:
        userinput = input(prompt)
        try:
            return float(userinput)
        except ValueError:
            print("Invalid input! Please enter a valid number.")

# ------------------------------------------------------------------------------
# Parameter acquisition
# ------------------------------------------------------------------------------
def get_parameters_from_json(json_file):
    try:
        with open(json_file, "r") as f:
            config = json.load(f)
    except Exception as ex:
        print(f"Error reading JSON file: {ex}")
        sys.exit(1)
    for key in ("parameters", "outputFile", "logFile"):
        if key not in config:
            print(f"JSON file must contain the key '{key}' at top level.")
            sys.exit(1)
    return config["parameters"], config["outputFile"], config["logFile"]

def calculate_height_from_text(printing_matter):
    base_height = 300  # 10 characters -> 300 mm
    extra_per_10_chars = 100  # Every extra 10 characters = +100 mm
    max_height = 1000  # Cap height at 1000 mm

    if not printing_matter:
        return base_height  # If empty, still keep a minimum height

    length = len(printing_matter)

    # Calculate extra blocks of 10 characters
    extra_blocks = max(0, (length - 10) // 10)

    # Final height
    height = base_height + (extra_blocks * extra_per_10_chars)

    # Cap at max height
    return min(height, max_height)

def get_parameters_interactive():
    print("=== Enter core parameters ===")
    spacing_1 = get_float_input("Enter conductor radius: ")
    spacing_2 = get_float_input("Enter conductor screen thickness: ")
    if (spacing_2!=0):
        x = input("Enter RGB separated by commas for conductor screen color: ")
        Condscreencolor = []
        for t in x.split(","):
            try:
                Condscreencolor.append(float(t.strip()))
            except:
                continue
    else:
        Condscreencolor=[0,0,0]
    spacing_3 = get_float_input("Enter insulation thickness: ")
    if (spacing_3!=0):
        x = input("Enter RGB separated by commas for insulation color: ")
        Insulationcolor = []
        for t in x.split(","):
            try:
                Insulationcolor.append(float(t.strip()))
            except:
                continue  
    else:
        Insulationcolor=[0,0,0]       
    spacing_4 = get_float_input("Enter non-metallic insulation screen thickness: ")
    if (spacing_4!=0):
        x = input("Enter RGB separated by commas for non-metallic insulation screen color: ")
        nonmetallicscreencolor = []
        for t in x.split(","):
            try:
                nonmetallicscreencolor.append(float(t.strip()))
            except:
                continue 
    else:
        nonmetallicscreencolor=[0,0,0]       
    spacing_5 = get_float_input("Enter metallic insulation screen thickness: ")
    if (spacing_5!=0):
        x = input("Enter RGB separated by commas for metallic insulation screen color: ")
        metallicscreencolor = []
        for t in x.split(","):
            try:
                metallicscreencolor.append(float(t.strip()))
            except:
                continue
    else:
        metallicscreencolor=[0,0,0]        
    spacing_6 = get_float_input("Enter ID tape lapping thickness: ")
    if (spacing_6!=0):
        x = input("Enter RGB separated by commas for ID tape lapping color: ")
        idtapecolor = []
        for t in x.split(","):
            try:
                idtapecolor.append(float(t.strip()))
            except:
                continue        
    else:
        idtapecolor=[0,0,0]
    spacing_7 = get_float_input("Enter lapping thickness: ")
    if (spacing_7!=0):
        x = input("Enter RGB separated by commas for lapping color: ")
        lappingcolor = []
        for t in x.split(","):
            try:
                lappingcolor.append(float(t.strip()))
            except:
                continue 
    else:
        lappingcolor=[0,0,0]        
    wire_radius = get_float_input("Enter wire radius: ")
    x = input("Enter RGB separated by commas for wire color: ")
    wirecolor = []
    for t in x.split(","):
        try:
            wirecolor.append(float(t.strip()))
        except:
            continue      
    # Height is defined as conductor radius * 100
    height = spacing_1 * 100
    #height = calculate_height_from_text(params.get("printingMatter", ""))
    increment = spacing_1
    # Ask for layer configuration (comma separated)
    layers_str = input("Enter comma-separated values for num_cylinders_per_layer (e.g., 1, 5.5): ")
    num_cylinders_per_layer = []
    for token in layers_str.split(","):
        try:
            num_cylinders_per_layer.append(float(token.strip()))
        except:
            continue
    # If any layer value is fractional, prompt for half–core radius.
    if any(n != int(n) for n in num_cylinders_per_layer):
        halfcore_radius = get_float_input("Enter halfcore radius: ")
    else:
        halfcore_radius = 0.0
    print("=== Enter insulation parameters ===")
    preinnersheaththickness = get_float_input("Enter Pre-Inner sheath insulation thickness: ")
    if (preinnersheaththickness!=0):
        preinnersheathcolor = list(map(float, input("Enter RGB separated by commas for preinnersheath color: ").split(',')))
    else:
        preinnersheathcolor=[ 0.8,0.8,0.8]
    innersheaththickness = get_float_input("Enter inner sheath thickness: ")
    if (innersheaththickness!=0):
        innersheathcolor = list(map(float, input("Enter RGB separated by commas for inner sheath color: ").split(',')))
    else:
        innersheathcolor=[ 0.8,0.8,0.8]
    overinnersheaththickness = get_float_input("Enter Insulation over inner sheath thickness: ")
    if (overinnersheaththickness!=0):
        overinnersheathcolor = list(map(float, input("Enter RGB separated by commas for over inner sheath color: ").split(',')))
    else:
        overinnersheathcolor=[ 0.8,0.8,0.8]
    print("=== Enter armor parameters ===")
    armor_choice = input("Choose armor sheath type (enter 1 for circular, 2 for cubical): ").strip()
    if armor_choice == "1":
        cylinder_radius = get_float_input("Enter armour wire radius: ")
        side_length = 0.0
        side_thickness = 0.0
    elif armor_choice == "2":
        side_length = get_float_input("Enter armour wire edge length: ")
        side_thickness = get_float_input("Enter armour wire thickness: ")
        cylinder_radius = 0.0
    else:
        print("Invalid choice; defaulting to circular armor.")
        armor_choice = "1"
        cylinder_radius = get_float_input("Enter armour wire radius: ")
        side_length = 0.0
        side_thickness = 0.0
    armorcolor = list(map(float, input("Enter RGB separated by commas for armor color: ").split(',')))
    armortapingthickness = get_float_input("Enter armor taping thickness: ")
    if (armortapingthickness!=0):
        armortapingcolor = list(map(float, input("Enter RGB separated by commas for armor taping color: ").split(',')))
    else:
        armortapingcolor=[0.8,0.8,0.8]
    outersheaththickness = get_float_input("Enter outer sheath thickness: ")
    if (outersheaththickness!=0):
        outersheathcolor = list(map(float, input("Enter RGB separated by commas for outer sheath color: ").split(',')))
    else:
        outersheathcolor=[0.8,0.8,0.8]
    print("=== Enter filler parameters ===")
    fillerDiameters_input = input("Enter comma-separated filler diameters (or leave blank for default): ")
    if fillerDiameters_input.strip() == "":
        fillerDiameters = list(range(50, 8, -1))
    else:
        try:
            fillerDiameters = [float(x.strip()) for x in fillerDiameters_input.split(",")]
        except:
            fillerDiameters = list(range(50, 8, -1))
    leftoverRadius = get_float_input("Enter leftoverRadius (enter 0 or negative for auto-calculation): ")

    printingMatter = input("Enter printing matter text (e.g., company name): ").strip()  # Prompt for printing matter

    output_file = input("Enter output file path (or leave blank): ").strip()
    if output_file == "":
        output_file = None
    log_file = input("Enter log file path (default 'cableconfig.log'): ").strip()
    if log_file == "":
        log_file = "cableconfig.log"
    params = {
        "spacing_1": spacing_1,
        "spacing_2": spacing_2,
        "spacing_3": spacing_3,
        "spacing_4": spacing_4,
        "spacing_5": spacing_5,
        "spacing_6": spacing_6,
        "spacing_7": spacing_7,
        "wire_radius": wire_radius,
        "num_cylinders_per_layer": num_cylinders_per_layer,
        "Condscreencolor": Condscreencolor,
        "Insulationcolor": Insulationcolor,
        "nonmetallicscreencolor": nonmetallicscreencolor,
        "metallicscreencolor": metallicscreencolor,
        "idtapecolor": idtapecolor,
        "lappingcolor": lappingcolor,
        "wirecolor": wirecolor,
        "preinnersheathcolor": preinnersheathcolor,
        "innersheathcolor": innersheathcolor,
        "overinnersheathcolor": overinnersheathcolor,
        "armorcolor": armorcolor,
        "armortapingcolor": armortapingcolor,
        "outersheathcolor": outersheathcolor,
        "halfcore_radius": halfcore_radius,
        "preinnersheaththickness": preinnersheaththickness,
        "innersheaththickness": innersheaththickness,
        "overinnersheaththickness": overinnersheaththickness,
        "armor_choice": armor_choice,
        "cylinder_radius": cylinder_radius,
        "side_length": side_length,
        "side_thickness": side_thickness,
        "armortapingthickness": armortapingthickness,
        "outersheaththickness": outersheaththickness,
        "fillerDiameters": fillerDiameters,
        "leftoverRadius": leftoverRadius,
        "printingMatter": printingMatter,        
    }
    return params, output_file, log_file

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
def setup_logger(log_file_path):
    logger = logging.getLogger("CableConfigLogger")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_file_path, mode='w')
    fh.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger
def parse_color(color_str):
    # Remove any parentheses and whitespace, then split by comma
    s = color_str.strip().strip("()")
    return tuple(float(x.strip()) for x in s.split(','))
# ------------------------------------------------------------------------------
# Build Core Geometry
# ------------------------------------------------------------------------------
def build_core_geometry(params, doc, logger,condlayercount):
    num_concentric_cylinders = 7
    spacing_1 = params["spacing_1"]
    spacing_2 = params["spacing_2"]
    spacing_3 = params["spacing_3"]
    spacing_4 = params["spacing_4"]
    spacing_5 = params["spacing_5"]
    spacing_6 = params["spacing_6"]
    spacing_7 = params["spacing_7"]
    condscreencolor1=parse_color(params.get("condscreencolor1", "(0.8, 0.8, 0.8)"))
    condscreencolor2=parse_color(params.get("condscreencolor2", "(0.8, 0.8, 0.8)"))
    condscreencolor3=parse_color(params.get("condscreencolor3", "(0.8, 0.8, 0.8)"))
    condscreencolor4=parse_color(params.get("condscreencolor4", "(0.8, 0.8, 0.8)"))
    condscreencolor5=parse_color(params.get("condscreencolor5", "(0.8, 0.8, 0.8)"))
    # insulationcolor1=parse_color(params.get("insulationcolor1", "(0.8, 0.8, 0.8)"))
    # insulationcolor2=parse_color(params.get("insulationcolor2", "(0.8, 0.8, 0.8)"))
    # insulationcolor3=parse_color(params.get("insulationcolor3", "(0.8, 0.8, 0.8)"))
    # insulationcolor4=parse_color(params.get("insulationcolor4", "(0.8, 0.8, 0.8)"))
    # insulationcolor5=parse_color(params.get("insulationcolor5", "(0.8, 0.8, 0.8)"))
    # nonmetallicscreencolor1=parse_color(params.get("nonmetallicscreencolor1", "(0.8, 0.8, 0.8)"))
    # nonmetallicscreencolor2=parse_color(params.get("nonmetallicscreencolor2", "(0.8, 0.8, 0.8)"))
    # nonmetallicscreencolor3=parse_color(params.get("nonmetallicscreencolor3", "(0.8, 0.8, 0.8)"))
    # nonmetallicscreencolor4=parse_color(params.get("nonmetallicscreencolor4", "(0.8, 0.8, 0.8)"))
    # nonmetallicscreencolor5=parse_color(params.get("nonmetallicscreencolor5", "(0.8, 0.8, 0.8)"))
    # metallicscreencolor1=parse_color(params.get("metallicscreencolor1", "(0.8, 0.8, 0.8)"))
    # metallicscreencolor2=parse_color(params.get("metallicscreencolor2", "(0.8, 0.8, 0.8)"))
    # metallicscreencolor3=parse_color(params.get("metallicscreencolor3", "(0.8, 0.8, 0.8)"))
    # metallicscreencolor4=parse_color(params.get("metallicscreencolor4", "(0.8, 0.8, 0.8)"))
    # metallicscreencolor5=parse_color(params.get("metallicscreencolor5", "(0.8, 0.8, 0.8)"))
    # idtapecolor1=parse_color(params.get("idtapecolor1", "(0.8, 0.8, 0.8)"))
    # idtapecolor2=parse_color(params.get("idtapecolor2", "(0.8, 0.8, 0.8)"))
    # idtapecolor3=parse_color(params.get("idtapecolor3", "(0.8, 0.8, 0.8)"))
    # idtapecolor4=parse_color(params.get("idtapecolor4", "(0.8, 0.8, 0.8)"))
    # idtapecolor5=parse_color(params.get("idtapecolor5", "(0.8, 0.8, 0.8)"))
    # lappingcolor1=parse_color(params.get("lappingcolor1", "(0.8, 0.8, 0.8)"))
    # lappingcolor2=parse_color(params.get("lappingcolor2", "(0.8, 0.8, 0.8)"))
    # lappingcolor3=parse_color(params.get("lappingcolor3", "(0.8, 0.8, 0.8)"))
    # lappingcolor4=parse_color(params.get("lappingcolor4", "(0.8, 0.8, 0.8)"))
    # lappingcolor5=parse_color(params.get("lappingcolor5", "(0.8, 0.8, 0.8)"))
    halfcondscreencolor=parse_color(params.get("halfcondscreencolor", "(0.8, 0.8, 0.8)"))
    # halfinsulationcolor=parse_color(params.get("halfinsulationcolor", "(0.8, 0.8, 0.8)"))
    # halfnonmetallicscreencolor=parse_color(params.get("halfnonmetallicscreencolor", "(0.8, 0.8, 0.8)"))
    # halfmetallicscreencolor=parse_color(params.get("halfmetallicscreencolor", "(0.8, 0.8, 0.8)"))
    # halfidtapecolor=parse_color(params.get("halfidtapecolor", "(0.8, 0.8, 0.8)"))
    # halflappingcolor=parse_color(params.get("halflappingcolor", "(0.8, 0.8, 0.8)"))
    
    wirecolor = parse_color(params.get("wireColor", "(0.8, 0.8, 0.8)"))
                                                                                                
    # Condscreencolor = params["Condscreencolor"]
    # Insulationcolor = params["Insulationcolor"]
    # nonmetallicscreencolor = params["nonmetallicscreencolor"]
    # metallicscreencolor = params["metallicscreencolor"]
    # idtapecolor = params["idtapecolor"]
    # lappingcolor = params["lappingcolor"]
    
    wire_radius = params["wire_radius"]
        # Height is computed as conductor radius * 100
    num_cylinders_per_layer = params["num_cylinders_per_layer"]
    outer_radius = spacing_1 + spacing_2 + spacing_3 + spacing_4 + spacing_5 + spacing_6 + spacing_7
    htfac = (len(num_cylinders_per_layer))*2
    height = spacing_1 * 40 * htfac
    increment =2* spacing_1 *htfac/2
    conductor_radius = spacing_1
    
    

    logger.info("Building core geometry; outer_radius = %.2f", outer_radius)
    prev_layer_radius = 0
    main_cores_info = []
    circle_radius = 0  # will be updated for each layer
    Conductor_wire_count = 0
    Conductor_count = 0
    
    if (num_cylinders_per_layer==[1]) or (num_cylinders_per_layer==[2]) or (num_cylinders_per_layer==[3]) or (num_cylinders_per_layer==[4]) or (num_cylinders_per_layer==[5]) or (num_cylinders_per_layer==[1.5]) or (num_cylinders_per_layer==[2.5]) or (num_cylinders_per_layer==[3.5]) or (num_cylinders_per_layer==[4.5]):
        for layer_index, nc in enumerate(num_cylinders_per_layer):
            # If the layer value is fractional, then an extra (half) core is needed.
            if nc != int(nc):
                num_whole = int(nc)
                halfcoreradii = params["halfcore_radius"]
                extra_cylinder_radius = halfcoreradii + spacing_2 + spacing_3 + spacing_4 + spacing_5 + spacing_6 + spacing_7
                num_cylinders = num_whole
                extra_cylinder_needed = True
                angle_step = 2 * math.pi / (num_cylinders + 1)
            else:
                extra_cylinder_needed = False
                num_cylinders = int(nc)
                angle_step = 2 * math.pi / num_cylinders if num_cylinders > 0 else 0

            # Calculate circle radius for this layer.
            if layer_index == 0 and (num_cylinders == 1 or num_cylinders == 0):
                circle_radius = 0
            else:
                if layer_index == 0:
                    circle_radius = outer_radius / math.sin(angle_step / 2) if angle_step != 0 else 0
                else:
                    circle_radius = prev_layer_radius + 2 * outer_radius
            prev_layer_radius = circle_radius

            # Place cores in a circular pattern.
            for i in range(num_cylinders):
                Conductor_count=Conductor_count+1
                if i==0 and layer_index==0:
                    height = spacing_1 *factorforheight* htfac*condlayercount/6
                else:
                    height=spacing_1 *factorforheight* htfac*condlayercount/6
                radius=outer_radius
                
                x = circle_radius * math.cos(i * angle_step)
                y = circle_radius * math.sin(i * angle_step)
                position = App.Vector(x, y, 0)
                # For each core, add concentric cylinders.
                for j in range(num_concentric_cylinders):
                    if j == 0:
                        spacing = 0
                        colors = parse_color(params.get("lappingColor", "(0.8, 0.8, 0.8)"))
                        name = "Lapping"
                        radius = outer_radius - spacing
                        if(spacing_7!=0):
                            cylinder = Part.makeCylinder(radius, height, position)
                            hole_cyl = Part.makeCylinder(conductor_radius, height * 10, position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                            obj4.Shape = hollow_cyl
                            #if i == 0:
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            # elif i == 1:
                            #     obj4.ViewObject.ShapeColor = tuple(lappingcolor2)
                            # elif i == 2:
                            #     obj4.ViewObject.ShapeColor = tuple(lappingcolor3)
                            # elif i == 3:
                            #     obj4.ViewObject.ShapeColor = tuple(lappingcolor4)
                            # elif i == 4:
                            #     obj4.ViewObject.ShapeColor = tuple(lappingcolor5)
                            height=height+increment
                            main_cores_info.append((x, y, outer_radius))
                            print(f"Added to main_cores_info: {(x, y, outer_radius)}")
                    elif j == 1:
                        spacing = spacing_7
                        colors = parse_color(params.get("idTapeColor", "(0.8, 0.8, 0.8)"))
                        name = "Id_tape"
                        radius = outer_radius - spacing
                        if(spacing_6 != 0):
                            cylinder = Part.makeCylinder(radius, height,position)
                            hole_cyl = Part.makeCylinder(conductor_radius, height * 10, position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                            obj4.Shape = hollow_cyl
                            #if i == 0:
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            # elif i == 1:
                            #     obj4.ViewObject.ShapeColor = tuple(idtapecolor2)
                            # elif i == 2:
                            #     obj4.ViewObject.ShapeColor = tuple(idtapecolor3)
                            # elif i == 3:
                            #     obj4.ViewObject.ShapeColor = tuple(idtapecolor4)
                            # elif i == 4:
                            #     obj4.ViewObject.ShapeColor = tuple(idtapecolor5)
                            height=height+increment
                    elif j == 2:
                        spacing = spacing_7 + spacing_6
                        colors = parse_color(params.get("metallicScreenColor", "(0.8, 0.8, 0.8)"))
                        name = "Metallic_Screen"
                        radius = outer_radius - spacing
                        if(spacing_5 != 0):
                            cylinder = Part.makeCylinder(radius, height, position)
                            hole_cyl = Part.makeCylinder(conductor_radius, height , position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                            obj4.Shape = hollow_cyl
                            #if i == 0:
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            # elif i == 1:
                            #     obj4.ViewObject.ShapeColor = tuple(metallicscreencolor2)
                            # elif i == 2:
                            #     obj4.ViewObject.ShapeColor = tuple(metallicscreencolor3)
                            # elif i == 3:
                            #     obj4.ViewObject.ShapeColor = tuple(metallicscreencolor4)
                            # elif i == 4:
                            #     obj4.ViewObject.ShapeColor = tuple(metallicscreencolor5)
                            height=height+increment
                    elif j == 3:
                        spacing = spacing_7 + spacing_5 + spacing_6
                        colors = parse_color(params.get("nometallicScreenColor", "(0.8, 0.8, 0.8)"))
                        name = "Non-metallic_Screen"
                        radius = outer_radius - spacing
                        if(spacing_4 != 0):
                            cylinder = Part.makeCylinder(radius, height, position)
                            hole_cyl = Part.makeCylinder(conductor_radius, height , position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                            obj4.Shape = hollow_cyl
                            #if i == 0:
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            # elif i == 1:
                            #     obj4.ViewObject.ShapeColor = tuple(nonmetallicscreencolor2)
                            # elif i == 2:
                            #     obj4.ViewObject.ShapeColor = tuple(nonmetallicscreencolor3)
                            # elif i == 3:
                            #     obj4.ViewObject.ShapeColor = tuple(nonmetallicscreencolor4)
                            # elif i == 4:
                            #     obj4.ViewObject.ShapeColor = tuple(nonmetallicscreencolor5)
                            height=height+increment
                    elif j == 4:
                        spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4
                        colors = parse_color(params.get("insulationColor", "(0.8, 0.8, 0.8)"))
                        name = "Insulation"
                        radius = outer_radius - spacing
                        if(spacing_3 != 0):
                            cylinder = Part.makeCylinder(radius, height, position)
                            hole_cyl = Part.makeCylinder(conductor_radius, height , position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                            obj4.Shape = hollow_cyl
                            #if i == 0:
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            # elif i == 1:
                            #     obj4.ViewObject.ShapeColor = tuple(insulationcolor2)
                            # elif i == 2:
                            #     obj4.ViewObject.ShapeColor = tuple(insulationcolor3)
                            # elif i == 3:
                            #     obj4.ViewObject.ShapeColor = tuple(insulationcolor4)
                            # elif i == 4:
                            #     obj4.ViewObject.ShapeColor = tuple(insulationcolor5)
                            height=height+increment
                    elif j == 5:
                        
                        spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4 + spacing_3
                        colors = parse_color(params.get("conductorScreenColor", "(0.8, 0.8, 0.8)"))
                        name = "Conductor_Screen"
                        radius = outer_radius - spacing
                        if(spacing_2 != 0):
                            height=height+increment
                            cylinder = Part.makeCylinder(radius, height, position)
                            hole_cyl = Part.makeCylinder(conductor_radius, height, position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                            obj4.Shape = hollow_cyl
                            if i == 0:
                                obj4.ViewObject.ShapeColor = tuple(condscreencolor1)
                            elif i == 1:
                                obj4.ViewObject.ShapeColor = tuple(condscreencolor2)
                            elif i == 2:
                                obj4.ViewObject.ShapeColor = tuple(condscreencolor3)
                            elif i == 3:
                                obj4.ViewObject.ShapeColor = tuple(condscreencolor4)
                            elif i == 4:
                                obj4.ViewObject.ShapeColor = tuple(condscreencolor5)
                           
                    elif j == 6:
                        spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4 + spacing_3 + spacing_2
                        colors = [1,1,1]
                        radius = outer_radius - spacing
                                
                                                        
                                
                                                                                            
                                                                                                                                            
                                                                                                                                
                                                
                                                                            
                                                                                                                                
                                                                                            
                                                                        
                                                
                                                        
                                                                    
                        small_cylinder_radius = wire_radius
                        num_levels = int((conductor_radius - small_cylinder_radius) / (2 * small_cylinder_radius))
                        for level in range(num_levels + 1):
                                level_radius = level * 2 * small_cylinder_radius
                                if level_radius < conductor_radius:
                                    if level == 0:
                                        num_cylinders_in_level = 1
                                    else:
                                        num_cylinders_in_level = int(2 * math.pi * level_radius / (2 * small_cylinder_radius))
                                    if num_cylinders_in_level > 0:
                                        angle_step_level = 2 * math.pi / num_cylinders_in_level
                                        for k in range(num_cylinders_in_level):
                                            x_level = level_radius * math.cos(k * angle_step_level)
                                            y_level = level_radius * math.sin(k * angle_step_level)
                                            level_position = App.Vector(x + x_level, y + y_level, 0)
                                            small_cyl = Part.makeCylinder(small_cylinder_radius, height + (increment), level_position)
                                            obj3 = doc.addObject("Part::Feature", f"Wires_{Conductor_wire_count+1}")
                                            obj3.Shape = small_cyl
                                            obj3.ViewObject.ShapeColor = tuple(wirecolor)
                    # radius = outer_radius - spacing
                    # if radius > 0:
                    #     current_height = height + increment
                    #     if j == 6:
                    #         # Create a hollow cylinder (a hole).
                    #         outer_cyl = Part.makeCylinder(spacing_1 + spacing_2, current_height, position)
                    #         obj1 = doc.addObject("Part::Feature", f"Conductor_{Conductor_count}")
                    #         obj1.Shape = outer_cyl
                    #         obj1.ViewObject.ShapeColor = tuple(Condscreencolor)
                    #         hole_cyl = Part.makeCylinder(conductor_radius, height * 10, position)
                    #         hollow_cyl = outer_cyl.cut(hole_cyl) 
                    #         Part.show(hollow_cyl)                       
                    #         for obj in doc.Objects:
                    #             if hasattr(obj, "Shape"):
                    #                 obj.Shape = obj.Shape.cut(hole_cyl)
                    #         small_cylinder_radius = wire_radius
                    #         num_levels = int((conductor_radius - small_cylinder_radius) / (2 * small_cylinder_radius))
                    #         for level in range(num_levels + 1):
                    #             level_radius = level * 2 * small_cylinder_radius
                    #             if level_radius < conductor_radius:
                    #                 if level == 0:
                    #                     num_cylinders_in_level = 1
                    #                 else:
                    #                     num_cylinders_in_level = int(2 * math.pi * level_radius / (2 * small_cylinder_radius))
                    #                 if num_cylinders_in_level > 0:
                    #                     angle_step_level = 2 * math.pi / num_cylinders_in_level
                    #                     for k in range(num_cylinders_in_level):
                    #                         x_level = level_radius * math.cos(k * angle_step_level)
                    #                         y_level = level_radius * math.sin(k * angle_step_level)
                    #                         level_position = App.Vector(x + x_level, y + y_level, 0)
                    #                         small_cyl = Part.makeCylinder(small_cylinder_radius, current_height + (j*increment), level_position)
                    #                         obj3 = doc.addObject("Part::Feature", f"Wires_{Conductor_wire_count+1}")
                    #                         obj3.Shape = small_cyl
                    #                         obj3.ViewObject.ShapeColor = tuple(wirecolor)
                    #     else:
                    #         cylinder = Part.makeCylinder(radius, current_height+(j*increment), position)
                    #         obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                    #         obj4.Shape = cylinder
                    #         obj4.ViewObject.ShapeColor = tuple(colors)

                        main_cores_info.append((x, y, outer_radius))
                        print(f"Added to main_cores_info: {(x, y, outer_radius)}")
                # Conductor_count=Conductor_count+1
            # If an extra half–core is needed:
            if extra_cylinder_needed:
                height = spacing_1 *factorforheight* htfac*condlayercount/6
                radius=extra_cylinder_radius
                angle_extra = num_cylinders * angle_step
                x_extra = circle_radius * math.cos(angle_extra)
                y_extra = circle_radius * math.sin(angle_extra)
                extra_position = App.Vector(x_extra, y_extra, 0)
                for j in range(num_concentric_cylinders):
                    if j == 0:
                        spacing = 0
                        colors = parse_color(params.get("lappingColor", "(0.8, 0.8, 0.8)"))
                        name = "Lapping"
                        radius = extra_cylinder_radius - spacing
                        if(spacing_7!=0):
                            cylinder = Part.makeCylinder(radius, height, extra_position)
                            hole_cyl = Part.makeCylinder(halfcoreradii, height * 10, extra_position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                            main_cores_info.append((x, y, outer_radius))
                            print(f"Added to main_cores_info: {(x, y, outer_radius)}")
                    elif j == 1:
                        spacing = spacing_7
                        colors = parse_color(params.get("idTapeColor", "(0.8, 0.8, 0.8)"))
                        name = "Id_tape"
                        radius = extra_cylinder_radius - spacing
                        if(spacing_6 != 0):
                            cylinder = Part.makeCylinder(radius, height,extra_position)
                            hole_cyl = Part.makeCylinder(halfcoreradii, height * 10, extra_position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                    elif j == 2:
                        spacing = spacing_7 + spacing_6
                        colors = parse_color(params.get("metallicScreenColor", "(0.8, 0.8, 0.8)"))
                        name = "Metallic_Screen"
                        radius = extra_cylinder_radius - spacing
                        if(spacing_5 != 0):
                            cylinder = Part.makeCylinder(radius, height, extra_position)
                            hole_cyl = Part.makeCylinder(halfcoreradii, height , extra_position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                    elif j == 3:
                        spacing = spacing_7 + spacing_5 + spacing_6
                        colors = parse_color(params.get("nometallicScreenColor", "(0.8, 0.8, 0.8)"))
                        name = "Non-metallic_Screen"
                        radius = extra_cylinder_radius - spacing
                        if(spacing_4 != 0):
                            cylinder = Part.makeCylinder(radius, height, extra_position)
                            hole_cyl = Part.makeCylinder(halfcoreradii, height , extra_position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                    elif j == 4:
                        spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4
                        colors = parse_color(params.get("insulationColor", "(0.8, 0.8, 0.8)"))
                        name = "Insulation"
                        radius = extra_cylinder_radius - spacing
                        if(spacing_3 != 0):
                            cylinder = Part.makeCylinder(radius, height, extra_position)
                            hole_cyl = Part.makeCylinder(halfcoreradii, height , extra_position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                    elif j == 5:
                        
                        spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4 + spacing_3
                        colors = parse_color(params.get("conductorScreenColor", "(0.8, 0.8, 0.8)"))
                        name = "Conductor_Screen"
                        radius = extra_cylinder_radius - spacing
                        if(spacing_2 != 0):
                            height=height+increment
                            cylinder = Part.makeCylinder(radius, height, extra_position)
                            hole_cyl = Part.makeCylinder(halfcoreradii, height, extra_position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(halfcondscreencolor)
                            
                    elif j == 6:
                        spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4 + spacing_3 + spacing_2
                        colors = [1,1,1]

                        radius = extra_cylinder_radius - spacing
                                
                                                        
                                
                                                                                                                                                        
                                                                                
                                                
                                                                            
                                                                                                                                    
                                                                                            
                                                
                                                
                                                        
                                                                    
                        small_cylinder_radius = wire_radius
                        num_levels = int((halfcoreradii - small_cylinder_radius) / (2 * small_cylinder_radius))
                        for level in range(num_levels + 1):
                                level_radius = level * 2 * small_cylinder_radius
                                if level_radius < halfcoreradii:
                                    if level == 0:
                                        num_cylinders_in_level = 1
                                    else:
                                        num_cylinders_in_level = int(2 * math.pi * level_radius / (2 * small_cylinder_radius))
                                    if num_cylinders_in_level > 0:
                                        angle_step_level = 2 * math.pi / num_cylinders_in_level
                                        for k in range(num_cylinders_in_level):
                                            x_level = level_radius * math.cos(k * angle_step_level)
                                            y_level = level_radius * math.sin(k * angle_step_level)
                                            level_position = App.Vector(x_extra + x_level, y_extra + y_level, 0)
                                            small_cyl = Part.makeCylinder(small_cylinder_radius, height + (increment), level_position)
                                            obj1 = doc.addObject("Part::Feature", f"Wires_{Conductor_wire_count+1}")
                                            obj1.Shape = small_cyl
                                            obj1.ViewObject.ShapeColor = tuple(wirecolor)
                    #     spacing = spacing_7
                    #     colors = idtapecolor
                    #     name1 = "Id_tape"
                    # elif j == 2:
                    #     spacing = spacing_7 + spacing_6
                    #     colors = metallicscreencolor
                    #     name1 = "Metallic_Screen"
                    # elif j == 3:
                    #     spacing = spacing_7 + spacing_5 + spacing_6
                    #     colors = nonmetallicscreencolor
                    #     name1 = "Non metallic_Screen"
                    # elif j == 4:
                    #     spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4
                    #     colors = Insulationcolor
                    #     name1 = "Insulation"
                    # elif j == 5:
                    #     spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4 + spacing_3
                    #     colors = Condscreencolor
                    #     name1 = "Conductor_Screen"
                    # elif j == 6:
                    #     spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4 + spacing_3 + spacing_2
                    #     colors = [1,1,1]

                    # radius = extra_cylinder_radius - spacing
                    # if radius > 0:
                    #     current_height = height + increment
                    #     if j == 6:
                    #         outer_cyl = Part.makeCylinder(halfcoreradii + spacing_2, current_height, extra_position)
                    #         obj1 = doc.addObject("Part::Feature", f"HalfConductor")
                    #         obj1.Shape = outer_cyl
                    #         obj1.ViewObject.ShapeColor =tuple(Condscreencolor)
                    #         hole_cyl = Part.makeCylinder(halfcoreradii, height * 10, extra_position)
                    #         hollow_cyl = outer_cyl.cut(hole_cyl)
                    #         Part.show(hollow_cyl)
                    #         for obj in doc.Objects:
                    #             if hasattr(obj, "Shape"):
                    #                 obj.Shape = obj.Shape.cut(hole_cyl)
                    #         small_cylinder_radius = wire_radius
                    #         num_levels = int((halfcoreradii - small_cylinder_radius) / (2 * small_cylinder_radius))
                    #         for level in range(num_levels + 1):
                    #             level_radius = level * 2 * small_cylinder_radius
                    #             if level_radius < halfcoreradii:
                    #                 if level == 0:
                    #                     num_cylinders_in_level = 1
                    #                 else:
                    #                     num_cylinders_in_level = int(2 * math.pi * level_radius / (2 * small_cylinder_radius))
                    #                 if num_cylinders_in_level > 0:
                    #                     angle_step_level = 2 * math.pi / num_cylinders_in_level
                    #                     for k in range(num_cylinders_in_level):
                    #                         x_level = level_radius * math.cos(k * angle_step_level)
                    #                         y_level = level_radius * math.sin(k * angle_step_level)
                    #                         level_position = App.Vector(x_extra + x_level, y_extra + y_level, 0)
                    #                         small_cyl = Part.makeCylinder(small_cylinder_radius, current_height + (j*increment), level_position)
                    #                         obj1 = doc.addObject("Part::Feature", f"Wires_{Conductor_wire_count+1}")
                    #                         obj1.Shape = small_cyl
                    #                         obj1.ViewObject.ShapeColor = tuple(wirecolor)
                    #     else:
                    #         cylinder = Part.makeCylinder(radius, current_height+(j*increment), extra_position)
                    #         obj1 = doc.addObject("Part::Feature", f"Half core_{name1}")
                    #         obj1.Shape = cylinder
                    #         obj1.ViewObject.ShapeColor = tuple(colors)
                        main_cores_info.append((x_extra, y_extra, extra_cylinder_radius))
                        print(f"Added to main_cores_info: {(x_extra, y_extra, extra_cylinder_radius)}")
                        doc.recompute()
    else:
        for layer_index, nc in enumerate(num_cylinders_per_layer):
            # If the layer value is fractional, then an extra (half) core is needed.
            if nc != int(nc):
                num_whole = int(nc)
                halfcoreradii = params["halfcore_radius"]
                extra_cylinder_radius = halfcoreradii + spacing_2 + spacing_3 + spacing_4 + spacing_5 + spacing_6 + spacing_7
                num_cylinders = num_whole
                extra_cylinder_needed = True
                angle_step = 2 * math.pi / (num_cylinders + 1)
            else:
                extra_cylinder_needed = False
                num_cylinders = int(nc)
                angle_step = 2 * math.pi / num_cylinders if num_cylinders > 0 else 0

            # Calculate circle radius for this layer.
            if layer_index == 0 and (num_cylinders == 1 or num_cylinders == 0):
                circle_radius = 0
            else:
                if layer_index == 0:
                    circle_radius = outer_radius / math.sin(angle_step / 2) if angle_step != 0 else 0
                else:
                    circle_radius = prev_layer_radius + 2 * outer_radius
            prev_layer_radius = circle_radius

            # Place cores in a circular pattern.
            for i in range(num_cylinders):
                Conductor_count=Conductor_count+1
                if i==0 and layer_index==0:
                    height = spacing_1 *factorforheight* htfac*condlayercount/6
                else:
                    height=spacing_1 *factorforheight* htfac*condlayercount/6
                radius=outer_radius
                
                x = circle_radius * math.cos(i * angle_step)
                y = circle_radius * math.sin(i * angle_step)
                position = App.Vector(x, y, 0)
                # For each core, add concentric cylinders.
                for j in range(num_concentric_cylinders):
                    if j == 0:
                        spacing = 0
                        colors = parse_color(params.get("lappingColor", "(0.8, 0.8, 0.8)"))
                        name = "Lapping"
                        radius = outer_radius - spacing
                        if(spacing_7!=0):
                            cylinder = Part.makeCylinder(radius, height, position)
                            hole_cyl = Part.makeCylinder(conductor_radius, height * 10, position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                            main_cores_info.append((x, y, outer_radius))
                            print(f"Added to main_cores_info: {(x, y, outer_radius)}")
                    elif j == 1:
                        spacing = spacing_7
                        colors = parse_color(params.get("idTapeColor", "(0.8, 0.8, 0.8)"))
                        name = "Id_tape"
                        radius = outer_radius - spacing
                        if(spacing_6 != 0):
                            cylinder = Part.makeCylinder(radius, height,position)
                            hole_cyl = Part.makeCylinder(conductor_radius, height * 10, position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                    elif j == 2:
                        spacing = spacing_7 + spacing_6
                        colors = parse_color(params.get("metallicScreenColor", "(0.8, 0.8, 0.8)"))
                        name = "Metallic_Screen"
                        radius = outer_radius - spacing
                        if(spacing_5 != 0):
                            cylinder = Part.makeCylinder(radius, height, position)
                            hole_cyl = Part.makeCylinder(conductor_radius, height , position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                    elif j == 3:
                        spacing = spacing_7 + spacing_5 + spacing_6
                        colors = parse_color(params.get("nometallicScreenColor", "(0.8, 0.8, 0.8)"))
                        name = "Non-metallic_Screen"
                        radius = outer_radius - spacing
                        if(spacing_4 != 0):
                            cylinder = Part.makeCylinder(radius, height, position)
                            hole_cyl = Part.makeCylinder(conductor_radius, height , position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                    elif j == 4:
                        spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4
                        colors = parse_color(params.get("insulationColor", "(0.8, 0.8, 0.8)"))
                        name = "Insulation"
                        radius = outer_radius - spacing
                        if(spacing_3 != 0):
                            cylinder = Part.makeCylinder(radius, height, position)
                            hole_cyl = Part.makeCylinder(conductor_radius, height , position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                    elif j == 5:
                        
                        spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4 + spacing_3
                        colors = parse_color(params.get("conductorScreenColor", "(0.8, 0.8, 0.8)"))
                        name = "Conductor_Screen"
                        radius = outer_radius - spacing
                        if(spacing_2 != 0):
                            height=height+increment
                            cylinder = Part.makeCylinder(radius, height, position)
                            hole_cyl = Part.makeCylinder(conductor_radius, height, position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            
                    elif j == 6:
                        spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4 + spacing_3 + spacing_2
                        colors = [1,1,1]
                        radius = outer_radius - spacing
                                
                                                        
                                
                                                                                            
                                                                                                                                            
                                                                                                                                
                                                
                                                                            
                                                                                                                                
                                                                                            
                                                                        
                                                
                                                        
                                                                    
                        small_cylinder_radius = wire_radius
                        num_levels = int((conductor_radius - small_cylinder_radius) / (2 * small_cylinder_radius))
                        for level in range(num_levels + 1):
                                level_radius = level * 2 * small_cylinder_radius
                                if level_radius < conductor_radius:
                                    if level == 0:
                                        num_cylinders_in_level = 1
                                    else:
                                        num_cylinders_in_level = int(2 * math.pi * level_radius / (2 * small_cylinder_radius))
                                    if num_cylinders_in_level > 0:
                                        angle_step_level = 2 * math.pi / num_cylinders_in_level
                                        for k in range(num_cylinders_in_level):
                                            x_level = level_radius * math.cos(k * angle_step_level)
                                            y_level = level_radius * math.sin(k * angle_step_level)
                                            level_position = App.Vector(x + x_level, y + y_level, 0)
                                            small_cyl = Part.makeCylinder(small_cylinder_radius, height + (increment), level_position)
                                            obj3 = doc.addObject("Part::Feature", f"Wires_{Conductor_wire_count+1}")
                                            obj3.Shape = small_cyl
                                            obj3.ViewObject.ShapeColor = tuple(wirecolor)
                    # radius = outer_radius - spacing
                    # if radius > 0:
                    #     current_height = height + increment
                    #     if j == 6:
                    #         # Create a hollow cylinder (a hole).
                    #         outer_cyl = Part.makeCylinder(spacing_1 + spacing_2, current_height, position)
                    #         obj1 = doc.addObject("Part::Feature", f"Conductor_{Conductor_count}")
                    #         obj1.Shape = outer_cyl
                    #         obj1.ViewObject.ShapeColor = tuple(Condscreencolor)
                    #         hole_cyl = Part.makeCylinder(conductor_radius, height * 10, position)
                    #         hollow_cyl = outer_cyl.cut(hole_cyl) 
                    #         Part.show(hollow_cyl)                       
                    #         for obj in doc.Objects:
                    #             if hasattr(obj, "Shape"):
                    #                 obj.Shape = obj.Shape.cut(hole_cyl)
                    #         small_cylinder_radius = wire_radius
                    #         num_levels = int((conductor_radius - small_cylinder_radius) / (2 * small_cylinder_radius))
                    #         for level in range(num_levels + 1):
                    #             level_radius = level * 2 * small_cylinder_radius
                    #             if level_radius < conductor_radius:
                    #                 if level == 0:
                    #                     num_cylinders_in_level = 1
                    #                 else:
                    #                     num_cylinders_in_level = int(2 * math.pi * level_radius / (2 * small_cylinder_radius))
                    #                 if num_cylinders_in_level > 0:
                    #                     angle_step_level = 2 * math.pi / num_cylinders_in_level
                    #                     for k in range(num_cylinders_in_level):
                    #                         x_level = level_radius * math.cos(k * angle_step_level)
                    #                         y_level = level_radius * math.sin(k * angle_step_level)
                    #                         level_position = App.Vector(x + x_level, y + y_level, 0)
                    #                         small_cyl = Part.makeCylinder(small_cylinder_radius, current_height + (j*increment), level_position)
                    #                         obj3 = doc.addObject("Part::Feature", f"Wires_{Conductor_wire_count+1}")
                    #                         obj3.Shape = small_cyl
                    #                         obj3.ViewObject.ShapeColor = tuple(wirecolor)
                    #     else:
                    #         cylinder = Part.makeCylinder(radius, current_height+(j*increment), position)
                    #         obj4 = doc.addObject("Part::Feature", f"{name}_{Conductor_count}")
                    #         obj4.Shape = cylinder
                    #         obj4.ViewObject.ShapeColor = tuple(colors)

                        main_cores_info.append((x, y, outer_radius))
                        print(f"Added to main_cores_info: {(x, y, outer_radius)}")
                # Conductor_count=Conductor_count+1
            # If an extra half–core is needed:
            if extra_cylinder_needed:
                height = spacing_1 *factorforheight* htfac*condlayercount/6
                radius=extra_cylinder_radius
                angle_extra = num_cylinders * angle_step
                x_extra = circle_radius * math.cos(angle_extra)
                y_extra = circle_radius * math.sin(angle_extra)
                extra_position = App.Vector(x_extra, y_extra, 0)
                for j in range(num_concentric_cylinders):
                    if j == 0:
                        spacing = 0
                        colors = parse_color(params.get("lappingColor", "(0.8, 0.8, 0.8)"))
                        name = "Lapping"
                        radius = extra_cylinder_radius - spacing
                        if(spacing_7!=0):
                            cylinder = Part.makeCylinder(radius, height, extra_position)
                            hole_cyl = Part.makeCylinder(halfcoreradii, height * 10, extra_position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                            main_cores_info.append((x, y, outer_radius))
                            print(f"Added to main_cores_info: {(x, y, outer_radius)}")
                    elif j == 1:
                        spacing = spacing_7
                        colors = parse_color(params.get("idTapeColor", "(0.8, 0.8, 0.8)"))
                        name = "Id_tape"
                        radius = extra_cylinder_radius - spacing
                        if(spacing_6 != 0):
                            cylinder = Part.makeCylinder(radius, height,extra_position)
                            hole_cyl = Part.makeCylinder(halfcoreradii, height * 10, extra_position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                    elif j == 2:
                        spacing = spacing_7 + spacing_6
                        colors = parse_color(params.get("metallicScreenColor", "(0.8, 0.8, 0.8)"))
                        name = "Metallic_Screen"
                        radius = extra_cylinder_radius - spacing
                        if(spacing_5 != 0):
                            cylinder = Part.makeCylinder(radius, height, extra_position)
                            hole_cyl = Part.makeCylinder(halfcoreradii, height , extra_position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                    elif j == 3:
                        spacing = spacing_7 + spacing_5 + spacing_6
                        colors = parse_color(params.get("nometallicScreenColor", "(0.8, 0.8, 0.8)"))
                        name = "Non-metallic_Screen"
                        radius = extra_cylinder_radius - spacing
                        if(spacing_4 != 0):
                            cylinder = Part.makeCylinder(radius, height, extra_position)
                            hole_cyl = Part.makeCylinder(halfcoreradii, height , extra_position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                    elif j == 4:
                        spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4
                        colors = parse_color(params.get("insulationColor", "(0.8, 0.8, 0.8)"))
                        name = "Insulation"
                        radius = extra_cylinder_radius - spacing
                        if(spacing_3 != 0):
                            cylinder = Part.makeCylinder(radius, height, extra_position)
                            hole_cyl = Part.makeCylinder(halfcoreradii, height , extra_position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            height=height+increment
                    elif j == 5:
                        
                        spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4 + spacing_3
                        colors = parse_color(params.get("conductorScreenColor", "(0.8, 0.8, 0.8)"))
                        name = "Conductor_Screen"
                        radius = extra_cylinder_radius - spacing
                        if(spacing_2 != 0):
                            height=height+increment
                            cylinder = Part.makeCylinder(radius, height, extra_position)
                            hole_cyl = Part.makeCylinder(halfcoreradii, height, extra_position)
                            hollow_cyl = cylinder.cut(hole_cyl) 
                            obj4 = doc.addObject("Part::Feature", f"{name}")
                            obj4.Shape = hollow_cyl
                            obj4.ViewObject.ShapeColor = tuple(colors)
                            
                    elif j == 6:
                        spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4 + spacing_3 + spacing_2
                        colors = [1,1,1]

                        radius = extra_cylinder_radius - spacing
                                
                                                        
                                
                                                                                                                                                        
                                                                                
                                                
                                                                            
                                                                                                                                    
                                                                                            
                                                
                                                
                                                        
                                                                    
                        small_cylinder_radius = wire_radius
                        num_levels = int((halfcoreradii - small_cylinder_radius) / (2 * small_cylinder_radius))
                        for level in range(num_levels + 1):
                                level_radius = level * 2 * small_cylinder_radius
                                if level_radius < halfcoreradii:
                                    if level == 0:
                                        num_cylinders_in_level = 1
                                    else:
                                        num_cylinders_in_level = int(2 * math.pi * level_radius / (2 * small_cylinder_radius))
                                    if num_cylinders_in_level > 0:
                                        angle_step_level = 2 * math.pi / num_cylinders_in_level
                                        for k in range(num_cylinders_in_level):
                                            x_level = level_radius * math.cos(k * angle_step_level)
                                            y_level = level_radius * math.sin(k * angle_step_level)
                                            level_position = App.Vector(x_extra + x_level, y_extra + y_level, 0)
                                            small_cyl = Part.makeCylinder(small_cylinder_radius, height + (increment), level_position)
                                            obj1 = doc.addObject("Part::Feature", f"Wires_{Conductor_wire_count+1}")
                                            obj1.Shape = small_cyl
                                            obj1.ViewObject.ShapeColor = tuple(wirecolor)
                    #     spacing = spacing_7
                    #     colors = idtapecolor
                    #     name1 = "Id_tape"
                    # elif j == 2:
                    #     spacing = spacing_7 + spacing_6
                    #     colors = metallicscreencolor
                    #     name1 = "Metallic_Screen"
                    # elif j == 3:
                    #     spacing = spacing_7 + spacing_5 + spacing_6
                    #     colors = nonmetallicscreencolor
                    #     name1 = "Non metallic_Screen"
                    # elif j == 4:
                    #     spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4
                    #     colors = Insulationcolor
                    #     name1 = "Insulation"
                    # elif j == 5:
                    #     spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4 + spacing_3
                    #     colors = Condscreencolor
                    #     name1 = "Conductor_Screen"
                    # elif j == 6:
                    #     spacing = spacing_7 + spacing_6 + spacing_5 + spacing_4 + spacing_3 + spacing_2
                    #     colors = [1,1,1]

                    # radius = extra_cylinder_radius - spacing
                    # if radius > 0:
                    #     current_height = height + increment
                    #     if j == 6:
                    #         outer_cyl = Part.makeCylinder(halfcoreradii + spacing_2, current_height, extra_position)
                    #         obj1 = doc.addObject("Part::Feature", f"HalfConductor")
                    #         obj1.Shape = outer_cyl
                    #         obj1.ViewObject.ShapeColor =tuple(Condscreencolor)
                    #         hole_cyl = Part.makeCylinder(halfcoreradii, height * 10, extra_position)
                    #         hollow_cyl = outer_cyl.cut(hole_cyl)
                    #         Part.show(hollow_cyl)
                    #         for obj in doc.Objects:
                    #             if hasattr(obj, "Shape"):
                    #                 obj.Shape = obj.Shape.cut(hole_cyl)
                    #         small_cylinder_radius = wire_radius
                    #         num_levels = int((halfcoreradii - small_cylinder_radius) / (2 * small_cylinder_radius))
                    #         for level in range(num_levels + 1):
                    #             level_radius = level * 2 * small_cylinder_radius
                    #             if level_radius < halfcoreradii:
                    #                 if level == 0:
                    #                     num_cylinders_in_level = 1
                    #                 else:
                    #                     num_cylinders_in_level = int(2 * math.pi * level_radius / (2 * small_cylinder_radius))
                    #                 if num_cylinders_in_level > 0:
                    #                     angle_step_level = 2 * math.pi / num_cylinders_in_level
                    #                     for k in range(num_cylinders_in_level):
                    #                         x_level = level_radius * math.cos(k * angle_step_level)
                    #                         y_level = level_radius * math.sin(k * angle_step_level)
                    #                         level_position = App.Vector(x_extra + x_level, y_extra + y_level, 0)
                    #                         small_cyl = Part.makeCylinder(small_cylinder_radius, current_height + (j*increment), level_position)
                    #                         obj1 = doc.addObject("Part::Feature", f"Wires_{Conductor_wire_count+1}")
                    #                         obj1.Shape = small_cyl
                    #                         obj1.ViewObject.ShapeColor = tuple(wirecolor)
                    #     else:
                    #         cylinder = Part.makeCylinder(radius, current_height+(j*increment), extra_position)
                    #         obj1 = doc.addObject("Part::Feature", f"Half core_{name1}")
                    #         obj1.Shape = cylinder
                    #         obj1.ViewObject.ShapeColor = tuple(colors)
                        main_cores_info.append((x_extra, y_extra, extra_cylinder_radius))
                        print(f"Added to main_cores_info: {(x_extra, y_extra, extra_cylinder_radius)}")
    doc.recompute()
    return main_cores_info, circle_radius, outer_radius, height, increment

# ------------------------------------------------------------------------------
# Build Insulation Layers
# ------------------------------------------------------------------------------
def build_insulation(doc, circle_radius, outer_radius, height, increment, logger, params,condlayercount):
    spacing1= params["spacing_1"]
    num_cylinders_per_layer = params["num_cylinders_per_layer"]
    htfac = (len(num_cylinders_per_layer))*2
    height = spacing1 *factorforheight* htfac*condlayercount/6
    preinnersheaththickness = params["preinnersheaththickness"]
    preinnersheathcolor = parse_color(params.get("preinnersheathcolor", "(0.8, 0.8, 0.8)"))
    # The pre–inner sheath insulation radius
    innersheathinsuradii = circle_radius + outer_radius + preinnersheaththickness
    if preinnersheaththickness!=0:
        core = Part.makeCylinder(circle_radius + outer_radius, height)
        height = height - (increment)
        innersheathinsu_cylinder = Part.makeCylinder(innersheathinsuradii, height)
        innersheathinsu = innersheathinsu_cylinder.cut(core)
        part = doc.addObject("Part::Feature", "Pre-innersheath insulation")
        part.Shape = innersheathinsu
        part.ViewObject.ShapeColor = tuple(preinnersheathcolor)
      

    innersheaththickness = params["innersheaththickness"]
    innersheathcolor = parse_color(params.get("innersheathcolor", "(0.8, 0.8, 0.8)"))
    innersheathradii = innersheathinsuradii + innersheaththickness
    if innersheaththickness!=0:
        core = Part.makeCylinder(innersheathinsuradii, height)
        height = height - increment
        innersheath_cylinder = Part.makeCylinder(innersheathradii, height )
        innersheath = innersheath_cylinder.cut(core)
        part = doc.addObject("Part::Feature", "Innersheath")
        part.Shape = innersheath
        part.ViewObject.ShapeColor = tuple(innersheathcolor)
       

    overinnersheaththickness = params["overinnersheaththickness"]
    overinnersheathcolor = parse_color(params.get("overinnersheathcolor", "(0.8, 0.8, 0.8)"))
    overinnersheathradii = innersheathradii + overinnersheaththickness
    if overinnersheaththickness!=0:
        core = Part.makeCylinder(innersheathradii, height)
        height = height - (increment)
        overinnersheath_cylinder = Part.makeCylinder(overinnersheathradii, height)
        overinnersheath = overinnersheath_cylinder.cut(core)
        part = doc.addObject("Part::Feature", "Insulation over innersheath")
        part.Shape = overinnersheath
        part.ViewObject.ShapeColor = tuple(overinnersheathcolor)
    doc.recompute()
    return innersheathinsuradii, overinnersheathradii,height

# ------------------------------------------------------------------------------
# Build Armor
# ------------------------------------------------------------------------------
def create_armorstrips(doc,outer_diameter, inner_diameter, ht, arc_length, name="Armor strips"):      
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
        
        # return cut_pieces
def build_armor(doc, overinnersheathradii, height, increment, logger, params):
    
    armor_wire_count=0
    armor_choice = params.get("armor_choice", 1)
    armorcolor = parse_color(params.get("armorcolor", "(0.8, 0.8, 0.8)"))
    if str(armor_choice) == "1":
        cylinder_radius = params.get("cylinder_radius",0)
        r = overinnersheathradii + cylinder_radius
        
        if cylinder_radius!=0:
            height = height - (increment)
            num_cylinders = int(math.floor((2 * math.pi * r) / (2 * cylinder_radius)))
        else:
            num_cylinders = 0
        angle_step = 2 * math.pi / num_cylinders if num_cylinders > 0 else 0
        for i in range(num_cylinders):
            x = r * math.cos(i * angle_step)
            y = r * math.sin(i * angle_step)
            position = App.Vector(x, y, 0)
            cylinder = Part.makeCylinder(cylinder_radius, height, position)
            obj1 = doc.addObject("Part::Feature", f"Armor_wires_{armor_wire_count+1}")
            obj1.Shape = cylinder
            obj1.ViewObject.ShapeColor = tuple(armorcolor)
        logger.info("Built circular armor with %d cylinders", num_cylinders)
        height= height-increment
        return r, height, cylinder_radius
    elif str(armor_choice) == "2":
        side_length = params["side_length"]
        side_thickness = params["side_thickness"]
        r = overinnersheathradii
        height = height - ( increment)
        create_armorstrips(doc,outer_diameter=2*(overinnersheathradii+side_thickness), inner_diameter=2*overinnersheathradii, ht=height, arc_length=side_length)
        # num_cylinders = int(math.floor((2 * math.pi * r) / side_length))
        # angle_step = 360 / num_cylinders if num_cylinders > 0 else 0
        # for i in range(num_cylinders):
        #     angle = math.radians(i * angle_step)
        #     x = r * math.cos(angle)
        #     y = r * math.sin(angle)
        #     cube = Part.makeBox(side_thickness, side_length, cylinder_height)
        #     rotation_angle = (i + 0.5) * angle_step
        #     cube.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), rotation_angle)
        #     cube.translate(App.Vector(x, y, 0))
        #     obj = doc.addObject("Part::Feature", f"Armor_strips_{i+1}")
        #     obj.Shape = cube
        #     obj.ViewObject.ShapeColor = tuple(armorcolor)
        # logger.info("Built cubical armor with %d cylinders", num_cylinders)
        height= height-increment
        return r, height, side_thickness
    else:
        return overinnersheathradii, 0, 0

# ------------------------------------------------------------------------------
# Build Armor Taping and Outer Sheath
# ------------------------------------------------------------------------------
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


def build_armor_taping_and_outersheath(doc, r, armor_ref, height, increment, logger, params,json_file):
    armortapingthickness = params["armortapingthickness"]
    armortapingcolor = parse_color(params.get("armortapingcolor", "(0.8, 0.8, 0.8)"))
    outersheaththickness = params["outersheaththickness"]
    outersheathcolor = parse_color(params.get("outersheathcolor", "(0.8, 0.8, 0.8)"))
    outercolorchoice = params["outercolorchoice"]
    oangle = params["Outerstripangle"]
    outercolor1 = parse_color(params.get("outercolor1", "(0.8, 0.8, 0.8)"))
    outercolor2 = parse_color(params.get("outercolor2", "(0.8, 0.8, 0.8)"))
    armortapingradii = armor_ref + r + armortapingthickness
    
    if armortapingthickness!=0:
        cylinder_height = height 
        height = height - increment
        armoursheath = Part.makeCylinder(armor_ref + r, cylinder_height)
        armorsheath_cylinder = Part.makeCylinder(armortapingradii, height )
        armourtaping = armorsheath_cylinder.cut(armoursheath)
        part = doc.addObject("Part::Feature", "Armor_taping")
        part.Shape = armourtaping
        part.ViewObject.ShapeColor = tuple(armortapingcolor)
        height = height - increment
    logger.info("Armor taping built with outer radius %.2f", armortapingradii)

    outersheathradii = armortapingradii + outersheaththickness    
    with open(json_file, "r") as file:
        params = json.load(file)
    params["Calculated outer radius"] = outersheathradii
    with open(json_file, "w") as file:
        json.dump(params, file, indent=4)
    if outersheaththickness!=0:
        if outercolorchoice == 1:
            cylinder_height = height 
            
            armoursheath = Part.makeCylinder(armortapingradii, cylinder_height)
            outersheath_cylinder = Part.makeCylinder(outersheathradii, height )
            outersheath = outersheath_cylinder.cut(armoursheath)
            part = doc.addObject("Part::Feature", "Outersheath")
            part.Shape = outersheath
            part.ViewObject.ShapeColor = tuple(outersheathcolor)
        if outercolorchoice == 2:                
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

# ------------------------------------------------------------------------------
# Filler Functions
# ------------------------------------------------------------------------------
def place_circles_of_fixed_diameter(doc, existing_circles, boundary_radius, circle_diameter, tries=80000, filler_height=0):
    import random
    r_fixed = circle_diameter / 2.0
    all_circles = list(existing_circles)
    placed_count = 0
    for _ in range(tries):
        angle = 2 * math.pi * random.random()
        rr = boundary_radius * math.sqrt(random.random())
        x_new = rr * math.cos(angle)
        y_new = rr * math.sin(angle)
        if math.hypot(x_new, y_new) + r_fixed > boundary_radius:
            continue
        overlap = False
        for (cx, cy, cr) in all_circles:
            if math.hypot(cx - x_new, cy - y_new) < (cr + r_fixed):
                overlap = True
                break
        if not overlap:
            pos = App.Vector(x_new, y_new, 0)
            cobj = Part.makeCylinder(r_fixed, filler_height, pos)
            doc_obj = doc.addObject("Part::Feature", f"Filler_{circle_diameter:.1f}_{placed_count+1}")
            doc_obj.Shape = cobj
            doc.recompute()
            all_circles.append((x_new, y_new, r_fixed))
            placed_count += 1
    print(f"[place_circles_of_fixed_diameter] Placed {placed_count} of diameter {circle_diameter}")
    return all_circles

def fill_with_discrete_sweeps(doc, existing_circles, boundary_radius, diameters_desc, tries_per_size=80000, filler_height=0):
    all_circles = list(existing_circles)
    for d in diameters_desc:
        print(f"\n===== FILLING with diameter={d} =====")
        all_circles = place_circles_of_fixed_diameter(doc, all_circles, boundary_radius, d, tries_per_size, filler_height)
    return all_circles

def bubble_pack_circles_no_grow(circles, boundary_radius, max_passes=50, step_size=0.001):
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

# ------------------------------------------------------------------------------
# Run Filler Generation
# ------------------------------------------------------------------------------
def run_filler(doc, main_cores_info, innersheathinsuradii, preinnersheaththickness, height, increment, logger, params):
    # Define the leftover region (using pre-innersheath insulation geometry)
    outer_sheath_radius = innersheathinsuradii - preinnersheaththickness

    # Attempt to get filler diameters from params or default to a range if none or empty
    standard_diameters_desc = params.get("fillerDiameters", None)
    if not standard_diameters_desc:  # This will be True if the list is empty or None
        standard_diameters_desc = list(range(50, 8, -1))

    # Log the starting of the filler process with the diameters used
    logger.info(f"[INFO] Starting multi-sweep fill with diameters: {standard_diameters_desc}")

    # Calculate filler height by adding increment to the core height
    filler_height = height

    # Call the function to fill with discrete sweeps and capture the result
    filled_circles = fill_with_discrete_sweeps(doc, main_cores_info, outer_sheath_radius, standard_diameters_desc, tries_per_size=180000, filler_height=filler_height)

    # Return the result of the filling process
    return filled_circles

def create_images(output_file,archoice):
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
    # if str(archoice) == "1":
    #     Gui.runCommand('Std_DrawStyle', 5)

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
    
def create_text_on_outersheath(doc,ocolor,ocolor1, logger, text,text_size, font_path=r"C:\Windows\Fonts\times.ttf"):
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
    candidate_names = ["Outersheath", "Armor_taping", "Insulation_over_innersheath", "Insulation"]
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
    #     if height < est_text_length:
    #         shape_str = Draft.makeShapeString(String=text, FontFile=font_path, Size=adjusted_text_size, Tracking = adjusted_text_size * 0.1)
    #     else:
    #         shape_str = Draft.makeShapeString(String=text, FontFile=font_path, Size=text_size, Tracking = text_size * 0.4)
    # #elif (char_count > 30 and char_count < 50):
    #     #shape_str = Draft.makeShapeString(String=text, FontFile=font_path, Size=text_size, Tracking = text_size * 0.3)
    # else:
    shape_str = Draft.makeShapeString(String=text, FontFile=font_path, Size=adjusted_text_size, Tracking = adjusted_text_size * 0.1)

    #shape_str = Draft.makeShapeString(String=text, FontFile=font_path, Size=adjusted_text_size, Tracking = adjusted_text_size * 0.1)
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

def getFactorForHeight(conductorDia):
    global factorforheight
    if conductorDia > 0    and conductorDia <= 10:
        factorforheight = 70
    elif conductorDia > 10 and conductorDia <= 30:
        factorforheight = 60
    elif conductorDia > 30 and conductorDia <= 60:
        factorforheight = 55
    elif conductorDia > 60 and conductorDia <= 90:
        factorforheight = 50
    elif conductorDia > 90 and conductorDia <= 100:
        factorforheight = 45

# ------------------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="CableConfigCmd Script (Command Prompt Version)")
    parser.add_argument("--jsonFile", help="Path to JSON file with parameters", default=None)
    args = parser.parse_args()

    if args.jsonFile:
        params, output_file, log_file = get_parameters_from_json(args.jsonFile)
    else:
        params, output_file, log_file = get_parameters_interactive()

    getFactorForHeight(params["spacing_1"])
    print(factorforheight)

    logger = setup_logger(log_file)
    logger.info("Starting CableConfig script.")

    doc = App.newDocument("cableconfig")
    QtCore.QCoreApplication.processEvents()

    from conductorlayercalculator import get_non_zero_count
    keys_to_check = ["preinnersheaththickness", "outersheaththickness","innersheaththickness","overinnersheaththickness","armortapingthickness","cylinder_radius","side_thickness"]
    condlayercount = get_non_zero_count(args.jsonFile,keys_to_check)
    # Build core geometry
    main_cores_info, circle_radius, outer_radius, height, increment = build_core_geometry(params, doc, logger,condlayercount)
    QtCore.QCoreApplication.processEvents()
    # Build insulation layers
    innersheathinsuradii, overinnersheathradii,height = build_insulation(doc, circle_radius, outer_radius, height, increment, logger, params,condlayercount)
    QtCore.QCoreApplication.processEvents()
    # Build armor
    r, height, armor_ref = build_armor(doc, overinnersheathradii, height, increment, logger, params)
    # Build armor taping and outer sheath
    build_armor_taping_and_outersheath(doc, r, armor_ref, height, increment, logger, params,args.jsonFile)
    QtCore.QCoreApplication.processEvents()
    # Filler generation
    fillerchoice = params["fillerchoice"]
    if (fillerchoice==1):
        spacing1 = params["spacing_1"]
        num_cylinders_per_layer = params["num_cylinders_per_layer"]
        htfac = (len(num_cylinders_per_layer))*2
        height = (spacing1 *factorforheight* htfac*condlayercount/6)-(increment/2)
        filled_circles = run_filler(doc, main_cores_info, innersheathinsuradii, params["preinnersheaththickness"], height, increment, logger, params)
    doc.recompute()
    QtCore.QCoreApplication.processEvents()
    logger.info("Filler generation complete.")
    doc.saveAs(output_file)                       
    doc.recompute()

    # Make all objects visible
    for obj in doc.Objects:
        vo = getattr(obj, "ViewObject", None)
        if vo is not None:
            vo.Visibility = True
            if hasattr(vo, "ShowInTree"):
                vo.ShowInTree = True
    doc.recompute()
    outersheathcolor = parse_color(params.get("outersheathcolor", "(0, 0, 0)"))
    outercolor1 = parse_color(params.get("outercolor2", "(0, 0, 0)"))
    QtCore.QCoreApplication.processEvents()
    printingMatterText = params.get("printingMatter", "").strip()

    if printingMatterText:
        create_text_on_outersheath(
            doc,
            outersheathcolor,
            outercolor1,
            logger,
            printingMatterText,
            overinnersheathradii * 0.6,
            r"C:\Windows\Fonts\times.ttf"
        )
    else:
        logger.info("No printing matter specified; skipping text creation.")

    #create_text_on_outersheath(doc,outersheathcolor, outercolor1, logger,  params["printingMatter"],overinnersheathradii * 0.6, r"C:\Windows\Fonts\times.ttf")
    doc.saveAs(output_file)                       
    doc.recompute()
    QtCore.QCoreApplication.processEvents()

    #Create Image
    archoice = params.get("armor_choice", 1)
    create_images(output_file,archoice)
    doc.recompute()
    #Create Drawing
    
    import CreateDrawing
    CreateDrawing.CreateDrawing(doc)
    doc.recompute()
                                                                                           

    if output_file:
        try:
            logger.info("Saving FreeCAD document to: %s", output_file)
            doc.saveAs(output_file)
            logger.info("Saved file successfully.")
        except Exception as e:
            logger.error("Error saving document: %s", e)
            sys.exit(1)
    else:
        logger.info("No output file specified; document not saved.")

    
    QMessageBox.information(None, "Operation Complete", "Done Generating! Please Check FreeCad for adjustments!")
    logger.info("CableConfig script completed successfully.")

# ------------------------------------------------------------------------------
# Updated main entry point: launch GUI first then run main() via Qt timer
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Launch the FreeCAD GUI main window
    Gui.showMainWindow()
    # Delay execution of the main function to ensure the GUI is visible.
    delay_ms = 1000  # delay in milliseconds; adjust if needed
    QtCore.QTimer.singleShot(delay_ms, main)
    # Start the FreeCAD GUI event loop (this call blocks until the GUI is closed)
    Gui.exec_loop()
