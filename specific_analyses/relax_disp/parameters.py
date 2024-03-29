###############################################################################
#                                                                             #
# Copyright (C) 2004-2013 Edward d'Auvergne                                   #
# Copyright (C) 2009 Sebastien Morin                                          #
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
"""Functions relating to the parameters of the relaxation dispersion models."""

# Python module imports.
from copy import deepcopy
from numpy import array, float64, identity, zeros
import sys

# relax module imports.
from lib.errors import RelaxError, RelaxNoSequenceError
from lib.text.sectioning import subsection
from pipe_control import pipes
from pipe_control.mol_res_spin import exists_mol_res_spin_data, return_spin
from specific_analyses.relax_disp.disp_data import generate_r20_key, has_exponential_exp_type, loop_cluster, loop_exp_frq, return_value_from_frq_index
from specific_analyses.relax_disp.variables import MODEL_LIST_MMQ, MODEL_M61B, MODEL_NS_MMQ_3SITE, MODEL_NS_MMQ_3SITE_LINEAR, MODEL_NS_R1RHO_3SITE, MODEL_NS_R1RHO_3SITE_LINEAR


def assemble_param_vector(spins=None, key=None, sim_index=None):
    """Assemble the dispersion relaxation dispersion curve fitting parameter vector.

    @keyword spins:         The list of spin data containers for the block.
    @type spins:            list of SpinContainer instances
    @keyword key:           The key for the R2eff and I0 parameters.
    @type key:              str or None
    @keyword sim_index:     The optional MC simulation index.
    @type sim_index:        int
    @return:                An array of the parameter values of the dispersion relaxation model.
    @rtype:                 numpy float array
    """

    # Initialise.
    param_vector = []

    # Loop over the parameters of the cluster.
    for param_name, param_index, spin_index, r20_key in loop_parameters(spins=spins):
        # Get the value.
        value = get_value(key=key, spins=spins, sim_index=sim_index, param_name=param_name, spin_index=spin_index, r20_key=r20_key)

        # Add to the vector.
        param_vector.append(value)

    # Convert all None values to 0.0.
    for i in range(len(param_vector)):
        if param_vector[i] == None:
            param_vector[i] = 0.0

    # Return a numpy array.
    return array(param_vector, float64)


def assemble_scaling_matrix(spins=None, key=None, scaling=True):
    """Create and return the scaling matrix.

    @keyword spins:         The list of spin data containers for the block.
    @type spins:            list of SpinContainer instances
    @keyword key:           The key for the R2eff and I0 parameters.
    @type key:              str or None
    @keyword scaling:       A flag which if False will cause the identity matrix to be returned.
    @type scaling:          bool
    @return:                The diagonal and square scaling matrix.
    @rtype:                 numpy diagonal matrix
    """

    # Initialise.
    scaling_matrix = identity(param_num(spins=spins), float64)
    i = 0
    param_index = 0

    # No diagonal scaling.
    if not scaling:
        return scaling_matrix

    # Loop over the parameters of the cluster.
    for param_name, param_index, spin_index, r20_key in loop_parameters(spins=spins):
        # Transversal relaxation rate scaling.
        if param_name in ['r2', 'r2a', 'r2b']:
            scaling_matrix[param_index, param_index] = 10

        # The pA.pB.dw**2, phi_ex_B, phi_ex_C and pA.dw**2 parameters.
        elif param_name in ['phi_ex', 'phi_ex_B', 'phi_ex_C', 'padw2']:
            scaling_matrix[param_index, param_index] = 1

        # Chemical shift difference between states A and B scaling.
        elif param_name in ['dw', 'dw_AB', 'dw_AC', 'dw_BC', 'dwH', 'dwH_AB', 'dwH_AC', 'dwH_BC']:
            scaling_matrix[param_index, param_index] = 1

        # The population of state X.
        elif param_name in ['pA', 'pB', 'pC']:
            scaling_matrix[param_index, param_index] = 1

        # Exchange rate scaling.
        elif param_name in ['kex', 'kex_AB', 'kex_AC', 'kex_BC', 'k_AB', 'kB', 'kC']:
            scaling_matrix[param_index, param_index] = 10000

        # Time of exchange scaling.
        elif param_name == 'tex':
            scaling_matrix[param_index, param_index] = 1e-4

    # Return the scaling matrix.
    return scaling_matrix


