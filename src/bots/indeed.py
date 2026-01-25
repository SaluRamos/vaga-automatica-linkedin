#modules
from src.base import Bot
#libs
from selenium.webdriver.common.by import By

class IndeedBot(Bot):

    def __init__(self, opt:dict):
        super().__init__(opt)

    def subscribe_to_all_jobs(self):
        self.driver.get("https://br.indeed.com/")
        self.wait_for_page_load()