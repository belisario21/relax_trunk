###############################################################################
#                                                                             #
# Copyright (C) 2003-2013 Edward d'Auvergne                                   #
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
"""Module containing functions for the handling of alignment tensors."""

# Python module imports.
from copy import deepcopy
from math import pi, sqrt
from numpy import arccos, dot, float64, linalg, zeros
from numpy.linalg import norm
from re import search
import sys
from warnings import warn

# relax module imports.
from data_store.align_tensor import AlignTensorList
from pipe_control.angles import wrap_angles
from pipe_control import pipes
from lib.physical_constants import g1H, h_bar, kB, mu0, return_gyromagnetic_ratio
from lib.errors import RelaxError, RelaxNoTensorError, RelaxStrError, RelaxTensorError, RelaxUnknownParamCombError, RelaxUnknownParamError
from lib.io import write_data
from lib.warnings import RelaxWarning


def align_data_exists(tensor, pipe=None):
    """Function for determining if alignment data exists in the current data pipe.

    @param tensor:  The alignment tensor identification string.
    @type tensor:   str
    @param pipe:    The data pipe to search for data in.
    @type pipe:     str
    @return:        The answer to the question.
    @rtype:         bool
    """

    # The data pipe to check.
    if pipe == None:
        pipe = pipes.cdp_name()

    # Get the data pipe.
    pipe = pipes.get_pipe(pipe)

    # Test if an alignment tensor corresponding to the arg 'tensor' exists.
    if hasattr(pipe, 'align_tensors'):
        for data in pipe.align_tensors:
            if data.name == tensor:
                return True
    else:
        return False


def all_tensors_fixed():
    """Determine if all alignment tensors are fixed.

    @return:    True if all tensors are fixed, False otherwise.
    @rtype:     bool
    """

    # Loop over the tensors.
    for i in range(len(cdp.align_tensors)):
        # Not fixed, so return False.
        if not cdp.align_tensors[i].fixed:
            return False

    # All tensors are fixed.
    return True


def calc_chi_tensor(A, B0, T):
    """Convert the alignment tensor into the magnetic susceptibility (chi) tensor.

    A can be either the full tensor (3D or 5D), a component Aij of the tensor, Aa, or Ar, anything that can be multiplied by the constants to convert from one to the other.


    @param A:       The alignment tensor or alignment tensor component.
    @type A:        numpy array or float
    @param B0:      The magnetic field strength in Hz.
    @type B0:       float
    @param T:       The temperature in Kalvin.
    @type T:        float
    @return:        A multiplied by the PCS constant.
    @rtype:         numpy array or float
    """

    # B0 in Tesla.
    B0 = 2.0 * pi * B0 / g1H

    # The conversion factor.
    conv = 15.0 * mu0 * kB * T / B0**2

    # Return the converted value.
    return conv * A


def copy(tensor_from=None, pipe_from=None, tensor_to=None, pipe_to=None):
    """Function for copying alignment tensor data from one data pipe to another.

    @param tensor_from: The identification string of the alignment tensor to copy the data from.
    @type tensor_from:  str
    @param pipe_from:   The data pipe to copy the alignment tensor data from.  This defaults to the current data pipe.
    @type pipe_from:    str
    @param tensor_to:   The identification string of the alignment tensor to copy the data to.  If set to None, then the ID string will be set to the value of tensor_from.
    @type tensor_to:    str or None
    @param pipe_to:     The data pipe to copy the alignment tensor data to.  This defaults to the current data pipe.
    @type pipe_to:      str
    """

    # Defaults.
    if tensor_from == tensor_to and pipe_from == None and pipe_to == None:
        raise RelaxError("The pipe_from and pipe_to arguments cannot both be set to None when the tensor names are the same.")
    elif pipe_from == None:
        pipe_from = pipes.cdp_name()
    elif pipe_to == None:
        pipe_to = pipes.cdp_name()

    # The target tensor ID string.
    if tensor_to == None:
        tensor_to = tensor_from

    # Test if the pipe_from and pipe_to data pipes exist.
    pipes.test(pipe_from)
    pipes.test(pipe_to)

    # Get the data pipes.
    dp_from = pipes.get_pipe(pipe_from)
    dp_to = pipes.get_pipe(pipe_to)

    # Test if pipe_from contains alignment tensor data.
    if not align_data_exists(tensor_from, pipe_from):
        raise RelaxNoTensorError('alignment')

    # Test if pipe_to contains alignment tensor data.
    if align_data_exists(tensor_to, pipe_to):
        raise RelaxTensorError('alignment')

    # Create the align_tensors dictionary if it doesn't yet exist.
    if not hasattr(dp_to, 'align_tensors'):
        dp_to.align_tensors = AlignTensorList()

    # Add the tensor if it doesn't already exist.
    if tensor_to not in dp_to.align_tensors.names():
        dp_to.align_tensors.add_item(tensor_to)

    # Find the tensor index.
    index_from = get_tensor_index(tensor=tensor_from, pipe=pipe_from)
    index_to = get_tensor_index(tensor=tensor_to, pipe=pipe_to)

    # Copy the data.
    if index_to == None:
        dp_to.align_tensors.append(deepcopy(dp_from.align_tensors[index_from]))
        index_to = len(dp_to.align_tensors) - 1
    else:
        dp_to.align_tensors[index_to] = deepcopy(dp_from.align_tensors[index_from])

    # Update the tensor's name.
    dp_to.align_tensors[index_to].set('name', tensor_to)

    # Add the align ID to the target data pipe if needed.
    align_id = dp_from.align_tensors[index_from].align_id
    if not hasattr(dp_to, 'align_ids'):
        dp_to.align_ids = []
    if align_id not in dp_to.align_ids:
        dp_to.align_ids.append(align_id)


def data_names():
    """Function for returning a list of names of data structures associated with the sequence."""

    names = [ 'align_params' ]

    return names


def default_value(param):
    """Return the default values for the alignment tensor parameters.

    @param param:   The name of the parameter.
    @type param:    str
    @return:        The default value, which for all parameters is set to zero.
    @rtype:         float
    """

    # Return 0.0.
    return 0.0

# User function documentation.
__default_value_prompt_doc__ = """
    Alignment tensor parameter default values
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    ________________________________________________________________________
    |                        |                    |                        |
    | Data type              | Object name        | Value                  |
    |________________________|____________________|________________________|
    |                        |                    |                        |
    | Axx                    | 'Axx'              | 0.0                    |
    |                        |                    |                        |
    | Ayy                    | 'Ayy'              | 0.0                    |
    |                        |                    |                        |
    | Azz                    | 'Azz'              | 0.0                    |
    |                        |                    |                        |
    | Axxyy                  | 'Axxyy'            | 0.0                    |
    |                        |                    |                        |
    | Axy                    | 'Axy'              | 0.0                    |
    |                        |                    |                        |
    | Axz                    | 'Axz'              | 0.0                    |
    |                        |                    |                        |
    | Ayz                    | 'Ayz'              | 0.0                    |
    |                        |                    |                        |
    | alpha                  | 'alpha'            | 0.0                    |
    |                        |                    |                        |
    | beta                   | 'beta'             | 0.0                    |
    |                        |                    |                        |
    | gamma                  | 'gamma'            | 0.0                    |
    |________________________|____________________|________________________|

"""