def copy(pipe_from=None, pipe_to=None):
    """Copy dispersion parameters from one data pipe to another, averaging values for clusters.

    @param pipe_from:   The data pipe to copy the value from.  This defaults to the current data pipe.
    @type pipe_from:    str
    @param pipe_to:     The data pipe to copy the value to.  This defaults to the current data pipe.
    @type pipe_to:      str
    """

    # The current data pipe.
    pipe_orig = pipes.cdp_name()
    if pipe_from == None:
        pipe_from = pipe_orig
    if pipe_to == None:
        pipe_to = pipe_orig

    # Test that the pipes exist.
    pipes.test(pipe_from)
    pipes.test(pipe_to)

    # Test that the pipes are not the same.
    if pipe_from == pipe_to:
        raise RelaxError("The source and destination pipes cannot be the same.")

    # Test if the sequence data for pipe_from is loaded.
    if not exists_mol_res_spin_data(pipe_from):
        raise RelaxNoSequenceError(pipe_from)

    # Test if the sequence data for pipe_to is loaded.
    if not exists_mol_res_spin_data(pipe_to):
        raise RelaxNoSequenceError(pipe_to)

    # Switch to the destination data pipe.
    pipes.switch(pipe_to)

    # Loop over the clusters.
    for spin_ids in loop_cluster():
        # Initialise some variables.
        model = None
        pA = 0.0
        pB = 0.0
        pC = 0.0
        kex = 0.0
        kex_AB = 0.0
        kex_AC = 0.0
        kex_BC = 0.0
        k_AB = 0.0
        kB = 0.0
        kC = 0.0
        tex = 0.0
        count = 0
        spins_from = []
        spins_to = []
        selected_cluster = False

        # Loop over the spins, summing the parameters to be averaged.
        for id in spin_ids:
            # Get the spins, then store them.
            spin_from = return_spin(id, pipe=pipe_from)
            spin_to = return_spin(id, pipe=pipe_to)
            spins_from.append(spin_from)
            spins_to.append(spin_to)

            # Skip deselected spins.
            if not spin_from.select or not spin_to.select:
                continue

            # The first printout.
            if not selected_cluster:
                subsection(file=sys.stdout, text="Copying parameters for the spin block %s"%spin_ids, prespace=2)

            # Change the cluster selection flag.
            selected_cluster = True

            # The model.
            if not model:
                model = spin_from.model

            # Check that the models match for all spins of the cluster.
            if spin_from.model != model:
                raise RelaxError("The model '%s' of spin '%s' from the source data pipe does not match the '%s' model of previous spins of the cluster." % (spin_from.model, id, model))
            if spin_to.model != model:
                raise RelaxError("The model '%s' of spin '%s' from the destination data pipe does not match the '%s' model of previous spins of the cluster." % (spin_from.model, id, model))

            # Sum the source parameters.
            if 'pA' in spin_from.params:
                pA += spin_from.pA
            if 'pB' in spin_from.params:
                pB += spin_from.pB
            if 'pC' in spin_from.params:
                pC += spin_from.pC
            if 'kex' in spin_from.params:
                kex += spin_from.kex
            if 'kex_AB' in spin_from.params:
                kex_AB += spin_from.kex_AB
            if 'kex_AC' in spin_from.params:
                kex_AC += spin_from.kex_AC
            if 'kex_BC' in spin_from.params:
                kex_BC += spin_from.kex_BC
            if 'k_AB' in spin_from.params:
                k_AB += spin_from.k_AB
            if 'kB' in spin_from.params:
                kB += spin_from.kB
            if 'kC' in spin_from.params:
                kC += spin_from.kC
            if 'tex' in spin_from.params:
                tex += spin_from.tex

            # Increment the spin count.
            count += 1

        # The cluster is not selected, so move to the next.
        if not selected_cluster:
            continue

        # Average parameters.
        if pA != 0.0:
            pA = pA / count
            print("Averaged pA value:  %.15f" % pA)
        if pB != 0.0:
            pB = pB / count
            print("Averaged pA value:  %.15f" % pA)
        if pC != 0.0:
            pC = pC / count
            print("Averaged pC value:  %.15f" % pC)
        if kex != 0.0:
            kex = kex / count
            print("Averaged kex value: %.15f" % kex)
        if kex_AB != 0.0:
            kex_AB = kex_AB / count
            print("Averaged k_AB value: %.15f" % kex_AB)
        if kex_AC != 0.0:
            kex_AC = kex_AC / count
            print("Averaged k_AC value: %.15f" % kex_AC)
        if kex_BC != 0.0:
            kex_BC = kex_BC / count
            print("Averaged k_BC value: %.15f" % kex_BC)
        if k_AB != 0.0:
            k_AB = k_AB / count
            print("Averaged k_AB value: %.15f" % k_AB)
        if kB != 0.0:
            kB = kB / count
            print("Averaged kB value:  %.15f" % kB)
        if kC != 0.0:
            kC = kC / count
            print("Averaged kC value:  %.15f" % kC)
        if tex != 0.0:
            tex = tex / count
            print("Averaged tex value: %.15f" % tex)

        # Loop over the spins, this time copying the parameters.
        for i in range(len(spin_ids)):
            # Alias the containers.
            spin_from = spins_from[i]
            spin_to = spins_to[i]

            # Skip deselected spins.
            if not spin_from.select or not spin_to.select:
                continue

            # The R20 parameters.
            if 'r2' in spin_from.params:
                spin_to.r2 = deepcopy(spin_from.r2)
            if 'r2a' in spin_from.params:
                spin_to.r2a = deepcopy(spin_from.r2a)
            if 'r2b' in spin_from.params:
                spin_to.r2b = deepcopy(spin_from.r2b)

            # The averaged parameters.
            if 'pB' in spin_from.params and 'pC' not in spin_from.params:
                spin_to.pA = pA
                spin_to.pB = pB
                spin_to.pC = 1.0 - pA - pB
            elif 'pA' in spin_from.params:
                spin_to.pA = pA
                spin_to.pB = 1.0 - pA
            if 'kex' in spin_from.params:
                spin_to.kex = kex
            if 'kex_AB' in spin_from.params:
                spin_to.kex_AB = kex_AB
            if 'kex_AC' in spin_from.params:
                spin_to.kex_AC = kex_AC
            if 'kex_BC' in spin_from.params:
                spin_to.kex_BC = kex_BC
            if 'k_AB' in spin_from.params:
                spin_to.k_AB = k_AB
            if 'kB' in spin_from.params:
                spin_to.kB = kB
            if 'kC' in spin_from.params:
                spin_to.kC = kC
            if 'tex' in spin_from.params:
                spin_to.tex = tex

            # All other spin specific parameters.
            for param in spin_from.params:
                if param in ['r2', 'pA', 'pB', 'pC', 'kex', 'kex_AB', 'kex_AC', 'kex_BC', 'k_AB', 'kB', 'kC', 'tex']:
                    continue

                # Copy the value.
                setattr(spin_to, param, deepcopy(getattr(spin_from, param)))

    # Switch back to the original data pipe.
    pipes.switch(pipe_orig)


