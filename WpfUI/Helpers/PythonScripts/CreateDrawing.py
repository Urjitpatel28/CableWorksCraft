import os
import FreeCAD as App
import FreeCADGui as Gui
import TechDraw
import TechDrawGui
import Part
import sys
#sys.path.append(r"D:\00.WORK\SOURCE_REPS\CableWorksCraft\WpfUI\Helpers\PythonScripts")
import BaloonHelper

# Use the active document in FreeCAD
def CreateBallonOld(doc):
    top_view_obj = doc.getObject("TopView")
    if not top_view_obj:
        import FreeCAD
        FreeCAD.Console.PrintWarning("TopView not found.\n")
    else:
        
        balloon_obj = BaloonHelper.attach_balloon_to_shape(doc, "Wires", 30, 80, top_view_obj, -1, 0, "A")
        balloon_obj = BaloonHelper.attach_balloon_to_shape(doc, "conductor", 30, 60, top_view_obj, -1, 0, "B")
        
        balloon_obj = BaloonHelper.attach_balloon_to_shape(doc, "Pre_innersheath_insulation", 35, 40, top_view_obj, -1, 0, "C")
        balloon_obj = BaloonHelper.attach_balloon_to_shape(doc, "innersheath", 30, 20, top_view_obj, -1, 0, "D")
        balloon_obj = BaloonHelper.attach_balloon_to_shape(doc, "outersheath", 30, -20, top_view_obj, -1, 0, "E")
        balloon_obj = BaloonHelper.attach_balloon_to_shape(doc, "armor_taping", 30, -40, top_view_obj, -1, 0, "F")
        balloon_obj = BaloonHelper.attach_balloon_to_shape(doc, "armor_wires", 30, -60, top_view_obj, -1, 0, "G")
        balloon_obj = BaloonHelper.attach_balloon_to_shape(doc, "Insulation_over_innersheath", 30, -80, top_view_obj, -1, 0, "H")
import re

def CreateBallon(doc):
    #import FreeCAD
    top_view_obj = doc.getObject("TopView")


    # 1) Collect all Part::Feature objects with a valid Shape.
    all_shapes = [
        obj for obj in doc.Objects
        if obj.TypeId.startswith("Part::Feature")
        and hasattr(obj, "Shape")
        and not obj.Shape.isNull()
    ]

    # 2) Define a custom reference list of name prefixes in the order you want them labeled.
        #    (Adjust these entries to match your actual naming conventions.)
    custom_list = [
        "Wires",
        "Conductor",
        "Conductor_Screen",
        "Insulation",
        "Innersheath",
        "Insulation_over_innersheath",
        "Armor_taping",
        "Outersheath",
        "Armor_wires",
        "Outersheath",
        "Pre_innersheath_insulation",
        "Lapping",
        "Id_tape",
        "Metallic_Screen",
        "Non_metallic_Screen",
        "Filler",
        # ... and so on, as needed ...
    ]

    def get_priority(base_name):
            """Return the index if base_name starts with an entry in custom_list, else fallback."""
            # Convert base_name to lowercase for comparison
            bn_lower = base_name.lower()
            for i, ref_prefix in enumerate(custom_list):
                if bn_lower == ref_prefix.lower():
                    return i
            # If no match found, return a large fallback
            return len(custom_list) + 999

    import re
    # 2) For each shape, compute a 'base name' by removing trailing _###.
    #    We keep the *first* shape encountered for each base name.
    shape_map = {}
    for obj in all_shapes:
        # Skip the object if its name is "CompoundForDrawing" (case-insensitive)
        if obj.Name.lower() == "compoundfordrawing":
            continue
        if obj.Name.lower() == "_outersheathstrip":
            continue
        # Skip objects whose name is in the form "Shape" followed by only digits (e.g., "Shape001")
        if re.match(r'^Shape+$', obj.Name, re.IGNORECASE):
            continue
        if re.match(r'^Shape\d+$', obj.Name, re.IGNORECASE):
            continue
        # Split the name at the first underscore that is immediately followed by a digit.
        base_name = re.split(r'_(?=\d)', obj.Name)[0].strip()
        if base_name not in shape_map:
            shape_map[base_name] = obj

    # 4) Build a list of (obj, base_name, y_max, priority).
    shape_list = []
    for bn, shape_obj in shape_map.items():
        y_max = shape_obj.Shape.BoundBox.YMax
        priority = get_priority(bn)  # custom order index or fallback
        shape_list.append((shape_obj, bn, y_max, priority))

    # 5) Sort:
    #    First by priority ascending (lower = earlier in custom_list),
    #    then by YMax descending for shapes with the same priority
    #    so shapes in the same category are sorted top-to-bottom.
    shape_list.sort(key=lambda x: (x[3], -x[2]))

    # 5) Label them from top to bottom with A, B, C, ...
    # 6) Determine Y range from the TopView's source bounding box.
    # Retrieve a suitable object from the candidate list for text placement.
    candidate_names = ["Outersheath", "Armor_strips", "Insulation_over_innersheath", "innersheath", "Insulation"]
    cylinder_obj = None
    for name in candidate_names:
        cylinder_obj = doc.getObject(name)
        if cylinder_obj:
            break
    
    
    if cylinder_obj and hasattr(top_view_obj, "Source") and top_view_obj.Source:
        top_bbox = cylinder_obj.Shape.BoundBox
        total_height = float(top_bbox.YMax - top_bbox.YMin)
        num_balloons = len(shape_list)
        if num_balloons > 0:
            start_y = float(top_bbox.YMax)  # Starting position: Ymax - 20
            decrement = total_height / num_balloons  # Evenly distribute along Y direction
        else:
            start_y = 90
            decrement = 12
    else:
        start_y = 90
        decrement = 12

    label_ord = ord('A')     # Starting label: 'A'
    #start_y = 90            # Start Y offset
    #decrement = 12          # Decrement for each shape
    for i, (shape_obj, bn, y_max, priority) in enumerate(shape_list):
            current_y = start_y - i * decrement
            label_char = chr(label_ord + i)
            y = 0
            if i<5 or i>10:
                y = 0
       

            # We can pass shape_obj.Name as the balloon text to see the actual object name
            # Or we can use bn if you prefer the base name.
            BaloonHelper.attach_balloon_to_shape(
                doc,
                shape_obj.Name,  # pass the real object name to find the shape
                30,              # x_position offset (on the right)
                current_y,       # y_position offset
                top_view_obj,
                0,               # x_anchorOffset
                y,               # y_anchorOffset
                label_char,       
                #shape_obj.Name,   # balloon text = actual shape name
            )

