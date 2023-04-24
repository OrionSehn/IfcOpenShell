import ifcopenshell
from ifcopenshell.util.shape_builder import ShapeBuilder
from mathutils import Vector

V = lambda *x: Vector([float(i) for i in x])


# TODO: move examples to more suitable place
def simple_uses():
    def mm(x):
        """mm to meters"""
        return x / 1000

    ifc_file = ifcopenshell.file()
    builder = ShapeBuilder(ifc_file)

    coords = [V(0, 0, 1), V(1, 0, 1), V(2, 0, 1)]
    path = builder.polyline(coords, closed=False, arc_points=[])
    print(path)

    return
    railing_diameter = mm(50)
    railing_radius = railing_diameter/2
    coords = [V(0, 0, 1), V(1, 0, 1), V(2, 0, 1)]
    disk_path = builder.polyline(coords, closed=False)
    disk_solid = builder.create_swept_disk_solid(disk_path, railing_radius)

    terminal_radius = mm(150)
    start = coords[0]
    ter_dir = (coords[0]-coords[1]).xy.to_3d().normalized()
    terminal_coords = [start]
    terminal_coords.append(start + ter_dir * terminal_radius + terminal_radius*V(0,0,-1))
    terminal_coords.append(start + terminal_radius * 2 * V(0,0,-1))
    terminal_path = builder.polyline(terminal_coords, closed=False)
    terminal_solid = builder.create_swept_disk_solid(terminal_path, railing_radius)

    ifc_file.write("tmp.ifc")


def generate_desk_test():
    ifc_file = ifcopenshell.file()
    desks = [
        generate_simple_desk(ifc_file, 1000, 600, 730),
        generate_simple_desk(ifc_file, 1200, 700, 750),
        generate_simple_desk(ifc_file, 1500, 800, 750),
    ]
    print(f"desks: {desks}")

    table = generate_table(ifc_file, 1000, 600, 730)
    print(f"table: {table}")

    ifc_file.write("tmp.ifc")


def mirror_placement_test():
    ifc_file = ifcopenshell.api.run("project.create_file")
    project = ifcopenshell.api.run(
        "root.create_entity", ifc_file, ifc_class="IfcProject", name=f"Non-structural assets library"
    )
    library = ifcopenshell.api.run(
        "root.create_entity", ifc_file, ifc_class="IfcProjectLibrary", name=f"Non-structural assets library"
    )
    ifcopenshell.api.run("project.assign_declaration", ifc_file, definition=library, relating_context=project)
    unit = ifcopenshell.api.run("unit.add_si_unit", ifc_file, unit_type="LENGTHUNIT", prefix="MILLI")
    ifcopenshell.api.run("unit.assign_unit", ifc_file, units=[unit])
    model = ifcopenshell.api.run("context.add_context", ifc_file, context_type="Model")
    plan = ifcopenshell.api.run("context.add_context", ifc_file, context_type="Plan")

    representations = {
        "body": ifcopenshell.api.run(
            "context.add_context",
            ifc_file,
            context_type="Model",
            context_identifier="Body",
            target_view="MODEL_VIEW",
            parent=model,
        ),
        "annotation": ifcopenshell.api.run(
            "context.add_context",
            ifc_file,
            context_type="Plan",
            context_identifier="Annotation",
            target_view="PLAN_VIEW",
            parent=plan,
        ),
    }

    builder = ShapeBuilder(ifc_file)

    width = 15.0
    height = 5.0
    size = V(width, height)
    offset = 2.5
    second_size = V(offset, offset)

    rect = builder.rectangle(size=size)
    rect_small = builder.rectangle(size=size - second_size, position=second_size / 2)

    rect_profile = builder.profile(rect, inner_curves=rect_small)

    pl = builder.extrude(rect_profile, 
        magnitude=7.0,
        position_z_axis=V(0, -1, 0),
        extrusion_vector=V(0, 0, -1),
        position=V(0, 5, 0)
    )

    rect = builder.rectangle(size=size)

    back_wall = builder.extrude(rect,
        magnitude=2.0,
        position_z_axis=V(0, -1, 0),
        extrusion_vector=V(0, 0, -1),
        position=V(0, 1, 0)
    )

    items_3d = [pl, back_wall]
    builder.mirror(items_3d, mirror_axes=V(0, 1))

    representation_3d = builder.get_representation(context=representations["body"], items=items_3d)

    element = ifcopenshell.api.run("root.create_entity", ifc_file, ifc_class="IfcFurnitureType", name="test")
    ifcopenshell.api.run("geometry.assign_representation", ifc_file, product=element, representation=representation_3d)
    ifcopenshell.api.run("project.assign_declaration", ifc_file, definition=element, relating_context=library)

    ifc_file.write("tmp.ifc")