def disassemble_param_vector(param_vector=None, key=None, spins=None, sim_index=None):
    """Disassemble the parameter vector.

    @keyword param_vector:  The parameter vector.
    @type param_vector:     numpy array
    @keyword key:           The key for the R2eff and I0 parameters.
    @type key:              str or None
    @keyword spins:         The list of spin data containers for the block.
    @type spins:            list of SpinContainer instances
    @keyword sim_index:     The optional MC simulation index.
    @type sim_index:        int
    """

    # Initialise parameters if needed.
    for spin in spins:
        # The R2 parameter.
        if 'r2' in spin.params:
            if sim_index != None:
                spin.r2_sim[sim_index] = {}
            else:
                spin.r2 = {}

        # The R2A parameter.
        if 'r2a' in spin.params:
            if sim_index != None:
                spin.r2a_sim[sim_index] = {}
            else:
                spin.r2a = {}

        # The R2B parameter.
        if 'r2b' in spin.params:
            if sim_index != None:
                spin.r2b_sim[sim_index] = {}
            else:
                spin.r2b = {}

    # Loop over the parameters of the cluster, setting the values.
    for param_name, param_index, spin_index, r20_key in loop_parameters(spins=spins):
        set_value(value=param_vector[param_index], key=key, spins=spins, sim_index=sim_index, param_name=param_name, spin_index=spin_index, r20_key=r20_key)


