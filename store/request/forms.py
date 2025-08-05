from django import forms
from .models import RequestItem


class RequestItemForm(forms.ModelForm):
    class Meta:
        model = RequestItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product_unit'].queryset = self.fields['product_unit'].queryset.filter(
            status='candidate_in_request'
        )