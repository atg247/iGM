import os
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
import re
from ics import Calendar
from models.user import db, User
from flask import session
import json





# Configure logging to a file
    
class JopoxScraper:
    def __init__(self, user_id, username, password):
#       self.login_url = "https://s-kiekko-app.jopox.fi/login"
        self.user = db.session.get(User, user_id)
        self.login_url = self.user.jopox_login_url
        self.admin_login_url = self.login_url.replace('/login', '/adminlogin')
        self.base_url = "https://hallinta3.jopox.fi//Admin/HockeyPox2020/Games/Games.aspx"
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.cookies = None
        self.last_login_time = None
        self.event_validation_data = None

        self.load_session_from_flask()

    def save_session_to_flask(self):
        """Tallentaa istunnon evästeet ja validointitiedot Flask-sessioniin"""
        session["jopox_cookies"] = json.dumps(self.session.cookies.get_dict())
        session["jopox_validation"] = json.dumps(self.event_validation_data)
        session["jopox_last_login"] = self.last_login_time.isoformat() if self.last_login_time else None

    def load_session_from_flask(self):
        """Lataa aiemmin tallennetun istunnon evästeet ja validointitiedot Flask-sessionista"""
        if "jopox_cookies" in session:
            self.session.cookies.update(json.loads(session["jopox_cookies"]))
        if "jopox_validation" in session:
            self.event_validation_data = json.loads(session["jopox_validation"])
        if "jopox_last_login" in session:
            self.last_login_time = datetime.fromisoformat(session["jopox_last_login"])

    def get_event_validation(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
        eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]
        viewstategenerator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"]
        return {
        '__VIEWSTATE': viewstate,
        '__EVENTVALIDATION': eventvalidation,
        '__VIEWSTATEGENERATOR': viewstategenerator
        }

    def login(self):
        url = self.login_url
        response = self.session.get(url)
        event_validation_data = self.get_event_validation(response)
        
        login_payload = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": event_validation_data['__VIEWSTATE'],
            "__VIEWSTATEGENERATOR": event_validation_data['__VIEWSTATEGENERATOR'],
            "__EVENTVALIDATION": event_validation_data['__EVENTVALIDATION'],            "UsernameTextBox": self.username,
            "UsernameTextBox": self.username,            
            "PasswordTextBox": self.password,
            "LoginButton": "Kirjaudu"
        }
        logging.debug("sending login data")
        response = self.session.post(self.login_url, data=login_payload)
        if response.status_code == 200:
            logging.info("login(): Login successful!")
            self.cookies = self.session.cookies
            logging.info("Cookies after login: %s", self.cookies)
            self.event_validation_data = event_validation_data
            self.last_login_time = datetime.now()

            self.save_session_to_flask()

            return True

        else:
            logging.error("Login failed!")
            return False
        
    def is_session_valid(self):
        if "jopox_last_login" not in session:
            return False
        
        last_login_time = datetime.fromisoformat(session["jopox_last_login"])
        session_duration = datetime.now() - last_login_time

        return session_duration < timedelta(hours=1)  # Assume session is valid for 1 hour

    def ensure_logged_in(self):
        if not self.is_session_valid():
            logging.info("Session is not valid, logging in again...")
            return self.login()

        logging.info("Ensure_logged_in: Session is still valid!")
        return True
    
    def access_admin(self):
        logging.info("Accessing admin...")
        if not self.is_session_valid():
            logging.warning("Session is not valid, logging in again...")
            if not self.login():
                logging.error("login() failed!")
                return False
        
        response = self.session.get(self.admin_login_url, cookies=self.cookies)
        logging.info("get to admin_login_url with cookies: %s", self.cookies)
        if response.status_code == 200:
            logging.info("Admin access successful!")
            return True
        else:
            logging.error("Admin access failed!")
            return False

    def login_for_credentials(self):    
        url = self.login_url
        response = self.session.get(url)
        event_validation_data = self.get_event_validation(response)
        
        login_payload = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": event_validation_data['__VIEWSTATE'],
            "__VIEWSTATEGENERATOR": event_validation_data['__VIEWSTATEGENERATOR'],
            "__EVENTVALIDATION": event_validation_data['__EVENTVALIDATION'],            "UsernameTextBox": self.username,
            "UsernameTextBox": self.username,
            "PasswordTextBox": self.password,
            "LoginButton": "Kirjaudu"
        }
        response = self.session.post(self.login_url, data=login_payload)
        #logging.info("Login attempt payload: %s", login_payload)
        #logging.info("Login response status code: %d", response.status_code)
        #logging.info("Login response text: %s", response.text)

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
                    
            #logging.info("Cookies after login: %s", self.session.cookies)
            return jopox_credentials
    
        else:
            logging.error("Login failed!")
            return False    

    def modify_game(self, game_data, uid):
        mod_game_url = f"https://hallinta3.jopox.fi//Admin/HockeyPox2020/Games/Game.aspx?gId={uid}"
        url = mod_game_url
        # Load the form page
        response = self.session.get(mod_game_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": mod_game_url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        })
        logging.info("Fetching game form page response status code: %d", response.status_code)
        #logging.info("Fetching game form page response text: %s", response.text)

        if response.status_code != 200:
            logging.error("Failed to load form page!")
            return
        logging.info('modify_game(): fetching event validation data...')

        # Parse HTML and extract necessary values
        event_validation_data = self.get_event_validation(response)            
        logging.info("Event validation data: %s", event_validation_data)
        # Build payload
        payload = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": event_validation_data['__VIEWSTATE'],
            "__VIEWSTATEGENERATOR": event_validation_data['__VIEWSTATEGENERATOR'],
            "__EVENTVALIDATION": event_validation_data['__EVENTVALIDATION'],            "UsernameTextBox": self.username,
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
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameMaxParticipatesTextBox": game_data.get("GameMaxParticipatesTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GamePublicInfoTextBox": f"<p>{game_data.get('GamePublicInfoTextBox')}</p>",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$FeedGameDropdown": "0",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameInfoTextBox": f"<p>{game_data.get('GamePublicInfoTextbox')}</p>",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameNotificationTextBox": "",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$SaveGameButton": "Tallenna"
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://hallinta3.jopox.fi/Admin/HockeyPox2020/Games/Game.aspx",
        }

        response = self.session.post(mod_game_url, data=payload, headers=headers)
        #logging.info("Add game response status code: %d", response.status_code)
        #logging.info("Add game response text: %s", response.text)
        #logging.info("Add game response headers: %s", response.headers)

        soup = BeautifulSoup(response.text, 'html.parser')

        error_message = soup.find('textarea', {'id': 'ErrorTextBox'})

        if error_message:
            logging.error("Error message from server: %s", error_message.text)
            return error_message.text
        else:
            logging.info("Game added successfully or no error message received.")
            return "Game added successfully!"

    def add_game(self, game_data, game):
        add_game_url = "https://hallinta3.jopox.fi/Admin/HockeyPox2020/Games/Game.aspx"

        # Load the form page
        response = self.session.get(add_game_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": add_game_url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        })
        #logging.info("Fetching game form page response status code: %d", response.status_code)
        #logging.info("Fetching game form page response text: %s", response.text)

        if response.status_code != 200:
            logging.error("Failed to load form page!")
            return

        # Parse HTML and extract necessary values
        event_validation_data = self.get_event_validation(response)
        team_name = game.get('Team Name')            
        HomeTeamTextBox = self.homeTeamTextBox(response, team_name)

        # Build payload
        payload = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": event_validation_data['__VIEWSTATE'],
            "__VIEWSTATEGENERATOR": event_validation_data['__VIEWSTATEGENERATOR'],
            "__EVENTVALIDATION": event_validation_data['__EVENTVALIDATION'],            
            "UsernameTextBox": self.username,
            "ctl00$MenuContentPlaceHolder$MainMenu$SiteSelector1$DropDownListSeasons": game_data.get("SeasonId", ""),
            "ctl00$MenuContentPlaceHolder$MainMenu$SiteSelector1$DropDownListSubSites": game_data.get("SubSiteId", ""),
            #"ctl00$MainContentPlaceHolder$GameTabs$TabsDropDownList": "javascript:void(0)", #TÄMÄ RIVI AIHEUTTI VIRHEEN
            "ctl00$MainContentPlaceHolder$GamesBasicForm$LeagueDropdownList": game_data.get("LeagueDropdownList", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$EventDropDownList": game_data.get("EventDropDownList", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$HomeTeamTextBox": HomeTeamTextBox,
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GuestTeamTextBox": game_data.get("GuestTeamTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$AwayCheckbox": game_data.get("AwayCheckbox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameLocationTextBox": game_data.get("GameLocationTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameDateTextBox": game_data.get("GameDateTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameStartTimeTextBox": game_data.get("GameStartTimeTextBox", ""),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameDurationTextBox": game_data.get("GameDurationTextBox", "120"),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameMaxParticipatesTextBox": game_data.get("GameMaxParticipatesTextBox", "0"),
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GamePublicInfoTextBox": f"""
            {game.get('Home Team')} - {game.get('Away Team')}<br>
            {'Pienpeli' if game.get('Small Area Game') == '1' else 'Ison kentän peli'}<br>
            <br>
            {game.get('Location')}<br>
            <br>
            <br>                    
            Kokoontuminen tuntia ennen ottelun alkua.<br>
            <br>
            Joukkue:
            <br>
            """,#Tähän kenttään logiikka, jolla määritetään tarvitaanko toimitsijoita ja niin, että huomioi pienpelit,
            "ctl00$MainContentPlaceHolder$GamesBasicForm$FeedGameDropdown": "0",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameInfoTextBox": f"""
            Ottelu {game.get('GameDateTextBox')} klo {game.get('GameStartTimeTextBox')}<br>
            {game.get('HomeTeamTextBox')} - {game.get('GuestTeamTextBox')}<br>
            {game.get('GameLocationTextBox')}<br>
            <br>
            {'Pienpeli' if game.get('Small Area Game') == '1' else 'Ison kentän peli'}<br>
            <br>                    
            Kokoontuminen tuntia ennen ottelun alkua.<br>
            <br>
            Joukkue:
            <br>
            """,#Tähän kenttään logiikka, jolla määritetään tarvitaanko toimitsijoita ja niin, että huomioi pienpelit
            "ctl00$MainContentPlaceHolder$GamesBasicForm$GameNotificationTextBox": "",
            "ctl00$MainContentPlaceHolder$GamesBasicForm$SaveGameButton": "Tallenna"
        }

        logging.info("Submitting game data payload: %s", payload)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": f"{add_game_url}",
        }

        response = self.session.post(add_game_url, data=payload, headers=headers)
        logging.info("Add game response status code: %d", response.status_code)

        soup = BeautifulSoup(response.text, 'html.parser')
        error_message = soup.find('textarea', {'id': 'ErrorTextBox'})
        if error_message:
            logging.error("Error message from server: %s", error_message.text)
            return error_message.text
        else:
            logging.info("Game added successfully or no error message received.")
            return "Game added successfully!"
    
    def homeTeamTextBox(self, response, team_name):
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            SiteNameLabel_tag = soup.find('span', {'id': 'MainContentPlaceHolder_GamesBasicForm_SitenameLabel'})
            SiteNameLabel = SiteNameLabel_tag.text.strip() if SiteNameLabel_tag else ''
            logging.info("SiteNameLabel: %s", SiteNameLabel)

            #remove anything in brackets from SiteNameLabel
            SiteNameLabel = re.sub(r'\([^)]*\)', '', SiteNameLabel)
            logging.info("SiteNameLabel: %s", SiteNameLabel)

            #check which are the common parts of SiteNameLabel and team_name
            common_part = os.path.commonprefix([SiteNameLabel, team_name])
            logging.info("Common part: %s", common_part)
            #remove common part from team_name
            HomeTeamTextBox = team_name.replace(common_part, '')
            logging.info("HomeTeamTextBox: %s", HomeTeamTextBox)
            return HomeTeamTextBox
        except Exception as e:
            logging.error("Error parsing home_team: %s", e)



    def scrape_jopox_games(self):
        if not self.ensure_logged_in():
            return []
        all_j_games_url = "https://hallinta3.jopox.fi//Admin/HockeyPox2020/Games/Games.aspx"
        
        # Haetaan ensimmäinen sivu
        soup = self.fetch_page(all_j_games_url)
        last_page = self.get_last_page_number(soup)

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

    def j_game_details(self, j_game_id):

        try:
            j_game_url = f"https://hallinta3.jopox.fi//Admin/HockeyPox2020/Games/Game.aspx?gId={j_game_id}"
            response = self.session.get(j_game_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Referer": j_game_url,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                })
        
            soup = BeautifulSoup(response.text, 'html.parser')

            league_dropdown = soup.find('select', {'id': 'LeagueDropdownList'})
            if league_dropdown:
                league_selected_tag = league_dropdown.find('option', selected=True)
                league_selected = league_selected_tag.text.strip() if league_selected_tag else ''
                league_options = [option.text.strip() for option in league_dropdown.find_all('option') if not option.get('selected')]
            
            else:
                league_selected = ''
                league_options = []
            
            event_selected_tag = soup.find('select', {'id': 'EventDropDownList'}).find('option', selected=True)
            event_selected = event_selected_tag.text.strip() if event_selected_tag else ''
            event_options = [option.text.strip() for option in soup.find('select', {'id': 'EventDropDownList'}).find_all('option') if not option.get('selected')]
            
            SiteNameLabel_tag = soup.find('span', {'id': 'MainContentPlaceHolder_GamesBasicForm_SitenameLabel'})
            SiteNameLabel = SiteNameLabel_tag.text.strip() if SiteNameLabel_tag else ''
            
            HomeTeamTextbox_tag = soup.find('input', {'id': 'HomeTeamTextBox'})
            HomeTeamTextbox = HomeTeamTextbox_tag.get('value').strip() if HomeTeamTextbox_tag else ''
            
            AwayCheckbox_tag = soup.find('input', {'id': 'AwayCheckbox'})
            AwayCheckbox = AwayCheckbox_tag.get('checked') if AwayCheckbox_tag else False
            AwayCheckbox = True if AwayCheckbox else False
            
            guest_team_tag = soup.find('input', {'id': 'GuestTeamTextBox'})
            guest_team = guest_team_tag.get('value').strip() if guest_team_tag else ''
            
            game_location_tag = soup.find('input', {'id': 'GameLocationTextBox'})
            game_location = game_location_tag.get('value').strip() if game_location_tag else ''
            
            game_date_tag = soup.find('input', {'id': 'GameDateTextBox'})
            game_date = game_date_tag.get('value').strip() if game_date_tag else ''
            
            game_start_time_tag = soup.find('input', {'id': 'GameStartTimeTextBox'})
            game_start_time = game_start_time_tag.get('value').strip() if game_start_time_tag else ''
            
            game_duration_tag = soup.find('input', {'id': 'GameDurationTextBox'})
            game_duration = game_duration_tag.get('value').strip() if game_duration_tag else ''
            
            game_public_info_tag = soup.find('textarea', {'id': 'GamePublicInfoTextBox'})
            game_public_info = game_public_info_tag.text.strip() if game_public_info_tag else ''
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
        