def get_param_names(spins=None):
    """Generate a list of dispersion parameter names for the given spins.

    @keyword spins:         The list of spin data containers for the block.
    @type spins:            list of SpinContainer instances
    """

    # Initialise the structure.
    names = []

    # Loop over the parameters.
    for param_name, param_index, spin_index, r20_key in loop_parameters(spins=spins):
        # Set the initial text.
        param_text = param_name

        # The parameters with additional details.
        if param_name in ['r2', 'r2a', 'r2b']:
            param_text += " (%s)" % r20_key
 
        # Append the text.
        names.append(param_text)

    # Return the structure.
    return names


def get_value(key=None, spins=None, sim_index=None, param_name=None, spin_index=None, r20_key=None):
    """Return the value for the given parameter.

    @keyword key:           The key for the R2eff and I0 parameters.
    @type key:              str or None
    @keyword spins:         The list of spin data containers for the block.
    @type spins:            list of SpinContainer instances
    @keyword sim_index:     The optional MC simulation index.
    @type sim_index:        int
    @keyword param_name:    The parameter name.
    @type param_name:       str
    @keyword spin_index:    The spin index (for the cluster).
    @type spin_index:       int
    @keyword r20_key:       The unique R20 parameter key.
    @type r20_key:          str
    @return:                The parameter value.
    @rtype:                 float
    """

    # Default value of 0.0.
    value = 0.0

    # Spin specific parameters.
    if spin_index != None:
        # Get the simulation value.
        if sim_index != None:
            # Get the simulation object.
            sim_obj = getattr(spins[spin_index], param_name+'_sim')

            # R20 parameter.
            if r20_key != None:
                if r20_key in sim_obj[sim_index].keys():
                    value = sim_obj[sim_index][r20_key]

            # All other parameters.
            else:
                value = sim_obj[sim_index]

        # Get the normal value.
        else:
            # Get the object.
            obj = getattr(spins[spin_index], param_name)

            # R20 parameter.
            if r20_key != None:
                if r20_key in obj.keys():
                    value = obj[r20_key]

            # All other parameters.
            else:
                value = getattr(spins[spin_index], param_name)

    # Cluster specific parameters - use the parameter value from the first spin.
    else:
        # Set the simulation value.
        if sim_index != None:
            value = getattr(spins[0], param_name+'_sim')[sim_index]

        # Set the normal value.
        else:
            value = getattr(spins[0], param_name)

    # The R2eff model parameters.
    if key != None:
        if not key in value.keys():
            value = 0.0
        else:
            value = value[key]

    # Return the value.
    return value


