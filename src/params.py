class LinkedInParams:

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