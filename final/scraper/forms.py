from django import forms


class YelpURLForm(forms.Form):
    yelp_url = forms.URLField(label='Enter Yelp URL', required=True)