def linear_constraints(spins=None, scaling_matrix=None):
    """Set up the relaxation dispersion curve fitting linear constraint matrices A and b.

    Standard notation
    =================

    The different constraints used within different models are::

        0 <= R2 <= 200
        0 <= R2A <= 200
        0 <= R2B <= 200
        pC <= pB <= pA <= 1
        pA >= 0.85 (the skewed condition, pA >> pB)
        pB >= 0
        pC >= 0
        phi_ex >= 0
        phi_ex_B >= 0
        phi_ex_C >= 0
        padw2 >= 0
        dw >= 0
        0 <= kex <= 2e6
        0 <= k_AB <= 2e6
        0 <= kB <= 2e6
        0 <= kC <= 2e6
        tex >= 0
        k_AB >= 0


    Matrix notation
    ===============

    In the notation A.x >= b, where A is a matrix of coefficients, x is an array of parameter values, and b is a vector of scalars, these inequality constraints are::

        | 1  0  0 |     |    R2    |      |    0    |
        |         |     |          |      |         |
        |-1  0  0 |     |    R2    |      |  -200   |
        |         |     |          |      |         |
        | 1  0  0 |     |   R2A    |      |    0    |
        |         |     |          |      |         |
        |-1  0  0 |     |   R2A    |      |  -200   |
        |         |     |          |      |         |
        | 1  0  0 |     |   R2B    |      |    0    |
        |         |     |          |      |         |
        |-1  0  0 |     |   R2B    |      |  -200   |
        |         |     |          |      |         |
        | 1  0  0 |     |    pA    |      |   0.5   |
        |         |     |          |      |         |
        |-1  0  0 |     |    pA    |      |   -1    |
        |         |     |          |      |         |
        | 1  0  0 |     |    pA    |      |   0.85  |
        |         |     |          |      |         |
        | 1  0  0 |     |    pB    |      |    0    |
        |         |     |          |      |         |
        | 1  0  0 |     |  phi_ex  |      |    0    |
        |         |     |          |      |         |
        | 1  0  0 |  .  | phi_ex_B |  >=  |    0    |
        |         |     |          |      |         |
        | 1  0  0 |     | phi_ex_C |      |    0    |
        |         |     |          |      |         |
        | 1  0  0 |     |  padw2   |      |    0    |
        |         |     |          |      |         |
        | 1  0  0 |     |    dw    |      |    0    |
        |         |     |          |      |         |
        | 1  0  0 |     |   kex    |      |    0    |
        |         |     |          |      |         |
        |-1  0  0 |     |   kex    |      |  -2e6   |
        |         |     |          |      |         |
        | 1  0  0 |     |    kB    |      |    0    |
        |         |     |          |      |         |
        |-1  0  0 |     |    kB    |      |  -2e6   |
        |         |     |          |      |         |
        | 1  0  0 |     |    kC    |      |    0    |
        |         |     |          |      |         |
        |-1  0  0 |     |    kC    |      |  -2e6   |
        |         |     |          |      |         |
        | 1  0  0 |     |   tex    |      |    0    |
        |         |     |          |      |         |
        | 1  0  0 |     |   k_AB   |      |    0    |


    @keyword spins:             The list of spin data containers for the block.
    @type spins:                list of SpinContainer instances
    @keyword scaling_matrix:    The diagonal, square scaling matrix.
    @type scaling_matrix:       numpy diagonal matrix
    """

    # Initialisation (0..j..m).
    A = []
    b = []
    n = param_num(spins=spins)
    zero_array = zeros(n, float64)
    j = 0

    # Loop over the parameters of the cluster.
    for param_name, param_index, spin_index, r20_key in loop_parameters(spins=spins):
        # Effective transversal relaxation rate.
        if param_name == 'r2eff':
            A.append(zero_array * 0.0)
            A.append(zero_array * 0.0)
            A[j][param_index] = 1.0
            A[j+1][param_index] = -1.0
            b.append(0.0)
            b.append(-200.0 / scaling_matrix[param_index, param_index])
            j += 2

        # Initial intensity.
        elif param_name == 'i0':
            A.append(zero_array * 0.0)
            A[j][param_index] = 1.0
            b.append(0.0)
            j += 1

        # The transversal relaxation rates (0 <= r2 <= 200).
        elif param_name in ['r2', 'r2a', 'r2b']:
            A.append(zero_array * 0.0)
            A.append(zero_array * 0.0)
            A[j][param_index] = 1.0
            A[j+1][param_index] = -1.0
            b.append(0.0)
            b.append(-200.0 / scaling_matrix[param_index, param_index])
            j += 2

        # The pA.pB.dw**2, phi_ex_B, phi_ex_C and pA.dw**2 parameters (phi_ex* >= 0 and padw2 >= 0).
        elif param_name in ['phi_ex', 'phi_ex_B', 'phi_ex_C', 'padw2']:
            A.append(zero_array * 0.0)
            A[j][param_index] = 1.0
            b.append(0.0)
            j += 1

        # Chemical exchange difference (dw >= 0).
        elif param_name in ['dw', 'dw_AB', 'dw_AC', 'dw_BC', 'dwH', 'dwH_AB', 'dwH_AC', 'dwH_BC']:
            if not spins[0].model in MODEL_LIST_MMQ + [MODEL_NS_R1RHO_3SITE, MODEL_NS_R1RHO_3SITE_LINEAR]:
                A.append(zero_array * 0.0)
                A[j][param_index] = 1.0
                b.append(0.0)
                j += 1

        # The population of state A and B.
        elif param_name == 'pA':
            # First the pA <= 1 constraint (which also rearranged is pB >= 0).
            A.append(zero_array * 0.0)
            A[j][param_index] = -1.0
            b.append(-1.0 / scaling_matrix[param_index, param_index])
            j += 1

            # The skewed condition (pA >> pB).
            if spins[0].model == MODEL_M61B:
                A.append(zero_array * 0.0)
                A[j][param_index] = 1.0
                b.append(0.85 / scaling_matrix[param_index, param_index])
                j += 1

            # Otherwise use the pA >= pB constraint.
            else:
                A.append(zero_array * 0.0)
                A[j][param_index] = 1.0
                b.append(0.5 / scaling_matrix[param_index, param_index])
                j += 1

        # The population of state C (the pB parameter is only present when pC exists).
        elif param_name == 'pB':
            # Find pA.
            for param_name2, param_index2, spin_index2, r20_key2 in loop_parameters(spins=spins):
                if param_name2 == 'pA':
                    # First pC >= 0 (which rearranged is -pA - pB >= -1).
                    A.append(zero_array * 0.0)
                    A[j][param_index2] = -1.0
                    A[j][param_index] = -1.0
                    b.append(-1.0 / scaling_matrix[param_index, param_index])
                    j += 1

                    # Then the pA >= pC constraint.
                    A.append(zero_array * 0.0)
                    A[j][param_index2] = 1.0
                    A[j][param_index] = -1.0
                    b.append(0.0)
                    j += 1
                    break

        # Exchange rates and times (0 <= k <= 2e6).
        elif param_name in ['kex', 'kex_AB', 'kex_AC', 'kex_BC', 'k_AB', 'kB', 'kC']:
            A.append(zero_array * 0.0)
            A.append(zero_array * 0.0)
            A[j][param_index] = 1.0
            A[j+1][param_index] = -1.0
            b.append(0.0)
            b.append(-2e6 / scaling_matrix[param_index, param_index])
            j += 2

        # Exchange times (tex >= 0).
        elif param_name in ['tex']:
            A.append(zero_array * 0.0)
            A[j][param_index] = 1.0
            b.append(0.0)
            j += 1

    # Convert to numpy data structures.
    A = array(A, float64)
    b = array(b, float64)

    # Return the matrices.
    return A, b


