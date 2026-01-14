import undetected_chromedriver as uc
from undetected_chromedriver import webelement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from langdetect import detect
import time
import os
import ollama
import json
import logging
import random
from enum import Enum
from src.params import LinkedInParams
import glob
import ctypes
import sys

driver = None
actions = None
job_url = "https://www.linkedin.com/jobs/search/?"
is_premium = True
opt = {}

class InputType(Enum):
    NUMERIC = 1
    DROPDOWN = 2 #used in fieldset too

def require_admin() -> None:
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("Solicitando privilégios de administrador...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def get_profile_path() -> str:
    return os.path.join(os.getcwd(), "chrome_profile")

def clean_profile() -> None:
    profile_path = get_profile_path()
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

def get_driver_options() -> uc.ChromeOptions:
    driver_options = uc.ChromeOptions()
    # Desativa o Safe Browsing (que incha o arquivo Preferences com listas de URLs)
    driver_options.add_argument("--safebrowsing-disable-auto-update")
    driver_options.add_argument("--disable-features=SafeBrowsing")
    # Desativa métricas e relatórios de erro
    driver_options.add_argument("--disable-breakpad")
    driver_options.add_argument("--disable-report-whitelist")
    driver_options.add_argument("--no-pings")
    # Desativa o "Field Trials" (telemetria do Google)
    driver_options.add_argument("--disable-fext-trials")
    driver_options.add_argument("--remote-debugging-port=9222")
    driver_options.add_argument(f"--user-data-dir={get_profile_path()}")
    if opt["driver"]["headless"]:
        driver_options.add_argument("--headless")
    if opt["driver"]["auto_open_devtools"]:
        driver_options.add_argument("--auto-open-devtools-for-tabs")
    if opt["driver"]["maximized"]:
        driver_options.add_argument("--start-maximized")
    return driver_options

def get_dad(elem, levels=1) -> webelement.WebElement:
    if levels == 0:
        return elem
    dad = elem.find_element(By.XPATH, "..")
    return get_dad(dad, levels - 1)

def get_url_params() -> dict:
    args = {}
    url_args = driver.current_url.split("?")[1].split("&")
    for arg in url_args:
        buffer = arg.split("=")
        name = buffer[0]
        args[name] = buffer[1]
    return args

def get_actual_job_id() -> str:
    return get_url_params()["currentJobId"]

def answer_linkedin_question(question:str, language:str, input_type:InputType, options_list:list=[]) -> str:
    system_prompt = None
    if input_type == InputType.NUMERIC:
        key = f"{language}_numeric_prompt"
        system_prompt = opt["ai"][key].format(en_private_info=opt["ai"]["en_private_info"], pt_private_info=opt["ai"]["pt_private_info"])
    elif input_type == InputType.DROPDOWN:
        key = f"{language}_dropdown_prompt"
        system_prompt = opt["ai"][key].format(options_list=str(options_list))       
    try:
        if opt["print"]["system_prompt"]:
            print(f"SYSTEM PROMPT: {system_prompt}")
        response = ollama.chat(
            model=opt["ai"]["model"],
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': question},
            ]
        )
        return response['message']['content']
    except Exception as e:
        return f"Erro ao chamar o Ollama: {e}"

def scroll_element(element, steps=5):
    print(f"START SCROLLING ELEM {element} in {steps} steps")
    global driver
    total_height = driver.execute_script("return arguments[0].scrollHeight", element)
    target = total_height
    current_pos = 0
    while current_pos < target:
        step = random.randint(50, 150) # Deslocamento variável
        current_pos += step
        driver.execute_script(f"arguments[0].scrollTo(0, {current_pos});", element)
        time.sleep(random.uniform(0.05, 0.3)) # Pausa humana
    print(f"FINISH SCROLLING ELEM {element}")

def click_element(elem) -> None:
    global actions
    # driver.execute_script("arguments[0].click();", elem) #isso é facilmente detectado
    actions.move_to_element(elem).click().perform()

def verify_login() -> bool:
    global driver
    #se estiver logado, deve ser redirecionado para o feed
    if driver.current_url != "https://www.linkedin.com/":
        driver.get("https://www.linkedin.com") 
    time.sleep(1)
    if "/feed" in driver.current_url:
        return True
    return False

