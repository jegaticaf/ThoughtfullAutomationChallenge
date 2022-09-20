from libraries.common import log_message, files, convert_string_to_date
from config import OUTPUT_FOLDER, search_phrase, month_number, news_section, tabs_dict
import os, time
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta

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
        
        self.browser.click_element('//button[@data-test-id = "search-button"]')
        search_bar = self.browser.find_element('//input[@data-testid = "search-input"]')
        self.browser.input_text_when_element_is_visible('//input[@data-testid = "search-input"]', search_phrase)
        search_bar.send_keys(Keys.ENTER) 
        log_message("End - Initial Search of '{}'".format(search_phrase))   

    def filter_page(self):
        """
        Set the filters for the search
        """
        log_message("Start - Set the Filters")

        self.browser.click_element('//button[descendant::text()="Section"]')

        #Here, it tries to find the section that was entered as a environmental variable
        try:
            self.browser.find_element('//ul[@tabindex=-1]//label[descendant::text()="{}"]/input'.format(news_section))
            self.browser.click_element('//ul[@tabindex=-1]//label[descendant::text()="{}"]/input'.format(news_section))
            log_message("Filtered the news by Section '{}'".format(news_section))
        except Exception as e:
            #If it couldn't find that section, it defaults to "Any"
            log_message("Couldn't find Section '{}'. Filtered by 'Any'".format(news_section))
            self.browser.click_element('//ul[@tabindex=-1]//label[descendant::text()="Any"]/input')
        
        #This try-except block is there just in case the "Cookies pop-up" shows up
        try:
            hide_button = self.browser.find_element('//button[@data-testid="expanded-dock-btn-selector"]')
            self.browser.click_element(hide_button)
            log_message("Clicked the button to hide the pop-up")
            self.browser.click_element('//button[@data-testid="GDPR-accept"]')
            log_message("Clicked the accept button, if it is still there")
        except:
            #In case the pop-up doesn't show up, sends the message and keeps going
            log_message("Didn't find the pop-up")  

        self.browser.click_element('//select[@data-testid="SearchForm-sortBy"]')
        self.browser.click_element('//option[@value="newest"]')

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

        #Transforms both todays date and the start date to the format required
        if search_date.day < 10:
            start_date_day = "0{}".format(search_date.day)
        else:
            start_date_day = search_date.day

        if search_date.month < 10:
            start_date_month = "0{}".format(search_date.month)
        else:
            start_date_month = search_date.month

        start_date_year = search_date.year
        search_date_start_value = str(start_date_month)+"/"+str(start_date_day)+"/"+str(start_date_year)

        if datetime.now().day < 10:
            end_date_day = "0{}".format(datetime.now().day)
        else:
            end_date_day = search_date.day

        if datetime.now().month < 10:
            end_date_month = "0{}".format(datetime.now().month)
        else:
            end_date_month = search_date.month

        end_date_year = datetime.now().year
        search_date_end_value = str(end_date_month)+"/"+str(end_date_day)+"/"+str(end_date_year)

        self.browser.click_element('//button[descendant::text()="Date Range"]')
        self.browser.click_element('//button[@value="Specific Dates"]')
        self.browser.find_element('//div[@data-testid="search-day-picker"]//input[@data-testid="DateRange-startDate"]')
        self.browser.input_text_when_element_is_visible('//div[@data-testid="search-day-picker"]//input[@data-testid="DateRange-startDate"]', search_date_start_value)
        if search_date.day == 31:
            self.browser.click_element('//div[@data-testid="search-day-picker"]//div[text()="28"]') 
        else:
            self.browser.click_element('//div[@data-testid="search-day-picker"]//div[text()="{}"]'.format(search_date.day)) 
        self.browser.input_text_when_element_is_visible('//div[@data-testid="search-day-picker"]//input[@data-testid="DateRange-endDate"]', search_date_end_value) 
        self.browser.click_element('//div[@data-testid="search-day-picker"]//div[text()="{}"]'.format(datetime.now().day)) 
        #This sleep is to make sure the filters update the site, and it loads only the correct information
        time.sleep(5)
        
        #Clicks the "Show more" button while it exists
        #Since we've already done the date filter, this will give us back all the results
        data_range = True
        size = 0
        all_articles = ""
        while data_range:
            try:
                #Clicks the "Show more" button while it exists
                self.browser.click_element('//button[@data-testid="search-show-more-button"]')
            except:
                #Once the "Show more" button no longer exists, it changes the value
                data_range = False

        try:
            #Once it has loaded all the news in the given timeframe, checks the date individually
            #Appends all the articles that are between that timeframe
            all_articles = self.browser.find_elements('//ol[@data-testid="search-results"]/li[@data-testid]')
        except:
            #This means that there are no articles with this parameters
            log_message("Found no articles with this filters")
        
        size = len(all_articles)
        log_message("Loaded {} articles".format(size))
        articles_processed = 0
        continue_appending = True
        while size > articles_processed and continue_appending:
            article_date_text = self.browser.find_element('xpath:.//span[@data-testid="todays-date"]',parent=all_articles[articles_processed]).text
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
                
        log_message("Found {} articles in the specified timeframe".format(len(self.articles_container)))

        log_message("End - Find the Articles")
        
    def get_articles_information(self):
        """
        Obtain the information of all the articles
        """
        log_message("Start - Get the Articles Information")

        #With the articles found with the last method, grabs all the information of each new
        for article_container in self.articles_container:
            self.browser.switch_window(locator = self.browser.get_window_handles()[tabs_dict["NY Times"]])
            article_title = self.browser.find_element('xpath:.//h4',parent=article_container).text
            article_date = self.browser.find_element('xpath:.//span[@data-testid="todays-date"]',parent=article_container).text
            
            #This two try-except blocks check if the article has a description and image
            #If it hasn't, it sends a message to the log, and keeps going
            try:
                article_description = self.browser.find_element('xpath:.//a/p',parent=article_container).text
            except Exception as e:
                #This means that the article has no description
                article_description = ""
                log_message("Article {} has no description".format(article_title))               
            
            try:
                article_image = self.browser.find_element('xpath:.//img',parent=article_container).get_attribute("src")
            except Exception as e:
                #This means that the article has no image
                article_image = ""    
                log_message("Article {} has no image".format(article_title))

            keyword_count = len(article_title.split(search_phrase)) - 1
            keyword_count = keyword_count + len(article_description.split(search_phrase)) -1

            has_money = False
            money_in_title = "$" in article_title or "dollar" in article_title or "USD" in article_title
            money_in_description = "$" in article_description or "dollar" in article_description or "USD" in article_description
            if money_in_title:
                sign_in_title = article_title.split("$")
                dollar_in_title = article_title.split("dollar")
                usd_in_title = article_title.split("USD")
                if len(sign_in_title) > 1 and has_money == False:
                    number_after_sign = sign_in_title[1].split(" ")
                    try:
                        number_after_sign =number_after_sign[0].replace(",", "")
                        float(number_after_sign)
                        has_money = True
                    except:
                        #This means that, even if they found the keyword, it's not a number, so it shouldn't be counted
                        print("{} has '$' in the title, but it isn't a number".format(article_title))                    
                if len(dollar_in_title) > 1 and has_money == False:
                    number_before_dollar = dollar_in_title[0].split(" ")
                    try:
                        float(number_before_dollar[-1].replace(",", ""))
                        has_money = True
                    except:
                        #This means that, even if they found the keyword, it's not a number, so it shouldn't be counted
                        print("{} has 'dollar' in the title, but it isn't a number".format(article_title)) 
                if len(usd_in_title) > 1 and has_money == False:
                    number_before_usd = usd_in_title[1].split(" ")
                    try:
                        float(number_before_usd[-1].replace(",", ""))
                        has_money = True
                    except:
                        #This means that, even if they found the keyword, it's not a number, so it shouldn't be counted
                        print("{} has 'USD' in the title, but it isn't a number".format(article_title)) 
            elif money_in_description:
                sign_in_description = article_description.split("$")
                dollar_in_description = article_description.split("dollar")
                usd_in_description = article_description.split("USD")
                if len(sign_in_description) > 1 and has_money == False:
                    number_after_sign = sign_in_description[1].split(" ")
                    try:
                        number_after_sign = number_after_sign[0].replace(",", "")
                        float(number_after_sign)
                        has_money = True
                    except:
                        #This means that, even if they found the keyword, it's not a number, so it shouldn't be counted
                        print("{} has '$' in the description, but it isn't a number".format(article_title)) 
                if len(dollar_in_description) > 1 and has_money == False:
                    number_before_dollar = dollar_in_description[0].split(" ")
                    try:
                        float(number_before_dollar[-1].replace(",", ""))
                        has_money = True
                    except:
                        #This means that, even if they found the keyword, it's not a number, so it shouldn't be counted
                        print("{} has 'dollar' in the description, but it isn't a number".format(article_title)) 
                if len(usd_in_description) > 1 and has_money == False:
                    number_before_usd = usd_in_description[0].split(" ")
                    try:
                        float(number_before_usd[-1].replace(",", ""))
                        has_money = True
                    except:
                        #This means that, even if they found the keyword, it's not a number, so it shouldn't be counted
                        print("{} has 'USD' in the description, but it isn't a number".format(article_title)) 

            #Once it has all the information, opens the image in a new window and downloads it
            if article_image != "":
                self.browser.execute_javascript("window.open()")
                self.browser.switch_window(locator = "NEW")
                tabs_dict["Article Image"] = len(tabs_dict)
                self.browser.go_to(article_image)
                image_name = article_image.split("/")[-1].split("?")[0]

                with open('{}/{}'.format(OUTPUT_FOLDER, image_name), 'wb') as file:
                    image = self.browser.find_element("//img")
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
        files.create_workbook(path = os.path.join(OUTPUT_FOLDER, "News.xlsx"))
        files.create_worksheet(name = "Results", content= None, exist_ok = True, header = False)
        files.append_rows_to_worksheet(self.results_data, name = "Results", header = True, start= None)
        files.remove_worksheet(name = "Sheet")
        files.save_workbook(path = None)
        files.close_workbook()
        log_message("End - Create Excel")
