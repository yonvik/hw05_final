from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    sucess_url = reverse_lazy('posts:index.html')
    template_name = 'users/signup.html'
