from django.test import TestCase, SimpleTestCase
from .models import ContactForm
from .forms import ContactView
from datetime import datetime, timedelta


class UserModelTest(TestCase):

	@classmethod
	def setUpClass(cls):
		super(UserModelTest, cls).setUpClass()
		ContactForm(email="test@test.com", name="test").save()
		ContactForm(email="a@b.com", name="ab").save()
		cls.firstUser = ContactForm(
			email="first@first.com",
			name="first",
			timestamp=datetime.today() + timedelta(days=2)
		)
		cls.firstUser.save()

	def test_contactform_str_email_returns(self):
		self.assertEquals("first@first.com", str(self.firstUser))

	def test_order(self):
		contacts = ContactForm.objects.all()
		self.assertEquals(self.firstUser, contacts[0])

class ContactViewTests(SimpleTestCase):

	def test_displayed_fields(self):
		expected_fields = ['name', 'email', 'topic', 'message']
		self.assertEquals(ContactView.Meta.fields, expected_fields)

		