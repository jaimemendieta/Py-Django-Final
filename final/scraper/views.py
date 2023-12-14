from django.shortcuts import render, redirect
from .forms import YelpURLForm
from .scraper import scrape_page
from .models import Business, Comment, BusinessHour


def home(request):
    if request.method == 'POST':
        form = YelpURLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['yelp_url']
            business = scrape_page(url)
            return redirect('display_view', pk=business.pk)
    else:
        form = YelpURLForm()
    return render(request, 'home.html', {'form': form})


def display_view(request, pk):
    business = Business.objects.get(pk=pk)
    comments = Comment.objects.filter(business=business)
    business_hours = BusinessHour.objects.filter(business=business)
    return render(request, 'display_data.html', {
        'business': business,
        'comments': comments,
        'business_hours': business_hours
    })