def subscribe_to_all_jobs():
    global is_premium, opt
    actual_page = 1
    actual_job = 1
    submited_jobs = 0
    while True:
        time.sleep(3) # espera página carregar
        #encontra e scrolla o container da lista de jobs
        jobs = driver.find_elements(By.CSS_SELECTOR, "div[data-job-id]")
        print(f"jobs antes de scrolar = {len(jobs)}")
        jobs_list = get_dad(jobs[0], 3)
        jobs_scroll = get_dad(jobs_list)
        scroll_element(jobs_scroll)
        jobs = driver.find_elements(By.CSS_SELECTOR, "div[data-job-id]") #encontra os jobs de novo
        print(f"jobs após scrolar = {len(jobs)}")

        #encontra o container das informações do job
        job_info = driver.find_element(By.CLASS_NAME, "jobs-search__job-details--wrapper")

        #se inscreve em todos os jobs
        for job in jobs:
            print("------------------------------")
            print(f"ACTUAL JOB {actual_job}, SUBMITED JOBS {submited_jobs}")
            click_element(job)
            time.sleep(2) #espera carregar infos
            #verificar se já candidatou
            subscribe_btn = None
            try:
                subscribe_btn = driver.find_element(By.ID, "jobs-apply-button-id")
            except:
                if not subscribe_btn.is_enabled():
                    print("LINKEDIN ENCONTRA-SE BLOQUEADO POR EXCESSO DE TENTATIVAS")
                    raise Exception("APLICAÇÕES ESGOTADAS")
                print("IGNORANDO JOB, JÁ SE CANDIDATOU")
                actual_job = actual_job + 1
                continue #ignora job
            subscribe_btn_text = subscribe_btn.find_element(By.XPATH, "span").text
            is_simplified = subscribe_btn_text == "Candidatura simplificada"
            print(f"is_simplified = {is_simplified}")
            if not is_simplified:
                print("IGNORANDO JOB, NÃO POSSUI CANDIDATURA SIMPLIFICADA")
                actual_job = actual_job + 1
                continue #ignora job
            #scrolla as informações
            scroll_element(job_info)
            #coletar dados do job
            title = driver.find_element(By.CSS_SELECTOR, ".t-24.job-details-jobs-unified-top-card__job-title").text
            print(f"title = {title}")
            id = get_url_params()["currentJobId"]
            print(f"id = {id}")
            if is_premium:
                try:
                    amount_applicants_text = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, "jobs-premium-applicant-insights__list-item"))).text
                    amount_applicants = int(amount_applicants_text.split()[0].replace(".", ""))
                    print(f"amount_applicants = {amount_applicants}")
                except Exception as e:
                    print("NÃO FOI ENCONTRADO amount_applicants")
                    is_premium = False
                    
            details = driver.find_element(By.CLASS_NAME, "jobs-description__content").text
            if opt["print"]["details"]:
                print(f"details = {details}")
            details_lang = detect(details)
            is_english = False
            is_portuguese = False
            if details_lang == 'en':
                is_english = True
            elif details_lang == 'pt':
                is_portuguese = True
            print(f"details_lang = '{details_lang}'")
            print("---TERMINOU DE OBTER DADOS---")
            # lógica para se deve ou não candidatar
            must_apply = False
            if is_simplified:
                if opt["filters"]["apply_to_english_vacancy"] and is_english:
                    must_apply = True
                if opt["filters"]["apply_to_portuguese_vacancy"] and is_portuguese:
                    must_apply = True
            #inscrever no job
            if must_apply:
                click_element(subscribe_btn)
                time.sleep(3)
                actual_apply_page = 1
                has_progress_bar = True
                try:
                    progress_bar = driver.find_element(By.CLASS_NAME, "artdeco-completeness-meter-linear__progress-element")
                except Exception as e:
                    has_progress_bar = False
                    print("NÃO POSSUI PROGRESS BAR! VAGA SEM PERGUNTAS")
                while True:
                    print(f"ACTUAL APPLY PAGE: {actual_apply_page}")
                    if actual_apply_page > 2:
                        answer_questions(details_lang)

                    if actual_apply_page == 2 or not has_progress_bar:
                        select_resume(is_portuguese, is_english)
                    try:
                        subscribe_next = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, '//*[@aria-label="Avançar para próxima etapa"]')))
                        click_element(subscribe_next)
                        print("NEXT PAGE")
                        actual_apply_page = actual_apply_page + 1
                        time.sleep(0.5)
                    except Exception as e:
                        if has_progress_bar:
                            review = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, '//*[@aria-label="Revise sua candidatura"]')))
                            click_element(review)
                            print("REVISANDO CANDIDATURA")
                            time.sleep(0.5)
                        send = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, '//*[@aria-label="Enviar candidatura"]')))
                        click_element(send)
                        print("FINALIZANDO")
                        time.sleep(2)
                        try:
                            close_btn = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button[data-test-modal-close-btn]")))
                            click_element(close_btn)
                        except Exception as e:
                            pass
                        print("CONCLUIDO")
                        break
                #só deve esperar se efetuou uma candidatura
                print(f'ESPERANDO {opt["filters"]["sleep_time_between_applications"]} segundos até candidatar-se a próxima vaga')
                time.sleep(opt["filters"]["sleep_time_between_applications"])
            else:
                print("IGNORANDO JOB, NÃO É SIMPLIFICADO ou NÃO É PORTUGUES/INGLÊS")
            submited_jobs = submited_jobs + 1
            actual_job = actual_job + 1
        #encontra o botão de próxima página e pressiona, se não encontrar quebra o loop
        try:
            next_page = driver.find_element(By.XPATH, '//*[@aria-label="Ver próxima página"]')
            click_element(next_page)
            actual_page = actual_page + 1
            print("------------------------------")
            print(f"AVANÇANDO PARA A PÁGINA {actual_page}")
        except Exception as e:
            logging.error("Falha ao avançar página", exc_info=True)
            break
    print("CANDIDATURAS FINALIZADAS")