def loop_parameters(spins=None):
    """Generator function for looping of the parameters of the cluster.

    @keyword spins: The list of spin data containers for the block.
    @type spins:    list of SpinContainer instances
    @return:        The parameter name, the parameter index (for the parameter vector), the spin index (for the cluster), and the R20 parameter key (for R20, R20A, and R20B parameters stored as dictionaries).
    @rtype:         str, int, int, str
    """

    # The parameter index.
    param_index = -1

    # The R2eff model.
    if cdp.model_type == 'R2eff':
        # Loop over the spins.
        for spin_index in range(len(spins)):
            # Yield the two parameters.
            params = ['r2eff', 'i0']
            for i in range(2):
                # First increment the indices.
                param_index += 1

                # Yield the data.
                yield params[i], param_index, spin_index, None

    # All other models.
    else:
        # First the R2 parameters (one per spin per field strength).
        for spin_index in range(len(spins)):
            # The R2 parameter.
            if 'r2' in spins[0].params:
                for exp_type, frq in loop_exp_frq():
                    param_index += 1
                    yield 'r2', param_index, spin_index, generate_r20_key(exp_type=exp_type, frq=frq)

            # The R2A parameter.
            if 'r2a' in spins[0].params:
                for exp_type, frq in loop_exp_frq():
                    param_index += 1
                    yield 'r2a', param_index, spin_index, generate_r20_key(exp_type=exp_type, frq=frq)

            # The R2B parameter.
            if 'r2b' in spins[0].params:
                for exp_type, frq in loop_exp_frq():
                    param_index += 1
                    yield 'r2b', param_index, spin_index, generate_r20_key(exp_type=exp_type, frq=frq)

        # Then the chemical shift difference parameters 'phi_ex', 'phi_ex_B', 'phi_ex_C', 'padw2', 'dw', 'dw_AB', 'dw_BC', 'dw_AB' (one per spin).
        for spin_index in range(len(spins)):
            # Yield the data.
            if 'phi_ex' in spins[spin_index].params:
                param_index += 1
                yield 'phi_ex', param_index, spin_index, None
            if 'phi_ex_B' in spins[spin_index].params:
                param_index += 1
                yield 'phi_ex_B', param_index, spin_index, None
            if 'phi_ex_C' in spins[spin_index].params:
                param_index += 1
                yield 'phi_ex_C', param_index, spin_index, None
            if 'padw2' in spins[spin_index].params:
                param_index += 1
                yield 'padw2', param_index, spin_index, None
            if 'dw' in spins[spin_index].params:
                param_index += 1
                yield 'dw', param_index, spin_index, None
            if 'dw_AB' in spins[spin_index].params:
                param_index += 1
                yield 'dw_AB', param_index, spin_index, None
            if 'dw_BC' in spins[spin_index].params:
                param_index += 1
                yield 'dw_BC', param_index, spin_index, None
            if 'dw_AC' in spins[spin_index].params:
                param_index += 1
                yield 'dw_AC', param_index, spin_index, None

        # Then a separate block for the proton chemical shift difference parameters for the MQ models (one per spin).
        for spin_index in range(len(spins)):
            if 'dwH' in spins[spin_index].params:
                param_index += 1
                yield 'dwH', param_index, spin_index, None
            if 'dwH_AB' in spins[spin_index].params:
                param_index += 1
                yield 'dwH_AB', param_index, spin_index, None
            if 'dwH_BC' in spins[spin_index].params:
                param_index += 1
                yield 'dwH_BC', param_index, spin_index, None
            if 'dwH_AC' in spins[spin_index].params:
                param_index += 1
                yield 'dwH_AC', param_index, spin_index, None

        # All other parameters (one per spin cluster).
        for param in spins[0].params:
            if not param in ['r2', 'r2a', 'r2b', 'phi_ex', 'phi_ex_B', 'phi_ex_C', 'padw2', 'dw', 'dw_AB', 'dw_BC', 'dw_AB', 'dwH', 'dwH_AB', 'dwH_BC', 'dwH_AB']:
                param_index += 1
                yield param, param_index, None, None


