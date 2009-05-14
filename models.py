# -*- coding: UTF-8 -*-
"""
Models for Workflows. 

Copyright (c) 2009 Nicholas H.Tollervey (http://ntoll.org/contact)

All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in
the documentation and/or other materials provided with the
distribution.
* Neither the name of ntoll.org nor the names of its
contributors may be used to endorse or promote products
derived from this software without specific prior written
permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext as __
from django.contrib.auth.models import User

class Role(models.Model):
    """
    Represents a type of user who can be associated with a workflow. Used by
    the State and Transition models to define *who* has permission to view a
    state or use a transition.
    """
    name = models.CharField(
            _('Name of Role'),
            max_length=64
            )
    description = models.TextField(
            _('Description'),
            blank=True
            )

class Workflow(models.Model):
    """
    Instances of this class represent a named workflow that achieve a particular
    aim through a series of related states / transitions. A name for a directed
    graph.
    """

    # A workflow can be in one of three states:
    # 
    # * definition: you're building the thing to meet whatever requirements you
    # have
    #
    # * active: you're using the defined workflow in relation to things in your
    # application - the workflow definition is frozen from this point on.
    #
    # * retired: you no longer use the workflow (but we keep it so it can be 
    # cloned as the basis of new workflows starting in the definition state)
    #
    # Why do this? Imagine the mess that could be created if a "live" workflow
    # was edited and states were deleted or orphaned. These states at least
    # allow us to check things don't go horribly wrong. :-/
    DEFINITION = 0
    ACTIVE = 1
    RETIRED = 2

    STATUS_CHOICE_LIST  = (
                (DEFINITION, _('In definition')),
                (ACTIVE, _('Active')),
                (RETIRED, _('Retired')),
            )

    name = models.SlugField(
            _('Workflow Name')
            )
    description = models.TextField(
            _('Description'),
            blank=True
            )
    status = models.IntegerField(
            _('Status'),
            choices=STATUS_CHOICE_LIST,
            default = DEFINITION
            )

class State(models.Model):
    """
    Represents a specific state that a thing can be in during its progress
    through a workflow. A node in a directed graph.
    """
    name = models.CharField(
            _('Name'),
            max_length=256
            )
    description = models.TextField(
            _('Description'),
            blank=True
            )
    is_start_state = models.BooleanField(
            _('Is the start state?'),
            help_text=_('There can only be one start state for a workflow'),
            default=False
            )
    is_end_state = models.BooleanField(
            _('Is an end state?'),
            help_text=_('An end state shows that the workflow is complete'),
            default=False
            )
    workflow = models.ForeignKey(Workflow)
    # The roles defined here define *who* has permission to view the item in
    # this state.
    roles = models.ManyToManyField(Role)
    # My original workflow State model included fields to allow for estimation
    # of duration of this state. Managers seemed to like this feature!

class Transition(models.Model):
    """
    Represents how a workflow can move between different states. An edge 
    between state "nodes" in a directed graph.
    """
    name = models.CharField(
            _('Name of transition'),
            max_length=128,
            help_text=_('Use an "active" verb. e.g. "Close Issue"')
            )
    from_state = models.ForeignKey(
            State,
            related_name = 'next_actions'
            )
    to_state = models.ForeignKey(
            State,
            related_name = 'actions_into'
            )
    # The roles referenced here define *who* has permission to use this 
    # transition to move between states.
    roles = models.ManyToManyField(Role)

class Event(models.Model):
    """
    A definition of something that is supposed to happen when in a particular
    state.
    """
    name = models.CharField(
            _('Event summary'),
            max_length=256
            )
    description = models.TextField(
            _('Description'),
            blank=True
            )
    # The roles referenced here indicate *who* is supposed to be a part of the
    # event
    roles = models.ManyToManyField(Role)
    # In my original workflow the Event model included a "cost" and is_mandatory
    # field. Again, much loved by managers...

class WorkflowManager(models.Model):
    """
    Other models in the project reference this model so they are associated with
    a particular workflow.
    """
    workflow = models.ForeignKey(Workflow)
    created_on = models.DateTimeField(auto_now_add=True)
    completed_on = models.DateTimeField(
            null=True,
            blank=True
            )

class Participant(models.Model):
    """
    Defines which users have what roles in a particular run of a workflow
    """
    user = models.ForeignKey(User)
    role = models.ForeignKey(Role)
    workflowmanager = models.ForeignKey(WorkflowManager)

class WorkflowEvent(models.Model):
    """
    Records what has happened and when in a particular run of a workflow. The
    latest record for a WorkflowManager will indicate the current state.
    """
    workflowmanager = models.ForeignKey(WorkflowManager)
    state = models.ForeignKey(State)
    transition = models.ForeignKey(Transition, null=True)
    participant = models.ForeignKey(Participant)
    created_on = models.DateTimeField(auto_now_add=True)
