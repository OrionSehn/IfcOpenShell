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


def mm(x):
    """mm to meters shortcut for readability"""
    return x / 1000

class Usecase:
    def __init__(self, file, **settings):
        """
        units in settings expected to be in ifc project units

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
        ifc_context = self.settings["context"]
        railing_coords = self.settings['railing_path']
        arc_points = []
        
        railing_diameter = self.convert_si_to_unit(mm(50))
        railing_radius = railing_diameter / 2
        z_down = V(0,0,-1)
        terminal_radius = self.convert_si_to_unit(mm(150))

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

        add_cap(start=True)
        add_cap(start=False)

        pprint(railing_coords) # TODO: remove after debug

        builder = ShapeBuilder(self.file)
        railing_path = builder.polyline(railing_coords, closed=False, 
                                        arc_points=[railing_coords.index(p) for p in arc_points])
        railing_solid = builder.create_swept_disk_solid(railing_path, railing_radius)
        representation = builder.get_representation(ifc_context, items=railing_solid)
        return representation

    def convert_si_to_unit(self, value):
        return value / self.settings["unit_scale"]

    def path_si_to_units(self, path):
        """converts list of vectors from SI to ifc project units"""
        return [self.convert_si_to_unit(v) for v in path]