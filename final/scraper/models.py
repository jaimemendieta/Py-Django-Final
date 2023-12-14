from django.db import models


class Business(models.Model):
    name = models.CharField(max_length=255)
    about_text = models.TextField(blank=True, null=True)
    yelp_url = models.URLField(unique=True)
    menu_url = models.URLField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=100)
    rating = models.FloatField()
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    phone_area_code = models.CharField(max_length=5)
    phone_number = models.CharField(max_length=20)
    offers_delivery = models.BooleanField(default=False)
    offers_takeout = models.BooleanField(default=False)
    offers_catering = models.BooleanField(default=False)
    reservations = models.BooleanField(default=False)
    accepts_credit_cards = models.BooleanField(default=False)
    accepts_cash = models.BooleanField(default=False)
    accepts_android_pay = models.BooleanField(default=False)
    accepts_apple_pay = models.BooleanField(default=False)
    private_parking = models.BooleanField(default=False)
    waiter_service = models.BooleanField(default=False)
    free_wifi = models.BooleanField(default=False)
    full_bar = models.BooleanField(default=False)
    wheelchair_accessible = models.BooleanField(default=False)
    tv = models.BooleanField(default=False)
    open_to_all = models.BooleanField(default=False)
    outdoor_seating = models.BooleanField(default=False)
    dogs_allowed = models.BooleanField(default=False)
    bike_parking = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Comment(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=100)
    user_location = models.CharField(max_length=255)
    comment_date = models.DateField(null=True)
    user_follower_count = models.IntegerField(default=0)
    user_review_count = models.IntegerField(default=0)
    user_photo_count = models.IntegerField(default=0)
    comment_text = models.TextField()
    rating = models.FloatField()
    reactions_useful = models.IntegerField(default=0)
    reactions_funny = models.IntegerField(default=0)
    reactions_cool = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user_name} on {self.business.name}"


class BusinessHour(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='business_hours')
    day = models.CharField(max_length=9)  # e.g., "Monday"
    opening_time = models.TimeField()
    closing_time = models.TimeField()

    def __str__(self):
        return f"{self.day} hours for {self.business.name}"
