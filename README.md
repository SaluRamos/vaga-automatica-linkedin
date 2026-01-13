## A vaga vai chegar
  
![alt text](readme_images/video.gif)  
  
Nos últimos dias meu feed foi invadido pela propaganda do vaga automatica.  
Vi que tinham muitas reclamações no reclameaqui, então decidi fazer minha própria ferramenta.  
Trata-se de um bot para automatizar candidatura a vagas de emprego no linkedin.  
Na primeira execucão o bot espera que você faça login para continuar a funcionar.  
Seu linkedin deve possuir apenas dois curriculos, um em portugues e outro em ingles, com os respectivos nomes: INGLES.pdf e PORTUGUES.pdf  
Modifique seus curriculos aqui: https://www.linkedin.com/jobs/application-settings/  
O bot seleciona o curriculo de acordo com a linguagem da vaga, e precisa que eles tenham esse nomes para selecionar corretamente.  
configure o options.json como desejar.  
  
Observação: o driver deve ficar focado para melhor funcionamento, acredito que ocorrem falhas se ficar minimizado mas não testei.  
  
![alt text](readme_images/image.png)  
  
após rigorosos testes obtive esse problema, então adicionei um sleep de 30 segundos entre candidaturas configuravel.  
  
![alt text](readme_images/image2.png)  
  
Existe um limite de candidaturas que podem ser enviadas.  
Aparentemente 100 candidaturas por semana.  
  
### ☕ Apoie o Projeto

Por favor, não hesite em colaborar com o projeto. 
Deixe sua STAR como forma de agradecimento 👍 
  
| Rede | Ícone | Endereço |
| :--- | :---: | :--- |
| **Bitcoin** | <img src="https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/btc.png" width="20"> | `bc1qg6ava2w08d5k2588edylj08ux4yuhn74yygsnr` |
| **Ethereum** | <img src="https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/eth.png" width="20"> | `0xcD36cf511646bD39Cb23f425786a4f3699CcFD2a` |
| **Solana** | <img src="https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/sol.png" width="20"> | `FKotLMzTKNbdZcKXkXsPuP1hcXGiXfScjB7qvSCQAev2` |
| **BNB Chain** | <img src="https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/bnb.png" width="20"> | `0xcD36cf511646bD39Cb23f425786a4f3699CcFD2a` |
| **TRON** | <img src="https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/trx.png" width="20"> | `TWhZLJ61uY1bo8zicwhnfS5NKuuD6BJ8D8` |
  
### Requirements
  
- google chrome instalado
- Ollama instalado
- python 3 (testado com 3.10 e 3.14)
- opcional: crie uma venv
- pip install -r requirements.txt
- python main.py

### TODO

- a parte de preencher input é suscetível a falhas, é preciso refino. Não encontrei uma maneira de descobrir oque o field espera (numeric or string)
- quebrar a função principal, fiz tudo corrido e ficou essa bagunça.
- criar classe? Não acho que essa abordagem permita múltiplas instâncias.
- suportar curriculo em espanhol
- suporte ao site Indeed