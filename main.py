from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
import time
import smtplib


NUM_ADULTI = 4
CHECK_IN = '2023-11-01'
CHECK_OUT = '2023-11-03'
COSTO_TOT_MAX = 700

SENDER = # fill with sender mail
SENDER_PW = # fill with sender password, needed to send mail from 3rd party application (as a python script)
RECIPIENT = # fill recipient mail (as a list if more than one)

headers = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
}
url_booking = 'https://www.booking.com/searchresults.it.html?label=it-it-booking-desktop-VRZD0IC5lt9Ulq' \
               '*ajTZ_bgS652829000338%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap%3Aneg%3Afi%3Atikwd-65526620%3Alp1008611%3Ali' \
               '%3Adec%3Adm&aid=2311236&ss=Lucca%2C+Toscana%2C+Italia&ssne=Forl%C3%AC&ssne_untouched=Forl%C3%AC&lang' \
               '=it&sb=1&src_elem=sb&dest_id=-120405&dest_type=city&ac_position=0&ac_click_type=b&ac_langcode=it' \
               '&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=e9d64230739300df&ac_meta' \
               f'=GhBlOWQ2NDIzMDczOTMwMGRmIAAoATICaXQ6BWx1Y2NhQABKAFAA&checkin={CHECK_IN}&checkout={CHECK_OUT}' \
               f'&group_adults={NUM_ADULTI}&no_rooms=1&group_children=0&sb_travel_purpose=leisure&order=price#map_closed'
url_airbnb = f'https://www.airbnb.it/s/Lucca--LU/homes?adults={NUM_ADULTI}&place_id=ChIJ2aLWc2yD1RIRkJnl45AsCAQ&checkin={CHECK_IN}' \
             f'&checkout={CHECK_OUT}&tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&query=Lucca%2C%20LU' \
             '&flexible_trip_lengths%5B%5D=one_week&monthly_start_date=2023-08-01&monthly_length=3' \
             '&price_filter_input_type=0&price_filter_num_nights=2&channel=EXPLORE&ne_lat=43.90670277805213&ne_lng=10' \
             '.593727366507949&sw_lat=43.77308105884387&sw_lng=10.408981105287523&zoom=12&zoom_level=12&search_by_map' \
             '=true&search_type=user_map_move&price_max=350'

msg_ricerca_booking = f"<p><a href=\"{url_booking}\">Link ricerca booking</a></p>"
msg_ricerca_airbnb = f"<p><a href=\"{url_airbnb}\">Link ricerca airbnb</a></p>"

# -------------------------------- BOOKING --------------------------------
response_booking = requests.get(url_booking, headers=headers)
soup = BeautifulSoup(response_booking.text, "html.parser")

tutte_case = soup.find_all(attrs={'data-testid': 'property-card'})
case_dict = []
for casa in tutte_case:
    nome = casa.find(name='a', class_='e13098a59f')
    # Some attributes, like the data-* attributes in HTML 5, have names that can’t be used as the names of keyword arguments:
    # You can use these attributes in searches by putting them into a dictionary and passing the dictionary into find_all() as the attrs argument:
    distanza = casa.find(attrs={'data-testid': 'distance'})
    voto = casa.find(attrs={'data-testid': 'review-score'})
    costo = casa.find(attrs={'data-testid': 'price-and-discounted-price'})
    case_dict.append({'nome': nome.get_text('/').split('/')[0],
                      'distanza': distanza.get_text(),
                      'costo tot': costo.get_text().replace(u'\xa0', u'').split()[-1],
                      'voto': f"{voto.get_text('/').split('/')[0]}/10" if voto else '?',
                      'link': nome['href']
                      })
# print(case_dict)
# print(len(case_dict))

msg_booking = "<h2>BOOKING:</h2>"
for casa in case_dict:
    if int(casa['costo tot'].strip('€').replace('.', '')) < COSTO_TOT_MAX:
        # msg_booking += f"- {casa['costo tot']}: {casa['nome']} a {casa['distanza']} e voto {casa['voto']} (<a href=\"{casa['link']}\">link</a>)\n"
        msg_booking += f"<p>- {casa['costo tot']}: <a href=\"{casa['link']}\">{casa['nome']}</a> a {casa['distanza']} e voto {casa['voto']}</p>"


# -------------------------------- AIRBNB --------------------------------
driver = webdriver.Chrome()
driver.get(url_airbnb)
time.sleep(2)

# response_airbnb = requests.get(url_airbnb, headers=headers)
# soup doesn't work with this requests.text, so I first load the page with selenium
# can happen if the page is loaded with JS and only then contains results
# maybe for the same reason, I have to wait 2 seconds (time_sleep(2)) before loading the html, or else I get nothing
soup = BeautifulSoup(driver.page_source, "html.parser")

tutte_case = soup.select("div.cy5jw6o.dir.dir-ltr")
case_dict = []
for casa in tutte_case:
    titolo = casa.find(attrs={'data-testid': 'listing-card-title'})
    sottotitolo = casa.find_all(attrs={'data-testid': 'listing-card-subtitle'})
    costo = casa.find(class_='_tt122m')
    voto = casa.find(attrs={'aria-hidden': 'true', 'class': 'r1dxllyb'})
    link = casa.find(name='a')
    case_dict.append({'nome': titolo.get_text(),
                      'descrizione': '; '.join([elem.get_text() for elem in sottotitolo]).replace(u'\xa0', u'').replace('·', ''),
                      'costo tot': costo.get_text().replace(u'\xa0', u'').split()[0],
                      'voto': f"{voto.get_text().split()[0]}/5" if voto else '?',
                      'link': f"https://www.airbnb.it/{link['href']}"
                      })
# print(case_dict)
# print(len(case_dict))

msg_airbnb = "<h2>AIRBNB:</h2>"
for casa in case_dict:
    if int(casa['costo tot'].strip('€').replace('.', '')) < COSTO_TOT_MAX:
        msg_airbnb += f"<p>- {casa['costo tot']}: <a href=\"{casa['link']}\">{casa['nome']}</a>; {casa['descrizione']}; voto {casa['voto']}</p>"


# -------------------------------- SEND MAIL --------------------------------
# sending msg as html with MIMEtext
# this way is easier to add sender and recipient, and is possible to add formatting as a normal html
msg = MIMEText(f"{msg_booking}{msg_ricerca_booking}{msg_airbnb}{msg_ricerca_airbnb}", "html")
msg['Subject'] = f"Alloggi Lucca comics sotto i {COSTO_TOT_MAX}€"
msg['From'] = SENDER
msg['To'] = RECIPIENT

password = SENDER_PW
with smtplib.SMTP("smtp.gmail.com") as connection:
    connection.starttls()
    connection.login(user=msg['From'], password=password)
    connection.sendmail(from_addr=msg['From'], to_addrs=msg['To'], msg=msg.as_string())
