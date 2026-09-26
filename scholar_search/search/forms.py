from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import MAJORS


class SignupForm(UserCreationForm):
    major = forms.ChoiceField(choices=MAJORS, label="Research area")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "major", "password1", "password2")


class SearchForm(forms.Form):
    match = forms.ChoiceField(choices=[("any", "Any words"), ("all", "All words"), ("phrase", "Exact phrase")], required=False)
    q = forms.CharField(max_length=300, required=False, label="Search papers")
    year = forms.IntegerField(min_value=1900, max_value=2100, required=False)
    year_mode = forms.ChoiceField(choices=[("since", "Since year"), ("exact", "In year")], required=False)
    sort = forms.ChoiceField(choices=[("relevance", "Relevance"), ("newest", "Newest first")], required=False)
