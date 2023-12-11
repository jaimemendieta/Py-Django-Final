import requests
from bs4 import BeautifulSoup
import re
import datetime


def parse_time(time_str):
    return datetime.datetime.strptime(time_str, '%I:%M %p').time()


def scrape_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    business_hours = []

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
        'business_hours': business_hours
    }


url = 'https://www.yelp.com/biz/sicilia-mia-salt-lake-city?osq=Italian+Food'
data = scrape_page(url)
print(data)