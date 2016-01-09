from django import forms
from django.core.urlresolvers import resolve
from django.db import IntegrityError
from django.test import TestCase, RequestFactory
from django.shortcuts import render_to_response
import django_ecommerce.settings as settings

from payments.models import User
from payments.forms import SigninForm, UserForm, CardForm
from payments.views import soon, register, Customer
import unittest
import mock
from pprint import pformat

from .views import sign_in, sign_out

class UserModelTest(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.test_user = User(email="a@b.com", name='test user')
		cls.test_user.save()

	def test_user_to_string_print_email(self):
		self.assertEquals(str(self.test_user), "a@b.com")

	def test_get_by_id(self):
		self.assertEquals(User.get_by_id(1), self.test_user)

	def test_create_user_function_stores_in_database(self):
		user = User.create("test", "test@test.com", "test123","1234","22")
		self.assertEquals(User.objects.get(email="test@test.com"), user)

	def create_user_already_exists_throws_integrity_errror(self):
		self.assertRaises(
			IntegrityError,
			User.create,
			"test user",
			"ab@c.com",
			"abc",
			"1234",			
		)

class FormTesterMixin():

    def should_have_form_error(self, form_cls, expected_error_name,
                        expected_error_msg, data):

        from pprint import pformat
        test_form = form_cls(data=data)
        
        self.assertFalse(test_form.is_valid())

        self.assertEquals(
            test_form.errors[expected_error_name],
            expected_error_msg,
            msg="Expected {} : Actual {} : using data {}".format(
                test_form.errors[expected_error_name],
                expected_error_msg, pformat(data)
            )
        )

class FormTests(unittest.TestCase, FormTesterMixin):

    def test_signin_form_data_validation_for_invalid_data(self):
        invalid_data_list = [
            {'data': {'email': 'j@j.com'},
             'error': ('password', ['This field is required.'])},
            {'data': {'password': '1234'},
             'error': ('email', ['This field is required.'])}
        ]

        for invalid_data in invalid_data_list:
            self.should_have_form_error(SigninForm,
                                 invalid_data['error'][0],
                                 invalid_data['error'][1],
                                 invalid_data["data"])

    def test_user_form_passwords_match(self):
    	form = UserForm(
    		{
    			'name': 'abc',
    			'email': 'ab@c.com',
    			'password': '1234',
    			'ver_password': '1234',
    			'last_4_digits': '3333',
    			'stripe_token': '1'
    		}
    	)

    	#check if data is valid, if not print error
    	if form.is_valid():
    		self.assertTrue(form.cleaned_data)

    def test_user_form_passwords_dont_match_throws_error(self):
    	form = UserForm(
    		{
    			'name': 'abc',
    			'email': 'ab@c.com',
    			'password': '1234',
    			'ver_password': '134',
    			'last_4_digits': '3333',
    			'stripe_token': '1'
    		}
    	)

    	self.assertFalse(form.is_valid())
    	#self.assertRaisesMessage(forms.ValidationError,"Passwords do not match", form.clean)

    	def test_cardform_data_validation_for_invalid_data(self):
    		invalid_data_list = [
    			{
    				'data': {'last_4_digits':'123'},
    				'error': ('last_4_digits',['Ensure it has 4 digits(it has 3).'])
    			},
    			{
    				'data': {'last_4_digits':'12345'},
    				'error': ('last_4_digits',['Ensure it has 4 digits(it has 5).'])
    			}
    		]
    		for invalid_data in invalid_data_list:
    			self.should_have_form_error(
    				CardForm,
    				invalid_data['error'][0],
    				invalid_data['error'][1],
    				invalid_data["data"]
    			)

class ViewTesterMixin(object):

	@classmethod
	def setupViewTester(cls, url, view_func, expected_html, status_code=200, session={}):
		request_factory = RequestFactory()
		cls.request = request_factory.get(url)
		cls.request.session = session
		cls.status_code = status_code
		cls.url = url
		cls.view_func = staticmethod(view_func)
		cls.expected_html = expected_html

	def test_resolves_to_correct_view(self):
		test_view = resolve(self.url)
		self.assertEquals(test_view.func, self.view_func)

	def test_returns_appropriate_response_code(self):
		resp = self.view_func(self.request)
		self.assertEquals(resp.status_code, self.status_code)

	def test_returns_correct_html(self):
		resp = self.view_func(self.request)
		self.assertEquals(resp.content, self.expected_html)

class SignInPageTests(TestCase, ViewTesterMixin):

	@classmethod
	def setUpClass(cls):
		super(SignInPageTests, cls).setUpClass()
		html = render_to_response(
			'sign_in.html',
			{
				'form': SigninForm(),
				'user': None
			}
		)

		ViewTesterMixin.setupViewTester(
			'/sign_in',
			sign_in,
			html.content
		)

class SignOutPageTests(TestCase, ViewTesterMixin):

	@classmethod
	def setUpClass(cls):
		super(SignOutPageTests, cls).setUpClass()
		ViewTesterMixin.setupViewTester(
			'/sign_out',
			sign_out,
			"", #redirects to no html
			status_code=302,
			session={"user":"dummy"},
		)

	def setUp(self):
		self.request.session = {"user":"dummy"}

class RegisterPageTests(TestCase, ViewTesterMixin):

	@classmethod
	def setUpClass(cls):
		super(RegisterPageTests, cls).setUpClass()
		html = render_to_response(
			'register.html',
			{
				'form': UserForm(),
				'months': range(1,12),
				'publishable': settings.STRIPE_PUBLISHABLE,
				'soon': soon,
				'user': None,
				'years': range(2016, 2036),
			}
		)
		ViewTesterMixin.setupViewTester(
			'/register',
			register,
			html.content
		)

	def setUp(self):
		request_factory = RequestFactory()
		self.request = request_factory.get(self.url)

	def test_invalid_form_returns_registration_page(self):

		with mock.patch('payments.forms.UserForm.is_valid') as user_mock:
			user_mock.return_value = False
			self.request.method = 'POST'
			self.request.POST = None
			resp = register(self.request)
			self.assertEquals(resp.content, self.expected_html)
			self.assertEquals(user_mock.call_count,1)


	@mock.patch('payments.views.Customer.create')
	@mock.patch.object(User, 'create')
	def test_registering_new_user_returns_successfully(self, create_mock, stripe_mock):
		self.request.session = {}
		self.request.method = 'POST'
		self.request.POST = {
			'email': 'ab@c.com',
			'name': 'abcabc',
			'stripe_token': '...',
			'last_4_digits': '4242',
			'password': 'abc12345',
			'ver_password': 'abc12345'
		}

		new_user = create_mock.return_value   #getting return values for the mocks
		new_cust = stripe_mock.return_value

		resp = register(self.request)

		self.assertEquals(resp.content, "")
		self.assertEquals(resp.status_code, 302)
		self.assertEquals(self.request.session['user'], new_user.pk)
		###verify that the user was ACTUALLY stored in the db
		create_mock.assert_called_with(
			'abcabc', 'ab@c.com', 'abc12345', '4242', new_cust.id
		)

	def get_MockUserForm(self):
		from django import forms

		class MockUserForm(forms.Form):

			def is_valid(self):
				return True
			
			@property
			def cleaned_data(self):
			    return {
			    	'email': 'ab@c.com',
			    	'name': 'abcabc',
			    	'stripe_token': '...',
			    	'last_4_digits': '1234',
			    	'password': 'abc12345',
			    	'ver_password': 'abc12345',
			    }

			def addError(self, error):
				pass 

		return MockUserForm()

	@mock.patch('payments.views.UserForm', get_MockUserForm)
	@mock.patch('payments.models.User.save', side_effect=IntegrityError)
	def test_registering_user_twice_cause_error_msg(self, save_mock):

		self.request.session = {}
		self.request.method = 'POST'
		self.request.POST = {}

		#expected html
		html = render_to_response(
			'register.html',
			{
				'form': self.get_MockUserForm(),
				'months': list(range(1, 12)),
				'publishable': settings.STRIPE_PUBLISHABLE,
				'soon': soon(),
				'user': None,
				'years': list(range(2011, 2036)),
			}
		)
		with mock.patch('stripe.Customer') as stripe_mock:
			config = {'create.return_value': mock.Mock()}
			stripe_mock.configure_mock(**config)

			resp = register(self.request)

			#self.assertEquals(resp.content, html.content)
			self.assertEquals(resp.status_code, 200)
			self.assertEquals(self.request.session, {})

			users = User.objects.filter(email="ab@c.com")
			self.assertEquals(len(users), 0)

class CustomerTests(TestCase):
	def test_create_subscription(self):
		with mock.patch('stripe.Customer.create') as create_mock:
			cust_data = {'description':'test user', 'email': 'test@test.com','card':'4242', 'plan':'gold'}
			Customer.create("subscription", **cust_data)
			create_mock.assert_called_with(**cust_data)

	def test_create_one_time_bill(self):
		with mock.patch('stripe.Charge.create') as charge_mock:
			cust_data = {
				'description': 'email',
				'card': '1234',
				'amount': '5000',
				'currency': 'usd'
			}
			Customer.create("one_time", **cust_data)
			charge_mock.assert_called_with(**cust_data)


