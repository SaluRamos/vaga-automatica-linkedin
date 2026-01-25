#modules
from src.bots.linkedin import LinkedinBot
from src.bots.robot import RobotBot
from src.bots.indeed import IndeedBot
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

def indeed(opt:dict) -> None:
    opt["driver"]["width"] = 1600
    opt["driver"]["height"] = 900
    bot = IndeedBot(opt)
    bot.start_driver()
    bot.wait_login()
    bot.subscribe_to_all_jobs()
    time.sleep(1_000_000) #dar tempo de debugar
    bot.driver.quit()

def robot(opt:dict) -> None:
    opt["driver"]["width"] = 1200
    opt["driver"]["height"] = 700
    opt["driver"]["load_profile"] = False
    bot = RobotBot(opt)
    bot.start_driver()
    bot.solve_captcha()
    time.sleep(1_000_000) #dar tempo de debugar
    bot.driver.quit()

def linkedin(opt:dict) -> None:
    opt["driver"]["width"] = 1200
    opt["driver"]["height"] = 700
    bot = LinkedinBot(opt)
    bot.start_driver()
    bot.wait_login()
    bot.subscribe_to_all_jobs()
    time.sleep(1_000_000) #dar tempo de debugar
    bot.driver.quit()

if __name__ == "__main__":
    opt = load_options()
    if opt["actual_bot"] == "linkedin":
        linkedin(opt)
    elif opt["actual_bot"] == "robot":
        robot(opt)
    elif opt["actual_bot"] == "indeed":
        indeed(opt)
    else:
        raise Exception("No 'actual_bot' config recognized")