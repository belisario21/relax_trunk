###############################################################################
#                                                                             #
# Copyright (C) 2009 Sebastien Morin                                          #
# Copyright (C) 2013-2014 Edward d'Auvergne                                   #
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
"""The Meiboom (1961) 2-site fast exchange R1rho U{M61<http://wiki.nmr-relax.com/M61>} model.

Description
===========

This module is for the function, gradient and Hessian of the U{M61<http://wiki.nmr-relax.com/M61>} model.


References
==========

The model is named after the reference:

    - Meiboom S. (1961).  Nuclear magnetic resonance study of the proton transfer in water.  I{J. Chem. Phys.}, B{34}, 375-388.  (U{DOI: 10.1063/1.1700960<http://dx.doi.org/10.1063/1.1700960>}).


Equations
=========

The equation used is::

                       phi_ex * kex
    R1rho = R1rho' + ----------------- ,
                     kex^2 + omega_1^2

where::

    phi_ex = pA * pB * delta_omega^2 ,

R1rho' is the R1rho value in the absence of exchange, kex is the chemical exchange rate constant, pA and pB are the populations of states A and B, delta_omega is the chemical shift difference between the two states, and omega_1 is the spin-lock field strength.


Links
=====

More information on the M61 model can be found in the:

    - U{relax wiki<http://wiki.nmr-relax.com/M61>},
    - U{relax manual<http://www.nmr-relax.com/manual/M61_2_site_fast_exchange_R1_model.html>},
    - U{relaxation dispersion page of the relax website<http://www.nmr-relax.com/analyses/relaxation_dispersion.html#M61>}.
"""

# Python module imports.
from math import pi


def r1rho_M61(r1rho_prime=None, phi_ex=None, kex=None, spin_lock_fields2=None, back_calc=None, num_points=None):
    """Calculate the R2eff values for the M61 model.

    See the module docstring for details.


    @keyword r1rho_prime:       The R1rho_prime parameter value (R1rho with no exchange).
    @type r1rho_prime:          float
    @keyword phi_ex:            The phi_ex parameter value (pA * pB * delta_omega^2).
    @type phi_ex:               float
    @keyword kex:               The kex parameter value (the exchange rate in rad/s).
    @type kex:                  float
    @keyword spin_lock_fields2: The R1rho spin-lock field strengths squared (in rad^2.s^-2).
    @type spin_lock_fields2:    numpy rank-1 float array
    @keyword back_calc:         The array for holding the back calculated R1rho values.  Each element corresponds to one of the spin-lock fields.
    @type back_calc:            numpy rank-1 float array
    @keyword num_points:        The number of points on the dispersion curve, equal to the length of the spin_lock_fields and back_calc arguments.
    @type num_points:           int
    """

    # Repetitive calculations (to speed up calculations).
    kex2 = kex**2

    # The numerator.
    numer = phi_ex * kex

    # Loop over the dispersion points, back calculating the R1rho values.
    for i in range(num_points):
        # Catch zeros (to avoid pointless mathematical operations).
        if numer == 0.0:
            back_calc[i] = r1rho_prime
            continue

        # Denominator.
        denom = kex2 + spin_lock_fields2[i]

        # Avoid divide by zero.
        if denom == 0.0:
            back_calc[i] = 1e100
            continue

        # R1rho calculation.
        back_calc[i] = r1rho_prime + numer / denom
