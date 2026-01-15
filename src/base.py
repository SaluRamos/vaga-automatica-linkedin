#libs
import tensorflow as tf
import undetected_chromedriver as uc
from undetected_chromedriver import webelement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
#native libs
import os
import glob
import random
import math
import time

class Bot():

    def __init__(self, opt:dict):
        self.opt = opt
        self.driver = None
        self.actions = None
        self.mouse_mlp_model = tf.keras.models.load_model("models/mouse_mlp.keras")
        self.mx = 0
        self.my = 0
    
    def start_driver(self) -> None:
        chrome_exe_path = os.path.join(os.path.join(os.getcwd(), "bin"), "chrome-win64", "chrome.exe")
        self.driver = uc.Chrome(
            options=self.get_driver_options(),
            browser_executable_path=chrome_exe_path, # chrome com versão fixa na pasta bin
            headless=self.opt["driver"]["headless"], 
            use_subprocess=True
        )
        if not self.opt["driver"]["maximized"]:
            w = self.opt["driver"]["width"]
            h = self.opt["driver"]["height"]
            self.driver.set_window_size(w, h)

    def get_driver_options(self) -> uc.ChromeOptions:
        driver_options = uc.ChromeOptions()
        # Opções que ajudam na ocultação
        driver_options.add_argument("--disable-infobars")
        driver_options.add_argument("--disable-blink-features=AutomationControlled")
        # Desativa o Safe Browsing (que incha o arquivo Preferences com listas de URLs)
        driver_options.add_argument("--safebrowsing-disable-auto-update")
        driver_options.add_argument("--disable-features=SafeBrowsing")
        # Desativa métricas e relatórios de erro
        driver_options.add_argument("--disable-breakpad")
        driver_options.add_argument("--disable-report-whitelist")
        driver_options.add_argument("--no-pings")
        # Desativa o "Field Trials" (telemetria do Google)
        driver_options.add_argument("--disable-fext-trials")
        # Outros
        driver_options.add_argument("--remote-debugging-port=9222")
        if self.opt["driver"]["load_profile"]:
            driver_options.add_argument(f"--user-data-dir={self.get_profile_path()}")
        if self.opt["driver"]["headless"]:
            driver_options.add_argument("--headless")
        if self.opt["driver"]["auto_open_devtools"]:
            driver_options.add_argument("--auto-open-devtools-for-tabs")
        if self.opt["driver"]["maximized"]:
            driver_options.add_argument("--start-maximized")
        return driver_options

    def wait_for_page_load(self, timeout: int = 10) -> None:
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def clean_chrome_profile(self) -> None:
        profile_path = self.get_profile_path()
        # Remove arquivos temporários (.tmp) em qualquer subpasta do perfil
        tmp_files = glob.glob(os.path.join(profile_path, "**/*.tmp"), recursive=True)
        for f in tmp_files:
            try: 
                os.remove(f)
            except: 
                pass
        # Se o arquivo Preferences for maior que 50MB, algo está errado, reseta ele.
        pref_path = os.path.join(profile_path, "Default", "Preferences")
        if os.path.exists(pref_path):
            if os.path.getsize(pref_path) > 50 * 1024 * 1024: # 50MB
                try: 
                    os.remove(pref_path)
                except: 
                    pass

    def get_profile_path(self) -> str:
        return os.path.join(os.getcwd(), "chrome_profile")

    def get_dad(self, elem:webelement.WebElement, levels=1) -> webelement.WebElement:
        if levels == 0:
            return elem
        dad = elem.find_element(By.XPATH, "..")
        return self.get_dad(dad, levels - 1)

    def get_element(self, timeout:int, by:By, value:str) -> webelement.WebElement:
        if timeout == 0:
            return self.driver.find_element(by, value)
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, value)))

    def get_elements(self, timeout:int, by:By, value:str) -> webelement.WebElement:
        if timeout == 0:
            return self.driver.find_elements(by, value)
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_all_elements_located((by, value)))

    def get_url_params(self) -> dict:
        args = {}
        url_args = self.driver.current_url.split("?")[1].split("&")
        for arg in url_args:
            buffer = arg.split("=")
            name = buffer[0]
            args[name] = buffer[1]
        return args
    
    def start_actions(self) -> None:
        window_size = self.driver.get_window_size()
        width = window_size['width']
        height = window_size['height']
        self.mx = random.randrange(0, width)
        self.my = random.randrange(0, height)
        self.actions = ActionChains(self.driver)
        self.actions.move_by_offset(self.mx, self.my).perform()
        print(f"Mouse iniciado em: {self.mx}, {self.my}")

    def create_visual_cursor(self) -> None:
        script = """
        var cursor = document.createElement('div');
        cursor.id = 'selenium-cursor';
        cursor.style.position = 'fixed';
        cursor.style.zIndex = '2147483647';
        cursor.style.width = '12px';
        cursor.style.height = '12px';
        cursor.style.background = 'red';
        cursor.style.borderRadius = '50%';
        cursor.style.border = '2px solid white';
        cursor.style.pointerEvents = 'none'; // Não interfere nos cliques
        cursor.style.top = '0px';
        cursor.style.left = '0px';
        cursor.style.transition = 'all 0.05s ease-out'; // Deixa o movimento fluido
        document.body.appendChild(cursor);
        """
        self.driver.execute_script(script)

    def update_visual_cursor(self) -> None:
        script = f"""
        var cursor = document.getElementById('selenium-cursor');
        if(cursor) {{
            cursor.style.left = '{self.mx}px';
            cursor.style.top = '{self.my}px';
        }}
        """
        self.driver.execute_script(script)

    def click_element(self, elem:webelement.WebElement) -> None:
        btn_x, btn_y = elem.location_once_scrolled_into_view["x"], elem.location_once_scrolled_into_view["y"]
        bw = elem.size["width"]
        bh = elem.size["height"]
        window_size = self.driver.get_window_size()
        window_width = window_size['width']
        window_height = window_size['height']
        max_steps = 200 # Trava de segurança para não rodar infinito
        steps = 0
        while steps < max_steps:
            is_mouse_inside_btn = (btn_x <= self.mx <= btn_x + bw and btn_y <= self.my <= btn_y + bh)
            target_x = btn_x + bw/2
            target_y = btn_y + bh/2
            offset_x = (target_x - self.mx)/window_width
            offset_y = (target_y - self.my)/window_height
            #inferencia
            inp = tf.convert_to_tensor([[offset_x, offset_y, is_mouse_inside_btn]], dtype=tf.float32)
            mov_x_n, mov_y_n, click_p = self.mouse_mlp_model.predict(inp, verbose=0)
            # desnormaliza movimento
            mov_x = math.ceil(mov_x_n[0][0] * window_width)
            mov_y = math.ceil(mov_y_n[0][0] * window_height)
            # threshold de clique
            click = click_p[0][0] < 0.01
            # intenção e clamp (crome não aceita coordenadas negativas)
            intended_x = self.mx + mov_x
            intended_y = self.my + mov_y
            new_mx = max(0, min(intended_x, window_width - 1))
            new_my = max(0, min(intended_y, window_height - 1))
            adjusted_mov_x = new_mx - self.mx
            adjusted_mov_y = new_my - self.my
            #efetuar ação da IA
            print(f"{self.mx}, {self.my}, {mov_x}, {mov_y}, {is_mouse_inside_btn}, {click_p[0][0]}")
            if adjusted_mov_x != 0 or adjusted_mov_y != 0:
                self.actions.move_by_offset(adjusted_mov_x, adjusted_mov_y).perform()
            self.mx += adjusted_mov_x
            self.my += adjusted_mov_y
            self.update_visual_cursor()
            #calcular click
            if click and is_mouse_inside_btn:
                self.actions.click().perform()
                print("Click executado")
                return
            time.sleep(0.01)
        print("Click timeout")

    #melhorar isso para permitir scroll para cima também
    def scroll_element(self, element:webelement.WebElement, min_steps:int=3, max_steps:int=6) -> None:
        print(f"START SCROLLING")
        total_height = self.driver.execute_script("return arguments[0].scrollHeight", element)
        min_walk = int(total_height/max_steps)
        max_walk = int(total_height/min_steps)
        # print(f"min walk {min_walk}, max walk {max_walk}, height {total_height}")
        current_pos = 0
        while current_pos < total_height - 1:
            step = random.randint(min_walk, max_walk)
            # print(f"add {step}, current {current_pos}")
            current_pos += step
            if current_pos > total_height:
                current_pos = total_height - 1
            self.driver.execute_script(f"arguments[0].scrollTo({{top: {current_pos}, behavior: 'smooth'}});", element)
            time.sleep(random.uniform(0.3, 0.5))
        print(f"FINISH SCROLLING")