def curve_between_two_points_test():
    ifc_file = ifcopenshell.api.run("project.create_file")
    project = ifcopenshell.api.run(
        "root.create_entity", ifc_file, ifc_class="IfcProject", name=f"Non-structural assets library"
    )
    library = ifcopenshell.api.run(
        "root.create_entity", ifc_file, ifc_class="IfcProjectLibrary", name=f"Non-structural assets library"
    )
    ifcopenshell.api.run("project.assign_declaration", ifc_file, definition=library, relating_context=project)
    unit = ifcopenshell.api.run("unit.add_si_unit", ifc_file, unit_type="LENGTHUNIT", prefix="MILLI")
    ifcopenshell.api.run("unit.assign_unit", ifc_file, units=[unit])
    model = ifcopenshell.api.run("context.add_context", ifc_file, context_type="Model")
    plan = ifcopenshell.api.run("context.add_context", ifc_file, context_type="Plan")

    representations = {
        "body": ifcopenshell.api.run(
            "context.add_context",
            ifc_file,
            context_type="Model",
            context_identifier="Body",
            target_view="MODEL_VIEW",
            parent=model,
        ),
        "annotation": ifcopenshell.api.run(
            "context.add_context",
            ifc_file,
            context_type="Plan",
            context_identifier="Annotation",
            target_view="PLAN_VIEW",
            parent=plan,
        ),
    }

    builder = ShapeBuilder(ifc_file)

    width, depth = (200.0, 200.0)

    curve_coords = (
        (V(0, depth), V(-width, 0)), # ccw
        (V(0, depth), V(width, 0)), # cw
        (V(0, -depth), V(width, 0)), # ccw
        (V(0, -depth), V(-width, 0)), # cw

        (V(+width/2, 0), V(0, depth)), # ccw
        (V(-width/2, 0), V(0, depth)), # cw
        (V(-width/2, 0), V(0, -depth)), # ccw
        (V(+width/2, 0), V(0, -depth)), # cw

        (V(0, depth/2), V(+width, 0)), # cw
        (V(0, depth/2), V(-width, 0)), # ccw
        (V(0, -depth/2), V(+width, 0)), # ccw
        (V(0, -depth/2), V(-width, 0)), # cw
    )
    items_2d = [builder.curve_between_two_points(c) for c in curve_coords]

    representation_2d = builder.get_representation(context=representations["annotation"], items=items_2d)

    print(representation_2d)
    element = ifcopenshell.api.run("root.create_entity", ifc_file, ifc_class="IfcFurnitureType", name="test")
    ifcopenshell.api.run("geometry.assign_representation", ifc_file, product=element, representation=representation_2d)
    ifcopenshell.api.run("project.assign_declaration", ifc_file, definition=element, relating_context=library)

    ifc_file.write("tmp.ifc")


def generate_simple_desk(ifc_file, width, depth, height):
    # > width, depth, height in mm
    width, depth, height = [i / 1000 for i in (width, depth, height)]
    builder = ShapeBuilder(ifc_file)
    rectangle_curve = builder.rectangle(size=Vector((width, depth)))
    profile = builder.profile(rectangle_curve, "simple_desk")
    extruded_area = builder.extrude(profile, height)
    return extruded_area


def generate_table(ifc_file, width, depth, height, countertop_thickness=20, leg_size=40, leg_offset=50):
    # > width, depth, height in mm
    width, depth, height, countertop_thickness, leg_size, leg_offset = [
        i / 1000 for i in (width, depth, height, countertop_thickness, leg_size, leg_offset)
    ]
    builder = ShapeBuilder(ifc_file)

    countertop_curve = builder.rectangle(size=Vector((width, depth)))
    countertop_profile = builder.profile(countertop_curve, "table_countertop")
    countertop = builder.extrude(
        countertop_profile, countertop_thickness, position=V(0, 0, height - countertop_thickness)
    )

    leg_curve = builder.rectangle(size=V(leg_size, leg_size))
    builder.translate(leg_curve, Vector((leg_offset, leg_offset)))
    legs_curves = [leg_curve] + builder.mirror(
        leg_curve, mirror_axes=[V(1, 0), V(0, 1), V(1, 1)], mirror_point=V(width / 2, depth / 2), create_copy=True
    )
    legs_profiles = [builder.profile(leg, "table_leg") for leg in legs_curves]
    legs = [builder.extrude(leg, height - countertop_thickness) for leg in legs_profiles]
    return (countertop, legs)


if __name__ == "__main__":
    simple_uses()
    # main()
    # placement_mirror_test()
    # mirror_placement_test()
