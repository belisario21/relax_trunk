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
"""The Carver and Richards (1972) 2-site all time scale exchange U{CR72<http://wiki.nmr-relax.com/CR72>} and U{CR72 full<http://wiki.nmr-relax.com/CR72_full>} models.

Description
===========

This module is for the function, gradient and Hessian of the U{CR72<http://wiki.nmr-relax.com/CR72>} and U{CR72 full<http://wiki.nmr-relax.com/CR72_full>} models.


References
==========

The model is named after the reference:

    - Carver, J. P. and Richards, R. E. (1972).  General 2-site solution for chemical exchange produced dependence of T2 upon Carr-Purcell pulse separation.  I{J. Magn. Reson.}, B{6}, 89-105.  (U{DOI: 10.1016/0022-2364(72)90090-X<http://dx.doi.org/10.1016/0022-2364(72)90090-X>}).


Equations
=========

The equation used is::

    R2eff = 1/2 [ R2A0 + R2B0 + kex - 2.nu_cpmg.cosh^-1 (D+.cosh(eta+) - D-.cos(eta-)) ] ,

where::

           1 /        Psi + 2delta_omega^2 \ 
    D+/- = - | +/-1 + -------------------- | ,
           2 \        sqrt(Psi^2 + zeta^2) /

             2^(2/3)
    eta+/- = ------- sqrt(+/-Psi + sqrt(Psi^2 + zeta^2)) ,
             nu_cpmg

    Psi = (R2A0 - R2B0 - pA.kex + pB.kex)^2 - delta_omega^2 + 4pA.pB.kex^2 ,

    zeta = 2delta_omega (R2A0 - R2B0 - pA.kex + pB.kex).

kex is the chemical exchange rate constant, pA and pB are the populations of states A and B, and delta_omega is the chemical shift difference between the two states in ppm.


CR72 model
----------

Importantly for the implementation of this model, it is assumed that R2A0 and R2B0 are identical.  This simplifies some of the equations to::

    R2eff = R20 + kex/2 - nu_cpmg.cosh^-1 (D+.cosh(eta+) - D-.cos(eta-) ,

where::

    Psi = kex^2 - delta_omega^2 ,

    zeta = -2delta_omega (pA.kex - pB.kex).


Links
=====

More information on the CR72 model can be found in the:

    - U{relax wiki<http://wiki.nmr-relax.com/CR72>},
    - U{relax manual<http://www.nmr-relax.com/manual/reduced_CR72_2_site_CPMG_model.html>},
    - U{relaxation dispersion page of the relax website<http://www.nmr-relax.com/analyses/relaxation_dispersion.html#CR72>}.

More information on the CR72 full model can be found in the:

    - U{relax wiki<http://wiki.nmr-relax.com/CR72_full>},
    - U{relax manual<http://www.nmr-relax.com/manual/full_CR72_2_site_CPMG_model.html>},
    - U{relaxation dispersion page of the relax website<http://www.nmr-relax.com/analyses/relaxation_dispersion.html#CR72_full>}.
"""

# Python module imports.
from numpy import arccosh, cos, cosh, sqrt


def r2eff_CR72(r20a=None, r20b=None, pA=None, dw=None, kex=None, cpmg_frqs=None, back_calc=None, num_points=None):
    """Calculate the R2eff values for the CR72 model.

    See the module docstring for details.


    @keyword r20a:          The R20 parameter value of state A (R2 with no exchange).
    @type r20a:             float
    @keyword r20b:          The R20 parameter value of state B (R2 with no exchange).
    @type r20b:             float
    @keyword pA:            The population of state A.
    @type pA:               float
    @keyword dw:            The chemical exchange difference between states A and B in rad/s.
    @type dw:               float
    @keyword kex:           The kex parameter value (the exchange rate in rad/s).
    @type kex:              float
    @keyword cpmg_frqs:     The CPMG nu1 frequencies.
    @type cpmg_frqs:        numpy rank-1 float array
    @keyword back_calc:     The array for holding the back calculated R2eff values.  Each element corresponds to one of the CPMG nu1 frequencies.
    @type back_calc:        numpy rank-1 float array
    @keyword num_points:    The number of points on the dispersion curve, equal to the length of the cpmg_frqs and back_calc arguments.
    @type num_points:       int
    """

    # The B population.
    pB = 1.0 - pA

    # Repetitive calculations (to speed up calculations).
    dw2 = dw**2
    r20_kex = (r20a + r20b + kex) / 2.0
    k_BA = pA * kex
    k_AB = pB * kex

    # The Psi and zeta values.
    if r20a != r20b:
        fact = r20a - r20b - k_BA + k_AB
        Psi = fact**2 - dw2 + 4.0*pA*pB*kex**2
        zeta = 2.0*dw * fact
    else:
        Psi = kex**2 - dw2
        zeta = -2.0*dw * (k_BA - k_AB)

    # More repetitive calculations.
    sqrt_psi2_zeta2 = sqrt(Psi**2 + zeta**2)

    # The D+/- values.
    D_part = (Psi + 2.0*dw2) / sqrt_psi2_zeta2
    Dpos = 0.5 * (1.0 + D_part)
    Dneg = 0.5 * (-1.0 + D_part)

    # Partial eta+/- values.
    eta_scale = 2.0**(-3.0/2.0)
    etapos_part = eta_scale * sqrt(Psi + sqrt_psi2_zeta2)
    etaneg_part = eta_scale * sqrt(-Psi + sqrt_psi2_zeta2)

    # Loop over the time points, back calculating the R2eff values.
    for i in range(num_points):
        # The full eta+/- values.
        etapos = etapos_part / cpmg_frqs[i]
        etaneg = etaneg_part / cpmg_frqs[i]

        # Catch large values of etapos going into the cosh function.
        if etapos > 100:
            back_calc[i] = 1e100
            continue

        # The arccosh argument - catch invalid values.
        fact = Dpos * cosh(etapos) - Dneg * cos(etaneg)
        if fact < 1.0:
            back_calc[i] = r20_kex
            continue

        # The full formula.
        back_calc[i] = r20_kex - cpmg_frqs[i] * arccosh(fact)
