# A vaga vai chegar
  
![alt text](readme_images/video.gif)  
  
Nos últimos dias meu feed foi invadido pela propaganda do vaga automatica.  
Vi que tinham muitas reclamações no reclameaqui e não passava de uma automação selenium, então decidi fazer minha própria ferramenta.  
Trata-se de um bot para automatizar candidatura a vagas de emprego no linkedin.  
Na primeira execucão o bot espera que você faça login para continuar a funcionar.  
Seu linkedin deve possuir apenas dois curriculos, um em portugues e outro em ingles, com os respectivos nomes: INGLES.pdf e PORTUGUES.pdf  
modifique seus curriculos aqui: https://www.linkedin.com/jobs/application-settings/  
o bot seleciona o curriculo de acordo com a linguagem da vaga, e precisa que eles tenham esse nomes para selecionar corretamente.  
configure o options.json como desejar.  
  
![alt text](readme_images/image.png)  
  
após rigorosos testes obtive esse problema, então adicionei um sleep de 30 segundos entre candidaturas configuravel.  
Por favor, não exite em colaborar com o projeto ou abrir uma issue. 
Deixe sua STAR como forma de agradecimento 👍 
  
observação: o driver deve ficar focado para melhor funcionamento, acredito que ocorrem falhas se ficar minimizado mas não testei.

# Requirements
  
- google chrome instalado
- Ollama instalado
- python 3 (testado com 3.10 e 3.14)
- opcional: crie uma venv
- pip install -r requirements.txt
- python main.py


# TODO

- a parte de preencher input é suscetível a falhas, é preciso refino. Não encontrei uma maneira de descobrir oque o field espera (numeric or string)
- quebrar a função principal, fiz tudo corrido e ficou essa bagunça.
- criar classe? Não acho que essa abordagem permita múltiplas instâncias.
- suportar curriculo em espanhol