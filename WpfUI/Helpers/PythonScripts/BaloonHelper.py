import os
import FreeCAD as App
import FreeCADGui

def attach_balloon_to_shape(doc, shape_name, x_position, y_position, view_obj, x_anchorOffset, y_anchorOffset, ballon_text):
    """
    Searches for the first document object whose name starts with shape_name (case-insensitive),
    computes its bounding box, and creates a TechDraw balloon attached to the provided view.
    The balloon bubble is positioned to the right of the bounding box with a fixed horizontal offset.
    
    Parameters:
      shape_name (str): The prefix of the shape's name to search for (e.g., "outersheath").
      x_position (float): Additional x position offset for the balloon bubble.
      y_position (float): A vertical offset for the balloon bubble.
      view_obj: The TechDraw view object to attach the balloon to.
      x_anchorOffset (float): A value to add to the bounding box XMax for leader origin.
      y_anchorOffset (float): A value to add to the leader origin Y coordinate.
      ballon_text (str): The text to display in the balloon.
    
    Returns:
      The balloon object if created, otherwise None.
    """
    armor_obj = None
    for obj in doc.Objects:
        if obj.Name.lower().startswith(shape_name.lower()):
            armor_obj = obj
            break

    #TODO: This is hardcoded as per the model shape name ! Change It
    #outer_sheath_obj =  doc.getObject("Outersheath")
    # Retrieve a suitable object from the candidate list for text placement.
    candidate_names = ["Outersheath", "Armor_Taping", "Insulation_over_innersheath", "innersheath", "Insulation"]
    outer_sheath_obj = None
    for name in candidate_names:
        outer_sheath_obj = doc.getObject(name)
        if outer_sheath_obj:
            break
    if not outer_sheath_obj:
        #logger.error("No suitable object found from candidate list: {}.\n".format(candidate_names))
        return None
    
    
    if armor_obj and hasattr(armor_obj, "Shape") and not armor_obj.Shape.isNull():
        bbox = armor_obj.Shape.BoundBox
        # Use a fixed horizontal offset of 50 units from the right edge of the bounding box.
        
        # Use a fixed horizontal position from bounding box (example values)
        if outer_sheath_obj and hasattr(outer_sheath_obj, "Shape") and not outer_sheath_obj.Shape.isNull():
            view_x_max = float(outer_sheath_obj.Shape.BoundBox.XMax)
        else:
            view_x_max = 0.0
        top_view_obj1 = doc.getObject("TopView")
        if top_view_obj1:
            view_pos_x = float(top_view_obj1.X)
            view_pos_y = float(top_view_obj1.Y)
        else:
            view_pos_x = 0.0
            view_pos_y = 0.0

        balloon_pos = App.Vector(view_x_max + x_position, y_position, 0)

        bal = doc.addObject('TechDraw::DrawViewBalloon','Balloon')
        bal.Text = ballon_text
        # Set leader origin relative to the drawing view: here, we attach it at the right edge of the shape.
        bal.OriginX = bbox.XMax + x_anchorOffset
        bal.OriginY = 0.0 + y_anchorOffset
        #Get Origin for Armor
        if armor_obj.Name.lower().startswith("filler"):
            y_val = (bbox.YMax - bbox.YMin)/2
            if bbox.YMax < 0 and bbox.YMin < 0:
                y_val = y_val - bbox.YMin
                bal.OriginY = - y_val
            else:
                y_val = y_val + bbox.YMin
                bal.OriginY = y_val + y_anchorOffset
            bal.OriginX = bbox.XMax + x_anchorOffset
            
        # Set the balloon's bubble position
        bal.X = balloon_pos.x
        if view_x_max < 15:
            bal.X = balloon_pos.x - 20

        bal.Y = balloon_pos.y
        bal.Scale = 1.0
        bal.BubbleShape = u"Rectangle"
        bal.EndType = u"None"
        # Attach the balloon to the provided TechDraw view
        try:
            bal.SourceView = view_obj
        except AttributeError:
            # Some versions may not have SourceView; in that case, do nothing.
            pass
        # Retrieve the drawing page object (assumed to be named "DrawingPage")
        drawing_page = doc.getObject("DrawingPage")
        if drawing_page:
            drawing_page.addView(bal)
        else:
            FreeCAD.Console.PrintWarning("DrawingPage not found in document.\n")
        if view_x_max < 15:
            FreeCADGui.ActiveDocument.getObject(bal.Name).LineWidth = '0.0 mm'
            FreeCADGui.ActiveDocument.getObject(bal.Name).Fontsize = '1.5 mm'
            #FreeCADGui.ActiveDocument.getObject(bal.Name).Fontsize = 0.5
        elif view_x_max < 50 and view_x_max > 15:
            FreeCADGui.ActiveDocument.getObject(bal.Name).LineWidth = '0.0 mm'
            FreeCADGui.ActiveDocument.getObject(bal.Name).Fontsize = '3.0 mm'
        elif view_x_max < 100 and view_x_max > 50:
            FreeCADGui.ActiveDocument.getObject(bal.Name).LineWidth = '0.1 mm'
            FreeCADGui.ActiveDocument.getObject(bal.Name).Fontsize = '3.0 mm'
        else:
            FreeCADGui.ActiveDocument.getObject(bal.Name).LineWidth = '0.35 mm'
            #FreeCADGui.ActiveDocument.getObject(bal.Name).Fontsize = '3.0 mm'
        
        doc.recompute()
        # Debug: print the balloon's position and leader origin.
        print("Balloon '%s' created:" % ballon_text)
        print("  Leader Origin: (%.3f, %.3f)" % (bal.OriginX, bal.OriginY))
        print("  Leader position: (%.3f, %.3f)" % (view_pos_x, view_pos_y))
        print("  Balloon Bubble Position: (%.3f, %.3f)" % (bal.X, bal.Y))
        return bal
    else:
        FreeCAD.Console.PrintWarning("No shape found starting with '%s' to annotate.\n" % shape_name)
        return None
    
