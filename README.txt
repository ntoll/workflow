Django Workflow Application v0.1 (alpha)

(c) 2009 Nicholas H.Tollervey (http://ntoll.org/contact)

See the file LICENSE.txt for the licensing terms and conditions.

This Django application provides a workflow engine for use in your 
web-application. This work is an abstraction of / extraction from a workflow
engine built for an HR application.

Currently only the models have been "extracted". Commented doctests can be 
found in tests.py. I've also created some templates for generating .dot files
for processing by Graphviz. See: http://twitpic.com/7xiz7 for example output.
See the urls.py for paths to use to display the .dot file and resulting .png
image.

To make things easy I've described each model below and made up a couple of 
"user stories" to illustrate how stuff fits together (an Applicant Tracking 
System used by HR and a simple issue tracker for filing bugs, feature requests 
and whatnot). 

I realise the examples might be a tad contrived but I always find that thinking
about tangible examples relating to data models is always helpful.

The order that I describe the tables follows the code outline.

Role - defines what sort of users are associated with different aspects of the
workflow. In the HR project these roles might include: 'HR Consultant', 'Hiring
Manager', 'Interviewer' or 'Assessor'. In the issue tracker these might simply 
be 'Core Developer', 'Release Manager' or 'Tester'. The State and Transition 
models have a many-to-many relationship with Role to indicate what sort of 
person has permission to view a state or use a transition. The Event model has a
many-to-many relationship with Role to indicate who is participating in the
event.

Workflow - names / describes a workflow. In the HR project workflows might be:
'Generic Hiring Process', 'Executive Hiring Process' or 'Employee Appraisal'. In
the issue tracker these might include: 'Bug Report', 'Feature Request' or
'Release Lifecycle'. A workflow can be in one of three states that defines the
life of a workflow: definition -> active -> retired. A workflow can only be
changed when it has the state 'definition' (where changed means states and
transitions added or removed). A workflow can only be used when it has the state
'active'. When a workflow is no longer useful, or is found to contain errors
then it is marked as 'retired'. Why take so much trouble over this? Imagine the
mess that could ensue if a 'live' workflow were changed and states were deleted
or orphaned. Furthermore, retired workflows could be "cloned" as the basis of
new workflows in the 'definition' state. 

State - represents a specific state that a thing can be in. In the HR project
examples might be: 'Open for applications', 'Final shortlisting', 'Employee
Interviews'. In the issue tracker we might have: 'Open', 'Rejected', 'Awaiting
Approval'. Put simply a state is a description of a node in a directed graph. 
Only one state can be marked as 'is_start_state' for each workflow but many can
be marked as 'is_end_state' (indicating the workflow has been completed). Roles
associated with each state indicate *who* has access to the thing when in this
state.

Transition - defines how a workflow can move between states. They *should* be
given "active" names. For example, in the HR project transitions might be:
'Publish Vacancy' (leading to the 'Open for applications' state), 'Publish
applications' (leading to the 'Final shortlisting' state) or 'Publish
meeting slots' (leading to 'Employee Interviews'). The issue tracker transitions
are probably more obvious 'Submit issue' (leads to 'Open' state), 'Reject'
(leads to 'Rejected') and 'Propose new feature' (leads to 'Awaiting Approval').
Put simply, a transition is an edge in a directed graph. Roles associated with
each transition indicate *who* can use the transition to move the workflow to a
new state.

EventType - just defines the name of a type of event. Examples might be:
meeting, assessment, interview, deployment test, feature freeze and so on.

Event - is a specification for something that is supposed to happen whilst in
a state. In the HR project events might be: 'Meeting to approve job
specification', 'Meeting of review board' or 'Contact all managers conducting
employee interviews'. The issue tracker might have: 'Check for duplicate issue',
'Check unit tests pass on staging server'. The roles field indicates *who* is to
participate in the event. I've also included an is_mandatory flag. An event can
be associated with many EventTypes.

WorkflowActivity - is a core model to link "things" to workflows in a similar way
to User objects having a profile. Vacancy and Issue instances in the HR and
issue tracker examples should reference a WorkflowManager. The WorkflowManager
simply references an active Workflow and contains created_on and completed_on
timestamps. The various methods associated with this model should be used move
through the life of the workflow.

Participant - links django.contrib.auth.models.User instances to a Role and 
WorkflowManager. This way we know that user 'Joe Blogs' has the role 'Hiring 
Manager' for the duration of the WorkflowManager that is using the 'Executive
Hiring Process' workflow. We might also know that jtauber is Release Manager 
during the lifetime of the WorkflowManager for Pinax1.0 that follows the Release 
Lifecycle workflow.

WorkflowHistory - simply links up the WorkflowManager, State, Transition and
Events to the State, Participant, a descriptive note and a timestamp enabling 
us to track how the workflow has progressed (with the most recent being the 
current state). Examples might be: Pinax1.0 WorkflowManager, "RC1" state, 
"Prepare Release Candidate" transition, jtauber, 2009-11-5.

As always, comments, ideas, suggestions and improvements are most welcome.
