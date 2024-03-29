###############################################################################
#                                                                             #
# Copyright (C) 2007-2013 Edward d'Auvergne                                   #
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
"""The align_tensor user function definitions."""

# relax module imports.
from graphics import WIZARD_IMAGE_PATH
from pipe_control import align_tensor, pipes
from user_functions.data import Uf_info; uf_info = Uf_info()
from user_functions.objects import Desc_container


# The user function class.
uf_class = uf_info.add_class('align_tensor')
uf_class.title = "Class for manipulating the alignment tensor."
uf_class.menu_text = "&align_tensor"
uf_class.gui_icon = "relax.align_tensor"


# The align_tensor.copy user function.
uf = uf_info.add_uf('align_tensor.copy')
uf.title = "Copy alignment tensor data."
uf.title_short = "Alignment tensor copying."
uf.add_keyarg(
    name = "tensor_from",
    default = None,
    py_type = "str",
    desc_short = "source tensor ID",
    desc = "The identification string of the alignment tensor to copy the data from."
)
uf.add_keyarg(
    name = "pipe_from",
    default = None,
    py_type = "str",
    desc_short = "source data pipe",
    desc = "The name of the data pipe to copy the alignment tensor data from.",
    wiz_element_type = 'combo',
    wiz_combo_iter = pipes.pipe_names,
    can_be_none = True
)
uf.add_keyarg(
    name = "tensor_to",
    default = None,
    py_type = "str",
    desc_short = "destination tensor ID",
    desc = "The identification string of the alignment tensor to copy the data to.",
    can_be_none = True
)
uf.add_keyarg(
    name = "pipe_to",
    default = None,
    py_type = "str",
    desc_short = "destination data pipe",
    desc = "The name of the data pipe to copy the alignment tensor data to.",
    wiz_element_type = 'combo',
    wiz_combo_iter = pipes.pipe_names,
    can_be_none = True
)
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("This will copy the alignment tensor data to a new tensor or a new data pipe.  The destination data pipe must not contain any alignment tensor data corresponding to the tensor_to label.  If the source or destination data pipes are not supplied, then both will default to the current data pipe.  Both the source and destination tensor IDs must be supplied.")
# Prompt examples.
uf.desc.append(Desc_container("Prompt examples"))
uf.desc[-1].add_paragraph("To copy the alignment tensor data corresponding to 'Pf1' from the data pipe 'old' to the current data pipe, type one of:")
uf.desc[-1].add_prompt("relax> align_tensor.copy('Pf1', 'old')")
uf.desc[-1].add_prompt("relax> align_tensor.copy(tensor_from='Pf1', pipe_from='old')")
uf.desc[-1].add_paragraph("To copy the alignment tensor data corresponding to 'Otting' from the current data pipe to the data pipe new, type one of:")
uf.desc[-1].add_prompt("relax> align_tensor.copy('Otting', pipe_to='new')")
uf.desc[-1].add_prompt("relax> align_tensor.copy(tensor_from='Otting', pipe_to='new')")
uf.desc[-1].add_paragraph("To copy the alignment tensor data of 'Otting' to that of 'Otting new', type one of:")
uf.desc[-1].add_prompt("relax> align_tensor.copy('Otting', tensor_to='Otting new')")
uf.desc[-1].add_prompt("relax> align_tensor.copy(tensor_from='Pf1', tensor_to='Otting new')")
uf.backend = align_tensor.copy
uf.menu_text = "&copy"
uf.gui_icon = "oxygen.actions.list-add"
uf.wizard_size = (800, 600)
uf.wizard_image = WIZARD_IMAGE_PATH + 'align_tensor.png'


# The align_tensor.delete user function.
uf = uf_info.add_uf('align_tensor.delete')
uf.title = "Delete alignment tensor data from the relax data store."
uf.title_short = "Alignment tensor pipe deletion."
uf.add_keyarg(
    name = "tensor",
    py_type = "str",
    desc_short = "tensor",
    desc = "The alignment tensor identification string.",
    wiz_element_type = 'combo',
    wiz_combo_iter = align_tensor.get_tensor_ids,
    wiz_read_only = True,
    can_be_none = True
)
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("This will delete the specified alignment tensor data from the current data pipe.  If no tensor is specified, all tensors will be deleted.")
uf.backend = align_tensor.delete
uf.menu_text = "&delete"
uf.gui_icon = "oxygen.actions.list-remove"
uf.wizard_image = WIZARD_IMAGE_PATH + 'align_tensor.png'


