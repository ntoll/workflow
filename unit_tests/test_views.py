# -*- coding: UTF-8 -*-
"""
View tests for Workflows 

Author: Nicholas H.Tollervey

"""
# python
import datetime

# django
from django.test.client import Client
from django.test import TestCase

# project
from workflow.views import *
from workflow.models import Workflow

class ViewTestCase(TestCase):
        """
        Testing Views 
        """
        # Make sure the URLs play nice
        urls = 'workflow.urls'
        # Reference fixtures here
        fixtures = ['workflow_test_data']

        def test_get_dotfile(self):
            """
            Make sure we get the expected .dot file given the current state of
            the fixtures
            """
            w = Workflow.objects.get(id=1)
            result = get_dotfile(w)
            for state in w.states.all():
                # make sure we find references to the states
                self.assertEqual(True, result.find("state%d"%state.id) > -1)
                self.assertEqual(True, result.find(state.name) > -1)
            for transition in w.transitions.all():
                # make sure we find references to the transitions
                search = 'state%d -> state%d [label="%s"];'%(
                        transition.from_state.id,
                        transition.to_state.id,
                        transition.name)
                self.assertEqual(True, result.find(search) > -1)
            # Make sure we have START: and END:
            self.assertEqual(True, result.find("START:") > -1)
            self.assertEqual(True, result.find("END:") > -1)

        def test_dotfile(self):
            """
            Makes sure a GET to the url results in the .dot file as an
            attachment
            """
            c = Client()
            response = c.get('/test_workflow/dotfile/')
            self.assertContains(response, 'A definition for a diagram of the'\
                ' workflow: test workflow')

        def test_graphviz(self):
            """
            Makes sure a GET to the url results in a .png file
            """
            c = Client()
            response = c.get('/test_workflow.png')
            self.assertEqual(200, response.status_code)
            self.assertEqual('image/png', response['Content-Type'])

