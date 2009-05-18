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
import django.dispatch
import datetime

############
# Exceptions
############

class UnableToCloneWorkflow(Exception):
    """
    To be raised if unable to clone a workflow model (and related models)
    """

class UnableToStartWorkflow(Exception):
    """
    To be raised if a WorkflowManager is unable to start a workflow
    """

#########
# Signals
#########

# Fired when a role is assigned to a user for a particular run of a workflow
# (defined in the workflow_manager). The sender is an instance of the
# Participant model.
role_assigned = django.dispatch.Signal()
# Fired when a new workflow_manager starts navigating a workflow. The sender is
# an instance of the WorkflowManager model
workflow_started = django.dispatch.Signal()
# Fired when something happens during the life of a workflow_manager (the sender
# is an instance of the WorkflowHistory model)
workflow_incident = django.dispatch.Signal() 
# Fired when an active workflow_manager reaches a workflow's end state. The
# sender is an instance of the WorkflowManager model
workflow_ended = django.dispatch.Signal()

########
# Models
########
class Role(models.Model):
    """
    Represents a type of user who can be associated with a workflow. Used by
    the State and Transition models to define *who* has permission to view a
    state or use a transition. The Event model uses this model to reference
    *who* should be involved in a particular event.
    """
    name = models.CharField(
            _('Name of Role'),
            max_length=64
            )
    description = models.TextField(
            _('Description'),
            blank=True
            )

    class Meta:
        ordering = ['name',]
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')
        permissions = (
                ('can_define_roles','Can define roles'),
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

    def activate(self):
        """
        Puts the workflow in the "active" state and verifies that the directed
        graph doesn't contain any orphaned nodes or edges and contains exactly
        one start state and at least one end state
        """
        # TODO: Need to add the validation of the graph to this method.
        self.status = self.ACTIVE
        self.save()

    def retire(self):
        """
        Retires the workflow so it can no-longer be used with new
        WorkflowManager models
        """
        self.status = self.RETIRED
        self.save()

    def clone(self):
        """
        Returns a clone of the workflow. The clone will be in the DEFINITION
        state whereas the source workflow *must* be ACTIVE or RETIRED.
        """
        if self.status >= self.ACTIVE:
            # Clone this workflow
            # TODO: Finish this
            pass
        else:
            raise UnableToCloneWorkflow

    class Meta:
        ordering = ['status', 'name']
        verbose_name = _('Workflow')
        verbose_name_plural = _('Workflows')
        permissions = (
                ('can_manage_workflows','Can manage workflows'),
            )

class State(models.Model):
    """
    Represents a specific state that a thing can be in during its progress
    through a workflow. A node in a directed graph.
    """

    # Constant values to denote a period of time in seconds
    SECOND = 1
    MINUTE = 60
    HOUR = 3600
    DAY = 86400
    WEEK = 604800

    DURATIONS = (
            (SECOND, _('Second(s)')),
            (MINUTE, _('Minute(s)')),
            (HOUR, _('Hour(s)')),
            (DAY, _('Day(s)')),
            (WEEK, _('Week(s)')),
            )

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
    # The following two fields allow a specification of expected duration to be
    # associated with a state. The estimation_value field stores the amount of 
    # time, whilst estimation_unit stores the unit of time estimation_value is
    # in. For example, estimation_value=5, estimation_unit=DAY means something
    # is expected to be in this state for 5 days. By doing estimation_value *
    # estimation_unit we can get the number of seconds to pass into a timedelta
    # to discover when the deadline for a state is.
    estimation_value = models.IntegerField(
            _('Estimated time (value)'),
            default=0,
            help_text=_('Use whole numbers')
            )
    estimation_unit = models.IntegerField(
            _('Estimation unit of time'),
            default=DAY,
            choices = DURATIONS
            )

    def deadline(self):
        """
        Will return the expected deadline (or None) for this state calculated
        from datetime.today()
        """
        if self.estimation_value > 0:
            duration = datetime.timedelta(
                    seconds=(self.estimation_value*self.estimation_unit)
                    )
            return (self._today()+duration)
        else:
            return None

    def _today(self):
        """
        To help with the unit tests
        """
        return datetime.datetime.today()

    class Meta:
        verbose_name = _('State')
        verbose_name_plural = _('States')

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

    class Meta:
        verbose_name = _('Transition')
        verbose_name_plural = _('Transitions')

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
    state = models.ForeignKey(
            State,
            related_name='events'
            )
    # The roles referenced here indicate *who* is supposed to be a part of the
    # event
    roles = models.ManyToManyField(Role)
    # For the purposes of budgeting and cost estimation 
    estimated_cost = models.DecimalField(
            _('Cost'),
            max_digits=20,
            decimal_places=2,
            blank=True,
            null=True,
            help_text=_('The estimated cost (if any) of this event'))
    # If this field is true then the workflow cannot progress beyond the related
    # state
    is_mandatory = models.BooleanField(
            _('Mandatory event'),
            default=False,
            help_text=_('This event must be marked as complete before moving'\
                    ' out of the associated state.')
            )

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

class WorkflowManager(models.Model):
    """
    Other models in a project reference this model so they become associated 
    with a particular workflow.
    """
    workflow = models.ForeignKey(Workflow)
    created_by = models.ForeignKey(User)
    created_on = models.DateTimeField(auto_now_add=True)
    completed_on = models.DateTimeField(
            null=True,
            blank=True
            )

    def current_state(self):
        """ 
        Returns the instance of the WorkflowHistory model that represents the 
        current state this WorkflowManager is at.
        """
        if self.history:
            return self.history[0]
        else:
            return None

    def start(self, participant):
        """
        Starts a WorkflowManager by putting it into the start state of the
        workflow defined in the "workflow" field
        """
        start_state_result = State.objects.filter(
                workflow=self.workflow, 
                is_start_state=True
                )
        if len(start_state_result) == 1:
            first_step = WorkflowHistory(
                workflowmanager=self,
                state=start_state_result[0],
                participant=participant,
                note=_('Started workflow'),
                deadline=start_state.deadline()
                )
            first_step.save()
        else:
            raise UnableToStartWorkflow

    def force_stop(self):
        """
        Should a WorkflowManager need to be abandoned you should call this
        """
        self.completed_on = datetime.datetime.today()
        self.save()

    class Meta:
        ordering = ['-completed_on', '-created_on']
        verbose_name = _('Workflow Manager')
        verbose_name_plural = _('Workflow Managers')
        permissions = (
                ('can_start_workflow','Can start a workflow'),
            )

class Participant(models.Model):
    """
    Defines which users have what roles in a particular run of a workflow
    """
    user = models.ForeignKey(User)
    role = models.ForeignKey(Role)
    workflowmanager = models.ForeignKey(
            WorkflowManager,
            related_name='participants'
            )

    def save(self):
        super(Participant, self).save()
        role_assigned.send(sender=self)

    class Meta:
        ordering = ['workflowmanager', 'role']
        verbose_name = _('Participant')
        verbose_name_plural = _('Participants')

class WorkflowHistory(models.Model):
    """
    Records what has happened and when in a particular run of a workflow. The
    latest record for the referenced WorkflowManager will indicate the current 
    state.
    """
    workflowmanager = models.ForeignKey(
            WorkflowManager,
            related_name='history')
    state = models.ForeignKey(State)
    transition = models.ForeignKey(Transition, null=True)
    event = models.ForeignKey(Event, null=True)
    participant = models.ForeignKey(Participant)
    created_on = models.DateTimeField(auto_now_add=True)
    note = models.CharField(
            _('Note'),
            max_length=512,
            blank=True
            )
    deadline = models.DateTimeField(
            _('Deadline'),
            null=True,
            blank=True,
            help_text=_('The deadline for staying in this state')
            )

    def save(self):
        super(WorkflowHistory, self).save()
        # Various signals
        workflow_incident.send(sender=self) 
        if self.state and self.state.is_start_state:
            workflow_started.send(sender=self.workflowmanager)
        elif self.state and self.state.is_end_state:
            workflow_ended.send(sender=self.workflowmanager)

    class Meta:
        ordering = ['-created_on']
        verbose_name = _('Workflow History')
        verbose_name_plural = _('Workflow Histories')
