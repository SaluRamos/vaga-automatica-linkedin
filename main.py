import undetected_chromedriver as uc
from undetected_chromedriver import webelement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from langdetect import detect
import time
import os
import ollama
import json
from enum import Enum

driver = None
job_url = "https://www.linkedin.com/jobs/search/?"
is_premium = True
opt = {}

# UTILS

class InputType(Enum):
    NUMERIC = 1
    DROPDOWN = 2 #used in fieldset too

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

def get_actual_job_id():
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

# URL PARAMS

def remote_param(remote_job:bool, hibrid:bool, onsite:bool) -> str:
    final_filter_remote = "f_WT="
    addition = ""
    if (sum([remote_job, hibrid, onsite]) > 1):
        addition = "%2C"
    if (remote_job):
        final_filter_remote = final_filter_remote + "2"
    if (hibrid):
        final_filter_remote = final_filter_remote + f"{addition}3"
    if (onsite):
        final_filter_remote = final_filter_remote + f"{addition}1"
    return final_filter_remote

def timelapse_param(seconds:int) -> str:
    return f"f_TPR=r{seconds}"

def simplified_param() -> str: #candidatura simplificada
    return "f_AL=true"

def keyword_param(value:str) -> str:
    return f'keywords={value.replace(" ", "%20")}'

def geoid_param(value:str) -> str:
    return f"geoId={value}"

def distance_param(miles:int) -> str:
    return f"distance={miles}"

def origin_param() -> str:
    return "origin=JOB_SEARCH_PAGE_JOB_FILTER"

def ignore_cache_param() -> str:
    return "refresh=true"

def in_my_chain_param() -> str: #pessoas da minha rede no linkedin
    return "f_JIYN=true"

def low_candidates_param() -> str: #vagas com menos de 5 candidatos
    return "f_EA=true"

# def filter_by_sector_param() -> str:
#     # 4 = desenvolvimento de software
#     # 118 = segurança de redes de computadores
#     return "f_I=4%2C118" 

def experience_level_param(internship:bool, assistent:bool, junior:bool, pleno_and_senior:bool, director:bool, executive:bool) -> str:
    buf = []
    if internship:       buf.append("1")
    if assistent:        buf.append("2")
    if junior:           buf.append("3")
    if pleno_and_senior: buf.append("4")
    if director:         buf.append("5")
    if executive:        buf.append("6")
    if not buf:
        raise Exception("No experience selected!")
    final = "%2C".join(buf)
    return f"f_E={final}"

# BACKEND

