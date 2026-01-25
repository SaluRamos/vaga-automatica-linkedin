#modules
from src.base import Bot
from src.params import LinkedInParams
from src.enums import InputType
#libs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from langdetect import detect
import ollama
#native libs
import time
import logging

class LinkedinBot(Bot):

    def __init__(self, opt:dict):
        super().__init__(opt)

    def get_actual_job_id(self) -> str:
        return self.get_url_params()["currentJobId"]
    
    def get_jobsearch_url(self) -> str:
        params = []
        params.append(LinkedInParams.keyword_param(self.opt["linkedin"]["keyword"]))
        if self.opt["linkedin"]["use_job_model"]:
            params.append(LinkedInParams.remote_param(self.opt["linkedin"]["filter_remote_job"], self.opt["linkedin"]["filter_hibrid_job"], self.opt["linkedin"]["filter_onsite_job"]))
        if self.opt["linkedin"]["use_timelapse"]:
            params.append(LinkedInParams.timelapse_param(604800))
        if self.opt["linkedin"]["use_geoid"]:
            params.append(LinkedInParams.geoid_param(self.opt["linkedin"]["geoid"]))
        if self.opt["linkedin"]["use_max_distance"]:
            params.append(LinkedInParams.distance_param(self.opt["linkedin"]["max_distance_in_miles"]))
        if self.opt["linkedin"]["in_my_chain"]:
            params.append(LinkedInParams.in_my_chain_param())
        if self.opt["linkedin"]["low_candidates"]:
            params.append(LinkedInParams.low_candidates_param())
        if self.opt["linkedin"]["use_experience_level"]:
            params.append(LinkedInParams.experience_level_param(
                self.opt["linkedin"]["internship"], self.opt["linkedin"]["assistent"], self.opt["linkedin"]["junior"], 
                self.opt["linkedin"]["pleno_and_senior"], self.opt["linkedin"]["director"], self.opt["linkedin"]["executive"]
            ))
        # Parâmetros fixos/obrigatórios
        params.extend([
            LinkedInParams.simplified_param(),
            LinkedInParams.origin_param(),
            LinkedInParams.ignore_cache_param()
        ])
        final_query = "&".join(params)
        job_url = "https://www.linkedin.com/jobs/search/?"
        job_url = f"{job_url}{final_query}"
        print(f"url is: {job_url}")
        return job_url
    
    def subscribe_to_all_jobs(self) -> None:
        self.driver.get(self.get_jobsearch_url())
        is_premium = True
        actual_page = 1
        actual_job = 1
        submited_jobs = 0
        while True:
            self.wait_for_page_load()
            #encontra e scrolla o container da lista de jobs
            jobs = self.get_elements(3, By.CSS_SELECTOR, "div[data-job-id]")
            print(f"jobs antes de scrolar = {len(jobs)}")
            jobs_scroll = self.get_dad(jobs[0], 4)
            self.scroll_element(jobs_scroll)
            jobs = self.get_elements(3, By.CSS_SELECTOR, "div[data-job-id]")
            print(f"jobs após scrolar = {len(jobs)}")
            #encontra o container das informações do job
            job_info = self.get_element(3, By.CLASS_NAME, "jobs-search__job-details--wrapper")
            #se inscreve em todos os jobs
            for job in jobs:
                print("------------------------------")
                print(f"ACTUAL JOB {actual_job}, SUBMITED JOBS {submited_jobs}")
                self.click_element(job)
                time.sleep(2) #espera carregar infos
                #verificar se já candidatou
                subscribe_btn = None
                try:
                    subscribe_btn = self.get_element(0, By.ID, "jobs-apply-button-id")
                except:
                    if subscribe_btn is not None and not subscribe_btn.is_enabled():
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
                self.scroll_element(job_info)
                #coletar dados do job
                title = self.driver.find_element(By.CSS_SELECTOR, ".t-24.job-details-jobs-unified-top-card__job-title").text
                print(f"title = {title}")
                id = self.get_url_params()["currentJobId"]
                print(f"id = {id}")
                if is_premium:
                    try:
                        amount_applicants_text = self.get_element(5, By.CLASS_NAME, "jobs-premium-applicant-insights__list-item").text
                        amount_applicants = int(amount_applicants_text.split()[0].replace(".", ""))
                        print(f"amount_applicants = {amount_applicants}")
                    except Exception as e:
                        print("NÃO FOI ENCONTRADO amount_applicants")
                        is_premium = False
                        
                details = self.driver.find_element(By.CLASS_NAME, "jobs-description__content").text
                if self.opt["print"]["details"]:
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
                    if self.opt["linkedin"]["apply_to_english_vacancy"] and is_english:
                        must_apply = True
                    if self.opt["linkedin"]["apply_to_portuguese_vacancy"] and is_portuguese:
                        must_apply = True
                #inscrever no job
                if must_apply:
                    self.click_element(subscribe_btn)
                    time.sleep(3)
                    actual_apply_page = 1
                    has_progress_bar = True
                    try:
                        progress_bar = self.driver.find_element(By.CLASS_NAME, "artdeco-completeness-meter-linear__progress-element")
                    except Exception as e:
                        has_progress_bar = False
                        print("NÃO POSSUI PROGRESS BAR! VAGA SEM PERGUNTAS")
                    while True:
                        print(f"ACTUAL APPLY PAGE: {actual_apply_page}")
                        if actual_apply_page > 2:
                            self.answer_questions(details_lang)

                        if actual_apply_page == 2 or not has_progress_bar:
                            self.select_resume(is_portuguese, is_english)
                        try:
                            subscribe_next = self.get_element(5, By.XPATH, '//*[@aria-label="Avançar para próxima etapa"]')
                            self.click_element(subscribe_next)
                            print("NEXT PAGE")
                            actual_apply_page = actual_apply_page + 1
                            time.sleep(0.5)
                        except Exception as e:
                            if has_progress_bar:
                                review = self.get_element(5, By.XPATH, '//*[@aria-label="Revise sua candidatura"]')
                                self.click_element(review)
                                print("REVISANDO CANDIDATURA")
                                time.sleep(0.5)
                            send = self.get_element(5, By.XPATH, '//*[@aria-label="Enviar candidatura"]')
                            self.click_element(send)
                            print("FINALIZANDO")
                            time.sleep(2)
                            try:
                                close_btn = self.get_element(5, By.CSS_SELECTOR, "button[data-test-modal-close-btn]")
                                self.click_element(close_btn)
                            except Exception as e:
                                pass
                            print("CONCLUIDO")
                            break
                    #só deve esperar se efetuou uma candidatura
                    print(f'ESPERANDO {self.opt["linkedin"]["sleep_time_between_applications"]} segundos até candidatar-se a próxima vaga')
                    time.sleep(self.opt["linkedin"]["sleep_time_between_applications"])
                else:
                    print("IGNORANDO JOB, NÃO É SIMPLIFICADO ou NÃO É PORTUGUES/INGLÊS")
                submited_jobs = submited_jobs + 1
                actual_job = actual_job + 1
            #encontra o botão de próxima página e pressiona, se não encontrar quebra o loop
            try:
                next_page = self.driver.find_element(By.XPATH, '//*[@aria-label="Ver próxima página"]')
                self.click_element(next_page)
                actual_page = actual_page + 1
                print("------------------------------")
                print(f"AVANÇANDO PARA A PÁGINA {actual_page}")
            except Exception as e:
                logging.error("Falha ao avançar página", exc_info=True)
                break
        print("CANDIDATURAS FINALIZADAS")

    def answer_linkedin_question(self, question:str, language:str, input_type:InputType, options_list:list=[]) -> str:
        system_prompt = None

        if input_type == InputType.NUMERIC:
            key = f"{language}_numeric_prompt"
            system_prompt = self.opt["ai"][key].format(en_private_info=self.opt["ai"]["en_private_info"], pt_private_info=self.opt["ai"]["pt_private_info"])
        elif input_type == InputType.DROPDOWN:
            key = f"{language}_dropdown_prompt"
            system_prompt = self.opt["ai"][key].format(options_list=str(options_list))

        if self.opt["print"]["system_prompt"]:
            print(f"SYSTEM PROMPT: {system_prompt}")
        response = ollama.chat(
            model=self.opt["ai"]["model"],
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': question},
            ]
        )
        return response['message']['content']

    def wait_login(self) -> None:
        self.driver.get("https://www.linkedin.com") 
        while True:
            #se estiver logado, deve ser redirecionado para o feed
            time.sleep(1)
            if "/feed" in self.driver.current_url:
                break
        print("IS LOGGED!")

    def answer_questions(self, details_lang:str) -> None:
        try:
            preference_premium_checkbox = self.driver.find_element(By.NAME, "jobDetailsEasyApplyTopChoiceCheckbox")
            print("PREFERENCE PREMIUM CHECKBOX FOUND")
            return #nothing to do in this page
        except Exception as e:
            print("NOT IN PREMIUM PREFERENCE PAGE")
        #tratando inputs
        try:
            inputs = self.get_elements(3, By.CLASS_NAME, 'artdeco-text-input--input')
            print(f"QUANTIDADE DE INPUT's ENCONTRADOS: {len(inputs)}")
            for select in inputs:
                question = self.get_dad(select).text
                print(f"QUESTION: {question}")

                #not always using ai here because of dumb questions like: Do you have Knowledge of relational and non-relational databases and versioning of Git? (answer with int number duh)
                
                if "Número de celular" in question:
                    select.clear()
                    select.send_keys(self.opt["private_info"]["cellphone"])
                elif "Há quantos anos" in question:
                    select.clear()
                    select.send_keys(self.opt["private_info"]["base_years_of_experience"])
                else:
                    answer = self.answer_linkedin_question(question, details_lang, InputType.NUMERIC)
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
            selects = self.get_elements(3, By.CLASS_NAME, 'fb-dash-form-element__select-dropdown')
            print(f"QUANTIDADE DE DROPDOWN's ENCONTRADOS: {len(selects)}")
            for select in selects:
                dropdown = Select(select)
                question = self.get_dad(select).find_element(By.XPATH, "label").text
                dropdown_options = [opt.text.lower() for opt in dropdown.options if "selecionar" not in opt.text.lower()]
                print(f"QUESTION: {question}")
                print(f"DROPDOWN OPTIONS: {dropdown_options}")
                answer = self.answer_linkedin_question(question, details_lang, InputType.DROPDOWN, dropdown_options)
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
            fieldsets = self.get_elements(3, By.CSS_SELECTOR, "fieldset[data-test-form-builder-radio-button-form-component='true']")
            print(f"QUANTIDADE DE FIELDSET's ENCONTRADOS: {len(fieldsets)}")
            for fieldset in fieldsets:
                question = fieldset.find_element(By.XPATH, "legend").text
                labels = fieldset.find_elements(By.TAG_NAME, "label")
                options_map = {l.text.lower().strip(): l for l in labels}
                options_list = list(options_map.keys())
                print(f"QUESTION: {question}")
                print(f"RADIO OPTIONS: {options_list}")
                answer = self.answer_linkedin_question(question, details_lang, InputType.DROPDOWN, options_list)
                clean_answer = answer.strip().replace(".", "").lower()
                print(f"CLEAN ANSWER: '{clean_answer}'")
                if clean_answer in options_map:
                    self.click_element(options_map[clean_answer])
                else:
                    print("erro na resposta da ia, selecionando index 0")
                    self.click_element(labels[0])
        except Exception as e:
            pass

    def select_resume(self, is_portuguese:bool, is_english:bool) -> None:
        try:
            resumes = self.get_elements(3, By.CSS_SELECTOR, ".ui-attachment.jobs-document-upload-redesign-card__container")
            print(f"CURRICULOS ENCONTRADOS: {len(resumes)}")
            for resume in resumes:
                if is_portuguese and "PORTUGUES" in resume.text:
                    print("SELECTED PORTUGUESE RESUME")
                    if "Selecionado" not in resume.get_attribute("aria-label"):
                        self.click_element(resume)
                    break
                if is_english and "INGLES" in resume.text:
                    print("SELECTED ENGLISH RESUME")
                    if "Selecionado" not in resume.get_attribute("aria-label"):
                        self.click_element(resume)
                    break
            time.sleep(0.2)
        except Exception as e:
            logging.error("Falha ao selecionar curriculo", exc_info=True)