def CreateBallonSectoral(doc):
    #import FreeCAD
    top_view_obj = doc.getObject("TopView")


    # 1) Collect all Part::Feature objects with a valid Shape.
    all_shapes = [
        obj for obj in doc.Objects
        if obj.TypeId.startswith("Part::Feature")
        and hasattr(obj, "Shape")
        and not obj.Shape.isNull()
    ]

    # 2) Define a custom reference list of name prefixes in the order you want them labeled.
        #    (Adjust these entries to match your actual naming conventions.)
    custom_list = [
        "Wires",
        "Conductor",
        "Conductor_Screen",
        "Insulation",
        "Innersheath",
        "Insulation_over_innersheath",
        "Armor_taping",
        "Outersheath",
        "Armor_wires",
        "Outersheath",
        "Pre_innersheath_insulation",
        "Lapping",
        "Id_tape",
        "Metallic_Screen",
        "Non_metallic_Screen",
        "Filler",
        # ... and so on, as needed ...
    ]

    def get_priority(base_name):
            """Return the index if base_name starts with an entry in custom_list, else fallback."""
            # Convert base_name to lowercase for comparison
            bn_lower = base_name.lower()
            for i, ref_prefix in enumerate(custom_list):
                if bn_lower == ref_prefix.lower():
                    return i
            # If no match found, return a large fallback
            return len(custom_list) + 999

    import re
    # 2) For each shape, compute a 'base name' by removing trailing _###.
    #    We keep the *first* shape encountered for each base name.
    shape_map = {}
    for obj in all_shapes:
        # Skip the object if its name is "CompoundForDrawing" (case-insensitive)
        if obj.Name.lower() == "compoundfordrawing":
            continue
        # Skip objects whose name is in the form "Shape" followed by only digits (e.g., "Shape001")
        if re.match(r'^Shape+$', obj.Name, re.IGNORECASE):
            continue
        if re.match(r'^Shape\d+$', obj.Name, re.IGNORECASE):
            continue
        # Split the name at the first underscore that is immediately followed by a digit.
        base_name = re.split(r'_(?=\d)', obj.Name)[0].strip()
        if base_name not in shape_map:
            shape_map[base_name] = obj

    # 4) Build a list of (obj, base_name, y_max, priority).
    shape_list = []
    for bn, shape_obj in shape_map.items():
        y_max = shape_obj.Shape.BoundBox.YMax
        priority = get_priority(bn)  # custom order index or fallback
        shape_list.append((shape_obj, bn, y_max, priority))

    # 5) Sort:
    #    First by priority ascending (lower = earlier in custom_list),
    #    then by YMax descending for shapes with the same priority
    #    so shapes in the same category are sorted top-to-bottom.
    shape_list.sort(key=lambda x: (x[3], -x[2]))

    # 5) Label them from top to bottom with A, B, C, ...
    # 6) Determine Y range from the TopView's source bounding box.
    # Retrieve a suitable object from the candidate list for text placement.
    candidate_names = ["Outersheath", "Armor_strips", "Insulation_over_innersheath", "innersheath","Insulation_Screen", "Insulation"]
    cylinder_obj = None
    for name in candidate_names:
        cylinder_obj = doc.getObject(name)
        if cylinder_obj:
            break
    
    
    if cylinder_obj and hasattr(top_view_obj, "Source") and top_view_obj.Source:
        top_bbox = cylinder_obj.Shape.BoundBox
        total_height = float(top_bbox.YMax - top_bbox.YMin)
        num_balloons = len(shape_list)
        if num_balloons > 0:
            start_y = float(top_bbox.YMax)  # Starting position: Ymax - 20
            decrement = total_height / num_balloons  # Evenly distribute along Y direction
        else:
            start_y = 90
            decrement = 12
    else:
        start_y = 90
        decrement = 12

    label_ord = ord('A')     # Starting label: 'A'
    #start_y = 90            # Start Y offset
    #decrement = 12          # Decrement for each shape
    for i, (shape_obj, bn, y_max, priority) in enumerate(shape_list):
            current_y = start_y - i * decrement
            label_char = chr(label_ord + i)
            y = 0
            if i<5 or i>10:
                y = 0
       

            # We can pass shape_obj.Name as the balloon text to see the actual object name
            # Or we can use bn if you prefer the base name.
            BaloonHelper.attach_balloon_to_shape_sectoral(
                doc,
                shape_obj.Name,  # pass the real object name to find the shape
                30,              # x_position offset (on the right)
                current_y,       # y_position offset
                top_view_obj,
                0,               # x_anchorOffset
                y,               # y_anchorOffset
                label_char,       
                #shape_obj.Name,   # balloon text = actual shape name
            )