def delete(tensor=None):
    """Function for deleting alignment tensor data.

    @param tensor:          The alignment tensor identification string.
    @type tensor:           str or None
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Test if alignment tensor data exists.
    if tensor and not align_data_exists(tensor):
        raise RelaxNoTensorError('alignment')

    # The tensor list.
    if tensor:
        tensors = [tensor]
    else:
        tensors = []
        for i in range(len(cdp.align_tensors)):
            tensors.append(cdp.align_tensors[i].name)

    # Loop over the tensors.
    for tensor in tensors:
        # Print out.
        print("Removing the '%s' tensor." % tensor)

        # Find the tensor index.
        index = get_tensor_index(tensor=tensor)

        # Delete the alignment data.
        cdp.align_tensors.pop(index)

        # Delete the alignment tensor list if empty.
        if not len(cdp.align_tensors):
            del(cdp.align_tensors)


def display(tensor=None):
    """Function for displaying the alignment tensor.

    @keyword tensor:        The alignment tensor identification string.
    @type tensor:           str or None
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Construct the tensor list.
    tensor_list = []
    if not tensor:
        for tensor_cont in cdp.align_tensors:
            tensor_list.append(tensor_cont.name)
    else:
        tensor_list.append(tensor)

    # Loop over the tensors.
    for tensor in tensor_list:
        # Test if alignment tensor data exists.
        if not align_data_exists(tensor):
            raise RelaxNoTensorError('alignment')

        # Pull out the tensor.
        data = get_tensor_object(tensor)

        # Header.
        head = "# Tensor: %s #" % tensor
        print("\n\n\n" + '#' * len(head) + "\n" + head + "\n" + '#' * len(head))


        # The Saupe matrix.
        ###################

        title = "# Saupe order matrix."
        print("\n\n" + title + '\n' + '#'*len(title) + '\n')

        # The parameter set {Sxx, Syy, Sxy, Sxz, Syz}.
        print("# 5D, rank-1 notation {Sxx, Syy, Sxy, Sxz, Syz}:")
        print("[%25.12e, %25.12e, %25.12e, %25.12e, %25.12e]\n" % (data.Sxx, data.Syy, data.Sxy, data.Sxz, data.Syz))

        # The parameter set {Szz, Sxx-yy, Sxy, Sxz, Syz}.
        print("# 5D, rank-1 notation {Szz, Sxx-yy, Sxy, Sxz, Syz} (the Pales default format).")
        print("[%25.12e, %25.12e, %25.12e, %25.12e, %25.12e]\n" % (data.Szz, data.Sxxyy, data.Sxy, data.Sxz, data.Syz))

        # 3D form.
        print("# 3D, rank-2 notation.")
        print("%s" % (data.S))


        # The alignment tensor.
        #######################

        title = "# Alignment tensor."
        print("\n\n" + title + '\n' + '#'*len(title) + '\n')

        # The parameter set {Axx, Ayy, Axy, Axz, Ayz}.
        print("# 5D, rank-1 notation {Axx, Ayy, Axy, Axz, Ayz}:")
        print("[%25.12e, %25.12e, %25.12e, %25.12e, %25.12e]\n" % (data.Axx, data.Ayy, data.Axy, data.Axz, data.Ayz))

        # The parameter set {Azz, Axx-yy, Axy, Axz, Ayz}.
        print("# 5D, rank-1 notation {Azz, Axx-yy, Axy, Axz, Ayz} (the Pales default format).")
        print("[%25.12e, %25.12e, %25.12e, %25.12e, %25.12e]\n" % (data.Azz, data.Axxyy, data.Axy, data.Axz, data.Ayz))

        # 3D form.
        print("# 3D, rank-2 notation.")
        print("%s" % data.A)


        # The probability tensor.
        #########################

        title = "# Probability tensor."
        print("\n\n" + title + '\n' + '#'*len(title) + '\n')

        # The parameter set {Pxx, Pyy, Pxy, Pxz, Pyz}.
        print("# 5D, rank-1 notation {Pxx, Pyy, Pxy, Pxz, Pyz}:")
        print("[%25.12e, %25.12e, %25.12e, %25.12e, %25.12e]\n" % (data.Pxx, data.Pyy, data.Pxy, data.Pxz, data.Pyz))

        # The parameter set {Pzz, Pxx-yy, Pxy, Pxz, Pyz}.
        print("# 5D, rank-1 notation {Pzz, Pxx-yy, Pxy, Pxz, Pyz}.")
        print("[%25.12e, %25.12e, %25.12e, %25.12e, %25.12e]\n" % (data.Pzz, data.Pxxyy, data.Pxy, data.Pxz, data.Pyz))

        # 3D form.
        print("# 3D, rank-2 notation.")
        print("%s" % data.P)


        # The magnetic susceptibility tensor.
        #####################################

        title = "# Magnetic susceptibility tensor."
        print("\n\n" + title + '\n' + '#'*len(title) + '\n')
        chi_tensor = True

        # The field strength.
        print("# The magnetic field strength (MHz):")
        if hasattr(cdp, 'frq') and tensor in cdp.frq:
            print("%s\n" % (cdp.frq[tensor] / 1e6))
        else:
            print("Not set.\n")
            chi_tensor = False

        # The temperature.
        print("# The temperature (K):")
        if hasattr(cdp, 'temperature') and tensor in cdp.temperature:
            print("%s\n" % cdp.temperature[tensor])
        else:
            print("Not set.\n")
            chi_tensor = False

        # No chi tensor.
        if not chi_tensor:
            print("# The chi tensor:\nN/A.\n")

        # Calculate the chi tensor.
        else:
            # Conversions.
            chi_xx =    calc_chi_tensor(data.Axx, cdp.frq[tensor], cdp.temperature[tensor])
            chi_xy =    calc_chi_tensor(data.Axy, cdp.frq[tensor], cdp.temperature[tensor])
            chi_xz =    calc_chi_tensor(data.Axz, cdp.frq[tensor], cdp.temperature[tensor])
            chi_yy =    calc_chi_tensor(data.Ayy, cdp.frq[tensor], cdp.temperature[tensor])
            chi_yz =    calc_chi_tensor(data.Ayz, cdp.frq[tensor], cdp.temperature[tensor])
            chi_zz =    calc_chi_tensor(data.Azz, cdp.frq[tensor], cdp.temperature[tensor])
            chi_xxyy =  calc_chi_tensor(data.Axxyy, cdp.frq[tensor], cdp.temperature[tensor])
            chi =       calc_chi_tensor(data.A, cdp.frq[tensor], cdp.temperature[tensor])

            # The parameter set {chi_xx, chi_yy, chi_xy, chi_xz, chi_yz}.
            print("# 5D, rank-1 notation {chi_xx, chi_yy, chi_xy, chi_xz, chi_yz}:")
            print("[%25.12e, %25.12e, %25.12e, %25.12e, %25.12e]\n" % (chi_xx, chi_yy, chi_xy, chi_xz, chi_yz))

            # The parameter set {chi_zz, chi_xx-yy, chi_xy, chi_xz, chi_yz}.
            print("# 5D, rank-1 notation {chi_zz, chi_xx-yy, chi_xy, chi_xz, chi_yz}.")
            print("[%25.12e, %25.12e, %25.12e, %25.12e, %25.12e]\n" % (chi_zz, chi_xxyy, chi_xy, chi_xz, chi_yz))

            # 3D form.
            print("# 3D, rank-2 notation.")
            print("%s" % chi)


        # The Eigensystem.
        ##################

        title = "# Eigensystem."
        print("\n\n" + title + '\n' + '#'*len(title) + '\n')

        # Eigenvalues.
        print("# Saupe order matrix eigenvalues {Sxx, Syy, Szz}.")
        print("[%25.12e, %25.12e, %25.12e]\n" % (data.S_diag[0, 0], data.S_diag[1, 1], data.S_diag[2, 2]))
        print("# Alignment tensor eigenvalues {Axx, Ayy, Azz}.")
        print("[%25.12e, %25.12e, %25.12e]\n" % (data.A_diag[0, 0], data.A_diag[1, 1], data.A_diag[2, 2]))
        print("# Probability tensor eigenvalues {Pxx, Pyy, Pzz}.")
        print("[%25.12e, %25.12e, %25.12e]\n" % (data.P_diag[0, 0], data.P_diag[1, 1], data.P_diag[2, 2]))
        if chi_tensor:
            chi_diag =       calc_chi_tensor(data.A_diag, cdp.frq[tensor], cdp.temperature[tensor])
            print("# Magnetic susceptibility eigenvalues {chi_xx, chi_yy, chi_zz}.")
            print("[%25.12e, %25.12e, %25.12e]\n" % (chi_diag[0, 0], chi_diag[1, 1], chi_diag[2, 2]))

        # Eigenvectors.
        print("# Eigenvector x.")
        print("[%25.12f, %25.12f, %25.12f]\n" % (data.unit_x[0], data.unit_x[1], data.unit_x[2]))
        print("# Eigenvector y.")
        print("[%25.12f, %25.12f, %25.12f]\n" % (data.unit_y[0], data.unit_y[1], data.unit_y[2]))
        print("# Eigenvector z.")
        print("[%25.12f, %25.12f, %25.12f]\n" % (data.unit_z[0], data.unit_z[1], data.unit_z[2]))

        # Rotation matrix.
        print("# Rotation matrix.")
        print("%s\n" % data.rotation)

        # zyz.
        print("# Euler angles in zyz notation {alpha, beta, gamma}.")
        print("[%25.12f, %25.12f, %25.12f]\n" % (data.euler[0], data.euler[1], data.euler[2]))


        # Geometric description.
        ########################

        title = "# Geometric description."
        print("\n\n" + title + '\n' + '#'*len(title) + '\n')

        # The GDO.
        print("# Generalized degree of order (GDO).")
        print("GDO = %-25.12e\n" % gdo(data.A))

        # Anisotropy.
        print("# Alignment tensor axial component (Aa = 3/2 * Azz, where Aii are the eigenvalues).")
        print("Aa = %-25.12e\n" % data.Aa)

        # Rhombicity.
        print("# Rhombic component (Ar = Axx - Ayy, where Aii are the eigenvalues).")
        print("Ar = %-25.12e\n" % data.Ar)
        print("# Rhombicity (R = Ar / Aa).")
        print("R = %-25.12f\n" % data.R)
        print("# Asymmetry parameter (eta = (Axx - Ayy) / Azz, where Aii are the eigenvalues).")
        print("eta = %-25.12f\n" % data.eta)

        # Magnetic susceptibility tensor.
        if chi_tensor:
            # Chi tensor anisotropy.
            print("# Magnetic susceptibility axial parameter (chi_ax = chi_zz - (chi_xx + chi_yy)/2, where chi_ii are the eigenvalues).")
            print("chi_ax = %-25.12e\n" % (chi_diag[2, 2] - (chi_diag[0, 0] + chi_diag[1, 1])/2.0))

            # Chi tensor rhombicity.
            print("# Magnetic susceptibility rhombicity parameter (chi_rh = chi_xx - chi_yy, where chi_ii are the eigenvalues).")
            print("chi_rh = %-25.12e\n" % (chi_diag[0, 0] - chi_diag[1, 1]))

        # Some white space.
        print("\n\n\n")


