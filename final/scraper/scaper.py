import requests
from bs4 import BeautifulSoup
import re
import datetime
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def parse_time(time_str):
    return datetime.datetime.strptime(time_str, '%I:%M %p').time()


def scrape_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    driver_path = './tools/geckodriver.exe'
    service = Service(driver_path)
    driver = webdriver.Firefox(service=service)
    driver.get(url)

    business_hours = []

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
    rating = rating_tag.text.strip() if rating_tag else 'N/A'

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

    return {
        'business_name': business_name,
        'category': category,
        'rating': rating,
        'website': website,
        'phone_area_code': phone_area_code,
        'phone_number': phone_number,
        'address_line1': address_line1,
        'address_line2': address_line2,
        'city': city,
        'state': state,
        'zip_code': zip_code,
        'menu_url': menu_url,
        'business_hours': business_hours,
        'amenities': amenities_dict,
        'about': about_text
    }


url = 'https://www.yelp.com/biz/da-andrea-greenwich-village-new-york?osq=italian'
data = scrape_page(url)
print(data)