def attach_balloon_to_shape_sectoral(doc, shape_name, x_position, y_position, view_obj, x_anchorOffset, y_anchorOffset, ballon_text):
    """
    Searches for the first document object whose name starts with shape_name (case-insensitive),
    computes its bounding box, and creates a TechDraw balloon attached to the provided view.
    The balloon bubble is positioned to the right of the bounding box with a fixed horizontal offset.
    
    Parameters:
      shape_name (str): The prefix of the shape's name to search for (e.g., "outersheath").
      x_position (float): Additional x position offset for the balloon bubble.
      y_position (float): A vertical offset for the balloon bubble.
      view_obj: The TechDraw view object to attach the balloon to.
      x_anchorOffset (float): A value to add to the bounding box XMax for leader origin.
      y_anchorOffset (float): A value to add to the leader origin Y coordinate.
      ballon_text (str): The text to display in the balloon.
    
    Returns:
      The balloon object if created, otherwise None.
    """
    armor_obj = None
    for obj in doc.Objects:
        if obj.Name.lower().startswith(shape_name.lower()):
            armor_obj = obj
            break

    #TODO: This is hardcoded as per the model shape name ! Change It
    #outer_sheath_obj =  doc.getObject("Outersheath")
    # Retrieve a suitable object from the candidate list for text placement.
    candidate_names = ["Outersheath", "Armor_strips", "Insulation_over_innersheath", "innersheath","Insulation_Screen", "Insulation"]
    outer_sheath_obj = None
    for name in candidate_names:
        outer_sheath_obj = doc.getObject(name)
        if outer_sheath_obj:
            break
    if not outer_sheath_obj:
        #logger.error("No suitable object found from candidate list: {}.\n".format(candidate_names))
        return None
    
    
    if armor_obj and hasattr(armor_obj, "Shape") and not armor_obj.Shape.isNull():
        bbox = armor_obj.Shape.BoundBox
        # Use a fixed horizontal offset of 50 units from the right edge of the bounding box.
        
        # Use a fixed horizontal position from bounding box (example values)
        if outer_sheath_obj and hasattr(outer_sheath_obj, "Shape") and not outer_sheath_obj.Shape.isNull():
            view_x_max = float(outer_sheath_obj.Shape.BoundBox.XMax)
        else:
            view_x_max = 0.0
        top_view_obj1 = doc.getObject("TopView")
        if top_view_obj1:
            view_pos_x = float(top_view_obj1.X)
            view_pos_y = float(top_view_obj1.Y)
        else:
            view_pos_x = 0.0
            view_pos_y = 0.0

        balloon_pos = App.Vector(view_x_max + x_position, y_position, 0)

        bal = doc.addObject('TechDraw::DrawViewBalloon','Balloon')
        bal.Text = ballon_text
        # Set leader origin relative to the drawing view: here, we attach it at the right edge of the shape.
        bal.OriginX = bbox.XMax + x_anchorOffset
        bal.OriginY = 0.0 + y_anchorOffset
        #Get Origin for Armor
        if armor_obj.Name.lower().startswith("wires"):
            y_val = (bbox.YMax - bbox.YMin)/2
            if bbox.YMax < 0 and bbox.YMin < 0:
                y_val = y_val - bbox.YMin
                bal.OriginY = - y_val
            else:
                y_val = y_val + bbox.YMin
                bal.OriginY = y_val + y_anchorOffset
            bal.OriginX = bbox.XMax + x_anchorOffset
            
        # Set the balloon's bubble position
        bal.X = balloon_pos.x
        if view_x_max < 15:
            bal.X = balloon_pos.x - 20

        bal.Y = balloon_pos.y
        bal.Scale = 1.0
        bal.BubbleShape = u"Rectangle"
        bal.EndType = u"None"
        # Attach the balloon to the provided TechDraw view
        try:
            bal.SourceView = view_obj
        except AttributeError:
            # Some versions may not have SourceView; in that case, do nothing.
            pass
        # Retrieve the drawing page object (assumed to be named "DrawingPage")
        drawing_page = doc.getObject("DrawingPage")
        if drawing_page:
            drawing_page.addView(bal)
        else:
            FreeCAD.Console.PrintWarning("DrawingPage not found in document.\n")
        if view_x_max < 15:
            FreeCADGui.ActiveDocument.getObject(bal.Name).LineWidth = '0.0 mm'
            FreeCADGui.ActiveDocument.getObject(bal.Name).Fontsize = '1.5 mm'
            #FreeCADGui.ActiveDocument.getObject(bal.Name).Fontsize = 0.5
        elif view_x_max < 50 and view_x_max > 15:
            FreeCADGui.ActiveDocument.getObject(bal.Name).LineWidth = '0.0 mm'
            FreeCADGui.ActiveDocument.getObject(bal.Name).Fontsize = '3.0 mm'
        elif view_x_max < 100 and view_x_max > 50:
            FreeCADGui.ActiveDocument.getObject(bal.Name).LineWidth = '0.1 mm'
            FreeCADGui.ActiveDocument.getObject(bal.Name).Fontsize = '3.0 mm'
        else:
            FreeCADGui.ActiveDocument.getObject(bal.Name).LineWidth = '0.35 mm'
            #FreeCADGui.ActiveDocument.getObject(bal.Name).Fontsize = '3.0 mm'
        
        doc.recompute()
        # Debug: print the balloon's position and leader origin.
        print("Balloon '%s' created:" % ballon_text)
        print("  Leader Origin: (%.3f, %.3f)" % (bal.OriginX, bal.OriginY))
        print("  Leader position: (%.3f, %.3f)" % (view_pos_x, view_pos_y))
        print("  Balloon Bubble Position: (%.3f, %.3f)" % (bal.X, bal.Y))
        return bal
    else:
        FreeCAD.Console.PrintWarning("No shape found starting with '%s' to annotate.\n" % shape_name)
        return None