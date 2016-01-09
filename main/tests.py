from django.test import TestCase
from django.core.urlresolvers import resolve
from django.shortcuts import render_to_response
from django.test import RequestFactory

from payments.models import User
from .views import index

import mock


class MainPageTests(TestCase):

	######## SETUP ######

	@classmethod
	def setUpClass(cls):
		super(MainPageTests, cls).setUpClass()
		request_factory = RequestFactory()
		cls.request = request_factory.get('/')
		cls.request.session = {}

	###### TESTING ROUTES ######

	def test_root_resolves_to_main_view(self):
		main_page = resolve('/')
		self.assertEquals(main_page.func, index)

	def test_returns_appropriate_html_code(self):
		resp = index(self.request)
		self.assertEquals(resp.status_code,200)

	####### TESTING TEMPLATES AND VIEWS #######

	def test_returns_exact_html(self):
		resp = index(self.request)
		self.assertEquals(resp.content, render_to_response("index.html").content)

	def test_index_handles_logged_in_user(self):		
				
		self.request.session = {"user": "1"}
		with mock.patch('main.views.User') as user_mock:
			config = {'get_by_id.return_value': mock.Mock()}
			user_mock.configure_mock(**config)
			resp = index(self.request)
			self.request.session = {}
			expectedHtml = render_to_response('user.html', {'user': user_mock.get_by_id(1)})
			self.assertEquals(resp.content,	expectedHtml.content)
