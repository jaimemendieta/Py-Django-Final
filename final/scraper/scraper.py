import requests
from bs4 import BeautifulSoup
import re
import datetime
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .models import Business, Comment, BusinessHour


def parse_time(time_str):
    return datetime.datetime.strptime(time_str, '%I:%M %p').time()


def parse_date(date_str):
    date_obj = datetime.datetime.strptime(date_str, '%b %d, %Y')
    iso_date_str = date_obj.strftime('%Y-%m-%d')
    return iso_date_str


def scrape_page(url):
    # Check if business already exists
    business, created = Business.objects.get_or_create(yelp_url=url)

    if created:
        # Business did not previously exist in database, scrape data for newly added business
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        # driver_path = './tools/geckodriver.exe'
        # service = Service(driver_path)
        driver = webdriver.Firefox()
        driver.get(url)

        business_hours = []

        reviews = []

        amenities_dict = {
            'offers_delivery': False,
            'offers_takeout': False,
            'offers_catering': False,
            'reservations': False,
            'accepts_credit_cards': False,
            'accepts_cash': False,
            'accepts_android_pay': False,
            'accepts_apple_pay': False,
            'private_parking': False,
            'waiter_service': False,
            'free_wifi': False,
            'full_bar': False,
            'wheelchair_accessible': False,
            'tv': False,
            'open_to_all': False,
            'outdoor_seating': False,
            'dogs_allowed': False,
            'bike_parking': False
        }

        business_name_tag = soup.find('h1', class_='css-1se8maq')
        business_name = business_name_tag.text if business_name_tag else 'N/A'

        category_tags = soup.find_all('a', class_='css-19v1rkv')
        category = next((tag.text for tag in category_tags if tag['href'].startswith('/search?find_desc=')), 'N/A')

        rating_tag = soup.find('span', class_='css-1fdy0l5')
        if rating_tag:
            rating_str = rating_tag.text.strip()
            try:
                rating = float(rating_str)
            except ValueError:
                rating = 0
        else:
            rating = 0

        website_section = soup.find('p', string='Business website')
        website_tag = website_section.find_next('a') if website_section else None
        website = 'https://www.' + website_tag.text.strip() if website_tag else 'N/A'

        phone_section = soup.find('p', string='Phone number')
        phone_tag = phone_section.find_next('p', class_='css-1p9ibgf') if phone_section else None
        phone_full = phone_tag.text.strip() if phone_tag else 'N/A'
        phone_area_code = phone_full[1:4] if phone_full != 'N/A' else 'N/A'
        phone_number = phone_full[6:].replace(' ', '') if phone_full != 'N/A' else 'N/A'

        # Address Section (might need to change this to get it from the hours and location section)
        address_section = soup.find('p', string=lambda t: t and 'Get Directions' in t)
        address_tag = address_section.find_next('p', class_='css-qyp8bo') if address_section else None
        address_full = address_tag.text.strip() if address_tag else 'N/A'

        # Regex pattern to match 'Address City, ST Zip' format
        address_pattern = re.compile(
            r"(\d+\s*[NSWE]?\s*[\w\s]*\b(?:\d{1,3}(th|nd|rd|st)\s*[NSWE]?|St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|Ln|La|Lane|Rd|Rd.|Road|Broadway|Way|Terrace|Ter|Place|Pl|Court|Ct|Plaza|Plza|Square|Sq|Highway|Hwy|Parkway|Pkwy|Causeway|Cswy|Temple)\b)?\s*([\w\s]+),\s*(\w{2})\s*(\d{5})",
            re.IGNORECASE
        )
        address_match = address_pattern.search(address_full)

        if address_match:
            address_line1 = address_match.group(1).strip() if address_match.group(1) else 'N/A'
            address_line2 = 'N/A'  # No direct way to identify address line 2 from the pattern
            city = address_match.group(3).strip()
            state = address_match.group(4)
            zip_code = address_match.group(5)
        else:
            address_line1, address_line2, city, state, zip_code = 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'

        menu_section = soup.find('h2', string='Menu')
        menu_tag = menu_section.find_next('a', class_='css-1trqlu6') if menu_section else None
        menu_url = menu_tag['href'] if menu_tag else 'N/A'

        # Business Hours
        for row in soup.find_all('tr', class_='css-29kerx'):
            th = row.find('th')
            if th:
                day = th.get_text().strip()
                times = row.find('td').find_all('p', class_='no-wrap__09f24__c3plq')

                for time_period in times:
                    time_str = time_period.get_text().strip()
                    if time_str.lower() != 'closed':
                        opening_time, closing_time = time_str.split(' - ')
                        opening_time = parse_time(opening_time)
                        closing_time = parse_time(closing_time)
                        business_hours.append({
                            'day': day,
                            'opening_time': opening_time,
                            'closing_time': closing_time
                        })

        # Amenities & About
        amenities_section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//section[@aria-label='Amenities and More']"))
        )

        expand_button = amenities_section.find_element(By.CSS_SELECTOR, 'button[data-activated="false"]')
        expand_button.click()

        WebDriverWait(driver, 10).until(
            lambda d: expand_button.get_attribute("aria-expanded") == "true"
        )

        about_section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//section[@aria-label='About the Business']"))
        )

        read_more_button = about_section.find_element(By.CSS_SELECTOR, 'button[data-activated="false"]')
        read_more_button.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-modal='true']"))
        )

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.list__09f24__ynIEd"))
        )

        html = driver.page_source
        driver.quit()

        soup2 = BeautifulSoup(html, 'html.parser')

        amenities_section = soup2.find('section', {'aria-label': 'Amenities and More'})
        if amenities_section:
            amenities_items = amenities_section.find_all('div', class_='arrange-unit__09f24__rqHTg css-1qn0b6x')
            for item in amenities_items:
                icon = item.find('span', class_='icon--24-close-v2')
                amenity_text = item.find('span', class_='css-1p9ibgf')
                if amenity_text:
                    text = amenity_text.get_text().strip().lower()
                    if 'delivery' in text:
                        amenities_dict['offers_delivery'] = icon is None
                    elif 'takeout' in text:
                        amenities_dict['offers_takeout'] = icon is None
                    elif 'offers catering' in text:
                        amenities_dict['offers_catering'] = icon is None
                    elif 'reservations' in text:
                        amenities_dict['reservations'] = icon is None
                    elif 'credit cards' in text:
                        amenities_dict['accepts_credit_cards'] = icon is None
                    elif 'cash' in text:
                        amenities_dict['accepts_cash'] = icon is None
                    elif 'android pay' in text:
                        amenities_dict['accepts_android_pay'] = icon is None
                    elif 'apple pay' in text:
                        amenities_dict['accepts_apple_pay'] = icon is None
                    elif 'lot parking' in text:
                        amenities_dict['private_parking'] = icon is None
                    elif 'waiter service' in text:
                        amenities_dict['waiter_service'] = icon is None
                    elif 'wi-fi' in text:
                        amenities_dict['free_wifi'] = icon is None
                    elif 'bar' in text:
                        amenities_dict['full_bar'] = icon is None
                    elif 'wheelchair' in text:
                        amenities_dict['wheelchair_accessible'] = icon is None
                    elif 'tv' in text:
                        amenities_dict['tv'] = icon is None
                    elif 'open to all' in text:
                        amenities_dict['open_to_all'] = icon is None
                    elif 'outdoor seating' in text:
                        amenities_dict['outdoor_seating'] = icon is None
                    elif 'dogs' in text:
                        amenities_dict['dogs_allowed'] = icon is None
                    elif 'bike parking' in text:
                        amenities_dict['bike_parking'] = icon is None

        # About text fetch
        about_modal_section = soup2.find('div', {'id': 'modal-portal-container'})
        if about_modal_section:
            about_text = about_modal_section.find('p').text.strip()

        # Comments
        reviews_section = soup2.find('section', {'aria-label': 'Recommended Reviews'})
        reviews_ul = reviews_section.find('ul', class_='list__09f24__ynIEd')
        if reviews_section:
            for review in reviews_ul.find_all('li', class_='css-1q2nwpv'):
                # Extract user information
                user_name = review.find('a', class_='css-19v1rkv').get_text(strip=True) if review.find('a', class_='css-19v1rkv') else None
                user_location = review.find('span', class_='css-qgunke').get_text(strip=True) if review.find('span',
                                                                                                   class_='css-qgunke') else None
                date_str = review.find('span', class_='css-chan6m').get_text(strip=True) if review.find('span', class_='css-chan6m') else None
                if date_str:
                    comment_date = parse_date(date_str)

                # User Stats
                stats = review.find_all('span', class_='css-1fnccdf')
                user_friends = int(stats[0].get_text()) if len(stats) > 0 else 0
                user_reviews = int(stats[1].get_text()) if len(stats) > 1 else 0
                user_photos = int(stats[2].get_text()) if len(stats) > 2 else 0

                # Extract rating
                rating_element = review.find('div', class_='css-14g69b3')
                user_rating = None
                if rating_element:
                    aria_label = rating_element.get('aria-label', '')
                    rating_match = re.search(r'(\d+)', aria_label)
                    if rating_match:
                        user_rating = int(rating_match.group(1))

                # Extract comment
                user_comment = review.find('p', class_='comment__09f24__D0cxf').get_text(strip=True) if review.find('p', class_='comment__09f24__D0cxf') else None

                # Extract reactions
                reactions = {}

                for reaction_type, icon_class in [('useful', 'icon--16-useful-v2'), ('funny', 'icon--16-funny-v2'),
                                                  ('cool', 'icon--16-cool-v2')]:
                    reaction_span = review.find('span', class_=icon_class).find_parent('span', class_='css-inq9gi')
                    if reaction_span:
                        # Check if span with class 'css-1lr1m88' exists within parent span
                        reaction_count_span = reaction_span.find('span', class_='css-1lr1m88')
                        if reaction_count_span:
                            reactions[reaction_type] = int(reaction_count_span.get_text(strip=True))
                        else:
                            reactions[reaction_type] = 0
                    else:
                        reactions[reaction_type] = 0

                # Add review data to reviews array
                review_things = {
                    'user_name': user_name,
                    'user_location': user_location,
                    'comment_date': comment_date,
                    'user_friends': user_friends,
                    'user_reviews': user_reviews,
                    'user_photos': user_photos,
                    'user_rating': user_rating,
                    'user_comment': user_comment,
                    'reactions': reactions
                }
                reviews.append(review_things)

        for hour_data in business_hours:
            BusinessHour.objects.create(
                business=business,
                day=hour_data['day'],
                opening_time=hour_data['opening_time'],
                closing_time=hour_data['closing_time']
            )

        for review_data in reviews:
            Comment.objects.create(
                business=business,
                user_name=review_data['user_name'],
                user_location=review_data['user_location'],
                comment_date=review_data['comment_date'],
                user_friends=review_data['user_friends'],
                user_reviews=review_data['user_reviews'],
                user_photos=review_data['user_photos'],
                user_rating=review_data['user_rating'],
                user_comment=review_data['user_comment'],
                reactions_useful=review_data['reactions'].get('useful', 0),
                reactions_funny=review_data['reactions'].get('funny', 0),
                reactions_cool=review_data['reactions'].get('cool', 0)
            )

        business.name = business_name
        business.about_text = about_text
        business.yelp_url = url
        business.category = category
        business.rating = rating
        business.website_url = website
        business.phone_area_code = phone_area_code
        business.phone_number = phone_number
        business.address_line1 = address_line1
        business.address_line2 = address_line2
        business.city = city
        business.state = state
        business.zip_code = zip_code
        business.menu_url = menu_url
        business.offers_delivery = amenities_dict['offers_delivery']
        business.offers_takeout = amenities_dict['offers_takeout']
        business.offers_catering = amenities_dict['offers_catering']
        business.reservations = amenities_dict['reservations']
        business.accepts_credit_cards = amenities_dict['accepts_credit_cards']
        business.accepts_cash = amenities_dict['accepts_cash']
        business.accepts_android_pay = amenities_dict['accepts_android_pay']
        business.accepts_apple_pay = amenities_dict['accepts_apple_pay']
        business.private_parking = amenities_dict['private_parking']
        business.waiter_service = amenities_dict['waiter_service']
        business.free_wifi = amenities_dict['free_wifi']
        business.full_bar = amenities_dict['full_bar']
        business.wheelchair_accessible = amenities_dict['wheelchair_accessible']
        business.tv = amenities_dict['tv']
        business.open_to_all = amenities_dict['open_to_all']
        business.outdoor_seating = amenities_dict['outdoor_seating']
        business.dogs_allowed = amenities_dict['dogs_allowed']
        business.bike_parking = amenities_dict['bike_parking']
        business.save()

    return business

