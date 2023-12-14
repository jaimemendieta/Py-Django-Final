from django.shortcuts import render, redirect
from .forms import YelpURLForm
from .scraper import scrape_page
from .models import Business, Comment, BusinessHour


def home(request):
    if request.method == 'POST':
        form = YelpURLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['yelp_url']
            scrape_page(url)
            return redirect('display_view')
    else:
        form = YelpURLForm()
    return render(request, 'home.html', {'form': form})


def display_view(request):
    businesses = Business.objects.prefetch_related('business_hours').all()
    return render(request, 'display_data.html', {'businesses': businesses})