def fix(id=None, fixed=True):
    """Fix the alignment tensor during optimisation.

    @keyword id:    The alignment tensor ID string.  If set to None, then all alignment tensors will be fixed.
    @type id:       str or None
    @keyword fixed: If True, the alignment tensor will be fixed during optimisation.  If False, the alignment tensors will be optimised.
    @type fixed:    bool
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Loop over the tensors.
    for i in range(len(cdp.align_tensors)):
        # ID match.
        if id and cdp.align_tensors[i].name == id:
            cdp.align_tensors[i].set_fixed(fixed)

        # Set all tensor flags.
        if id == None:
            cdp.align_tensors[i].set_fixed(fixed)


def fold_angles(sim_index=None):
    """Wrap the Euler angles and remove the glide reflection and translational symmetries.

    Wrap the angles such that::

        0 <= alpha <= 2pi,
        0 <= beta <= pi,
        0 <= gamma <= 2pi.

    For the simulated values, the angles are wrapped as::

        alpha - pi <= alpha_sim <= alpha + pi
        beta - pi/2 <= beta_sim <= beta + pi/2
        gamma - pi <= gamma_sim <= gamma + pi


    @param sim_index:   The simulation index.  If set to None then the actual values will be folded
                        rather than the simulation values.
    @type sim_index:    int or None
    """


    # Wrap the angles.
    ##################

    # Get the current angles.
    alpha = cdp.align_tensors.alpha
    beta  = cdp.align_tensors.beta
    gamma = cdp.align_tensors.gamma

    # Simulated values.
    if sim_index != None:
        alpha_sim = cdp.align_tensors.alpha_sim[sim_index]
        beta_sim  = cdp.align_tensors.beta_sim[sim_index]
        gamma_sim = cdp.align_tensors.gamma_sim[sim_index]

    # Normal value.
    if sim_index == None:
        cdp.align_tensors.set(param='alpha', value=wrap_angles(alpha, 0.0, 2.0*pi))
        cdp.align_tensors.set(param='beta', value= wrap_angles(beta, 0.0, 2.0*pi))
        cdp.align_tensors.set(param='gamma', value=wrap_angles(gamma, 0.0, 2.0*pi))

    # Simulation values.
    else:
        cdp.align_tensors.set(param='alpha', value=wrap_angles(alpha_sim, alpha - pi, alpha + pi), category='sim', sim_index=sim_index)
        cdp.align_tensors.set(param='beta', value= wrap_angles(beta_sim, beta - pi, beta + pi), category='sim', sim_index=sim_index)
        cdp.align_tensors.set(param='gamma', value=wrap_angles(gamma_sim, gamma - pi, gamma + pi), category='sim', sim_index=sim_index)


    # Remove the glide reflection and translational symmetries.
    ###########################################################

    # Normal value.
    if sim_index == None:
        # Fold beta inside 0 and pi.
        if cdp.align_tensors.beta >= pi:
            cdp.align_tensors.set(param='alpha', value=pi - cdp.align_tensors.alpha)
            cdp.align_tensors.set(param='beta', value=cdp.align_tensors.beta - pi)

    # Simulation values.
    else:
        # Fold beta_sim inside beta-pi/2 and beta+pi/2.
        if cdp.align_tensors.beta_sim[sim_index] >= cdp.align_tensors.beta + pi/2.0:
            cdp.align_tensors.set(param='alpha', value=pi - cdp.align_tensors.alpha_sim[sim_index], category='sim', sim_index=sim_index)
            cdp.align_tensors.set(param='beta', value=cdp.align_tensors.beta_sim[sim_index] - pi, category='sim', sim_index=sim_index)
        elif cdp.align_tensors.beta_sim[sim_index] <= cdp.align_tensors.beta - pi/2.0:
            cdp.align_tensors.set(param='alpha', value=pi - cdp.align_tensors.alpha_sim[sim_index], category='sim', sim_index=sim_index)
            cdp.align_tensors.set(param='beta', value=cdp.align_tensors.beta_sim[sim_index] + pi, category='sim', sim_index=sim_index)


def gdo(A):
    """Calculate the generalized degree of order (GDO) for the given alignment tensor.

    @param A:   The alignment tensor.
    @type A:    rank-2, 3D numpy array
    @return:    The GDO value.
    @rtype:     float
    """

    # The matrix norm.
    gdo = sqrt(3.0/2.0) *  norm(A)

    # Return the GDO.
    return gdo


def get_align_ids():
    """Return the list of all alignment IDs.

    @return:        The list of all alignment IDs.
    @rtype:         list of str
    """

    # No pipe.
    if cdp == None:
        return []

    # No tensor data.
    if not hasattr(cdp, 'align_ids'):
        return []

    # The tensor IDs.
    return cdp.align_ids


def get_tensor_ids():
    """Return the list of all tensor IDs.

    @return:        The list of all tensor IDs.
    @rtype:         list of str
    """

    # Init.
    ids = []

    # No pipe.
    if cdp == None:
        return ids

    # No tensor data.
    if not hasattr(cdp, 'align_tensors'):
        return ids

    # Loop over the tensors.
    for i in range(len(cdp.align_tensors)):
        if cdp.align_tensors[i].name != None:
            ids.append(cdp.align_tensors[i].name)

    # Return the object.
    return ids


def get_tensor_index(tensor=None, align_id=None, pipe=None):
    """Function for returning the index corresponding to the 'tensor' argument.

    @keyword tensor:    The alignment tensor identification string.
    @type tensor:       str or None
    @keyword align_id:  Alternative to the tensor argument, used to return the tensor index for the tensors corresponding to the alignment ID string.  If more than one tensor exists, then this will fail.
    @type align_id:     str or None
    @keyword pipe:      The data pipe to search for data in.
    @type pipe:         str
    @return:            The index corresponding to the 'tensor' arg.
    @rtype:             int
    """

    # The data pipe to check.
    if pipe == None:
        pipe = pipes.cdp_name()

    # Get the data pipe.
    dp = pipes.get_pipe(pipe)

    # Init.
    index = None
    count = 0

    # Loop over the tensors.
    for i in range(len(dp.align_tensors)):
        # Tensor name match.
        if tensor and dp.align_tensors[i].name == tensor:
            index = i
            count += 1

        # Alignment ID match.
        if align_id and hasattr(dp.align_tensors[i], 'align_id') and dp.align_tensors[i].align_id == align_id:
            index = i
            count += 1

    # No match.
    if count == 0:
        warn(RelaxWarning("No alignment tensors match the tensor name '%s' or alignment ID '%s' in the data pipe '%s'." % (tensor, align_id, pipe)))
        return None

    # More than one match.
    if count > 1: 
        warn(RelaxWarning("More than one alignment tensors matches the tensor name '%s' or alignment ID '%s' in the data pipe '%s'." % (tensor, align_id, pipe)))
        return None

    # Return the index.
    return index


def get_tensor_object(tensor, pipe=None):
    """Return the AlignTensorData instance corresponding to the tensor ID.

    @param tensor:  The alignment tensor identification string.
    @type tensor:   str
    @param pipe:    The data pipe to search for data in.
    @type pipe:     str
    @return:        The alignment tensor object corresponding to the 'tensor' arg.
    @rtype:         AlignTensorData instance
    """

    # The data pipe to check.
    if pipe == None:
        pipe = pipes.cdp_name()

    # Init.
    data = None

    # Loop over the tensors.
    for i in range(len(cdp.align_tensors)):
        if cdp.align_tensors[i].name == tensor:
            data = cdp.align_tensors[i]

    # Return the object.
    return data


def get_tensor_object_from_align(align_id, pipe=None):
    """Return the unique AlignTensorData instance corresponding to the alignment ID.

    @param align_id:    The alignment ID for the unique tensor.
    @type align_id:     str
    @return:            The alignment tensor object corresponding to the 'tensor' arg.
    @rtype:             AlignTensorData instance
    """

    # The data pipe to check.
    if pipe == None:
        pipe = pipes.cdp_name()

    # Init.
    data = None

    # Loop over the tensors.
    count = 0
    for i in range(len(cdp.align_tensors)):
        if hasattr(cdp.align_tensors[i], 'align_id') and cdp.align_tensors[i].align_id == align_id:
            data = cdp.align_tensors[i]
            count += 1

    # Multiple matches.
    if count > 1:
        raise RelaxError("Multiple alignment tensors match the alignment ID '%s'." % align_id)
    # Return the object.
    return data


def init(tensor=None, align_id=None, params=None, scale=1.0, angle_units='deg', param_types=0, domain=None, errors=False):
    """Function for initialising the alignment tensor.

    @keyword tensor:        The alignment tensor identification string.
    @type tensor:           str
    @keyword align_id:      The alignment ID string that the tensor corresponds to.
    @type align_id:         str or None
    @keyword params:        The alignment tensor parameters.
    @type params:           float
    @keyword scale:         The alignment tensor eigenvalue scaling value.
    @type scale:            float
    @keyword angle_units:   The units for the angle parameters (either 'deg' or 'rad').
    @type angle_units:      str
    @keyword param_types:   The type of parameters supplied.  The flag values correspond to, 0: {Axx, Ayy, Axy, Axz, Ayz}, and 1: {Azz, Axx-yy, Axy, Axz, Ayz}.
    @type param_types:      int
    @keyword domain:        The domain label.
    @type domain:           str or None
    @keyword errors:        A flag which determines if the alignment tensor data or its errors are being input.
    @type errors:           bool
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Parameter checks.
    if align_id == None:
        raise RelaxError("The alignment ID must be given.")

    # Check the validity of the angle_units argument.
    valid_types = ['deg', 'rad']
    if not angle_units in valid_types:
        raise RelaxError("The alignment tensor 'angle_units' argument " + repr(angle_units) + " should be either 'deg' or 'rad'.")

    # Test if alignment tensor data already exists.
    if errors and (not hasattr(cdp, 'align_ids') or not align_id in cdp.align_ids):
        raise RelaxNoTensorError('alignment')

    # Check that the domain is defined.
    if domain and (not hasattr(cdp, 'domain') or domain not in cdp.domain.keys()):
        raise RelaxError("The domain '%s' has not been defined.  Please use the domain user function." % domain)

    # Add the align ID to the current data pipe if needed.
    if not hasattr(cdp, 'align_ids'):
        cdp.align_ids = []
    if align_id not in cdp.align_ids:
        cdp.align_ids.append(align_id)

    # Add the align_tensors object to the data pipe.
    tensor_obj = None
    if not errors:
        # Initialise the super structure.
        if not hasattr(cdp, 'align_tensors'):
            cdp.align_tensors = AlignTensorList()

        # Add the tensor, if it doesn't already exist.
        if tensor == None or tensor not in cdp.align_tensors.names():
            tensor_obj = cdp.align_tensors.add_item(tensor)

    # Get the tensor.
    if not tensor_obj:
        if tensor:
            tensor_obj = get_tensor_object(tensor)
        else:
            tensor_obj = get_tensor_object_from_align(align_id)

    # {Sxx, Syy, Sxy, Sxz, Syz}.
    if param_types == 0:
        # Unpack the tuple.
        Sxx, Syy, Sxy, Sxz, Syz = params

        # Scaling.
        Sxx = Sxx * scale
        Syy = Syy * scale
        Sxy = Sxy * scale
        Sxz = Sxz * scale
        Syz = Syz * scale

        # Set the parameters.
        set(tensor=tensor_obj, value=[Sxx, Syy, Sxy, Sxz, Syz], param=['Sxx', 'Syy', 'Sxy', 'Sxz', 'Syz'], errors=errors)

    # {Szz, Sxx-yy, Sxy, Sxz, Syz}.
    elif param_types == 1:
        # Unpack the tuple.
        Szz, Sxxyy, Sxy, Sxz, Syz = params

        # Scaling.
        Szz = Szz * scale
        Sxxyy = Sxxyy * scale
        Sxy = Sxy * scale
        Sxz = Sxz * scale
        Syz = Syz * scale

        # Set the parameters.
        set(tensor=tensor_obj, value=[Szz, Sxxyy, Sxy, Sxz, Syz], param=['Szz', 'Sxxyy', 'Sxy', 'Sxz', 'Syz'], errors=errors)

    # {Axx, Ayy, Axy, Axz, Ayz}.
    elif param_types == 2:
        # Unpack the tuple.
        Axx, Ayy, Axy, Axz, Ayz = params

        # Scaling.
        Axx = Axx * scale
        Ayy = Ayy * scale
        Axy = Axy * scale
        Axz = Axz * scale
        Ayz = Ayz * scale

        # Set the parameters.
        set(tensor=tensor_obj, value=[Axx, Ayy, Axy, Axz, Ayz], param=['Axx', 'Ayy', 'Axy', 'Axz', 'Ayz'], errors=errors)

    # {Azz, Axx-yy, Axy, Axz, Ayz}.
    elif param_types == 3:
        # Unpack the tuple.
        Azz, Axxyy, Axy, Axz, Ayz = params

        # Scaling.
        Azz = Azz * scale
        Axxyy = Axxyy * scale
        Axy = Axy * scale
        Axz = Axz * scale
        Ayz = Ayz * scale

        # Set the parameters.
        set(tensor=tensor_obj, value=[Azz, Axxyy, Axy, Axz, Ayz], param=['Azz', 'Axxyy', 'Axy', 'Axz', 'Ayz'], errors=errors)

    # {Axx, Ayy, Axy, Axz, Ayz}.
    elif param_types == 4:
        # Unpack the tuple.
        Axx, Ayy, Axy, Axz, Ayz = params

        # Get the bond length.
        r = None
        for spin in spin_loop():
            # First spin.
            if r == None:
                r = spin.r

            # Different value.
            if r != spin.r:
                raise RelaxError("Not all spins have the same bond length.")

        # Scaling.
        scale = scale / kappa() * r**3
        Axx = Axx * scale
        Ayy = Ayy * scale
        Axy = Axy * scale
        Axz = Axz * scale
        Ayz = Ayz * scale

        # Set the parameters.
        set(tensor=tensor_obj, value=[Axx, Ayy, Axy, Axz, Ayz], param=['Axx', 'Ayy', 'Axy', 'Axz', 'Ayz'], errors=errors)

    # {Azz, Axx-yy, Axy, Axz, Ayz}.
    elif param_types == 5:
        # Unpack the tuple.
        Azz, Axxyy, Axy, Axz, Ayz = params

        # Get the bond length.
        r = None
        for spin in spin_loop():
            # First spin.
            if r == None:
                r = spin.r

            # Different value.
            if r != spin.r:
                raise RelaxError("Not all spins have the same bond length.")

        # Scaling.
        scale = scale / kappa() * r**3
        Azz = Azz * scale
        Axxyy = Axxyy * scale
        Axy = Axy * scale
        Axz = Axz * scale
        Ayz = Ayz * scale

        # Set the parameters.
        set(tensor=tensor_obj, value=[Azz, Axxyy, Axy, Axz, Ayz], param=['Azz', 'Axxyy', 'Axy', 'Axz', 'Ayz'], errors=errors)

    # {Pxx, Pyy, Pxy, Pxz, Pyz}.
    elif param_types == 6:
        # Unpack the tuple.
        Pxx, Pyy, Pxy, Pxz, Pyz = params

        # Scaling.
        Pxx = Pxx * scale
        Pyy = Pyy * scale
        Pxy = Pxy * scale
        Pxz = Pxz * scale
        Pyz = Pyz * scale

        # Set the parameters.
        set(tensor=tensor_obj, value=[Pxx, Pyy, Pxy, Pxz, Pyz], param=['Pxx', 'Pyy', 'Pxy', 'Pxz', 'Pyz'], errors=errors)

    # {Pzz, Pxx-yy, Pxy, Pxz, Pyz}.
    elif param_types == 7:
        # Unpack the tuple.
        Pzz, Pxxyy, Pxy, Pxz, Pyz = params

        # Scaling.
        Pzz = Pzz * scale
        Pxxyy = Pxxyy * scale
        Pxy = Pxy * scale
        Pxz = Pxz * scale
        Pyz = Pyz * scale

        # Set the parameters.
        set(tensor=tensor_obj, value=[Pzz, Pxxyy, Pxy, Pxz, Pyz], param=['Pzz', 'Pxxyy', 'Pxy', 'Pxz', 'Pyz'], errors=errors)

    # Unknown parameter combination.
    else:
        raise RelaxUnknownParamCombError('param_types', param_types)

    # Set the domain and alignment ID.
    if domain:
        set_domain(tensor=tensor, domain=domain)
    if align_id:
        tensor_obj.set(param='align_id', value=align_id)