def CreateDrawing(doc):
# Determine the output SVG file path: if the document is saved, use its directory; otherwise, use the current directory.
    doc_dir = ""
    if doc.FileName:
        doc_dir = os.path.dirname(doc.FileName)
    else:
        doc_dir = os.getcwd()
    target_dir = os.path.join(doc_dir,"Images")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    output_svg = os.path.join(target_dir, "2D_Drawing.svg")

    # Create a compound of all available Part::Feature shapes from the active document.
    shapes = [obj.Shape for obj in doc.Objects if obj.TypeId.startswith("Part::Feature") and hasattr(obj, "Shape") and not obj.Shape.isNull()]
    if not shapes:
        print("No shapes found in the document!")
        sys.exit(1)

    compound = Part.makeCompound(shapes)
    # Create a new object in the document to hold the compound shape.
    comp_obj = doc.addObject("Part::Feature", "CompoundForDrawing")
    comp_obj.Shape = compound
    comp_obj.ViewObject.Visibility = False  # <-- This hides it in the GUI
    doc.recompute()

    # Create a new TechDraw drawing page in the active document.
    page = doc.addObject("TechDraw::DrawPage", "DrawingPage")

    # Set up an A4 Landscape blank template using the correct path.
    #template_path = r"C:\Program Files\FreeCAD 1.0\data\Mod\TechDraw\Templates\A3_Landscape_blank.svg"
    #TODO: As per the sheet size ballon positions need to be changed
    template_path = os.path.join(App.getResourceDir(), "Mod", "TechDraw", "Templates", "A2_Landscape_blank.svg")
    
    if not os.path.exists(template_path):
        print("Template not found at:", template_path)
    else:
        template = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
        template.Template = template_path
        page.Template = template

    # Create a TechDraw DrawViewPart for a TOP view with 1:1 scale.
    view = doc.addObject("TechDraw::DrawViewPart", "TopView")
    view.Source = comp_obj  # Use the compound as the source for the view.
    view.Direction = (0.0, 0.0, 1.0)  # Set the view to look from the top.
    view.Scale = 1.0  # 1:1 scale.



    # Add the view to the drawing page.
    page.addView(view)
    doc.recompute()
    page.recompute()
    # -----------------------------------------------------------
    # Force GUI update (if needed) before exporting.
    import FreeCADGui
    FreeCADGui.updateGui()
    #TechDrawGui.updateGui()
    FreeCADGui.ActiveDocument.getObject('TopView').LineWidth = '0.0 mm'
    import FreeCAD
    #bal1 = FreeCAD.ActiveDocument.addObject('TechDraw::DrawViewBalloon','Balloon')
    #rc = page.addView(bal1)
    FreeCADGui.updateGui()
    doc.recompute()
    page.recompute()
    CreateBallon(doc)

    FreeCADGui.updateGui()
    doc.recompute()
    page.recompute()
    # Optionally, save the document with the drawing page included.
    FreeCADGui.updateGui()
    view.recompute()
    doc.save()
    FreeCADGui.SendMsgToActiveView("ViewTop")
    import time
    time.sleep(3)
    top_view = doc.getObject("TopView")
    if top_view:
        FreeCADGui.updateGui()
        top_view.recompute()
        page.recompute()
        doc.recompute()
        FreeCADGui.updateGui()
    
    # Export the drawing page to an SVG file using the correct method.
    try:
          # Sleep for 1000 milliseconds (1 second)
        TechDrawGui.exportPageAsSvg(page, output_svg)
        #TechDrawGui.exportPageAsSvg(view, "C:\\ProjectRoot\\CircularColTest\\Output\\Test.svg")
        print("Drawing exported to:", output_svg)
    except Exception as e:
        print("Error exporting drawing:", e)