# The align_tensor.display user function.
uf = uf_info.add_uf('align_tensor.display')
uf.title = "Display the alignment tensor information in full detail."
uf.title_short = "Align tensor display."
uf.display = True
uf.add_keyarg(
    name = "tensor",
    py_type = "str",
    desc_short = "tensor",
    desc = "The alignment tensor identification string.",
    wiz_element_type = 'combo',
    wiz_combo_iter = align_tensor.get_tensor_ids,
    wiz_read_only = True,
    can_be_none = True
)
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("This will show all information relating to the alignment tensor, including the different tensor forms:")
uf.desc[-1].add_list_element("Probability tensor.")
uf.desc[-1].add_list_element("Saupe order matrix.")
uf.desc[-1].add_list_element("Alignment tensor.")
uf.desc[-1].add_list_element("Magnetic susceptibility tensor.")
uf.desc[-1].add_paragraph("All possible tensor parameters and information will also be shown (Eigensystem, GDO, Aa, Ar, R, eta, chi_ax, chi_rh, etc).  The printout will be extensive.")
uf.desc[-1].add_paragraph("If no tensor is specified, all tensors will be displayed.")
uf.backend = align_tensor.display
uf.menu_text = "dis&play"
uf.gui_icon = "oxygen.actions.document-preview"
uf.wizard_height_desc = 400
uf.wizard_size = (800, 600)
uf.wizard_image = WIZARD_IMAGE_PATH + 'align_tensor.png'


# The align_tensor.fix user function.
uf = uf_info.add_uf('align_tensor.fix')
uf.title = "Fix all alignment tensors so that they do not change during optimisation."
uf.title_short = "Fix alignment tensors."
uf.add_keyarg(
    name = "id",
    py_type = "str",
    desc_short = "tensor ID",
    desc = "The alignment tensor identification string.",
    wiz_element_type = 'combo',
    wiz_combo_iter = align_tensor.get_tensor_ids,
    wiz_read_only = True,
    can_be_none = True
)
uf.add_keyarg(
    name = "fixed",
    default = True,
    py_type = "bool",
    desc_short = "fixed flag",
    desc = "The flag specifying if the tensors should be fixed or variable."
)
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("If the ID string is left unset, then all alignment tensors will be fixed.")
uf.backend = align_tensor.fix
uf.menu_text = "&fix"
uf.gui_icon = "oxygen.status.object-locked"
uf.wizard_size = (800, 500)
uf.wizard_image = WIZARD_IMAGE_PATH + 'align_tensor.png'