def answer_questions(details_lang:str) -> None:
    global driver
    try:
        preference_premium_checkbox = driver.find_element(By.NAME, "jobDetailsEasyApplyTopChoiceCheckbox")
        print("PREFERENCE PREMIUM CHECKBOX FOUND")
        return #nothing to do in this page
    except Exception as e:
        print("NOT IN PREMIUM PREFERENCE PAGE")
    #tratando inputs
    try:
        inputs = WebDriverWait(driver, 3).until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'artdeco-text-input--input')))
        print(f"QUANTIDADE DE INPUT's ENCONTRADOS: {len(inputs)}")
        for select in inputs:
            question = get_dad(select).text
            print(f"QUESTION: {question}")

            #not always using ai here because of dumb questions like: Do you have Knowledge of relational and non-relational databases and versioning of Git? (answer with int number duh)
            
            if "Número de celular" in question:
                select.clear()
                select.send_keys(opt["private_info"]["cellphone"])
            elif "Há quantos anos" in question:
                select.clear()
                select.send_keys(opt["private_info"]["base_years_of_experience"])
            else:
                answer = answer_linkedin_question(question, details_lang, InputType.NUMERIC)
                clean_answer = answer.strip().replace(".", "")
                print(f"CLEAN ANSWER: '{clean_answer}'")
                select.send_keys(clean_answer)
                select.clear()
                select.send_keys(clean_answer)
        print("INPUT's PREENCHIDOS")
    except Exception as e:
        pass
    #tratando dropdowns
    try:
        selects = WebDriverWait(driver, 3).until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'fb-dash-form-element__select-dropdown')))
        print(f"QUANTIDADE DE DROPDOWN's ENCONTRADOS: {len(selects)}")
        for select in selects:
            dropdown = Select(select)
            question = get_dad(select).find_element(By.XPATH, "label").text
            dropdown_options = [opt.text.lower() for opt in dropdown.options if "selecionar" not in opt.text.lower()]
            print(f"QUESTION: {question}")
            print(f"DROPDOWN OPTIONS: {dropdown_options}")
            answer = answer_linkedin_question(question, details_lang, InputType.DROPDOWN, dropdown_options)
            clean_answer = answer.strip().replace(".", "").lower()
            print(f"CLEAN ANSWER: '{clean_answer}'")
            if clean_answer not in dropdown_options:
                print("answer not in dropdown_options")
            try:
                dropdown.select_by_index(dropdown_options.index(clean_answer) + 1)
            except Exception as e:
                print("erro na resposta da ia, selecionando index 1")
                dropdown.select_by_index(1)
        print("DROPDOWN's PREENCHHIDOS")
    except Exception as e:
        pass
    #tratando fieldset
    try:
        fieldsets = driver.find_elements(By.CSS_SELECTOR, "fieldset[data-test-form-builder-radio-button-form-component='true']")
        print(f"QUANTIDADE DE FIELDSET's ENCONTRADOS: {len(fieldsets)}")
        for fieldset in fieldsets:
            question = fieldset.find_element(By.XPATH, "legend").text
            labels = fieldset.find_elements(By.TAG_NAME, "label")
            options_map = {l.text.lower().strip(): l for l in labels}
            options_list = list(options_map.keys())
            print(f"QUESTION: {question}")
            print(f"RADIO OPTIONS: {options_list}")
            answer = answer_linkedin_question(question, details_lang, InputType.DROPDOWN, options_list)
            clean_answer = answer.strip().replace(".", "").lower()
            print(f"CLEAN ANSWER: '{clean_answer}'")
            if clean_answer in options_map:
                click_element(options_map[clean_answer])
            else:
                print("erro na resposta da ia, selecionando index 0")
                click_element(labels[0])
    except Exception as e:
        pass