def map_bounds(param):
    """The function for creating bounds for the mapping function."""

    # {Axx, Ayy, Azz, Axxyy, Axy, Axz, Ayz}.
    if param in ['Axx', 'Ayy', 'Azz', 'Axxyy', 'Axy', 'Axz', 'Ayz']:
        return [-50, 50]

    # alpha.
    elif param == 'alpha':
        return [0, 2*pi]

    # beta.
    elif param == 'beta':
        return [0, pi]

    # gamma.
    elif param == 'gamma':
        return [0, 2*pi]


def kappa(nuc1='15N', nuc2='1H'):
    """Function for calculating the kappa constant.

    The kappa constant is::

        kappa = -3/(8pi^2).gI.gS.mu0.h_bar,

    where gI and gS are the gyromagnetic ratios of the I and S spins, mu0 is the permeability of
    free space, and h_bar is Planck's constant divided by 2pi.

    @param nuc1:    The first nucleus type.
    @type nuc1:     str
    @param nuc2:    The first nucleus type.
    @type nuc2:     str
    @return:        The kappa constant value.
    @rtype:         float
    """

    # Gyromagnetic ratios.
    gI = return_gyromagnetic_ratio(nuc1)
    gS = return_gyromagnetic_ratio(nuc2)

    # Kappa.
    return -3.0/(8.0*pi**2) * gI * gS * mu0 * h_bar


def map_labels(index, params, bounds, swap, inc):
    """Function for creating labels, tick locations, and tick values for an OpenDX map.

    @param index:   The index (which isn't used here?!?).
    @type index:    int
    @param params:  The list of parameter names.
    @type params:   list of str
    @param bounds:  The bounds of the map.
    @type bounds:   list of lists (of a float and bin)
    @param swap:    An array for switching axes around.
    @type swap:     list of int
    @param inc:     The number of increments of one dimension in the map.
    @type inc:      list of int
    """

    # Initialise.
    labels = "{"
    tick_locations = []
    tick_values = []
    n = len(params)
    axis_incs = 5
    loc_inc = inc / axis_incs

    # Increment over the model parameters.
    for i in range(n):
        # Parameter conversion factors.
        factor = return_conversion_factor(params[swap[i]])

        # Parameter units.
        units = return_units(params[swap[i]])

        # Labels.
        if units:
            labels = labels + "\"" + params[swap[i]] + " (" + units + ")\""
        else:
            labels = labels + "\"" + params[swap[i]] + "\""

        # Tick values.
        vals = bounds[swap[i], 0] / factor
        val_inc = (bounds[swap[i], 1] - bounds[swap[i], 0]) / (axis_incs * factor)

        if i < n - 1:
            labels = labels + " "
        else:
            labels = labels + "}"

        # Tick locations.
        string = "{"
        val = 0.0
        for j in range(axis_incs + 1):
            string = string + " " + repr(val)
            val = val + loc_inc
        string = string + " }"
        tick_locations.append(string)

        # Tick values.
        string = "{"
        for j in range(axis_incs + 1):
            string = string + "\"" + "%.2f" % vals + "\" "
            vals = vals + val_inc
        string = string + "}"
        tick_values.append(string)

    return labels, tick_locations, tick_values


