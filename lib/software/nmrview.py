###############################################################################
#                                                                             #
# Copyright (C) 2004-2013 Edward d'Auvergne                                   #
# Copyright (C) 2008 Sebastien Morin                                          #
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

# Module docstring.
"""Module containing functions for handling NMRView files."""


# Python module imports.
from warnings import warn

# relax module imports.
from lib.errors import RelaxError
from lib.io import strip
from lib.warnings import RelaxWarning


def read_list_intensity(file_data=None, int_col=None):
    """Return the peak intensity information from the NMRView peak intensity file.

    The residue number, heteronucleus and proton names, and peak intensity will be returned.


    @keyword file_data: The data extracted from the file converted into a list of lists.
    @type file_data:    list of lists of str
    @keyword int_col:   The column containing the peak intensity data. The default is 16 for intensities. Setting the int_col argument to 15 will use the volumes (or evolumes). For a non-standard formatted file, use a different value.
    @type int_col:      int
    @raises RelaxError: When the expected peak intensity is not a float.
    @return:            The extracted data as a list of lists.  The first dimension corresponds to the spin.  The second dimension consists of the proton name, heteronucleus name, residue number, the intensity value, and the original line of text
    @rtype:             list of lists of str, str, int, float, str
    """

    # Assume the NMRView file has six header lines!
    num = 6
    print("Number of header lines: " + repr(num))

    # Remove the header.
    file_data = file_data[num:]

    # Strip the data.
    file_data = strip(file_data)

    # The peak intensity column.
    if int_col == None:
        int_col = 16
    if int_col == 16:
        print('Using peak heights.')
    if int_col == 15:
        print('Using peak volumes (or evolumes).')

    # Loop over the file data.
    data = []
    for line in file_data:
        # Unknown assignment.
        if line[1] == '{}':
            warn(RelaxWarning("The assignment '%s' is unknown, skipping this peak." % line[1]))
            continue

        # The residue number
        res_num = ''
        try:
            res_num = line[1].strip('{')
            res_num = res_num.strip('}')
            res_num = res_num.split('.')
            res_num = res_num[0]
        except ValueError:
            raise RelaxError("The peak list is invalid.")

        # Nuclei names.
        x_name = ''
        if line[8]!='{}':
            x_name = line[8].strip('{')
            x_name = x_name.strip('}')
            x_name = x_name.split('.')
            x_name = x_name[1]
        h_name = ''
        if line[1]!='{}':
            h_name = line[1].strip('{')
            h_name = h_name.strip('}')
            h_name = h_name.split('.')
            h_name = h_name[1]

        # Intensity.
        try:
            intensity = float(line[int_col])
        except ValueError:
            raise RelaxError("The peak intensity value " + repr(intensity) + " from the line " + repr(line) + " is invalid.")

        # Append the data.
        data.append([h_name, x_name, res_num, intensity, line])

    # Return the data.
    return data