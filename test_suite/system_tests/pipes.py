###############################################################################
#                                                                             #
# Copyright (C) 2006-2012 Edward d'Auvergne                                   #
#                                                                             #
# This file is part of the program relax.                                     #
#                                                                             #
# relax is free software; you can redistribute it and/or modify               #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 2 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# relax is distributed in the hope that it will be useful,                    #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with relax; if not, write to the Free Software                        #
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA   #
#                                                                             #
###############################################################################

# Python module imports.
from os import sep

# relax module imports.
from base_classes import SystemTestCase
from data import Relax_data_store; ds = Relax_data_store()
from generic_fns import pipes
from status import Status; status = Status()


class Pipes(SystemTestCase):
    """TestCase class for the functional tests of relax data pipes."""

    def test_pipe_bundle(self):
        """Test the pipe bundle concepts."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'pipe_bundle.py')

        # Checks.
        self.assertEqual(pipes.cdp_name(), None)
        self.assertEqual(pipes.has_bundle('test bundle 1'), True)
        self.assertEqual(pipes.has_bundle('test bundle 2'), True)
        self.assertEqual(pipes.has_bundle('test bundle 3'), False)
        self.assertEqual(pipes.bundle_names(), ['test bundle 1', 'test bundle 2'])
        for pipe, name in pipes.pipe_loop(name=True):
            self.assert_(name in ['test pipe 1', 'test pipe 2', 'test pipe 3', 'test pipe 4', 'test pipe 5', 'test pipe 6'])
            self.assert_(pipes.get_bundle(name) in ['test bundle 1', 'test bundle 2'])


    def test_pipe_create(self):
        """Create a data pipe."""

        # Create the data pipe.
        self.interpreter.pipe.create('test', 'mf')