def matrix_angles(basis_set=0, tensors=None):
    """Function for calculating the 5D angles between the alignment tensors.

    The basis set used for the 5D vector construction changes the angles calculated.

    @param basis_set:   The basis set to use for constructing the 5D vectors.  If set to 0, the
                        basis set is {Sxx, Syy, Sxy, Sxz, Syz}.  If 1, then the basis set is {Szz,
                        Sxxyy, Sxy, Sxz, Syz}.
    @type basis_set:    int
    @param tensors:     An array of tensors to apply SVD to.  If None, all tensors will be used.
    @type tensors:      None or array of str
    """

    # Test that alignment tensor data exists.
    if not hasattr(cdp, 'align_tensors') or len(cdp.align_tensors) == 0:
        raise RelaxNoTensorError('alignment')

    # Count the number of tensors.
    tensor_num = 0
    for tensor in cdp.align_tensors:
        if tensors and tensor.name not in tensors:
            continue
        tensor_num = tensor_num + 1

    # Create the matrix which contains the 5D vectors.
    matrix = zeros((tensor_num, 5), float64)

    # Loop over the tensors.
    i = 0
    for tensor in cdp.align_tensors:
        # Skip tensors.
        if tensors and tensor.name not in tensors:
            continue

        # Unitary basis set.
        if basis_set == 0:
            # Pack the elements.
            matrix[i, 0] = tensor.Sxx
            matrix[i, 1] = tensor.Syy
            matrix[i, 2] = tensor.Sxy
            matrix[i, 3] = tensor.Sxz
            matrix[i, 4] = tensor.Syz

        # Geometric basis set.
        elif basis_set == 1:
            # Pack the elements.
            matrix[i, 0] = tensor.Szz
            matrix[i, 1] = tensor.Sxxyy
            matrix[i, 2] = tensor.Sxy
            matrix[i, 3] = tensor.Sxz
            matrix[i, 4] = tensor.Syz

        # Normalisation.
        norm = linalg.norm(matrix[i])
        matrix[i] = matrix[i] / norm

        # Increment the index.
        i = i + 1

    # Initialise the matrix of angles.
    cdp.align_tensors.angles = zeros((tensor_num, tensor_num), float64)

    # Header printout.
    sys.stdout.write("\nData pipe: " + repr(pipes.cdp_name()) + "\n")
    sys.stdout.write("\n5D angles in deg between the vectors ")
    if basis_set == 0:
        sys.stdout.write("{Sxx, Syy, Sxy, Sxz, Syz}")
    elif basis_set == 1:
        sys.stdout.write("{Szz, Sxx-yy, Sxy, Sxz, Syz}")
    sys.stdout.write(":\n")

    # Initialise the table of data.
    table = []

    # The table header.
    table.append([''])
    for i in range(tensor_num):
        if cdp.align_tensors[i].name == None:
            table[0].append(repr(i))
        else:
            table[0].append(cdp.align_tensors[i].name)

    # First loop over the rows.
    for i in range(tensor_num):
        # Add the tensor name.
        if cdp.align_tensors[i].name == None:
            table.append([repr(i)])
        else:
            table.append([cdp.align_tensors[i].name])

        # Second loop over the columns.
        for j in range(tensor_num):
            # Dot product.
            delta = dot(matrix[i], matrix[j])

            # Check.
            if delta > 1:
                delta = 1

            # The angle (in rad).
            cdp.align_tensors.angles[i, j] = arccos(delta)

            # Add to the table as degrees.
            table[i+1].append("%8.1f" % (cdp.align_tensors.angles[i, j]*180.0/pi))

    # Write out the table.
    write_data(out=sys.stdout, data=table)


def num_tensors(skip_fixed=True):
    """Count the number of tensors.

    @keyword skip_fixed:    If set to True, then only the tensors without the fixed flag will be counted.  If set to False, then all tensors will be counted.
    @type skip_fixed:       bool
    @return:                The number of tensors (excluding fixed tensors by default).
    @rtype:                 int
    """

    # Init.
    count = 0

    # Loop over the tensors.
    for tensor_cont in cdp.align_tensors:
        # Skip fixed tensors.
        if skip_fixed and tensor_cont.fixed:
            continue

        # Increment.
        count += 1

    # Return the count.
    return count


def reduction(full_tensor=None, red_tensor=None):
    """Specify which tensor is a reduction of which other tensor.

    @param full_tensor: The full alignment tensor.
    @type full_tensor:  str
    @param red_tensor:  The reduced alignment tensor.
    @type red_tensor:   str
    """

    # Tensor information.
    match_full = False
    match_red = False
    i = 0
    for tensor_cont in cdp.align_tensors:
        # Test the tensor names.
        if tensor_cont.name == full_tensor:
            match_full = True
            index_full = i
        if tensor_cont.name == red_tensor:
            match_red = True
            index_red = i

        # Increment.
        i = i + 1

    # No match.
    if not match_full:
        raise RelaxNoTensorError('alignment', full_tensor)
    if not match_red:
        raise RelaxNoTensorError('alignment', red_tensor)

    # Store.
    if not hasattr(cdp.align_tensors, 'reduction'):
        cdp.align_tensors.reduction = []
    cdp.align_tensors.reduction.append([index_full, index_red])


def return_conversion_factor(param):
    """Function for returning the factor of conversion between different parameter units.

    @param param:   The parameter name.
    @type param:    str
    @return:        The conversion factor.
    @rtype:         float
    """

    # Get the object name.
    object_name = return_data_name(param)

    # {Axx, Ayy, Azz, Axxyy, Axy, Axz, Ayz}.
    if object_name in ['Axx', 'Ayy', 'Azz', 'Axxyy', 'Axy', 'Axz', 'Ayz']:
        return 1.0

    # Angles.
    elif object_name in ['alpha', 'beta', 'gamma']:
        return (2.0*pi) / 360.0

    # No conversion factor.
    else:
        return 1.0


def return_data_name(name):
    """Return the parameter name.

    @param name:    The name of the parameter to return the name of.
    @type name:     str
    @return:        The parameter name.
    @rtype:         str
    """

    # Enforce that the name must be a string.
    if not isinstance(name, str):
        raise RelaxStrError('name', name)

    # Sxx.
    if search('^[Ss]xx$', name):
        return 'Sxx'

    # Syy.
    if search('^[Ss]yy$', name):
        return 'Syy'

    # Szz.
    if search('^[Ss]zz$', name):
        return 'Szz'

    # Sxy.
    if search('^[Ss]xy$', name):
        return 'Sxy'

    # Sxz.
    if search('^[Ss]xz$', name):
        return 'Sxz'

    # Syz.
    if search('^[Ss]yz$', name):
        return 'Syz'

    # Sxx-yy.
    if search('^[Ss]xxyy$', name):
        return 'Sxxyy'

    # Axx.
    if search('^[Aa]xx$', name):
        return 'Axx'

    # Ayy.
    if search('^[Aa]yy$', name):
        return 'Ayy'

    # Azz.
    if search('^[Aa]zz$', name):
        return 'Azz'

    # Axy.
    if search('^[Aa]xy$', name):
        return 'Axy'

    # Axz.
    if search('^[Aa]xz$', name):
        return 'Axz'

    # Ayz.
    if search('^[Aa]yz$', name):
        return 'Ayz'

    # Axx-yy.
    if search('^[Aa]xxyy$', name):
        return 'Axxyy'

    # Pxx.
    if search('^[Pp]xx$', name):
        return 'Pxx'

    # Pyy.
    if search('^[Pp]yy$', name):
        return 'Pyy'

    # Pzz.
    if search('^[Pp]zz$', name):
        return 'Pzz'

    # Pxy.
    if search('^[Pp]xy$', name):
        return 'Pxy'

    # Pxz.
    if search('^[Pp]xz$', name):
        return 'Pxz'

    # Pyz.
    if search('^[Pp]yz$', name):
        return 'Pyz'

    # Pxx-yy.
    if search('^[Pp]xxyy$', name):
        return 'Pxxyy'

    # alpha.
    if search('^a$', name) or search('alpha', name):
        return 'alpha'

    # beta.
    if search('^b$', name) or search('beta', name):
        return 'beta'

    # gamma.
    if search('^g$', name) or search('gamma', name):
        return 'gamma'

    # No parameter?
    raise RelaxUnknownParamError(name)

