#modules
from src.base import Bot
#libs
from selenium.webdriver.common.by import By
#native libs
import time

class IndeedBot(Bot):

    def __init__(self, opt:dict):
        super().__init__(opt)

    def wait_login(self) -> None:
        self.driver.get("https://br.indeed.com/?from=gnav-homepage")
        while True:
            try:
                elem = self.get_element(1, By.XPATH, "/html/body/div[1]/header/nav/div/div/div/div[2]/div[2]/div[2]/a")
                break
            except Exception as e:
                time.sleep(1)
        print("IS LOGGED!")
    
    def subscribe_to_all_jobs(self) -> None:
        self.driver.get("https://br.indeed.com/?from=gnav-homepage")
        self.wait_for_page_load()