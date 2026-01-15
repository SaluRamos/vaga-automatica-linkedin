#modules
from src.linkedin import LinkedinBot
from src.robot import RobotBot
#libs
from selenium.webdriver.common.by import By
#native libs
import time
import ctypes
import sys
import logging

def require_admin() -> None:
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("Solicitando privilégios de administrador...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def robot_test() -> None:
    bot = RobotBot()
    bot.load_options()
    bot.clean_chrome_profile()
    bot.start_driver()
    #https://bot.sannysoft.com/
    #https://pixelscan.net/
    #https://nowsecure.nl
    bot.driver.get("https://neal.fun/not-a-robot/")
    #level 1
    checkbox = bot.get_element(5, By.CLASS_NAME, "captcha-box-checkbox-input")
    time.sleep(10000)
    bot.driver.quit()

def main() -> None:
    bot = LinkedinBot()
    bot.load_options()
    bot.clean_chrome_profile()
    bot.start_driver()
    bot.start_actions()
    bot.verify_login()
    bot.driver.get(bot.get_jobsearch_url())
    try:
        bot.subscribe_to_all_jobs()
    except Exception as e:
        logging.error("Falha genérica sem tratamento", exc_info=True)
        time.sleep(1000000) #dar tempo de debugar
    bot.driver.quit()

if __name__ == "__main__":
    main()