# User function documentation.
__return_data_name_prompt_doc__ = """
    Alignment tensor parameter string matching patterns
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    ____________________________________________________________________________________________
    |                                                        |              |                  |
    | Data type                                              | Object name  | Patterns         |
    |________________________________________________________|______________|__________________|
    |                                                        |              |                  |
    | The xx component of the Saupe order matrix - Sxx       | 'Sxx'        | '^[Sa]xx$'       |
    |                                                        |              |                  |
    | The yy component of the Saupe order matrix - Syy       | 'Syy'        | '^[Sa]yy$'       |
    |                                                        |              |                  |
    | The zz component of the Saupe order matrix - Szz       | 'Szz'        | '^[Sa]zz$'       |
    |                                                        |              |                  |
    | The xy component of the Saupe order matrix - Sxy       | 'Sxy'        | '^[Sa]xy$'       |
    |                                                        |              |                  |
    | The xz component of the Saupe order matrix - Sxz       | 'Sxz'        | '^[Sa]xz$'       |
    |                                                        |              |                  |
    | The yz component of the Saupe order matrix - Syz       | 'Syz'        | '^[Sa]yz$'       |
    |                                                        |              |                  |
    | The xx-yy component of the Saupe order matrix - Sxx-yy | 'Sxxyy'      | '^[Sa]xxyy$'     |
    |                                                        |              |                  |
    | The xx component of the alignment tensor - Axx         | 'Axx'        | '^[Aa]xx$'       |
    |                                                        |              |                  |
    | The yy component of the alignment tensor - Ayy         | 'Ayy'        | '^[Aa]yy$'       |
    |                                                        |              |                  |
    | The zz component of the alignment tensor - Azz         | 'Azz'        | '^[Aa]zz$'       |
    |                                                        |              |                  |
    | The xy component of the alignment tensor - Axy         | 'Axy'        | '^[Aa]xy$'       |
    |                                                        |              |                  |
    | The xz component of the alignment tensor - Axz         | 'Axz'        | '^[Aa]xz$'       |
    |                                                        |              |                  |
    | The yz component of the alignment tensor - Ayz         | 'Ayz'        | '^[Aa]yz$'       |
    |                                                        |              |                  |
    | The xx-yy component of the alignment tensor - Axx-yy   | 'Axxyy'      | '^[Aa]xxyy$'     |
    |                                                        |              |                  |
    | The xx component of the probability matrix - Pxx       | 'Pxx'        | '^[Pa]xx$'       |
    |                                                        |              |                  |
    | The yy component of the probability matrix - Pyy       | 'Pyy'        | '^[Pa]yy$'       |
    |                                                        |              |                  |
    | The zz component of the probability matrix - Pzz       | 'Pzz'        | '^[Pa]zz$'       |
    |                                                        |              |                  |
    | The xy component of the probability matrix - Pxy       | 'Pxy'        | '^[Pa]xy$'       |
    |                                                        |              |                  |
    | The xz component of the probability matrix - Pxz       | 'Pxz'        | '^[Pa]xz$'       |
    |                                                        |              |                  |
    | The yz component of the probability matrix - Pyz       | 'Pyz'        | '^[Pa]yz$'       |
    |                                                        |              |                  |
    | The xx-yy component of the probability matrix - Pxx-yy | 'Pxxyy'      | '^[Pa]xxyy$'     |
    |                                                        |              |                  |
    | The first Euler angle of the alignment tensor - alpha  | 'alpha'      | '^a$' or 'alpha' |
    |                                                        |              |                  |
    | The second Euler angle of the alignment tensor - beta  | 'beta'       | '^b$' or 'beta'  |
    |                                                        |              |                  |
    | The third Euler angle of the alignment tensor - gamma  | 'gamma'      | '^g$' or 'gamma' |
    |________________________________________________________|______________|__________________|
"""


def return_tensor(index, skip_fixed=True):
    """Return the tensor container for the given index, skipping fixed tensors if required.

    @param index:           The index of the tensor (if skip_fixed is True, then fixed tensors are not included in the index count).
    @type index:            int
    @keyword skip_fixed:    A flag which if True will exclude fixed tensors from the indexation.
    @type skip_fixed:       bool
    @return:                The tensor corresponding to the index.
    @rtype:                 data.align_tensor.AlignTensorData instance
    """

    # Init.
    count = 0

    # Loop over the tensors.
    for tensor_cont in cdp.align_tensors:
        # Skip fixed tensors.
        if skip_fixed and tensor_cont.fixed:
            continue

        # Index match, so return the container.
        if index == count:
            return tensor_cont

        # Increment.
        count += 1

    # Return False if the container was not found.
    return False


def return_units(param):
    """Function for returning a string representing the parameters units.

    @param param:   The parameter name.
    @type param:    str
    @return:        The string representation of the units.
    @rtype:         str
    """

    # Get the object name.
    object_name = return_data_name(param)

    # {Axx, Ayy, Azz, Axxyy, Axy, Axz, Ayz}.
    if object_name in ['Axx', 'Ayy', 'Azz', 'Axxyy', 'Axy', 'Axz', 'Ayz']:
        return 'Hz'

    # Angles.
    elif object_name in ['alpha', 'beta', 'gamma']:
        return 'deg'