# The align_tensor.init user function.
uf = uf_info.add_uf('align_tensor.init')
uf.title = "Initialise an alignment tensor."
uf.title_short = "Alignment tensor initialisation."
uf.add_keyarg(
    name = "tensor",
    py_type = "str",
    desc_short = "tensor ID",
    desc = "The optional alignment tensor ID string, required if multiple tensors exist per alignment.",
    can_be_none = True
)
uf.add_keyarg(
    name = "align_id",
    py_type = "str",
    desc_short = "alignment ID",
    desc = "The alignment ID string that the tensor corresponds to.",
    wiz_element_type = "combo",
    wiz_combo_iter = align_tensor.get_tensor_ids,
    wiz_read_only = False
)
uf.add_keyarg(
    name = "domain",
    py_type = "str",
    desc_short = "domain ID",
    desc = "The optional domain ID string that the tensor corresponds to.",
    can_be_none = True
)
uf.add_keyarg(
    name = "params",
    py_type = "num_tuple",
    desc_short = "alignment tensor parameters",
    dim = 5,
    desc = "The alignment tensor data.",
    wiz_read_only = False
)
uf.add_keyarg(
    name = "scale",
    default = 1.0,
    py_type = "float",
    desc_short = "scale",
    desc = "The alignment tensor eigenvalue scaling value."
)
uf.add_keyarg(
    name = "angle_units",
    default = "deg",
    py_type = "str",
    desc_short = "angle units",
    desc = "The units for the angle parameters."
)
uf.add_keyarg(
    name = "param_types",
    default = 2,
    py_type = "int",
    desc_short = "parameter types",
    desc = "A flag to select different parameter combinations.",
    wiz_element_type = "combo",
    wiz_combo_choices = [
        "{Sxx, Syy, Sxy, Sxz, Syz}",
        "{Szz, Sxx-yy, Sxy, Sxz, Syz}",
        "{Axx, Ayy, Axy, Axz, Ayz}",
        "{Azz, Axx-yy, Axy, Axz, Ayz}",
        "{Axx, Ayy, Axy, Axz, Ayz}",
        "{Azz, Axx-yy, Axy, Axz, Ayz}",
        "{Pxx, Pyy, Pxy, Pxz, Pyz}",
        "{Pzz, Pxx-yy, Pxy, Pxz, Pyz}"
    ],
    wiz_combo_data = [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7
    ],
    wiz_read_only = True
)
uf.add_keyarg(
    name = "errors",
    default = False,
    py_type = "bool",
    desc_short = "errors flag",
    desc = "A flag which determines if the alignment tensor data or its errors are being input."
)
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("The tensor ID is only required if there are multiple unique tensors per alignment.  An example is if internal domain motions cause multiple parts of the molecule to align differently.  The tensor ID is optional and in the case of only a single tensor per alignment, the tensor can be identified using the alignment ID instead.")
uf.desc[-1].add_paragraph("The alignment tensor parameters should be a tuple of floating point numbers (a list surrounded by round brakets).  These correspond to the parameters of the tensor which can be specified by the parameter types whereby the values correspond to:")
uf.desc[-1].add_item_list_element("0", "{Sxx, Syy, Sxy, Sxz, Syz}  (unitless),")
uf.desc[-1].add_item_list_element("1", "{Szz, Sxx-yy, Sxy, Sxz, Syz}  (Pales default format),")
uf.desc[-1].add_item_list_element("2", "{Axx, Ayy, Axy, Axz, Ayz}  (unitless),")
uf.desc[-1].add_item_list_element("3", "{Azz, Axx-yy, Axy, Axz, Ayz}  (unitless),")
uf.desc[-1].add_item_list_element("4", "{Axx, Ayy, Axy, Axz, Ayz}  (units of Hertz),")
uf.desc[-1].add_item_list_element("5", "{Azz, Axx-yy, Axy, Axz, Ayz}  (units of Hertz),")
uf.desc[-1].add_item_list_element("6", "{Pxx, Pyy, Pxy, Pxz, Pyz}  (unitless),")
uf.desc[-1].add_item_list_element("7", "{Pzz, Pxx-yy, Pxy, Pxz, Pyz}  (unitless).")
uf.desc[-1].add_paragraph("Other formats may be added later.  The relationship between the Saupe order matrix S and the alignment tensor A is")
uf.desc[-1].add_item_list_element(None, "S = 3/2 A.")
uf.desc[-1].add_paragraph("The probability matrix P is related to the alignment tensor A by")
uf.desc[-1].add_item_list_element(None, "A = P - 1/3 I,")
uf.desc[-1].add_paragraph("where I is the identity matrix.  For the alignment tensor to be supplied in Hertz, the bond vectors must all be of equal length.")
# Prompt examples.
uf.desc.append(Desc_container("Prompt examples"))
uf.desc[-1].add_paragraph("To set a rhombic tensor for the domain labelled 'domain 1' with the alignment named 'super media', type one of:")
uf.desc[-1].add_prompt("relax> align_tensor.init('domain 1', 'super media', (-8.6322e-05, -5.5786e-04, -3.1732e-05, 2.2927e-05, 2.8599e-04), param_types=1)")
uf.desc[-1].add_prompt("relax> align_tensor.init(tensor='domain 1', align_id='super media', params=(-8.6322e-05, -5.5786e-04, -3.1732e-05, 2.2927e-05, 2.8599e-04), param_types=1)")
uf.backend = align_tensor.init
uf.menu_text = "&init"
uf.wizard_height_desc = 370
uf.wizard_size = (1000, 750)
uf.gui_icon = "relax.align_tensor"
uf.wizard_image = WIZARD_IMAGE_PATH + 'align_tensor.png'


