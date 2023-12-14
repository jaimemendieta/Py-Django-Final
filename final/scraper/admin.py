from django.contrib import admin
from .models import Business, Comment, BusinessHour


admin.site.register(Business)
admin.site.register(Comment)
admin.site.register(BusinessHour)

