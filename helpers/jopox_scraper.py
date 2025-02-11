import os
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import re
from ics import Calendar
from models.user import db, User



# Configure logging to a file
    
class JopoxScraper:
    def __init__(self, username, password):
        self.login_url = "https://s-kiekko-app.jopox.fi/login"
        self.admin_login_url = "https://s-kiekko-app.jopox.fi/adminlogin"
        self.base_url = "https://hallinta3.jopox.fi//Admin/HockeyPox2020/Games/Games.aspx"
        self.session = requests.Session()
        self.username = username
        self.password = password

    def login(self):
        login_payload = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": "4NWxflGFghGP1YQS8e08WYCq4fy7aPmfxX2P9iMaq3kvQexgiHGK35tLcG77/xt4MDDtp662387WiA5Bcai5gz8fQtPpsn0h3nqcEJ33oYxx9f+l+T0npKKclOHufqhPKm3PLVLrlIPZnSQuT+x6Fg==",
            "__VIEWSTATEGENERATOR": "808BB379",
            "__EVENTVALIDATION": "oIx/wD7w2bUUazztMa7cwiQ7iwXYV37eSeEkhhcCymnZfmS/rK6dBHKMP6oGzR/6yqZkHtooWHXFZjpJmHe1u25Pby/DuE5SX+FsCZkCnurPafqJg+XIz2EbNG3Hzqlu1ywyR3Kyo2cwYaO0/sKiZtIf/fvWKtmno06o+U+53spSJ34jG5+ZjVWKlDz6XtuU",
            "UsernameTextBox": self.username,
            "PasswordTextBox": self.password,
            "LoginButton": "Kirjaudu"
        }
        response = self.session.post(self.login_url, data=login_payload)
        #logging.debug("Login attempt payload: %s", login_payload)
        #logging.debug("Login response status code: %d", response.status_code)
        #logging.debug("Login response text: %s", response.text)

        if response.status_code == 200:
            logging.info("Login successful!")
            #logging.debug("Cookies after login: %s", self.session.cookies)
            return True
    
        else:
            logging.error("Login failed!")
            return False
        
    def login_for_credentials(self):
        login_payload = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": "4NWxflGFghGP1YQS8e08WYCq4fy7aPmfxX2P9iMaq3kvQexgiHGK35tLcG77/xt4MDDtp662387WiA5Bcai5gz8fQtPpsn0h3nqcEJ33oYxx9f+l+T0npKKclOHufqhPKm3PLVLrlIPZnSQuT+x6Fg==",
            "__VIEWSTATEGENERATOR": "808BB379",
            "__EVENTVALIDATION": "oIx/wD7w2bUUazztMa7cwiQ7iwXYV37eSeEkhhcCymnZfmS/rK6dBHKMP6oGzR/6yqZkHtooWHXFZjpJmHe1u25Pby/DuE5SX+FsCZkCnurPafqJg+XIz2EbNG3Hzqlu1ywyR3Kyo2cwYaO0/sKiZtIf/fvWKtmno06o+U+53spSJ34jG5+ZjVWKlDz6XtuU",
            "UsernameTextBox": self.username,
            "PasswordTextBox": self.password,
            "LoginButton": "Kirjaudu"
        }
        response = self.session.post(self.login_url, data=login_payload)
        #logging.debug("Login attempt payload: %s", login_payload)
        #logging.debug("Login response status code: %d", response.status_code)
        #logging.debug("Login response text: %s", response.text)

        if response.status_code == 200:
            logging.info("Login successful!")
            
            jopox_credentials = []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip()
            jopox_team_name = title.split('Jopox -', 1)[1].strip()
            logging.info(jopox_team_name)

            a_tag = soup.find('a', href=re.compile(r'\d+'))

            # Poimi ja tulosta numerot (poimimme vain ensimmäisen osan href-attribuutista)
            if a_tag:
                jopox_team_id = re.search(r'\d+', a_tag['href']).group()  # Numerosarja stringinä
                
            logging.info(f"Poimittu joukkueen tunnus: {jopox_team_id}")
            #add jopox credentials:
            jopox_credentials.append({'jopox_team_name': jopox_team_name})
            jopox_credentials.append({'jopox_team_id': jopox_team_id})
                    
            #logging.debug("Cookies after login: %s", self.session.cookies)
            return jopox_credentials
    
        else:
            logging.error("Login failed!")
            return False    

    def access_admin(self):
        response = self.session.get(self.admin_login_url)
        #logging.debug("Admin access response status code: %d", response.status_code)
        #logging.debug("Admin access response text: %s", response.text)
        #logging.debug("Cookies after admin access: %s", self.session.cookies)

        if response.status_code == 200:
            logging.info("Admin access successful!")
            return True
        else:
            logging.error("Admin access failed!")
            return False

    def modify_game(self, game_data, uid):
        mod_game_url = f"https://hallinta3.jopox.fi//Admin/HockeyPox2020/Games/Game.aspx?gId={uid}"

        # Load the form page
        response = self.session.get(mod_game_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": mod_game_url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        })
        #logging.debug("Fetching game form page response status code: %d", response.status_code)
        #logging.debug("Fetching game form page response text: %s", response.text)

        if response.status_code != 200:
            logging.error("Failed to load form page!")
            return

        # Parse HTML and extract necessary values
        soup = BeautifulSoup(response.text, 'html.parser')
        viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
        eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]
        viewstategenerator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"]
        logging.debug("game_data received for modifying game: %s", game_data)

    
        # Build payload
        payload = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            #"ctl00$MenuContentPlaceHolder$MainMenu$SiteSelector1$DropDownListSeasons": game_data.get("SeasonId", ""),
            #"ctl00$MenuContentPlaceHolder$MainMenu$SiteSelector1$DropDownListSubSites": game_data.get("SubSiteId", ""),
            #"ctl00$MainContentPlaceHolder$GameTabs$TabsDropDownList": "javascript:void(0)", #TÄMÄ RIVI AIHEUTTI VIRHEEN
            "ctl00$MainContentPlaceHolder$GamesBasicForm$LeagueDropdownList": game_data.get("LeagueDropdownList", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$EventDropDownList": game_data.get("EventDropDownList", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$HomeTeamTextBox": game_data.get("HomeTeamTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GuestTeamTextBox": game_data.get("GuestTeamTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$AwayCheckbox": game_data.get("AwayCheckbox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameLocationTextBox": game_data.get("GameLocationTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameDateTextBox": game_data.get("GameDateTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameStartTimeTextBox": game_data.get("GameStartTimeTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameDurationTextBox": game_data.get("GameDurationTextBox", "120"),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameMaxParticipatesTextBox": game_data.get("GameMaxParticipatesTextBox", "0"),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GamePublicInfoTextBox": f"<p>{game_data.get('GamePublicInfoTextBox')}</p>",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$FeedGameDropdown": "0",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameInfoTextBox": f"<p>{game_data.get('GamePublicInfoTextbox')}</p>",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameNotificationTextBox": "",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$SaveGameButton": "Tallenna"
        }

        print(payload)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://hallinta3.jopox.fi/Admin/HockeyPox2020/Games/Game.aspx",
        }

        response = self.session.post(mod_game_url, data=payload, headers=headers)
        #logging.debug("Add game response status code: %d", response.status_code)
        #logging.debug("Add game response text: %s", response.text)
        #logging.debug("Add game response headers: %s", response.headers)

        soup = BeautifulSoup(response.text, 'html.parser')

        error_message = soup.find('textarea', {'id': 'ErrorTextBox'})
        logging.debug("Response HTML: %s", soup.prettify())
        if error_message:
            logging.error("Error message from server: %s", error_message.text)
            return error_message.text
        else:
            logging.info("Game added successfully or no error message received.")
            return "Game added successfully!"

    def add_game(self, game_data):
        add_game_url = "https://hallinta3.jopox.fi/Admin/HockeyPox2020/Games/Game.aspx"

        # Load the form page
        response = self.session.get(add_game_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": add_game_url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        })
        #logging.debug("Fetching game form page response status code: %d", response.status_code)
        #logging.debug("Fetching game form page response text: %s", response.text)

        if response.status_code != 200:
            logging.error("Failed to load form page!")
            return

        # Parse HTML and extract necessary values
        soup = BeautifulSoup(response.text, 'html.parser')
        viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
        eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]
        viewstategenerator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"]


        # Build payload
        payload = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation,
            "ctl00$MenuContentPlaceHolder$MainMenu$SiteSelector1$DropDownListSeasons": game_data.get("SeasonId", ""),
            "ctl00$MenuContentPlaceHolder$MainMenu$SiteSelector1$DropDownListSubSites": game_data.get("SubSiteId", ""),
            #"ctl00$MainContentPlaceHolder$GameTabs$TabsDropDownList": "javascript:void(0)", #TÄMÄ RIVI AIHEUTTI VIRHEEN
            "ctl00$MainContentPlaceHolder$GamesBasicForm$LeagueDropdownList": game_data.get("LeagueDropdownList", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$EventDropDownList": game_data.get("EventDropDownList", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$HomeTeamTextBox": game_data.get("HomeTeamTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GuestTeamTextBox": game_data.get("GuestTeamTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$AwayCheckbox": game_data.get("AwayCheckbox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameLocationTextBox": game_data.get("GameLocationTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameDateTextBox": game_data.get("GameDateTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameStartTimeTextBox": game_data.get("GameStartTimeTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameDurationTextBox": game_data.get("GameDurationTextBox", "120"),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameMaxParticipatesTextBox": game_data.get("GameMaxParticipatesTextBox", "0"),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GamePublicInfoTextBox": f"<p>{game_data.get('GamePublicInfoTextBox', '')}</p>",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$FeedGameDropdown": "0",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameInfoTextBox": f"""
            #    Ottelu {game_data.get('GameDateTextBox')} klo {game_data.get('GameStartTimeTextBox')}\n
            #    {game_data.get('HomeTeamTextBox')} - {game_data.get('GuestTeamTextBox')}\n
            #    {game_data.get('GameLocationTextBox')}\n\nKaikki joukkueen jäsenet""",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameNotificationTextBox": "",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$SaveGameButton": "Tallenna"
        }

        #logging.debug("Submitting game data payload: %s", payload)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://hallinta3.jopox.fi/Admin/HockeyPox2020/Games/Game.aspx",
        }

        response = self.session.post(add_game_url, data=payload, headers=headers)
        #logging.debug("Add game response status code: %d", response.status_code)
        #logging.debug("Add game response text: %s", response.text)
        #logging.debug("Add game response headers: %s", response.headers)

        soup = BeautifulSoup(response.text, 'html.parser')
        error_message = soup.find('textarea', {'id': 'ErrorTextBox'})
        if error_message:
            logging.error("Error message from server: %s", error_message.text)
            return error_message.text
        else:
            logging.info("Game added successfully or no error message received.")
            return "Game added successfully!"


    def fetch_page(self, url):
        # Lähetetään GET-pyyntö
        response = self.session.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        })
        return BeautifulSoup(response.text, 'html.parser')

    def get_last_page_number(self, soup):
        # Etsitään viimeinen sivu
        try:
            last_page = int(soup.find_all('a', class_='page')[-1].text)
        except IndexError:
            last_page = 1  # Jos sivuja ei ole, oletetaan että vain yksi sivu
        return last_page

    def scrape_jopox_games(self):
        all_j_games_url = "https://hallinta3.jopox.fi//Admin/HockeyPox2020/Games/Games.aspx"
        print("Scraping Jopox games...")

        # Haetaan ensimmäinen sivu
        soup = self.fetch_page(all_j_games_url)
        last_page = self.get_last_page_number(soup)

        print(f"Total pages: {last_page}")

        jopox_games = []  # Kerätään peli-info listaan

        # Haetaan pelit ensimmäiseltä sivulta
        rows = soup.find_all('tr', id=lambda x: x and x.startswith('MainContentPlaceHolder_GamesList1_GamesListView_GameRow_'))
        for row in rows:
            game_data = {}
            # Pvm (päivämäärä ja aika)
            pvm_td = row.find_all('td')[1]
            pvm_full = pvm_td.text.strip()
            game_data['pvm'] = pvm_full.split(' ')[0]  # Päivämäärä
            game_data['aika'] = pvm_full.split(' ')[1]  # Kellonaika

            # Yhdistetään päivämäärä ja kellonaika sortable_date-kenttään (muoto YYYY-MM-DD HH:MM)
            sortable_date_str = f"{game_data['pvm']} {game_data['aika']}"
            game_data['sortable_date'] = datetime.strptime(sortable_date_str, '%d.%m.%Y %H:%M').strftime('%Y-%m-%d %H:%M')

            # Paikka
            paikka_td = row.find_all('td')[2]
            game_data['paikka'] = paikka_td.text.strip()

            # Joukkueet
            joukkueet_td = row.find_all('td')[3]
            game_data['joukkueet'] = joukkueet_td.find('a').text.strip()
            game_data['uid'] = joukkueet_td.find('a')['href'].split('=')[1]


            jopox_games.append(game_data)

        # Käydään läpi kaikki jäljellä olevat sivut
        for page in range(2, last_page + 1):
            print(f"Processing page {page}")
            page_url = f"https://hallinta3.jopox.fi//Admin/HockeyPox2020/Games/Games.aspx?Page={page}"
            soup = self.fetch_page(page_url)

            rows = soup.find_all('tr', id=lambda x: x and x.startswith('MainContentPlaceHolder_GamesList1_GamesListView_GameRow_'))
            for row in rows:
                game_data = {}
                # Pvm (päivämäärä ja aika)
                pvm_td = row.find_all('td')[1]
                pvm_full = pvm_td.text.strip()
                game_data['pvm'] = pvm_full.split(' ')[0]  # Päivämäärä
                game_data['aika'] = pvm_full.split(' ')[1]  # Kellonaika

                # Yhdistetään päivämäärä ja kellonaika sortable_date-kenttään (muoto YYYY-MM-DD HH:MM)
                sortable_date_str = f"{game_data['pvm']} {game_data['aika']}"
                game_data['sortable_date'] = datetime.strptime(sortable_date_str, '%d.%m.%Y %H:%M').strftime('%Y-%m-%d %H:%M')

                # Paikka
                paikka_td = row.find_all('td')[2]
                game_data['paikka'] = paikka_td.text.strip()

                # Joukkueet
                joukkueet_td = row.find_all('td')[3]
                game_data['joukkueet'] = joukkueet_td.find('a').text.strip()
                game_data['uid'] = joukkueet_td.find('a')['href'].split('=')[1]
                
                jopox_games.append(game_data)

        return jopox_games  # Palautetaan kerätyt pelitiedot

    def j_game_details(self, j_game_id):

        try:
            j_game_url = f"https://hallinta3.jopox.fi//Admin/HockeyPox2020/Games/Game.aspx?gId={j_game_id}"
            print ('j_game_url:', j_game_url)
            response = self.session.get(j_game_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Referer": j_game_url,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                })
        
            soup = BeautifulSoup(response.text, 'html.parser')

            print('parsing...')
            #save parsed data to log
            #logging.debug("Parsing game details: %s", soup)

            league_dropdown = soup.find('select', {'id': 'LeagueDropdownList'})
            if league_dropdown:
                league_selected_tag = league_dropdown.find('option', selected=True)
                league_selected = league_selected_tag.text.strip() if league_selected_tag else ''
                league_options = [option.text.strip() for option in league_dropdown.find_all('option') if not option.get('selected')]
                print('found league options')
            else:
                league_selected = ''
                league_options = []
                print('league dropdown not found')
            event_selected_tag = soup.find('select', {'id': 'EventDropDownList'}).find('option', selected=True)
            event_selected = event_selected_tag.text.strip() if event_selected_tag else ''
            event_options = [option.text.strip() for option in soup.find('select', {'id': 'EventDropDownList'}).find_all('option') if not option.get('selected')]
            print('found event options')
            SiteNameLabel_tag = soup.find('span', {'id': 'MainContentPlaceHolder_GamesBasicForm_SitenameLabel'})
            SiteNameLabel = SiteNameLabel_tag.text.strip() if SiteNameLabel_tag else ''
            print('found sitename')
            HomeTeamTextbox_tag = soup.find('input', {'id': 'HomeTeamTextBox'})
            HomeTeamTextbox = HomeTeamTextbox_tag.get('value').strip() if HomeTeamTextbox_tag else ''
            print('found hometeam')
            AwayCheckbox_tag = soup.find('input', {'id': 'AwayCheckbox'})
            AwayCheckbox = AwayCheckbox_tag.get('checked') if AwayCheckbox_tag else False
            AwayCheckbox = True if AwayCheckbox else False
            print('found awaycheckbox')
            guest_team_tag = soup.find('input', {'id': 'GuestTeamTextBox'})
            guest_team = guest_team_tag.get('value').strip() if guest_team_tag else ''
            print('found guestteam')
            game_location_tag = soup.find('input', {'id': 'GameLocationTextBox'})
            game_location = game_location_tag.get('value').strip() if game_location_tag else ''
            print('found location')
            game_date_tag = soup.find('input', {'id': 'GameDateTextBox'})
            game_date = game_date_tag.get('value').strip() if game_date_tag else ''
            print('found date')
            game_start_time_tag = soup.find('input', {'id': 'GameStartTimeTextBox'})
            game_start_time = game_start_time_tag.get('value').strip() if game_start_time_tag else ''
            print('found start time')
            game_duration_tag = soup.find('input', {'id': 'GameDurationTextBox'})
            game_duration = game_duration_tag.get('value').strip() if game_duration_tag else ''
            print('found duration')
            game_public_info_tag = soup.find('textarea', {'id': 'GamePublicInfoTextBox'})
            game_public_info = game_public_info_tag.text.strip() if game_public_info_tag else ''
            print('found public info')
            # Return the parsed data
            return {
                "league_selected": league_selected,
                "league_options": league_options,
                "event_selected": event_selected,
                "event_options": event_options,
                "SiteNameLabel": SiteNameLabel,
                "HomeTeamTextbox": HomeTeamTextbox,
                "guest_team": guest_team,
                "AwayCheckbox": AwayCheckbox,
                "game_location": game_location,
                "game_date": game_date,
                "game_start_time": game_start_time,
                "game_duration": game_duration,
                "game_public_info": game_public_info
            }
        
        except Exception as e:
            logging.error("Error parsing game details: %s", e)
            raise e
        