from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

# User registration form
class CreateUserForm(UserCreationForm):

	email = forms.EmailField(required=True)

	class Meta:
		model = User
		fields = ['username', 'email', 'password1', 'password2']

	# Checks if the provided email exists
	def cleanEmail(self):
		if User.objects.filter(email=self.cleaned_data['email']).exists():
			raise forms.ValidationError("El correo electrónico proporcionado ya está registrado.")
		return self.cleaned_data['email']
