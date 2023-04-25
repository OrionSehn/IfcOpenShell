# IfcOpenShell - IFC toolkit and geometry engine
# Copyright (C) 2023 @Andrej730
#
# This file is part of IfcOpenShell.
#
# IfcOpenShell is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# IfcOpenShell is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with IfcOpenShell.  If not, see <http://www.gnu.org/licenses/>.

import ifcopenshell.util.unit
from ifcopenshell.util.shape_builder import ShapeBuilder, V
from itertools import chain
from mathutils import Vector
import collections
from pprint import pprint
from math import pi, cos, sin


def mm(x):
    """mm to meters shortcut for readability"""
    return x / 1000
class Usecase:
    def __init__(self, file, **settings):
        """
        units in settings expected to be in ifc project units

        `railing_path` is a list of point coordinates for the railing path, 
        coordinates are expected to be at the top of the railing, not at the center

        `railing_path` is expected to be a list of Vector objects
        """
        self.file = file
        self.settings = {"unit_scale": ifcopenshell.util.unit.calculate_unit_scale(self.file)}
        self.settings.update(
            {
                "context": None,  # IfcGeometricRepresentationContext
                "railing_type": "WALL_MOUNTED_HANDRAIL",
                "railing_path": self.path_si_to_units( [V(0, 0, 1), V(1, 0, 1), V(2, 0, 1)] ),
            }
        )

        for key, value in settings.items():
            self.settings[key] = value

        if self.settings['railing_type'] != 'WALL_MOUNTED_HANDRAIL':
            raise Exception('Only WALL_MOUNTED_HANDRAIL railing_type is supported at the moment.')

    def execute(self):
        builder = ShapeBuilder(self.file)
        arc_points = []
        items_3d = []
        railing_diameter = self.convert_si_to_unit(mm(50))
        terminal_radius = self.convert_si_to_unit(mm(150))
        clear_width = self.convert_si_to_unit(mm(40))
        railing_radius = railing_diameter / 2
        support_length = clear_width + railing_radius
        support_radius = self.convert_si_to_unit(mm(10))
        support_disk_radius = railing_radius
        support_disk_depth = self.convert_si_to_unit(mm(20))
        z_down = V(0,0,-1)

        ifc_context = self.settings["context"]
        railing_coords = self.settings['railing_path']
        railing_coords = [p - z_down * railing_radius for p in railing_coords]
        
        def add_cap(start=False):
            nonlocal railing_coords, arc_points            
            railing_coords_for_cap = railing_coords[::-1] if start else railing_coords

            start = railing_coords_for_cap[-1]
            cap_dir = (railing_coords_for_cap[-1]-railing_coords_for_cap[-2]).xy.to_3d().normalized()
            arc_point = start + cap_dir * terminal_radius + terminal_radius*z_down
            arc_points.append(arc_point)
            cap_coords = [arc_point, start + terminal_radius * 2 * z_down]

            railing_coords = railing_coords_for_cap + cap_coords

            if start:
                railing_coords = railing_coords[::-1]

        def get_support_on_point(point, direction):
            ortho_dir = (direction.yx * V(1, -1)).to_3d().normalized()
            arc_center = point + ortho_dir * support_length
            support_points = [
                point, 
                arc_center - ortho_dir * support_length * cos(pi/4)  + z_down * support_length * sin(pi/4) , 
                arc_center + z_down * support_length]
            print('support points', support_points)
            polyline = builder.polyline(support_points, closed=False, arc_points=[1])
            solid = builder.create_swept_disk_solid(polyline, support_radius)

            support_disk_circle = builder.circle(radius=support_disk_radius)
            support_disk = builder.extrude(support_disk_circle, support_disk_depth, position=support_points[-1],
                                           **builder.extrude_by_y_kwargs())
            return [solid, support_disk]

        pprint(railing_coords) # TODO: rad
        support_items = get_support_on_point(
            point=(railing_coords[0] + railing_coords[-1])/2,
            direction=(railing_coords[-1]-railing_coords[0])
        )
        items_3d.extend(support_items)

        add_cap(start=True)
        add_cap(start=False)

        railing_path = builder.polyline(railing_coords, closed=False, 
                                        arc_points=[railing_coords.index(p) for p in arc_points])
        railing_solid = builder.create_swept_disk_solid(railing_path, railing_radius)
        items_3d.append(railing_solid)
        representation = builder.get_representation(ifc_context, items=items_3d)
        return representation

    def convert_si_to_unit(self, value):
        return value / self.settings["unit_scale"]

    def path_si_to_units(self, path):
        """converts list of vectors from SI to ifc project units"""
        return [self.convert_si_to_unit(v) for v in path]