def param_conversion(key=None, spins=None, sim_index=None):
    """Convert Disassemble the parameter vector.

    @keyword key:           The key for the R2eff and I0 parameters.
    @type key:              str or None
    @keyword spins:         The list of spin data containers for the block.
    @type spins:            list of SpinContainer instances
    @keyword sim_index:     The optional MC simulation index.
    @type sim_index:        int
    """

    # Loop over the parameters of the cluster.
    for param_name, param_index, spin_index, r20_key in loop_parameters(spins=spins):
        # Get the value.
        value = get_value(key=key, spins=spins, sim_index=sim_index, param_name=param_name, spin_index=spin_index, r20_key=r20_key)

        # The pA to pB to pC conversion.
        if param_name == 'pA':
            # 3-site exchange.
            if spins[0].model in [MODEL_NS_MMQ_3SITE, MODEL_NS_MMQ_3SITE_LINEAR]:
                # Get the pB value.
                pB = get_value(key=key, spins=spins, sim_index=sim_index, param_name='pB', spin_index=spin_index, r20_key=r20_key)

                # Set the pC value.
                pC = 1.0 - value - pB
                set_value(value=pC, key=key, spins=spins, sim_index=sim_index, param_name='pC', spin_index=spin_index)

            # 2-site exchange.
            else:
                pB = 1.0 - value
                set_value(value=pB, key=key, spins=spins, sim_index=sim_index, param_name='pB', spin_index=spin_index)

        # The kex to tex conversion.
        if param_name == 'kex':
            tex = 1.0 / value
            set_value(value=tex, key=key, spins=spins, sim_index=sim_index, param_name='tex', spin_index=spin_index)

        # The kex to k_AB and k_BA conversion.
        if param_name == 'kex' and 'pA' in spins[0].params:
            # Get pA value.
            pA = get_value(key=key, spins=spins, sim_index=sim_index, param_name='pA', spin_index=spin_index)

            # Calculate k_AB value and set it.
            k_AB = value * (1.0 - pA)
            set_value(value=k_AB, key=key, spins=spins, sim_index=sim_index, param_name='k_AB', spin_index=spin_index)

            # Calculate k_BA value and set it.
            k_BA = value * pA
            set_value(value=k_BA, key=key, spins=spins, sim_index=sim_index, param_name='k_BA', spin_index=spin_index)

        # The tex to kex conversion.
        if param_name == 'tex':
            kex = 1.0 / value
            set_value(value=kex, key=key, spins=spins, sim_index=sim_index, param_name='kex', spin_index=spin_index)


