from django.urls import path
from .views import display_view, home

urlpatterns = [
    path('', home, name='home'),
    path('results/<int:pk>/', display_view, name='display_view'),
]
