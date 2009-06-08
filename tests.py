# -*- coding: UTF-8 -*-
"""
Define a simple document management workflow:

>>> from django.contrib.auth.models import User
>>> from workflow.models import *

A couple of users to interact with the workflow

>>> fred = User.objects.create_user('fred','fred@acme.com','password')
>>> joe = User.objects.create_user('joe','joe@acme.com','password')

A document class that really should be a models.Model class (but you get the
idea)

>>> class Document():
...     def __init__(self, title, body, workflow):
...             self.title = title
...             self.body = body
...             self.workflow = workflow
... 

Roles define the sort of person involved in a workflow.

>>> author = Role.objects.create(name="author", description="Author of a document")
>>> boss = Role.objects.create(name="boss", description="Departmental boss")

EventTypes define what sort of events can happen in a workflow.

>>> approval = EventType.objects.create(name="Document Approval", description="A document is reviewed by an approver")
>>> meeting = EventType.objects.create(name='Meeting', description='A meeting at the offices of Acme Inc')

Creating a workflow puts it into the "DEFINITION" status. It can't be used yet.

>>> wf = Workflow.objects.create(name='Simple Document Approval', description='A simple document approval process', created_by=joe)

Adding four states:

>>> s1 = State.objects.create(name='In Draft', description='The author is writing a draft of the document', is_start_state=True, workflow=wf)
>>> s2 = State.objects.create(name='Under Review', description='The approver is reviewing the document', workflow=wf)
>>> s3 = State.objects.create(name='Published', description='The document is published', workflow=wf)
>>> s4 = State.objects.create(name='Archived', description='The document is put into the archive', is_end_state=True, workflow=wf)

Defining what sort of person is involved in each state by associating roles.

>>> s1.roles.add(author)
>>> s2.roles.add(boss)
>>> s2.roles.add(author)
>>> s3.roles.add(boss)
>>> s4.roles.add(boss)

Adding transitions to define how the states relate to each other. Notice how the
name of each transition is an "active" description of what it does in order to
get to the next state.

>>> t1 = Transition.objects.create(name='Request Approval', workflow=wf, from_state=s1, to_state=s2)
>>> t2 = Transition.objects.create(name='Revise Draft', workflow=wf, from_state=s2, to_state=s1)
>>> t3 = Transition.objects.create(name='Publish', workflow=wf, from_state=s2, to_state=s3)
>>> t4 = Transition.objects.create(name='Archive', workflow=wf, from_state=s3, to_state=s4)

Once again, using roles to define what sort of person can transition between
states.

>>> t1.roles.add(author)
>>> t2.roles.add(boss)
>>> t3.roles.add(boss)
>>> t4.roles.add(boss)

Creating a mandatory event to be attended by the boss and author during the
"Under Review" state.

>>> approval_meeting = Event.objects.create(name='Approval Meeting', description='Approver and author meet to discuss document', workflow=wf, state=s2, is_mandatory=True)
>>> approval_meeting.roles.add(author)
>>> approval_meeting.roles.add(boss)

Notice how we can define what sort of event this is by associating event types
defined earlier

>>> approval_meeting.event_types.add(approval)
>>> approval_meeting.event_types.add(meeting)

The activate method on the workflow validates the directed graph and puts it in
the "active" state so it can be used.

>>> wf.activate()

Lets set up a workflow manager and assign roles to users for a new document

>>> wm = WorkflowManager(workflow=wf, created_by=fred)
>>> wm.save()
>>> p1 = Participant()
>>> p1 = Participant(user=fred, role=author, workflowmanager=wm)
>>> p1.save()
>>> p2 = Participant(user=joe, role=boss, workflowmanager=wm)
>>> p2.save()
>>> d = Document(title='Had..?', body="Bob, where Alice had had 'had', had had 'had had'; 'had had' had had the examiner's approval", workflow=wm)

Starting the workflow is easy... notice we have to pass the participant and that
the method returns the current state.

>>> d.workflow.start(p1)
<WorkflowHistory: WorkflowHistory object>

The WorkflowManager's current_state() method does exactly what it says. You can
find out lots of interesting things...

>>> current = d.workflow.current_state()
>>> current.participant
<Participant: fred (author)>
>>> current.note
u'Started workflow'
>>> current.state
<State: In Draft>
>>> current.state.transitions_from.all()
[<Transition: Request Approval>]

Lets progress the workflow for this document (the author has finished the draft
and submits it for approval)

>>> my_transition = current.state.transitions_from.all()[0]
>>> my_transition
<Transition: Request Approval>
>>> d.workflow.progress(my_transition, p1)
<WorkflowHistory: WorkflowHistory object>

Notice the WorkflowManager's progress method returns the new state. What is 
current_state() telling us..?

>>> current = d.workflow.current_state()
>>> current.state
<State: Under Review>
>>> current.state.roles.all()
[<Role: author>, <Role: boss>]
>>> current.transition
<Transition: Request Approval>
>>> current.note
u'Request Approval'
>>> current.state.events.all()
[<Event: Approval Meeting>]

So we have an event associated with this event. Lets pretend it's happened

>>> my_event = current.state.events.all()[0]
>>> d.workflow.log_event(my_event, p2)
<WorkflowHistory: WorkflowHistory object>
>>> current = d.workflow.current_state()
>>> current.state
<State: Under Review>
>>> current.event
<Event: Approval Meeting>
>>> current.note
u'Approval Meeting'

Continue with the progress of the workflow manager...

>>> current.state.transitions_from.all()
[<Transition: Revise Draft>, <Transition: Publish>]
>>> my_transition = current.state.transitions_from.all()[1]
>>> d.workflow.progress(my_transition, p2)
<WorkflowHistory: WorkflowHistory object>

Lets finish the workflow just to demonstrate what useful stuff is logged:

>>> current = d.workflow.current_state()
>>> current.state.transitions_from.all()
[<Transition: Archive>]
>>> my_transition = current.state.transitions_from.all()[0]
>>> d.workflow.progress(my_transition, p2)
<WorkflowHistory: WorkflowHistory object>
>>> for item in d.workflow.history.all():
...     print '%s by %s'%(item.note, item.participant.user.username)
... 
Archive by joe
Publish by joe
Approval Meeting by joe
Request Approval by fred
Started workflow by fred


Unit tests are found in the unit_tests module. In addition to doctests this file
is a hook into the Django unit-test framework. 

Author: Nicholas H.Tollervey

"""
from unit_tests.test_views import *
from unit_tests.test_models import *
from unit_tests.test_forms import *
