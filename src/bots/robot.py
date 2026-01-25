#modules
from src.base import Bot
#libs
from selenium.webdriver.common.by import By

class RobotBot(Bot):

    def __init__(self, opt:dict):
        super().__init__(opt)

    def solve_captcha(self):
        #https://bot.sannysoft.com/
        #https://pixelscan.net/
        #https://nowsecure.nl
        self.driver.get("https://neal.fun/not-a-robot/")
        self.wait_for_page_load()
        #level 1
        checkbox = self.get_element(5, By.CLASS_NAME, "captcha-box-checkbox-input")
        self.click_element(checkbox)