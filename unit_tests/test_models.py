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
        fixtures = ['workflow_test_data']

        def test_workflow_unicode(self):
            """
            Makes sure that the slug field (name) is returned from a call to
            __unicode__()
            """
            w = Workflow.objects.get(id=1)
            self.assertEquals(u'Test Workflow', w.__unicode__())

        def test_workflow_lifecycle(self):
            """
            Makes sure the methods in the Workflow model work as expected
            """
            # All new workflows start with status DEFINITION - from the fixtures
            w = Workflow.objects.get(id=1)
            self.assertEquals(Workflow.DEFINITION, w.status)

            # Activate the workflow
            w.activate()
            self.assertEquals(Workflow.ACTIVE, w.status)

            # Retire it.
            w.retire()
            self.assertEquals(Workflow.RETIRED, w.status)

        def test_workflow_is_valid(self):
            """
            Makes sure that the validation for a workflow works as expected
            """
            # from the fixtures
            w = Workflow.objects.get(id=1)
            self.assertEquals(Workflow.DEFINITION, w.status)

            # make sure the workflow contains exactly one start state
            # 0 start states
            state1 = State.objects.get(id=1)
            state1.is_start_state=False
            state1.save()
            self.assertEqual(False, w.is_valid())
            self.assertEqual(True, u'There must be only one start state' in w.errors['workflow'])
            state1.is_start_state=True
            state1.save()

            # >1 start states
            state2 = State.objects.get(id=2)
            state2.is_start_state=True
            state2.save()
            self.assertEqual(False, w.is_valid())
            self.assertEqual(True, u'There must be only one start state' in w.errors['workflow'])
            state2.is_start_state=False
            state2.save()

            # make sure we have at least one end state
            # 0 end states
            end_states = w.states.filter(is_end_state=True)
            for state in end_states:
                state.is_end_state=False
                state.save()
            self.assertEqual(False, w.is_valid())
            self.assertEqual(True, u'There must be at least one end state' in w.errors['workflow'])
            for state in end_states:
                state.is_end_state=True
                state.save()
            
            # make sure we don't have any orphan states 
            orphan_state = State(name='orphaned_state', workflow=w)
            orphan_state.save()
            self.assertEqual(False, w.is_valid())
            self.assertEqual(True, orphan_state.id in w.errors['states'])
            msg = u'This state is orphaned. There is no way to get to it given'\
                    ' the current workflow topology.'
            self.assertEqual(True, msg in w.errors['states'][orphan_state.id])
            orphan_state.delete()

            # make sure we don't have any cul-de-sacs from which one can't
            # escape (re-using an end state for the same effect)
            cul_de_sac = end_states[0]
            cul_de_sac.is_end_state = False
            cul_de_sac.save()
            self.assertEqual(False, w.is_valid())
            self.assertEqual(True, cul_de_sac.id in w.errors['states'])
            msg = u'This state is a dead end. It is not marked as an end state'\
                    ' and there is no way to exit from it.'
            self.assertEqual(True, msg in w.errors['states'][cul_de_sac.id])
            cul_de_sac.is_end_state = True
            cul_de_sac.save()

            # make sure transition's roles are a subset of the roles associated
            # with the transition's from_state (otherwise you'll have a
            # transition that none of the participants for a state can make use
            # of)
            role = Role.objects.get(id=2)
            transition = Transition.objects.get(id=10)
            transition.roles.clear()
            transition.roles.add(role)
            self.assertEqual(False, w.is_valid())
            self.assertEqual(True, transition.id in w.errors['transitions'])
            msg = u'This transition is not navigable because none of the'\
                ' roles associated with the parent state have permission to'\
                ' use it.'
            self.assertEqual(True, msg in w.errors['transitions'][transition.id])

            # so all the potential pitfalls have been vaidated. Lets make sure
            # we *can* validate it as expected.
            transition.roles.clear()
            admin_role = Role.objects.get(id=1)
            staff_role = Role.objects.get(id=3)
            transition.roles.add(admin_role)
            transition.roles.add(staff_role)
            self.assertEqual(True, w.is_valid())
            self.assertEqual([], w.errors['workflow'])
            self.assertEqual({}, w.errors['states'])
            self.assertEqual({}, w.errors['transitions'])

        def test_workflow_has_errors(self):
            """
            Ensures that has_errors() returns the appropriate response for all
            possible circumstances
            """
            # Some housekeepeing
            w = Workflow.objects.get(id=1)
            u = User.objects.get(id=1)
            w.activate()
            w2 = w.clone(u)

            # A state with no errors
            state1 = State.objects.get(id=1)
            w.is_valid()
            self.assertEqual([], w.has_errors(state1))

            # A state with errors
            state1.is_start_state = False
            state1.save()
            w.is_valid()
            msg = u'This state is orphaned. There is no way to get to it given'\
                    ' the current workflow topology.'
            self.assertEqual([msg], w.has_errors(state1))
            
            # A transition with no errors
            transition = Transition.objects.get(id=10)
            w.is_valid()
            self.assertEqual([], w.has_errors(transition))

            # A transition with errors
            role = Role.objects.get(id=2)
            transition.roles.clear()
            transition.roles.add(role)
            w.is_valid()
            msg = u'This transition is not navigable because none of the'\
                ' roles associated with the parent state have permission to'\
                ' use it.'
            self.assertEqual([msg], w.has_errors(transition))

            # A state not associated with the workflow
            state2 = w2.states.all()[0]
            state2.is_start_state = False
            state2.save()
            w.is_valid()
            # The state is a problem state but isn't anything to do with the
            # workflow w
            self.assertEqual([], w.has_errors(state2))

            # A transition not associated with the workflow
            transition2 = w2.transitions.all()[0]
            transition2.roles.clear()
            w.is_valid()
            # The transition has a problem but isn't anything to do with the
            # workflow w
            self.assertEqual([], w.has_errors(transition2))

            # Something not either a state or transition (e.g. a string)
            w.is_valid()
            self.assertEqual([], w.has_errors("Test"))

        def test_workflow_activate_validation(self):
            """
            Makes sure that the appropriate validation of a workflow happens
            when the activate() method is called
            """
            # from the fixtures
            w = Workflow.objects.get(id=1)
            self.assertEquals(Workflow.DEFINITION, w.status)

            # make sure only workflows in definition can be activated
            w.status=Workflow.ACTIVE
            w.save()
            try:
                w.activate()
            except Exception, instance:
                self.assertEqual(u'Only workflows in the "definition" state may'\
                        ' be activated', instance.args[0]) 
            else:
                self.fail('Exception expected but not thrown')
            w.status=Workflow.DEFINITION
            w.save()

            # Lets make sure the workflow is validated before being activated by
            # making sure the workflow in not valid
            state1 = State.objects.get(id=1)
            state1.is_start_state=False
            state1.save()
            try:
                w.activate()
            except Exception, instance:
                self.assertEqual(u"Cannot activate as the workflow doesn't"\
                        " validate.", instance.args[0])
            else:
                self.fail('Exception expected but not thrown')
            state1.is_start_state=True
            state1.save()
            
            # so all the potential pitfalls have been validated. Lets make sure
            # we *can* approve it as expected.
            w.activate()
            self.assertEqual(Workflow.ACTIVE, w.status)

        def test_workflow_retire_validation(self):
            """
            Makes sure that the appropriate state is set against a workflow when
            this method is called
            """
            w = Workflow.objects.get(id=1)
            w.retire()
            self.assertEqual(Workflow.RETIRED, w.status)

        def test_workflow_clone(self):
            """
            Makes sure we can clone a workflow correctly.
            """
            # We can't clone workflows that are in definition because they might
            # not be "correct" (see the validation that happens when activate()
            # method is called
            u = User.objects.get(id=1)
            w = Workflow.objects.get(id=1)
            try:
                w.clone(u)
            except Exception, instance:
                self.assertEqual(u'Only active or retired workflows may be'\
                        ' cloned', instance.args[0])
            else:
                self.fail('Exception expected but not thrown')
            w.activate()
            clone = w.clone(u)
            self.assertEqual(Workflow.DEFINITION, clone.status)
            self.assertEqual(u, clone.created_by)
            self.assertEqual(w, clone.cloned_from)
            self.assertEqual(w.name, clone.name)
            self.assertEqual(w.description, clone.description)
            # Lets check we get the right number of states, transitions and
            # events
            self.assertEqual(w.transitions.all().count(),
                    clone.transitions.all().count())
            self.assertEqual(w.states.all().count(), clone.states.all().count())
            self.assertEqual(w.events.all().count(), clone.events.all().count())

        def test_state_deadline(self):
            """
            Makes sure we get the right result from the deadline() method in the
            State model
            """
            w = Workflow.objects.get(id=1)
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
            w = Workflow.objects.get(id=1)
            u = User.objects.get(id=1)
            r = Role.objects.get(id=1)
            wm = WorkflowManager(workflow=w, created_by=u)
            wm.save()
            p = Participant(user=u, role=r, workflowmanager=wm)
            p.save()
            # We've not started the workflow yet so make sure we don't get
            # anything back
            self.assertEqual(None, wm.current_state())
            wm.start(p)
            # We should be in the first state
            s1 = State.objects.get(id=1) # From the fixtures
            current_state = wm.current_state()
            # check we have a good current state
            self.assertNotEqual(None, current_state)
            self.assertEqual(s1, current_state.state)
            self.assertEqual(p, current_state.participant)
            # Lets progress the workflow and make sure the *latest* state is the
            # current state
            tr = Transition.objects.get(id=1)
            wm.progress(tr, p)
            s2 = State.objects.get(id=2)
            current_state = wm.current_state()
            self.assertEqual(s2, current_state.state)
            self.assertEqual(tr, current_state.transition)
            self.assertEqual(p, current_state.participant)

        def test_workflowmanager_start(self):
            """
            Make sure the method works in the right way for all possible
            situations
            """
            w = Workflow.objects.get(id=1)
            u = User.objects.get(id=1)
            r = Role.objects.get(id=1)
            wm = WorkflowManager(workflow=w, created_by=u)
            wm.save()
            p = Participant(user=u, role=r, workflowmanager=wm)
            p.save()
            # Lets make sure we can't start a workflow that has been stopped
            wm.force_stop(p, 'foo')
            try:
                wm.start(p)
            except Exception, instance:
                self.assertEqual(u'Already completed', instance.args[0])
            else:
                self.fail('Exception expected but not thrown')
            wm = WorkflowManager(workflow=w, created_by=u)
            wm.save()
            # Lets make sure we can't start a workflow manager if there isn't
            # a single start state
            s2 = State.objects.get(id=2)
            s2.is_start_state=True
            s2.save()
            try:
                wm.start(p)
            except Exception, instance:
                self.assertEqual(u'Cannot find single start state', 
                        instance.args[0])
            else:
                self.fail('Exception expected but not thrown')
            s2.is_start_state=False
            s2.save()
            # Lets make sure we *can* start it now we only have a single start
            # state
            wm.start(p)
            # We should be in the first state
            s1 = State.objects.get(id=1) # From the fixtures
            current_state = wm.current_state()
            # check we have a good current state
            self.assertNotEqual(None, current_state)
            self.assertEqual(s1, current_state.state)
            self.assertEqual(p, current_state.participant)
            # Lets make sure we can't "start" the workflowmanager again
            try:
                wm.start(p)
            except Exception, instance:
                self.assertEqual(u'Already started', instance.args[0])
            else:
                self.fail('Exception expected but not thrown')

        def test_workflowmanager_progress(self):
            """
            Make sure the transition from state to state is validated and
            recorded in the correct way.
            """
            # Some housekeeping...
            w = Workflow.objects.get(id=1)
            u = User.objects.get(id=1)
            r = Role.objects.get(id=1)
            wm = WorkflowManager(workflow=w, created_by=u)
            wm.save()
            p = Participant(user=u, role=r, workflowmanager=wm)
            p.save()
            wm.start(p)
            # Validation checks:
            # 1. The transition's from_state *must* be the current state
            tr5 = Transition.objects.get(id=5)
            try:
                wm.progress(tr5, p)
            except Exception, instance:
                self.assertEqual(u'Transition not valid (wrong parent)', 
                        instance.args[0])
            else:
                self.fail('Exception expected but not thrown')
            # Lets test again with a valid transition with the correct
            # from_state
            tr1 = Transition.objects.get(id=1)
            wm.progress(tr1, p)
            s2 = State.objects.get(id=2)
            self.assertEqual(s2, wm.current_state().state)
            # 2. All mandatory events for the state are in the worklow history
            # (s2) has a single mandatory event associated with it
            tr2 = Transition.objects.get(id=2)
            try:
                wm.progress(tr2, p)
            except Exception, instance:
                self.assertEqual(u'Transition not valid (mandatory event'\
                        ' missing)', instance.args[0])
            else:
                self.fail('Exception expected but not thrown')
            # Lets log the event and make sure we *can* progress
            e = Event.objects.get(id=1)
            wm.log_event(e, p)
            # Lets progress with a custom note
            wm.progress(tr2, p, 'A Test')
            s3 = State.objects.get(id=3)
            self.assertEqual(s3, wm.current_state().state)
            self.assertEqual('A Test', wm.current_state().note)
            # 3. The participant has the correct role to make the transition
            r2 = Role.objects.get(id=2)
            p2 = Participant(user=u, role=r2, workflowmanager=wm)
            tr4 = Transition.objects.get(id=4) # won't work with p2/r2
            try:
                wm.progress(tr4, p2)
            except Exception, instance:
                self.assertEqual(u'Participant has insufficient authority to'\
                        ' use the specified transition', instance.args[0])
            else:
                self.fail('Exception expected but not thrown')
            # We have the good transition so make sure everything is logged in
            # the workflow history properly
            s5 = State.objects.get(id=5)
            wh = wm.progress(tr4, p)
            self.assertEqual(s5, wh.state)
            self.assertEqual(tr4, wh.transition)
            self.assertEqual(p, wh.participant)
            self.assertEqual(tr4.name, wh.note)
            self.assertNotEqual(None, wh.deadline)
            # Get to the end of the workflow and check that by progressing to an
            # end state the workflow manager is given a completed on timestamp
            tr8 = Transition.objects.get(id=8)
            tr10 = Transition.objects.get(id=10)
            tr11 = Transition.objects.get(id=11)
            wm.progress(tr8, p)
            wm.progress(tr10, p)
            wm.progress(tr11, p)
            self.assertNotEqual(None, wm.completed_on)

        def test_workflowmanager_log_event(self):
            """
            Make sure the logging of events for a workflow is validated and
            recorded in the correct way.
            """
            # Some housekeeping...
            w = Workflow.objects.get(id=1)
            u = User.objects.get(id=1)
            r = Role.objects.get(id=1)
            wm = WorkflowManager(workflow=w, created_by=u)
            wm.save()
            p = Participant(user=u, role=r, workflowmanager=wm)
            p.save()
            wm.start(p)
            # Validation checks:
            # 1. Make sure the event we're logging is for the appropriate
            # workflow
            wf2 = Workflow(name="dummy", created_by=u)
            wf2.save()
            dummy_state = State(name="dummy", workflow=wf2)
            dummy_state.save()
            dummy_event = Event(
                    name="dummy event", 
                    workflow=wf2, 
                    state=dummy_state
                    )
            dummy_event.save()
            try:
                wm.log_event(dummy_event, p)
            except Exception, instance:
                self.assertEqual(u'The event is not associated with the'\
                        ' workflow for the WorkflowManager', instance.args[0])
            else:
                self.fail('Exception expected but not thrown')
            # 2. Make sure the participant has the correct role to log the event
            # (Transition to second state where we have an appropriate event
            # already specified)
            tr1 = Transition.objects.get(id=1)
            wm.progress(tr1, p)
            e1 = Event.objects.get(id=1)
            r3 = Role.objects.get(id=3)
            p2 = Participant(user=u, role=r3, workflowmanager=wm)
            try:
                wm.log_event(e1, p2)
            except Exception, instance:
                self.assertEqual(u'The participant is not associated with the'\
                        ' specified event', instance.args[0])
            else:
                self.fail('Exception expected but not thrown')
            # Try again but with the right profile
            wm.log_event(e1, p)
            # 3. Make sure, if the event is mandatory it can only be logged
            # whilst in the correct state
            e2 = Event.objects.get(id=2)
            e2.is_mandatory = True
            e2.save()
            try:
                wm.log_event(e2, p)
            except Exception, instance:
                self.assertEqual(u'The mandatory event is not associated with'\
                        ' the current state', instance.args[0])
            else:
                self.fail('Exception expected but not thrown')
            # Save a good event instance and check everything is logged in the
            # workflow history properly
            tr2 = Transition.objects.get(id=2)
            s3 = State.objects.get(id=3)
            wm.progress(tr2, p)
            wh = wm.log_event(e2, p)
            self.assertEqual(s3, wh.state)
            self.assertEqual(e2, wh.event)
            self.assertEqual(p, wh.participant)
            self.assertEqual(e2.name, wh.note)
            # Lets log a second event of this type and make sure we handle the
            # bespoke note
            wh = wm.log_event(e2, p, 'A Test')
            self.assertEqual(s3, wh.state)
            self.assertEqual(e2, wh.event)
            self.assertEqual(p, wh.participant)
            self.assertEqual('A Test', wh.note)

        def test_workflowmanager_force_stop(self):
            """
            Make sure a WorkflowManager is stopped correctly with this method
            """
            # Make sure we can appropriately force_stop an un-started workflow
            # manager
            w = Workflow.objects.get(id=1)
            u = User.objects.get(id=1)
            r = Role.objects.get(id=1)
            wm = WorkflowManager(workflow=w, created_by=u)
            wm.save()
            p = Participant(user=u, role=r, workflowmanager=wm)
            p.save()
            wm.force_stop(p, 'foo')
            self.assertNotEqual(None, wm.completed_on)
            self.assertEqual(None, wm.current_state())
            # Lets make sure we can force_stop an already started workflow
            # manager
            wm = WorkflowManager(workflow=w, created_by=u)
            wm.save()
            wm.start(p)
            wm.force_stop(p, 'foo')
            self.assertNotEqual(None, wm.completed_on)
            wh = wm.current_state()
            self.assertEqual(p, wh.participant)
            self.assertEqual(u'Workflow forced to stop! Reason given: foo',
                    wh.note)
            self.assertEqual(None, wh.deadline)

        def test_participant_unicode(self):
            """
            Make sure the __unicode__() method returns the correct string in
            both enabled / disabled states
            """
            w = Workflow.objects.get(id=1)
            u = User.objects.get(id=1)
            r = Role.objects.get(id=1)
            wm = WorkflowManager(workflow=w, created_by=u)
            wm.save()
            p = Participant(user=u, role=r, workflowmanager=wm)
            p.save()
            self.assertEquals(u'test_admin (Administrator)', p.__unicode__())
            p.disabled = True
            p.save()
            self.assertEquals(u'test_admin (Administrator - disabled)', p.__unicode__())
