from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.contrib import messages
from .forms import ContactView


def contact(request):
	if request.method == 'POST':
		form = ContactView(request.POST)
		if form.is_valid():
			our_form = form.save(commit=False)
			our_form.save()
			messages.add_message(request, messages.INFO, 'Your message has been sent. Thank You.')
			return HttpResponseRedirect('/')
	else:
		form = ContactView()
	t = loader.get_template('contact.html')
	c = RequestContext(request, {'form': form})
	return HttpResponse(t.render(c))
