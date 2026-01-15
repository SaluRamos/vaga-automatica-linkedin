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
import json

def require_admin() -> None:
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("Solicitando privilégios de administrador...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def load_options() -> dict:
    try:
        with open("private.json", "r", encoding="utf-8") as file: #developer safety
            opt = json.load(file)
    except Exception as e:
        with open("options.json", "r", encoding="utf-8") as file:
            opt = json.load(file)
    return opt

def robot(opt:dict) -> None:
    opt["driver"]["load_profile"] = False
    bot = RobotBot(opt)
    bot.start_driver()
    bot.start_actions()
    bot.solve_captcha()
    time.sleep(10000) #dar tempo de debugar
    bot.driver.quit()

def main(opt:dict) -> None:
    bot = LinkedinBot(opt)
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
    opt = load_options()
    if opt["actual_bot"] == "linkedin":
        main(opt)
    if opt["actual_bot"] == "robot":
        robot(opt)