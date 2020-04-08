# Copyright 2019 Apex.AI, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import imp
import unittest

import launch
import launch.actions
import launch_testing
from launch_testing.actions import ReadyToTest
from launch_testing.loader import LoadTestsFromPythonModule
from launch_testing.test_runner import LaunchTestRunner


VALID_LAUNCH_DESCRIPTION = launch.LaunchDescription([ReadyToTest()])


def make_test_run_for_dut(generate_test_description_function):
    module = imp.new_module('test_module')
    module.generate_test_description = generate_test_description_function
    return LoadTestsFromPythonModule(module)


class TestLaunchTestRunnerValidation(unittest.TestCase):

    def test_catches_bad_signature(self):

        # This is an older test, but still valid.  We don't have ready_fn anymore, but
        # we can still check that we catch invalid arguments
        dut = LaunchTestRunner(
            make_test_run_for_dut(
                lambda misspelled_ready_fn: VALID_LAUNCH_DESCRIPTION
            )
        )

        with self.assertRaisesRegex(Exception, "unexpected extra argument 'misspelled_ready_fn'"):
            dut.validate()

        dut = LaunchTestRunner(
            make_test_run_for_dut(
                lambda: VALID_LAUNCH_DESCRIPTION
            )
        )

        dut.validate()

    def test_too_many_arguments(self):

        dut = LaunchTestRunner(
            make_test_run_for_dut(lambda extra_arg: VALID_LAUNCH_DESCRIPTION)
        )

        with self.assertRaisesRegex(Exception, "unexpected extra argument 'extra_arg'"):
            dut.validate()

    def test_bad_parametrization_argument(self):

        @launch_testing.parametrize('bad_argument', [1, 2, 3])
        def bad_launch_description():
            return VALID_LAUNCH_DESCRIPTION  # pragma: no cover

        dut = LaunchTestRunner(
            make_test_run_for_dut(bad_launch_description)
        )

        with self.assertRaisesRegex(Exception, 'Could not find an argument') as cm:
            dut.validate()
        self.assertIn('bad_argument', str(cm.exception))


class TestNewStyleTestDescriptions(unittest.TestCase):
    # Tests for `generate_test_description` functions that include a ReadyToTest action in
    # the test description

    def test_good_launch_description(self):

        def generate_test_description():
            return launch.LaunchDescription([
                ReadyToTest()
            ])

        runs = make_test_run_for_dut(generate_test_description)
        dut = LaunchTestRunner(
            runs
        )

        dut.validate()

    def test_launch_description_with_missing_ready_action(self):

        def generate_test_description():
            return launch.LaunchDescription([
            ])

        runs = make_test_run_for_dut(generate_test_description)
        dut = LaunchTestRunner(
            runs
        )

        with self.assertRaisesRegex(Exception, 'containing a ReadyToTest action'):
            dut.validate()

    def test_launch_description_with_conditional_ready_action(self):

        def generate_test_description():
            return launch.LaunchDescription([
                launch.actions.TimerAction(
                    period=10.0,
                    actions=[ReadyToTest()]
                )
            ])

        runs = make_test_run_for_dut(generate_test_description)
        dut = LaunchTestRunner(
            runs
        )

        dut.validate()  # Make sure this passes initial validation (probably redundant with above)

    def test_launch_description_with_multiple_conditionals_and_deeper_nesting(self):

        def generate_test_description():
            return launch.LaunchDescription([
                launch.actions.LogInfo(msg='Dummy Action'),
                launch.actions.TimerAction(
                    period=10.0,
                    actions=[
                        launch.actions.OpaqueFunction(function=lambda context: None),
                        launch.actions.TimerAction(
                            period=5.0,
                            actions=[
                                launch.actions.LogInfo(msg='Deeply Nested Action'),
                                ReadyToTest()
                            ]
                        )
                    ]
                )
            ])

        runs = make_test_run_for_dut(generate_test_description)
        dut = LaunchTestRunner(
            runs
        )

        dut.validate()  # Make sure this passes initial validation (probably redundant with above)

    def test_parametrized_launch_description(self):

        @launch_testing.parametrize('my_param', [1, 2, 3])
        def generate_test_description(my_param):
            return launch.LaunchDescription([
                ReadyToTest()
            ])

        runs = make_test_run_for_dut(generate_test_description)
        dut = LaunchTestRunner(
            runs
        )

        dut.validate()  # Make sure this passes initial validation (probably redundant with above)
