# -*- coding: UTF-8 -*-
"""
Model tests for Workflow 

Author: Nicholas H.Tollervey

"""
# python
import datetime
import sys

# django
from django.test.client import Client
from django.test import TestCase
from django.contrib.auth.models import User

# project
from workflow.models import *

class ModelTestCase(TestCase):
        """
        Testing Models 
        """
        # Reference fixtures here
        fixtures = []

        def test_workflow_lifecycle(self):
            """
            Makes sure the methods in the Workflow model work as expected
            """
            # All new workflows start with status DEFINITION
            w = Workflow(name="test")
            w.save()
            self.assertEquals(Workflow.DEFINITION, w.status)

            # Activate the workflow
            w.activate()
            self.assertEquals(Workflow.ACTIVE, w.status)

            # Retire it.
            w.retire()
            self.assertEquals(Workflow.RETIRED, w.status)

        def test_activate_validation(self):
            """
            Makes sure that the appropriate validation of a workflow happens
            when the activate() method is called
            """
            # TODO: Finish this when the method is finished off
            self.fail('To be written') 

        def test_clone_workflow(self):
            """
            Makes sure we can clone a workflow correctly.
            """
            # TODO: Finish this when the clone method is finished
            w = Workflow(name="test")
            w.save()

            # We can't clone workflows that are in definition because they might
            # not be "correct" (see the validation that happens when activate()
            # method is called
            got_exception = False
            try:
                w.clone()
            except:
                # Why not do except UnableToCloneWorkflow: ? Unfortunately,
                # Django or the Unittest module doesn't import correctly. You
                # might want to see the following as a good example of this:
                # http://stackoverflow.com/questions/549677?sort=votes
                got_exception = True
            self.assertEquals(True, got_exception)
            self.fail('To be finished') 

        def test_state_deadline(self):
            """
            Makes sure we get the right result from the deadline() method in the
            State model
            """
            w = Workflow(name='test')
            w.save()
            s = State(
                    name='test',
                    workflow=w
                    )
            s.save()

            # Lets make sure the default is correct
            self.assertEquals(None, s.deadline())

            # Changing the unit of time measurements mustn't change anything
            s.estimation_unit = s.HOUR
            s.save()
            self.assertEquals(None, s.deadline())

            # Only when we have a positive value in the estimation_value field
            # should a deadline be returned
            s._today = lambda : datetime.datetime(2000, 1, 1, 0, 0, 0)

            # Seconds
            s.estimation_unit = s.SECOND
            s.estimation_value = 1
            s.save()
            expected = datetime.datetime(2000, 1, 1, 0, 0, 1)
            actual = s.deadline()
            self.assertEquals(expected, actual)

            # Minutes
            s.estimation_unit = s.MINUTE
            s.save()
            expected = datetime.datetime(2000, 1, 1, 0, 1, 0)
            actual = s.deadline()
            self.assertEquals(expected, actual)

            # Hours
            s.estimation_unit = s.HOUR
            s.save()
            expected = datetime.datetime(2000, 1, 1, 1, 0)
            actual = s.deadline()
            self.assertEquals(expected, actual)

            # Days
            s.estimation_unit = s.DAY
            s.save()
            expected = datetime.datetime(2000, 1, 2)
            actual = s.deadline()
            self.assertEquals(expected, actual)
            
            # Weeks 
            s.estimation_unit = s.WEEK
            s.save()
            expected = datetime.datetime(2000, 1, 8)
            actual = s.deadline()
            self.assertEquals(expected, actual)

        def test_workflowmanager_current_state(self):
            """
            Check we always get the latest state (or None if the WorkflowManager
            hasn't started navigating a workflow
            """
            self.fail('To be written') 

        def test_workflowmanager_start(self):
            """
            Make sure the method works in the right way for all possible
            situations
            """
            self.fail('To be written') 

        def test_workflowmanager_force_stop(self):
            """
            Make sure a WorkflowManager is stopped correctly with this method
            """
            self.fail('To be written') 

        def test_role_assigned_signal(self):
            """
            Make sure the role_assigned signal is firing at the right time and
            has the right sender.
            """
            self.fail('To be written') 

        def test_workflow_incident_signal(self):
            """
            Make sure the workflow_incident signal is firing at the right time
            and has the right sender.
            """
            self.fail('To be written') 

        def test_workflow_started_signal(self):
            """
            Make sure the workflow_started signal is firing at the right time
            and has the right sender.
            """
            self.fail('To be written') 

        def test_workflow_ended_signal(self):
            """
            Make sure the workflow_ended signal is firing at the right time and
            has the right sender
            """
            self.fail('To be written') 