# The align_tensor.matrix_angles user function.
uf = uf_info.add_uf('align_tensor.matrix_angles')
uf.title = "Calculate the 5D angles between all alignment tensors."
uf.title_short = "Alignment tensor angle calculation."
uf.display = True
uf.add_keyarg(
    name = "basis_set",
    default = 0,
    py_type = "int",
    desc_short = "basis set",
    desc = "The basis set to operate with.",
    wiz_element_type = "combo",
    wiz_combo_choices = ["{Sxx, Syy, Sxy, Sxz, Syz}", "{Szz, Sxxyy, Sxy, Sxz, Syz}"],
    wiz_combo_data = [0, 1]
)
uf.add_keyarg(
    name = "tensors",
    py_type = "str_list",
    desc_short = "alignment tensor IDs",
    desc = "A list of the tensors to apply the calculation to.  If None, all tensors are used.",
    wiz_element_type = "combo_list",
    wiz_combo_iter = align_tensor.get_tensor_ids,
    wiz_read_only = True,
    can_be_none = True
)
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("This will calculate the angles between all loaded alignment tensors for the current data pipe.  The matrices are first converted to a 5D vector form and then then angles are calculated.  The angles are dependent on the basis set.  If the basis set is set to the default of 0, the vectors {Sxx, Syy, Sxy, Sxz, Syz} are used.  If the basis set is set to 1, the vectors {Szz, Sxxyy, Sxy, Sxz, Syz} are used instead.")
uf.backend = align_tensor.matrix_angles
uf.menu_text = "&matrix_angles"
uf.gui_icon = "oxygen.categories.applications-education"
uf.wizard_size = (800, 600)
uf.wizard_image = WIZARD_IMAGE_PATH + 'align_tensor.png'


# The align_tensor.reduction user function.
uf = uf_info.add_uf('align_tensor.reduction')
uf.title = "Specify that one tensor is a reduction of another."
uf.title_short = "Specify tensor reductions."
uf.add_keyarg(
    name = "full_tensor",
    py_type = "str",
    desc_short = "full tensor",
    desc = "The full alignment tensor.",
    wiz_element_type = 'combo',
    wiz_combo_iter = align_tensor.get_tensor_ids,
    wiz_read_only = True
)
uf.add_keyarg(
    name = "red_tensor",
    py_type = "str",
    desc_short = "reduced tensor",
    desc = "The reduced alignment tensor.",
    wiz_element_type = 'combo',
    wiz_combo_iter = align_tensor.get_tensor_ids,
    wiz_read_only = True
)
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("Prior to optimisation of the N-state model and Frame Order theories using alignment tensors, which tensor is a reduction of which other tensor must be specified through this user function.")
# Prompt examples.
uf.desc.append(Desc_container("Prompt examples"))
uf.desc[-1].add_paragraph("To state that the alignment tensor loaded as 'chi3 C-dom' is a reduction of 'chi3 N-dom', type:")
uf.desc[-1].add_prompt("relax> align_tensor.reduction(full_tensor='chi3 N-dom', red_tensor='chi3 C-dom')")
uf.backend = align_tensor.reduction
uf.menu_text = "&reduction"
uf.wizard_image = WIZARD_IMAGE_PATH + 'align_tensor.png'