def param_index_to_param_info(index=None, spins=None):
    """Convert the given parameter array index to parameter identifying information.
    
    The parameter index will be converted to the parameter name, the relevant spin index in the cluster, and relevant exponential curve key.

    @keyword index: The index of the parameter array.
    @type index:    int
    @keyword spins: The list of spin data containers for the block.
    @type spins:    list of SpinContainer instances
    @return:        The parameter name, the spin index (for the cluster), and the frequency index (for parameters with different values per spectrometer field strength).
    @rtype:         str, int, int
    """

    # Loop over the parameters, yielding when a match is found.
    for param_name, param_index, spin_index, r20_key in loop_parameters(spins=spins):
        if param_index == index:
            return param_name, spin_index, r20_key


def param_num(spins=None):
    """Determine the number of parameters in the model.

    @keyword spins:         The list of spin data containers for the block.
    @type spins:            list of SpinContainer instances
    @return:                The number of model parameters.
    @rtype:                 int
    """

    # Initialise the number.
    num = 0

    # The R2eff model.
    if cdp.model_type == 'R2eff':
        # Exponential curves (with clustering).
        if has_exponential_exp_type():
            return 2 * len(spins)

        # Fixed time period experiments (with clustering).
        return 1 * len(spins)

    # Check the spin cluster.
    for spin in spins:
        # Skip deselected spins.
        if not spin.select:
            continue

        if len(spin.params) != len(spins[0].params):
            raise RelaxError("The number of parameters for each spin in the cluster are not the same.")

    # Count the number of R20 parameters.
    r20_params = ['r2', 'r2a', 'r2b']
    for spin in spins:
        # Skip deselected spins.
        if not spin.select:
            continue

        for i in range(len(spin.params)):
            if spin.params[i] in r20_params:
                for exp_type, frq in loop_exp_frq():
                    num += 1

    # Count the number of spin specific parameters for all spins.
    spin_params = ['phi_ex', 'phi_ex_B', 'phi_ex_C', 'padw2', 'dw', 'dwH']
    for spin in spins:
        # Skip deselected spins.
        if not spin.select:
            continue

        for i in range(len(spin.params)):
            if spin.params[i] in spin_params:
                num += 1

    # Count all other parameters, but only for a single spin.
    all_params = r20_params + spin_params
    for spin in spins:
        # Skip deselected spins.
        if not spin.select:
            continue

        for i in range(len(spin.params)):
            if not spin.params[i] in all_params:
                num += 1
        break

    # Return the number.
    return num


def set_value(value=None, key=None, spins=None, sim_index=None, param_name=None, spin_index=None, r20_key=None):
    """Return the value for the given parameter.

    @keyword value:         The parameter value to set.
    @type value:            float
    @keyword key:           The key for the R2eff and I0 parameters.
    @type key:              str or None
    @keyword spins:         The list of spin data containers for the block.
    @type spins:            list of SpinContainer instances
    @keyword sim_index:     The optional MC simulation index.
    @type sim_index:        int
    @keyword param_name:    The parameter name.
    @type param_name:       str
    @keyword spin_index:    The spin index (for the cluster).
    @type spin_index:       int
    @keyword r20_key:       The unique R20 parameter key.
    @type r20_key:          str
    """

    # Spin specific parameters.
    if spin_index != None:
        # Set the simulation value.
        if sim_index != None:
            # Get the simulation object.
            obj = getattr(spins[spin_index], param_name+'_sim')

            # R20 parameter.
            if r20_key != None:
                obj[sim_index][r20_key] = value

            # All other parameters.
            else:
                if key != None:
                    obj[sim_index][key] = value
                else:
                    obj[sim_index] = value

        # Set the normal value.
        else:
            # Get the object.
            obj = getattr(spins[spin_index], param_name)

            # R20 parameter.
            if r20_key != None:
                obj[r20_key] = value

            # Set the normal value.
            else:
                if key != None:
                    obj[key] = value
                else:
                    setattr(spins[spin_index], param_name, value)

    # Cluster specific parameters.
    else:
        # Set the same parameter value for all spins in the cluster.
        for spin in spins:
            # Set the simulation value.
            if sim_index != None:
                sim_obj = getattr(spin, param_name+'_sim')
                sim_obj[sim_index] = value

            # Set the normal value.
            else:
                setattr(spin, param_name, value)