def select_resume(is_portuguese:bool, is_english:bool) -> None:
    global driver
    try:
        resumes = WebDriverWait(driver, 3).until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".ui-attachment.jobs-document-upload-redesign-card__container")))
        print(f"CURRICULOS ENCONTRADOS: {len(resumes)}")
        for resume in resumes:
            if is_portuguese and "PORTUGUES" in resume.text:
                print("SELECTED PORTUGUESE RESUME")
                if "Selecionado" not in resume.get_attribute("aria-label"):
                    click_element(resume)
                break
            if is_english and "INGLES" in resume.text:
                print("SELECTED ENGLISH RESUME")
                if "Selecionado" not in resume.get_attribute("aria-label"):
                    click_element(resume)
                break
        time.sleep(0.2)
    except Exception as e:
        logging.error("Falha ao selecionar curriculo", exc_info=True)

def main():
    global driver, actions, job_url, opt
    require_admin()

    try:
        with open("private.json", "r", encoding="utf-8") as file: #developer safety
            opt = json.load(file)
    except Exception as e:
        with open("options.json", "r", encoding="utf-8") as file:
            opt = json.load(file)
    print(f"loaded options = {opt}")

    chrome_exe_path = os.path.join(os.path.join(os.getcwd(), "bin"), "chrome-win64", "chrome.exe")
    print(f"chrome exe path: {chrome_exe_path}")

    clean_profile()
    driver = uc.Chrome(
        options=get_driver_options(),
        browser_executable_path=chrome_exe_path, # chrome com versão fixa na pasta bin
        headless=opt["driver"]["headless"], 
        use_subprocess=True
    )
    if not opt["driver"]["maximized"]:
        w = opt["driver"]["width"]
        h = opt["driver"]["height"]
        driver.set_window_size(h, w)

    actions = ActionChains(driver)
    
    is_logged = False
    while not is_logged:
        is_logged = verify_login()
    print("IS LOGGED!")

    params = []
    params.append(LinkedInParams.keyword_param(opt["filters"]["keyword"]))
    if opt["filters"]["use_job_model"]:
        params.append(LinkedInParams.remote_param(opt["filters"]["filter_remote_job"], opt["filters"]["filter_hibrid_job"], opt["filters"]["filter_onsite_job"]))
    if opt["filters"]["use_timelapse"]:
        params.append(LinkedInParams.timelapse_param(604800))
    if opt["filters"]["use_geoid"]:
        params.append(LinkedInParams.geoid_param(opt["filters"]["geoid"]))
    if opt["filters"]["use_max_distance"]:
        params.append(LinkedInParams.distance_param(opt["filters"]["max_distance_in_miles"]))
    if opt["filters"]["in_my_chain"]:
        params.append(LinkedInParams.in_my_chain_param())
    if opt["filters"]["low_candidates"]:
        params.append(LinkedInParams.low_candidates_param())
    if opt["filters"]["use_experience_level"]:
        params.append(LinkedInParams.experience_level_param(
            opt["filters"]["internship"], opt["filters"]["assistent"], opt["filters"]["junior"], 
            opt["filters"]["pleno_and_senior"], opt["filters"]["director"], opt["filters"]["executive"]
        ))
    # Parâmetros fixos/obrigatórios
    params.extend([
        LinkedInParams.simplified_param(),
        LinkedInParams.origin_param(),
        LinkedInParams.ignore_cache_param()
    ])

    final_query = "&".join(params)
    job_url = f"{job_url}{final_query}"
    print(f"url is: {job_url}")
    driver.get(job_url)

    try:
        subscribe_to_all_jobs()
    except Exception as e:
        logging.error("Falha genérica sem tratamento", exc_info=True)
        time.sleep(1000000) #dar tempo de debugar

    driver.quit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n" + "="*50)
        print(f"ERRO CRÍTICO DURANTE A EXECUÇÃO: {e}")
        import traceback
        traceback.print_exc()
        print("="*50)
    finally:
        print("\nScript finalizado.")
        input("Pressione ENTER para fechar esta janela...") # Impede o fechamento automático