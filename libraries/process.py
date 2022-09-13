from libraries.common import log_message, browser
from config import OUTPUT_FOLDER, tabs_dict
from libraries.nytimes.nytimes import Nytimes

class Process():
    
    def __init__(self, credentials: dict):
        log_message("Initialization")

        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_popups": 0,
            "directory_upgrade": True,
            "download.default_directory": OUTPUT_FOLDER,
            "plugins.always_open_pdf_externally": True,
            "download.prompt_for_download": False
        }

        browser.open_available_browser(preferences = prefs)
        browser.set_window_size(1920, 1080)
        browser.maximize_browser_window()

        nytimes = Nytimes(browser, {"url": "https://www.nytimes.com/"})
        tabs_dict["NY Times"] = len(tabs_dict)
        nytimes.access_nytimes()
        self.nytimes = nytimes

    def start(self):
        """
        main
        """
        self.nytimes.initial_search()
        self.nytimes.filter_page()
        self.nytimes.find_dates()
        self.nytimes.get_articles_information()
        self.nytimes.create_excel()

    
    def finish(self):
        log_message("DW Process Finished")
        browser.close_browser()