import os

OUTPUT_FOLDER = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), 'output')
tabs_dict = {}
search_phrase = os.environ.get("Search Phrase", "Queen")
news_section = os.environ.get("Category or Section", "New York")
month_number = os.environ.get("Number of Months", "1")