# The align_tensor.set_domain user function.
uf = uf_info.add_uf('align_tensor.set_domain')
uf.title = "Set the domain label for the alignment tensor."
uf.title_short = "Tensor domain labelling."
uf.add_keyarg(
    name = "tensor",
    py_type = "str",
    desc_short = "tensor ID",
    desc = "The alignment tensor to assign the domain label to.",
    wiz_element_type = 'combo',
    wiz_combo_iter = align_tensor.get_tensor_ids,
    wiz_read_only = True,
)
uf.add_keyarg(
    name = "domain",
    py_type = "str",
    desc_short = "domain",
    desc = "The domain label."
)
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("Prior to optimisation of the N-state model or Frame Order theories, the domain to which each alignment tensor belongs must be specified.")
# Prompt examples.
uf.desc.append(Desc_container("Prompt examples"))
uf.desc[-1].add_paragraph("To link the alignment tensor loaded as 'chi3 C-dom' to the C-terminal domain 'C', type:")
uf.desc[-1].add_prompt("relax> align_tensor.set_domain(tensor='chi3 C-dom', domain='C')")
uf.backend = align_tensor.set_domain
uf.menu_text = "&set_domain"
uf.gui_icon = "oxygen.actions.edit-select"
uf.wizard_image = WIZARD_IMAGE_PATH + 'align_tensor.png'


# The align_tensor.svd user function.
uf = uf_info.add_uf('align_tensor.svd')
uf.title = "Calculate the singular values and condition number for all alignment tensors."
uf.title_short = "Alignment tensor SVD calculation."
uf.display = True
uf.add_keyarg(
    name = "basis_set",
    default = 0,
    py_type = "int",
    desc_short = "basis set",
    desc = "The basis set to operate with.",
    wiz_element_type = "combo",
    wiz_combo_choices = ["{Sxx, Syy, Sxy, Sxz, Syz}", "{Szz, Sxxyy, Sxy, Sxz, Syz}"],
    wiz_combo_data = [0, 1]
)
uf.add_keyarg(
    name = "tensors",
    py_type = "str_list",
    desc_short = "alignment tensor IDs",
    desc = "A list of the tensors to apply the calculation to.  If None, all tensors are used.",
    wiz_element_type = "combo_list",
    wiz_combo_iter = align_tensor.get_tensor_ids,
    wiz_read_only = True,
    can_be_none = True
)
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("This will perform a singular value decomposition of all tensors loaded for the current data pipe.  If the basis set is set to the default of 0, the matrix on which SVD will be performed is composed of the unitary basis set {Sxx, Syy, Sxy, Sxz, Syz} layed out as:")
uf.desc[-1].add_verbatim("""
    | Sxx1 Syy1 Sxy1 Sxz1 Syz1 |
    | Sxx2 Syy2 Sxy2 Sxz2 Syz2 |
    | Sxx3 Syy3 Sxy3 Sxz3 Syz3 |
    |  .    .    .    .    .   |
    |  .    .    .    .    .   |
    |  .    .    .    .    .   |
    | SxxN SyyN SxyN SxzN SyzN |
""")
uf.desc[-1].add_paragraph("If basis_set is set to 1, the geometric basis set consisting of the stretching and skewing parameters Szz and Sxx-yy respectively {Szz, Sxxyy, Sxy, Sxz, Syz} will be used instead.  The matrix is:")
uf.desc[-1].add_verbatim("""
    | Szz1 Sxxyy1 Sxy1 Sxz1 Syz1 |
    | Szz2 Sxxyy2 Sxy2 Sxz2 Syz2 |
    | Szz3 Sxxyy3 Sxy3 Sxz3 Syz3 |
    |  .     .     .    .    .   |
    |  .     .     .    .    .   |
    |  .     .     .    .    .   |
    | SzzN SxxyyN SxyN SxzN SyzN |
""")
uf.desc[-1].add_paragraph("The relationships between the geometric and unitary basis sets are:")
uf.desc[-1].add_verbatim("""
    Szz = - Sxx - Syy,
    Sxxyy = Sxx - Syy,
""")
uf.desc[-1].add_paragraph("The SVD values and condition number are dependent upon the basis set chosen.")
uf.backend = align_tensor.svd
uf.menu_text = "s&vd"
uf.gui_icon = "oxygen.categories.applications-education"
uf.wizard_height_desc = 500
uf.wizard_size = (1000, 750)
uf.wizard_image = WIZARD_IMAGE_PATH + 'align_tensor.png'
