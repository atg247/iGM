import requests
from bs4 import BeautifulSoup
import logging


# Configure logging to a file
logging.basicConfig(
    filename="jopox_scraper.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode='w'
)

class JopoxScraper:
    def __init__(self, username, password):
        self.login_url = "https://s-kiekko-app.jopox.fi/login"
        self.admin_login_url = "https://s-kiekko-app.jopox.fi/adminlogin"
        self.base_url = "https://hallinta3.jopox.fi//Admin/HockeyPox2020/Games/Games.aspx"
        self.session = requests.Session()
        self.username = username
        self.password = password

        logging.basicConfig(
        filename="jopox_scraper.log",
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode='w'
        )


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

    def access_admin(self):
        response = self.session.get(self.admin_login_url)
        logging.debug("Admin access response status code: %d", response.status_code)
        #logging.debug("Admin access response text: %s", response.text)
        logging.debug("Cookies after admin access: %s", self.session.cookies)

        if response.status_code == 200:
            logging.info("Admin access successful!")
            return True
        else:
            logging.error("Admin access failed!")
            return False

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


    