def set(tensor=None, value=None, param=None, errors=False):
    """Set the tensor.

    @keyword tensor:    The alignment tensor object.
    @type tensor:       AlignTensorData instance
    @keyword value:     The list of values to set the parameters to.
    @type value:        list of float
    @keyword param:     The list of parameter names.
    @type param:        list of str
    @keyword errors:    A flag which determines if the alignment tensor data or its errors are being
                        input.
    @type errors:       bool
    """

    # Initialise.
    geo_params = []
    geo_values = []
    orient_params = []
    orient_values = []

    # Loop over the parameters.
    for i in range(len(param)):
        # Get the object name.
        param[i] = return_data_name(param[i])

        # Unknown parameter.
        if param[i] == None:
            raise RelaxUnknownParamError("alignment tensor", 'None')

        # Default value.
        if value[i] == None:
            value[i] = default_value(object_names[i])

        # Geometric parameter.
        if param[i] in ['Sxx', 'Syy', 'Szz', 'Sxxyy', 'Sxy', 'Sxz', 'Syz', 'Axx', 'Ayy', 'Azz', 'Axxyy', 'Axy', 'Axz', 'Ayz', 'Pxx', 'Pyy', 'Pzz', 'Pxxyy', 'Pxy', 'Pxz', 'Pyz']:
            geo_params.append(param[i])
            geo_values.append(value[i])

        # Orientational parameter.
        if param[i] in ['alpha', 'beta', 'gamma']:
            orient_params.append(param[i])
            orient_values.append(value[i])


    # Geometric parameters.
    #######################

    # A single geometric parameter.
    if len(geo_params) == 1:
        # Saupe order matrix.
        #####################

        # The single parameter Sxx.
        if geo_params[0] == 'Sxx':
            if errors:
                tensor.set(param='Sxx', value=geo_values[0], category='err')
            else:
                tensor.set(param='Sxx', value=geo_values[0])

        # The single parameter Syy.
        elif geo_params[0] == 'Syy':
            if errors:
                tensor.set(param='Syy', value=geo_values[0], category='err')
            else:
                tensor.set(param='Syy', value=geo_values[0])

        # The single parameter Sxy.
        elif geo_params[0] == 'Sxy':
            if errors:
                tensor.set(param='Sxy', value=geo_values[0], category='err')
            else:
                tensor.set(param='Sxy', value=geo_values[0])

        # The single parameter Sxz.
        elif geo_params[0] == 'Sxz':
            if errors:
                tensor.set(param='Sxz', value=geo_values[0], category='err')
            else:
                tensor.set(param='Sxz', value=geo_values[0])

        # The single parameter Syz.
        elif geo_params[0] == 'Syz':
            if errors:
                tensor.set(param='Syz', value=geo_values[0], category='err')
            else:
                tensor.set(param='Syz', value=geo_values[0])


        # Alignment tensor.
        ###################

        # The single parameter Axx.
        elif geo_params[0] == 'Axx':
            if errors:
                tensor.set(param='Sxx', value=3.0/2.0 * geo_values[0], category='err')
            else:
                tensor.set(param='Sxx', value=3.0/2.0 * geo_values[0])

        # The single parameter Ayy.
        elif geo_params[0] == 'Ayy':
            if errors:
                tensor.set(param='Syy', value=3.0/2.0 * geo_values[0], category='err')
            else:
                tensor.set(param='Syy', value=3.0/2.0 * geo_values[0])

        # The single parameter Axy.
        elif geo_params[0] == 'Axy':
            if errors:
                tensor.set(param='Sxy', value=3.0/2.0 * geo_values[0], category='err')
            else:
                tensor.set(param='Sxy', value=3.0/2.0 * geo_values[0])

        # The single parameter Axz.
        elif geo_params[0] == 'Axz':
            if errors:
                tensor.set(param='Sxz', value=3.0/2.0 * geo_values[0], category='err')
            else:
                tensor.set(param='Sxz', value=3.0/2.0 * geo_values[0])

        # The single parameter Ayz.
        elif geo_params[0] == 'Ayz':
            if errors:
                tensor.set(param='Syz', value=3.0/2.0 * geo_values[0], category='err')
            else:
                tensor.set(param='Syz', value=3.0/2.0 * geo_values[0])


        # Probability tensor.
        #####################

        # The single parameter Pxx.
        elif geo_params[0] == 'Pxx':
            if errors:
                tensor.set(param='Sxx', value=3.0/2.0 * (geo_values[0] - 1.0/3.0), category='err')
            else:
                tensor.set(param='Sxx', value=3.0/2.0 * (geo_values[0] - 1.0/3.0))

        # The single parameter Pyy.
        elif geo_params[0] == 'Pyy':
            if errors:
                tensor.set(param='Syy', value=3.0/2.0 * (geo_values[0] - 1.0/3.0), category='err')
            else:
                tensor.set(param='Syy', value=3.0/2.0 * (geo_values[0] - 1.0/3.0))

        # The single parameter Pxy.
        elif geo_params[0] == 'Pxy':
            if errors:
                tensor.set(param='Sxy', value=3.0/2.0 * geo_values[0], category='err')
            else:
                tensor.set(param='Sxy', value=3.0/2.0 * geo_values[0])

        # The single parameter Pxz.
        elif geo_params[0] == 'Pxz':
            if errors:
                tensor.set(param='Sxz', value=3.0/2.0 * geo_values[0], category='err')
            else:
                tensor.set(param='Sxz', value=3.0/2.0 * geo_values[0])

        # The single parameter Pyz.
        elif geo_params[0] == 'Pyz':
            if errors:
                tensor.set(param='Syz', value=3.0/2.0 * geo_values[0], category='err')
            else:
                tensor.set(param='Syz', value=3.0/2.0 * geo_values[0])

        # Cannot set the single parameter.
        else:
            raise RelaxError("The geometric alignment parameter " + repr(geo_params[0]) + " cannot be set.")

    # 5 geometric parameters.
    elif len(geo_params) == 5:
        # The geometric parameter set {Sxx, Syy, Sxy, Sxz, Syz}.
        if geo_params.count('Sxx') == 1 and geo_params.count('Syy') == 1 and geo_params.count('Sxy') == 1 and geo_params.count('Sxz') == 1 and geo_params.count('Syz') == 1:
            # The parameters.
            Sxx = geo_values[geo_params.index('Sxx')]
            Syy = geo_values[geo_params.index('Syy')]
            Sxy = geo_values[geo_params.index('Sxy')]
            Sxz = geo_values[geo_params.index('Sxz')]
            Syz = geo_values[geo_params.index('Syz')]

            # Set the internal parameter values.
            if errors:
                tensor.set(param='Axx', value=2.0/3.0 * Sxx, category='err')
                tensor.set(param='Ayy', value=2.0/3.0 * Syy, category='err')
                tensor.set(param='Axy', value=2.0/3.0 * Sxy, category='err')
                tensor.set(param='Axz', value=2.0/3.0 * Sxz, category='err')
                tensor.set(param='Ayz', value=2.0/3.0 * Syz, category='err')
            else:
                tensor.set(param='Axx', value=2.0/3.0 * Sxx)
                tensor.set(param='Ayy', value=2.0/3.0 * Syy)
                tensor.set(param='Axy', value=2.0/3.0 * Sxy)
                tensor.set(param='Axz', value=2.0/3.0 * Sxz)
                tensor.set(param='Ayz', value=2.0/3.0 * Syz)

        # The geometric parameter set {Szz, Sxxyy, Sxy, Sxz, Syz}.
        elif geo_params.count('Szz') == 1 and geo_params.count('Sxxyy') == 1 and geo_params.count('Sxy') == 1 and geo_params.count('Sxz') == 1 and geo_params.count('Syz') == 1:
            # The parameters.
            Szz = geo_values[geo_params.index('Szz')]
            Sxxyy = geo_values[geo_params.index('Sxxyy')]
            Sxy = geo_values[geo_params.index('Sxy')]
            Sxz = geo_values[geo_params.index('Sxz')]
            Syz = geo_values[geo_params.index('Syz')]

            # Set the internal parameter values.
            if errors:
                tensor.set(param='Axx', value=2.0/3.0 * -0.5*(Szz-Sxxyy), category='err')
                tensor.set(param='Ayy', value=2.0/3.0 * -0.5*(Szz+Sxxyy), category='err')
                tensor.set(param='Axy', value=2.0/3.0 * Sxy, category='err')
                tensor.set(param='Axz', value=2.0/3.0 * Sxz, category='err')
                tensor.set(param='Ayz', value=2.0/3.0 * Syz, category='err')
            else:
                tensor.set(param='Axx', value=2.0/3.0 * -0.5*(Szz-Sxxyy))
                tensor.set(param='Ayy', value=2.0/3.0 * -0.5*(Szz+Sxxyy))
                tensor.set(param='Axy', value=2.0/3.0 * Sxy)
                tensor.set(param='Axz', value=2.0/3.0 * Sxz)
                tensor.set(param='Ayz', value=2.0/3.0 * Syz)

        # The geometric parameter set {Axx, Ayy, Axy, Axz, Ayz}.
        elif geo_params.count('Axx') == 1 and geo_params.count('Ayy') == 1 and geo_params.count('Axy') == 1 and geo_params.count('Axz') == 1 and geo_params.count('Ayz') == 1:
            # The parameters.
            Axx = geo_values[geo_params.index('Axx')]
            Ayy = geo_values[geo_params.index('Ayy')]
            Axy = geo_values[geo_params.index('Axy')]
            Axz = geo_values[geo_params.index('Axz')]
            Ayz = geo_values[geo_params.index('Ayz')]

            # Set the internal parameter values.
            if errors:
                tensor.set(param='Axx', value=Axx, category='err')
                tensor.set(param='Ayy', value=Ayy, category='err')
                tensor.set(param='Axy', value=Axy, category='err')
                tensor.set(param='Axz', value=Axz, category='err')
                tensor.set(param='Ayz', value=Ayz, category='err')
            else:
                tensor.set(param='Axx', value=Axx)
                tensor.set(param='Ayy', value=Ayy)
                tensor.set(param='Axy', value=Axy)
                tensor.set(param='Axz', value=Axz)
                tensor.set(param='Ayz', value=Ayz)

        # The geometric parameter set {Azz, Axxyy, Axy, Axz, Ayz}.
        elif geo_params.count('Azz') == 1 and geo_params.count('Axxyy') == 1 and geo_params.count('Axy') == 1 and geo_params.count('Axz') == 1 and geo_params.count('Ayz') == 1:
            # The parameters.
            Azz = geo_values[geo_params.index('Azz')]
            Axxyy = geo_values[geo_params.index('Axxyy')]
            Axy = geo_values[geo_params.index('Axy')]
            Axz = geo_values[geo_params.index('Axz')]
            Ayz = geo_values[geo_params.index('Ayz')]

            # Set the internal parameter values.
            if errors:
                tensor.set(param='Axx', value=-0.5*(Azz-Axxyy), category='err')
                tensor.set(param='Ayy', value=-0.5*(Azz+Axxyy), category='err')
                tensor.set(param='Axy', value=Axy, category='err')
                tensor.set(param='Axz', value=Axz, category='err')
                tensor.set(param='Ayz', value=Ayz, category='err')
            else:
                tensor.set(param='Axx', value=-0.5*(Azz-Axxyy))
                tensor.set(param='Ayy', value=-0.5*(Azz+Axxyy))
                tensor.set(param='Axy', value=Axy)
                tensor.set(param='Axz', value=Axz)
                tensor.set(param='Ayz', value=Ayz)

        # The geometric parameter set {Pxx, Pyy, Pxy, Pxz, Pyz}.
        elif geo_params.count('Pxx') == 1 and geo_params.count('Pyy') == 1 and geo_params.count('Pxy') == 1 and geo_params.count('Pxz') == 1 and geo_params.count('Pyz') == 1:
            # The parameters.
            Pxx = geo_values[geo_params.index('Pxx')]
            Pyy = geo_values[geo_params.index('Pyy')]
            Pxy = geo_values[geo_params.index('Pxy')]
            Pxz = geo_values[geo_params.index('Pxz')]
            Pyz = geo_values[geo_params.index('Pyz')]

            # Set the internal parameter values.
            if errors:
                tensor.set(param='Axx', value=Pxx - 1.0/3.0, category='err')
                tensor.set(param='Ayy', value=Pyy - 1.0/3.0, category='err')
                tensor.set(param='Axy', value=Pxy, category='err')
                tensor.set(param='Axz', value=Pxz, category='err')
                tensor.set(param='Ayz', value=Pyz, category='err')
            else:
                tensor.set(param='Axx', value=Pxx - 1.0/3.0)
                tensor.set(param='Ayy', value=Pyy - 1.0/3.0)
                tensor.set(param='Axy', value=Pxy)
                tensor.set(param='Axz', value=Pxz)
                tensor.set(param='Ayz', value=Pyz)

        # The geometric parameter set {Pzz, Pxxyy, Pxy, Pxz, Pyz}.
        elif geo_params.count('Pzz') == 1 and geo_params.count('Pxxyy') == 1 and geo_params.count('Pxy') == 1 and geo_params.count('Pxz') == 1 and geo_params.count('Pyz') == 1:
            # The parameters.
            Pzz = geo_values[geo_params.index('Pzz')]
            Pxxyy = geo_values[geo_params.index('Pxxyy')]
            Pxy = geo_values[geo_params.index('Pxy')]
            Pxz = geo_values[geo_params.index('Pxz')]
            Pyz = geo_values[geo_params.index('Pyz')]

            # Set the internal parameter values.
            if errors:
                tensor.set(param='Axx', value=-0.5*(Pzz-Pxxyy) - 1.0/3.0, category='err')
                tensor.set(param='Ayy', value=-0.5*(Pzz+Pxxyy) - 1.0/3.0, category='err')
                tensor.set(param='Axy', value=Pxy, category='err')
                tensor.set(param='Axz', value=Pxz, category='err')
                tensor.set(param='Ayz', value=Pyz, category='err')
            else:
                tensor.set(param='Axx', value=-0.5*(Pzz-Pxxyy) - 1.0/3.0)
                tensor.set(param='Ayy', value=-0.5*(Pzz+Pxxyy) - 1.0/3.0)
                tensor.set(param='Axy', value=Pxy)
                tensor.set(param='Axz', value=Pxz)
                tensor.set(param='Ayz', value=Pyz)

        # Unknown parameter combination.
        else:
            raise RelaxUnknownParamCombError('geometric parameter set', geo_params)


    # Unknown geometric parameters.
    else:
        raise RelaxUnknownParamCombError('geometric parameter set', geo_params)


    # Orientational parameters.
    ###########################

    # A single orientational parameter.
    if len(orient_params) == 1:
        # The single parameter alpha.
        if orient_params[0] == 'alpha':
            if errors:
                tensor.set(param='alpha', value=orient_values[orient_params.index('alpha')], category='err')
            else:
                tensor.set(param='alpha', value=orient_values[orient_params.index('alpha')])

        # The single parameter beta.
        elif orient_params[0] == 'beta':
            if errors:
                tensor.set(param='beta', value=orient_values[orient_params.index('beta')], category='err')
            else:
                tensor.set(param='beta', value=orient_values[orient_params.index('beta')])

        # The single parameter gamma.
        elif orient_params[0] == 'gamma':
            if errors:
                tensor.set(param='gamma', value=orient_values[orient_params.index('gamma')], category='err')
            else:
                tensor.set(param='gamma', value=orient_values[orient_params.index('gamma')])

    # Two orientational parameters.
    elif len(orient_params) == 2:
        # The orientational parameter set {alpha, beta}.
        if orient_params.count('alpha') == 1 and orient_params.count('beta') == 1:
            if errors:
                tensor.set(param='alpha', value=orient_values[orient_params.index('alpha')], category='err')
                tensor.set(param='beta', value=orient_values[orient_params.index('beta')], category='err')
            else:
                tensor.set(param='alpha', value=orient_values[orient_params.index('alpha')])
                tensor.set(param='beta', value=orient_values[orient_params.index('beta')])

        # The orientational parameter set {alpha, gamma}.
        if orient_params.count('alpha') == 1 and orient_params.count('gamma') == 1:
            if errors:
                tensor.set(param='alpha', value=orient_values[orient_params.index('alpha')], category='err')
                tensor.set(param='gamma', value=orient_values[orient_params.index('gamma')], category='err')
            else:
                tensor.set(param='alpha', value=orient_values[orient_params.index('alpha')])
                tensor.set(param='gamma', value=orient_values[orient_params.index('gamma')])

        # The orientational parameter set {beta, gamma}.
        if orient_params.count('beta') == 1 and orient_params.count('gamma') == 1:
            if errors:
                tensor.set(param='beta', value=orient_values[orient_params.index('beta')], category='err')
                tensor.set(param='gamma', value=orient_values[orient_params.index('gamma')], category='err')
            else:
                tensor.set(param='beta', value=orient_values[orient_params.index('beta')])
                tensor.set(param='gamma', value=orient_values[orient_params.index('gamma')])

        # Unknown parameter combination.
        else:
            raise RelaxUnknownParamCombError('orientational parameter set', orient_params)

    # Three orientational parameters.
    elif len(orient_params) == 3:
        # The orientational parameter set {alpha, beta, gamma}.
        if orient_params.count('alpha') == 1 and orient_params.count('beta') == 1:
            if errors:
                tensor.set(param='alpha', value=orient_values[orient_params.index('alpha')], category='err')
                tensor.set(param='beta', value=orient_values[orient_params.index('beta')], category='err')
                tensor.set(param='gamma', value=orient_values[orient_params.index('gamma')], category='err')
            else:
                tensor.set(param='alpha', value=orient_values[orient_params.index('alpha')])
                tensor.set(param='beta', value=orient_values[orient_params.index('beta')])
                tensor.set(param='gamma', value=orient_values[orient_params.index('gamma')])

        # Unknown parameter combination.
        else:
            raise RelaxUnknownParamCombError('orientational parameter set', orient_params)

    # More than three orientational parameters.
    elif len(orient_params) > 3:
        raise RelaxUnknownParamCombError('orientational parameter set', orient_params)


    # Fold the angles in.
    #####################

    if orient_params:
        fold_angles()

