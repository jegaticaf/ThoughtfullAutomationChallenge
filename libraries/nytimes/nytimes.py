from libraries.common import log_message, act_on_element, files, convert_string_to_date
from config import OUTPUT_FOLDER, search_phrase, month_number, news_section, tabs_dict
import time
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

class Nytimes():

    def __init__(self, rpa_selenium_instance, credentials:dict):
        self.browser = rpa_selenium_instance
        self.nytimes_url = credentials["url"]
        self.articles_container = []
        self.results_data = []
        self.images_links = []

    def access_nytimes(self):
        """
        Access the NY Times from the browser
        """
        log_message("Start - Access NY Times")
        self.browser.go_to(self.nytimes_url)
        log_message("End - Access NY Times")

    def initial_search(self):
        """
        Search in the page with a Keyword given
        """
        log_message("Start - Initial Search of '{}'".format(search_phrase))
        
        act_on_element('//button[@data-test-id = "search-button"]', "click_element")
        search_bar = act_on_element('//input[@data-testid = "search-input"]', "find_element")
        self.browser.input_text_when_element_is_visible('//input[@data-testid = "search-input"]', search_phrase)
        search_bar.send_keys(Keys.ENTER) 
        log_message("End - Initial Search of '{}'".format(search_phrase))   

    def filter_page(self):
        """
        Set the filters for the search
        """
        log_message("Start - Set the Filters")

        act_on_element('//button[descendant::text()="Section"]', "click_element")

        #Here, it tries to find the section that was entered as a environmental variable
        #If it couldn't find that section, it defaults to "Any"
        try:
            act_on_element('//ul[@tabindex=-1]//label[descendant::text()="{}"]/input'.format(news_section), "find_element")
            act_on_element('//ul[@tabindex=-1]//label[descendant::text()="{}"]/input'.format(news_section), "click_element")
            log_message("Filtered the news by Section '{}'".format(news_section))
        except Exception as e:
            log_message("Couldn't find Section '{}'. Filtered by 'Any'".format(news_section))
            act_on_element('//ul[@tabindex=-1]//label[descendant::text()="Any"]/input', "click_element")
        
        act_on_element('//select[@data-testid="SearchForm-sortBy"]', "click_element")
        act_on_element('//option[@value="newest"]', "click_element")

        #This is to give it time to the website to load with the new filters
        time.sleep(5)

        log_message("End - Set the Filters")

    def find_dates(self):
        """
        Find the articles that meet the specified date criteria
        """
        log_message("Start - Find the Articles")

        search_date = datetime.now()

        #Given the environmental variable month_number, creates the latest date to check
        if int(month_number) > 1:
            search_date = search_date - timedelta(days= (int(month_number)-1)*30)
        else:
            search_date = search_date - timedelta(days=datetime.now().day)

        #Checks if the last article is in the desired timeframe
        #If it is then clicks the button to search for more articles, until it finds one that isn't
        data_range = True

        while data_range:
            time.sleep(5)
            try:
                act_on_element('//button[text()= "ACCEPT"]', "click_element", 2)
                log_message("Clicked the pop-up message")
            except:
                log_message("There was no pop-up message to close")

            articles_data = act_on_element('//span[@data-testid="todays-date"]', "find_elements")
            
            last_article_date = convert_string_to_date(articles_data[-1].text)

            if last_article_date > search_date:
                act_on_element('//button[@data-testid="search-show-more-button"]', "click_element")
            else:
                data_range = False

        #Once it has loaded all the news in the given timeframe, checks the date individually
        #Appends all the articles that are between that timeframe
        all_articles = act_on_element('//ol[@data-testid="search-results"]/li[@data-testid]', "find_elements")
        size = len(all_articles)
        log_message("Found {} articles in the specified timeframe".format(len(self.articles_container)))
        
        articles_processed = 0
        continue_appending = True
        while size > articles_processed and continue_appending:
            article_date_text = all_articles[articles_processed].find_element_by_xpath('.//span[@data-testid="todays-date"]').text
            article_date_elements = article_date_text.split(" ")
            
            if article_date_elements[1] == "ago":
                article_date = datetime.now()
            else:
                article_date = convert_string_to_date(article_date_text)
            
            if article_date > search_date:
                self.articles_container.append(all_articles[articles_processed])
                articles_processed += 1
            else:
                continue_appending = False


        log_message("End - Find the Articles")
        
    def get_articles_information(self):
        """
        Obtain the information of all the articles
        """
        log_message("Start - Get the Articles Information")

        #With the articles found with the last method, grabs all the information of each new
        for article_container in self.articles_container:
            self.browser.switch_window(locator = self.browser.get_window_handles()[tabs_dict["NY Times"]])
            article_title = article_container.find_element_by_xpath('.//h4').text
            article_date = article_container.find_element_by_xpath('.//span[@data-testid="todays-date"]').text
            article_description = ""
            try:
                article_description = article_container.find_element_by_xpath('.//a/p').text
            except Exception as e:
                log_message("Article {} has no description".format(article_title))
            
            try:
                article_image = article_container.find_element_by_xpath('.//img').get_attribute("src")
            except Exception as e:
                log_message("Article {} has no image".format(article_title))
                article_image = ""                       


            keyword_count = len(article_title.split(search_phrase)) - 1
            keyword_count = keyword_count + len(article_description.split(search_phrase)) -1

            has_money = False
            money_in_title = "$" in article_title or "dollar" in article_title or "USD" in article_title
            money_in_description = "$" in article_description or "dollar" in article_description or "USD" in article_description
            if money_in_title or money_in_description:
                has_money = True

            #Once it has all the information, opens the image in a new window and downloads it
            if article_image != "":
                self.browser.execute_javascript("window.open()")
                self.browser.switch_window(locator = "NEW")
                tabs_dict["Article Image"] = len(tabs_dict)
                self.browser.go_to(article_image)
                image_name = article_image.split("/")[-1].split("?")[0]

                with open('{}/{}'.format(OUTPUT_FOLDER, image_name), 'wb') as file:
                    image = act_on_element("//img", "find_element")
                    file.write(image.screenshot_as_png)
                
                log_message("Succesfully downloaded {}".format(image_name))
            else:
                image_name = ""
                log_message("Couldn't find image for {}".format(article_title))

            #Finally, appends all the information to a list of dictionaries
            self.results_data.append({"Title":article_title, "Date": article_date, "Description": article_description,
            "Image Link": article_image, "Keyword count": keyword_count, "Has Currency": has_money, "Image Name": image_name})

        log_message("End - Get the Articles Information")        

    def create_excel(self):
        """
        Create the Excel file with the information
        """
        #Given the list of dictionaries, create the Excel with all the information
        log_message("Start - Create Excel")
        files.create_workbook(path = "{}/News.xlsx".format(OUTPUT_FOLDER))
        files.create_worksheet(name = "Results", content= None, exist_ok = True, header = False)
        files.append_rows_to_worksheet(self.results_data, name = "Results", header = True, start= None)
        files.remove_worksheet(name = "Sheet")
        files.save_workbook(path = None)
        files.close_workbook()
        log_message("End - Create Excel")