def CreateDrawingSectoral(doc):
# Determine the output SVG file path: if the document is saved, use its directory; otherwise, use the current directory.
    doc_dir = ""
    if doc.FileName:
        doc_dir = os.path.dirname(doc.FileName)
    else:
        doc_dir = os.getcwd()
    target_dir = os.path.join(doc_dir,"Images")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    output_svg = os.path.join(target_dir, "2D_Drawing.svg")

    # Create a compound of all available Part::Feature shapes from the active document.
    shapes = [obj.Shape for obj in doc.Objects if obj.TypeId.startswith("Part::Feature") and hasattr(obj, "Shape") and not obj.Shape.isNull() and not obj.Name.startswith("Wires")]
    if not shapes:
        print("No shapes found in the document!")
        sys.exit(1)

    compound = Part.makeCompound(shapes)
    # Create a new object in the document to hold the compound shape.
    comp_obj = doc.addObject("Part::Feature", "CompoundForDrawing")
    comp_obj.Shape = compound
    comp_obj.ViewObject.Visibility = False  # <-- This hides it in the GUI
    doc.recompute()

    # Create a new TechDraw drawing page in the active document.
    page = doc.addObject("TechDraw::DrawPage", "DrawingPage")

    # Set up an A4 Landscape blank template using the correct path.
    #template_path = r"C:\Program Files\FreeCAD 1.0\data\Mod\TechDraw\Templates\A3_Landscape_blank.svg"
    #TODO: As per the sheet size ballon positions need to be changed
    template_path = os.path.join(App.getResourceDir(), "Mod", "TechDraw", "Templates", "A3_Landscape_blank.svg")
    
    if not os.path.exists(template_path):
        print("Template not found at:", template_path)
    else:
        template = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
        template.Template = template_path
        page.Template = template

    # Create a TechDraw DrawViewPart for a TOP view with 1:1 scale.
    view = doc.addObject("TechDraw::DrawViewPart", "TopView")
    view.Source = comp_obj  # Use the compound as the source for the view.
    view.Direction = (0.0, 0.0, 1.0)  # Set the view to look from the top.
    view.Scale = 1.0  # 1:1 scale.



    # Add the view to the drawing page.
    page.addView(view)
    doc.recompute()
    page.recompute()
    # -----------------------------------------------------------
    # Force GUI update (if needed) before exporting.
    import FreeCADGui
    FreeCADGui.updateGui()
    #TechDrawGui.updateGui()
    FreeCADGui.ActiveDocument.getObject('TopView').LineWidth = '0.0 mm'
    import FreeCAD
    #bal1 = FreeCAD.ActiveDocument.addObject('TechDraw::DrawViewBalloon','Balloon')
    #rc = page.addView(bal1)
    FreeCADGui.updateGui()
    doc.recompute()
    page.recompute()
    CreateBallonSectoral(doc)

    FreeCADGui.updateGui()
    doc.recompute()
    page.recompute()
    # Optionally, save the document with the drawing page included.
    FreeCADGui.updateGui()
    view.recompute()
    doc.save()
    FreeCADGui.SendMsgToActiveView("ViewTop")
    import time
    time.sleep(3)
    top_view = doc.getObject("TopView")
    if top_view:
        FreeCADGui.updateGui()
        top_view.recompute()
        page.recompute()
        doc.recompute()
        FreeCADGui.updateGui()
    
    # Export the drawing page to an SVG file using the correct method.
    try:
          # Sleep for 1000 milliseconds (1 second)
        TechDrawGui.exportPageAsSvg(page, output_svg)
        #TechDrawGui.exportPageAsSvg(view, "C:\\ProjectRoot\\CircularColTest\\Output\\Test.svg")
        print("Drawing exported to:", output_svg)
    except Exception as e:
        print("Error exporting drawing:", e)