# User function documentation.
__set_prompt_doc__ = """
    Alignment tensor set details
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    If the alignment tensor has not been setup, use the more powerful function
    'alignment_tensor.init' to initialise the tensor parameters.

    The alignment tensor parameters can only be set when the data pipe corresponds to model-free
    analysis.  The units of the parameters are:

        Unitless for Sxx, Syy, Szz, Sxxyy, Sxy, Sxz, Syz.
        Unitless for Axx, Ayy, Azz, Axxyy, Axy, Axz, Ayz.
        Unitless for Pxx, Pyy, Pzz, Pxxyy, Pxy, Pxz, Pyz.
        Radians for all angles (alpha, beta, gamma).

    If a single geometric parameter is supplied, it must be one of Bxx, Byy, Bxy, Bxz, Byz, where B
    is one of S, A, or P.  For the parameters Bzz and Bxxyy, it is not possible to determine how to
    use the currently set values together with the supplied value to calculate the new internal
    parameters.  When supplying multiple geometric parameters, the set must belong to one of

        {Sxx, Syy, Sxy, Sxz, Syz},
        {Szz, Sxxyy, Sxy, Sxz, Syz}.
        {Axx, Ayy, Axy, Axz, Ayz},
        {Azz, Axxyy, Axy, Axz, Ayz}.
        {Pxx, Pyy, Pxy, Pxz, Pyz},
        {Pzz, Pxxyy, Pxy, Pxz, Pyz}.
"""


def set_align_id(tensor=None, align_id=None):
    """Set the align ID string for the given tensor.

    @keyword tensor:    The alignment tensor label.
    @type tensor:       str
    @keyword align_id:  The alignment ID string.
    @type align_id:     str
    """

    # Loop over the tensors.
    match = False
    for tensor_cont in cdp.align_tensors:
        # Find the matching tensor and then store the ID.
        if tensor_cont.name == tensor:
            tensor_cont.align_id = align_id
            match = True

    # The tensor label doesn't exist.
    if not match:
        raise RelaxNoTensorError('alignment', tensor)


def set_domain(tensor=None, domain=None):
    """Set the domain label for the given tensor.

    @param tensor:  The alignment tensor label.
    @type tensor:   str
    @param domain:  The domain label.
    @type domain:   str
    """

    # Check that the domain is defined.
    if not hasattr(cdp, 'domain') or domain not in cdp.domain.keys():
        raise RelaxError("The domain '%s' has not been defined.  Please use the domain user function." % domain)

    # Loop over the tensors.
    match = False
    for tensor_cont in cdp.align_tensors:
        # Find the matching tensor and then store the domain label.
        if tensor_cont.name == tensor:
            tensor_cont.set(param='domain', value=domain)
            match = True

    # The tensor label doesn't exist.
    if not match:
        raise RelaxNoTensorError('alignment', tensor)


def svd(basis_set=0, tensors=None):
    """Function for calculating the singular values of all the loaded tensors.

    The matrix on which SVD will be performed is::

        | Sxx1 Syy1 Sxy1 Sxz1 Syz1 |
        | Sxx2 Syy2 Sxy2 Sxz2 Syz2 |
        | Sxx3 Syy3 Sxy3 Sxz3 Syz3 |
        |  .    .    .    .    .   |
        |  .    .    .    .    .   |
        |  .    .    .    .    .   |
        | SxxN SyyN SxyN SxzN SyzN |

    This is the default unitary basis set (selected when basis_set is 0).  Alternatively a geometric
    basis set consisting of the stretching and skewing parameters Szz and Sxx-yy respectively
    replacing Sxx and Syy can be chosen by setting basis_set to 1.  The matrix in this case is::

        | Szz1 Sxxyy1 Sxy1 Sxz1 Syz1 |
        | Szz2 Sxxyy2 Sxy2 Sxz2 Syz2 |
        | Szz3 Sxxyy3 Sxy3 Sxz3 Syz3 |
        |  .     .     .    .    .   |
        |  .     .     .    .    .   |
        |  .     .     .    .    .   |
        | SzzN SxxyyN SxyN SxzN SyzN |

    The relationships between the geometric and unitary basis sets are::

        Szz = - Sxx - Syy,
        Sxxyy = Sxx - Syy,

    The SVD values and condition number are dependendent upon the basis set chosen.


    @param basis_set:   The basis set to create the 5 by n matrix on which to perform SVD.
    @type basis_set:    int
    @param tensors:     An array of tensors to apply SVD to.  If None, all tensors will be used.
    @type tensors:      None or array of str
    """

    # Test that alignment tensor data exists.
    if not hasattr(cdp, 'align_tensors') or len(cdp.align_tensors) == 0:
        raise RelaxNoTensorError('alignment')

    # Count the number of tensors used in the SVD.
    tensor_num = 0
    for tensor in cdp.align_tensors:
        if tensors and tensor.name not in tensors:
            continue
        tensor_num = tensor_num + 1

    # Create the matrix to apply SVD on.
    matrix = zeros((tensor_num, 5), float64)

    # Pack the elements.
    i = 0
    for tensor in cdp.align_tensors:
        # Skip tensors.
        if tensors and tensor.name not in tensors:
            continue

        # Unitary basis set.
        if basis_set == 0:
            matrix[i, 0] = tensor.Sxx
            matrix[i, 1] = tensor.Syy
            matrix[i, 2] = tensor.Sxy
            matrix[i, 3] = tensor.Sxz
            matrix[i, 4] = tensor.Syz

        # Geometric basis set.
        elif basis_set == 1:
            matrix[i, 0] = tensor.Szz
            matrix[i, 1] = tensor.Sxxyy
            matrix[i, 2] = tensor.Sxy
            matrix[i, 3] = tensor.Sxz
            matrix[i, 4] = tensor.Syz

        # Increment the index.
        i = i + 1

    # SVD.
    u, s, vh = linalg.svd(matrix)

    # Store the singular values.
    cdp.align_tensors.singular_vals = s

    # Calculate and store the condition number.
    cdp.align_tensors.cond_num = s[0] / s[-1]

    # Print out.
    print("\nData pipe: " + repr(pipes.cdp_name()))
    print("\nSingular values:")
    for val in s:
        print("    %.4e" % val)
    print("\nCondition number: %.2f" % cdp.align_tensors.cond_num)