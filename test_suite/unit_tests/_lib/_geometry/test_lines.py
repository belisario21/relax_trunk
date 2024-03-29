###############################################################################
#                                                                             #
# Copyright (C) 2013 Edward d'Auvergne                                        #
#                                                                             #
# This file is part of the program relax (http://www.nmr-relax.com).          #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

# Python module imports.
from numpy import array, float64
from unittest import TestCase

# relax module imports.
from lib.geometry.lines import closest_point


class Test_lines(TestCase):
    """Unit tests for the lib.geometry.lines relax module."""

    def test_closest_point(self):
        """Test the closest_point() function."""

        # Get and check the point.
        pt = closest_point(line_pt1=array([1, 1, 0], float64), line_pt2=array([-1, -1, 0], float64), point=array([0, 0, 10]))
        self.assertEqual(pt[0], 0.0)
        self.assertEqual(pt[1], 0.0)
        self.assertEqual(pt[2], 0.0)