def verify_login() -> bool:
    global driver
    driver.get("https://www.linkedin.com") #se estiver logado, deve ser redirecionado para o feed
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
        driver.execute_script("arguments[0].scrollTo({top: arguments[0].scrollHeight/3, behavior: 'smooth'});", jobs_scroll)
        time.sleep(0.5)
        driver.execute_script("arguments[0].scrollTo({top: (arguments[0].scrollHeight/3)*2, behavior: 'smooth'});", jobs_scroll)
        time.sleep(0.5)
        driver.execute_script("arguments[0].scrollTo({top: arguments[0].scrollHeight, behavior: 'smooth'});", jobs_scroll)
        time.sleep(0.5)
        jobs = driver.find_elements(By.CSS_SELECTOR, "div[data-job-id]") #encontra os jobs de novo
        print(f"jobs após scrolar = {len(jobs)}")

        #encontra o container das informações do job
        job_info = driver.find_element(By.CLASS_NAME, "jobs-search__job-details--wrapper")

        #se inscreve em todos os jobs
        for job in jobs:
            try:
                close_btn = WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button[data-test-modal-close-btn]")))
                driver.execute_script("arguments[0].click();", close_btn)
            except Exception as e:
                pass

            print("------------------------------")
            print(f"ACTUAL JOB {actual_job}, SUBMITED JOBS {submited_jobs}")
            driver.execute_script("arguments[0].click();", job)
            time.sleep(2) #espera carregar infos
            #verificar se já candidatou
            try:
                subscribe_btn = driver.find_element(By.ID, "jobs-apply-button-id")
            except:
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
            driver.execute_script("arguments[0].scrollTo({top: arguments[0].scrollHeight/2, behavior: 'smooth'});", job_info)
            time.sleep(0.5)
            driver.execute_script("arguments[0].scrollTo({top: arguments[0].scrollHeight, behavior: 'smooth'});", job_info)
            time.sleep(0.5)
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
            #inscrever no job
            if is_simplified and (is_english or is_portuguese):
                driver.execute_script("arguments[0].click();", subscribe_btn)
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
                        driver.execute_script("arguments[0].click();", subscribe_next)
                        print("NEXT PAGE")
                        actual_apply_page = actual_apply_page + 1
                        time.sleep(0.5)
                    except Exception as e:
                        if has_progress_bar:
                            review = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, '//*[@aria-label="Revise sua candidatura"]')))
                            driver.execute_script("arguments[0].click();", review)
                            print("REVISANDO CANDIDATURA")
                            time.sleep(0.5)
                        send = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, '//*[@aria-label="Enviar candidatura"]')))
                        driver.execute_script("arguments[0].click();", send)
                        print("FINALIZANDO")
                        time.sleep(2)
                        try:
                            close_btn = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button[data-test-modal-close-btn]")))
                            driver.execute_script("arguments[0].click();", close_btn)
                        except Exception as e:
                            pass
                        print("CONCLUIDO")
                        break
            else:
                print("IGNORANDO JOB, NÃO É SIMPLIFICADO ou NÃO É PORTUGUES/INGLÊS")
            submited_jobs = submited_jobs + 1
            actual_job = actual_job + 1
            time.sleep(opt["required"]["sleep_time_between_applications"])
        #encontra o botão de próxima página e pressiona, se não encontrar quebra o loop
        try:
            next_page = driver.find_element(By.XPATH, '//*[@aria-label="Ver próxima página"]')
            driver.execute_script("arguments[0].click();", next_page)
            actual_page = actual_page + 1
            print("------------------------------")
            print(f"AVANÇANDO PARA A PÁGINA {actual_page}")
        except Exception as e:
            print(e)
            break
    print("INSCRIÇÕES FINALIZADAS")

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
                driver.execute_script("arguments[0].click();", options_map[clean_answer])
            else:
                print("erro na resposta da ia, selecionando index 0")
                driver.execute_script("arguments[0].click();", labels[0])
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
                    driver.execute_script("arguments[0].click();", resume)
                break
            if is_english and "INGLES" in resume.text:
                print("SELECTED ENGLISH RESUME")
                if "Selecionado" not in resume.get_attribute("aria-label"):
                    driver.execute_script("arguments[0].click();", resume)
                break
        time.sleep(0.2)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    try:
        with open("private.json", "r", encoding="utf-8") as file: #developer safety
            opt = json.load(file)
    except Exception as e:
        with open("options.json", "r", encoding="utf-8") as file:
            opt = json.load(file)
    print(f"loaded options = {opt}")

    project_path = os.getcwd()
    profile_path = os.path.join(project_path, "chrome_profile")
    driver_options = uc.ChromeOptions()
    driver_options.add_argument(f"--user-data-dir={profile_path}") #required
    driver_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    if opt["driver"]["headless"]:
        driver_options.add_argument("--headless")
    if opt["driver"]["auto_open_devtools"]:
        driver_options.add_argument("--auto-open-devtools-for-tabs")
    if opt["driver"]["maximized"]:
        driver_options.add_argument("--start-maximized")

    driver = uc.Chrome(options=driver_options, headless=False, use_subprocess=False)
    if not opt["driver"]["maximized"]:
        w = opt["driver"]["width"]
        h = opt["driver"]["height"]
        driver.set_window_size(h, w)

    
    is_logged = False
    while not is_logged:
        is_logged = verify_login()
    print("IS LOGGED!")

    params = []
    params.append(keyword_param(opt["required"]["keyword"]))
    if opt["optional"]["use_job_model"]:
        params.append(remote_param(opt["optional"]["filter_remote_job"], opt["optional"]["filter_hibrid_job"], opt["optional"]["filter_onsite_job"]))
    if opt["optional"]["use_timelapse"]:
        params.append(timelapse_param(604800))
    if opt["optional"]["use_geoid"]:
        params.append(geoid_param(opt["optional"]["geoid"]))
    if opt["optional"]["use_max_distance"]:
        params.append(distance_param(opt["optional"]["max_distance_in_miles"]))
    if opt["optional"]["in_my_chain"]:
        params.append(in_my_chain_param())
    if opt["optional"]["low_candidates"]:
        params.append(low_candidates_param())
    if opt["optional"]["use_experience_level"]:
        params.append(experience_level_param(
            opt["optional"]["internship"], opt["optional"]["assistent"], opt["optional"]["junior"], 
            opt["optional"]["pleno_and_senior"], opt["optional"]["director"], opt["optional"]["executive"]
        ))
    # Parâmetros fixos/obrigatórios
    params.extend([
        simplified_param(),
        origin_param(),
        ignore_cache_param()
    ])

    final_query = "&".join(params)
    job_url = f"{job_url}{final_query}"
    print(f"url is: {job_url}")
    driver.get(job_url)

    try:
        subscribe_to_all_jobs()
    except Exception as e:
        print(e)
        time.sleep(1000000) #dar tempo de debugar

    driver.quit()