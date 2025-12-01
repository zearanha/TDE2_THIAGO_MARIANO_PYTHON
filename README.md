🏥 API de Gestão de Clínicas (TDE2)

Contexto do Projeto

Este projeto consiste no desenvolvimento de uma API backend completa para a gestão de uma clínica, conforme os requisitos do TDE2. O sistema é construído utilizando a linguagem Python com o framework Flask, seguindo o padrão de arquitetura Model-View-Controller (MVC) e os princípios da Programação Orientada a Objetos.

O foco principal é a camada de serviços (endpoints), as regras de negócio (Controllers) e a persistência de dados.

🛠️ Tecnologias e Arquitetura

Linguagem: Python 3.x

Framework Web: Flask

Banco de Dados: SQLite (persistência relacional em instance/clinica.db)

ORM/Persistência: SQLAlchemy

Autenticação: JSON Web Tokens (JWT)

Configuração: Variáveis de Ambiente (.env)

Estrutura de Diretórios

O projeto segue a seguinte estrutura, que reflete o padrão MVC e a organização de funcionalidades:

TDE2-THIAGO_MARIANO/
├── instance/               # Contém o arquivo do banco de dados (clinica.db)
├── models/                 # Camada Model (Classes e mapeamento ORM)
│   ├── user_model.py
│   ├── patient_model.py
│   ├── procedure_model.py
│   └── appointment_model.py
├── routes/                 # Camada Controller (Endpoints da API e regras de negócio)
│   ├── auth.py             # Autenticação e Geração de Token
│   ├── users.py
│   ├── patients.py
│   ├── procedures.py
│   └── appointments.py
├── utils/                  # Utilitários e Configurações
│   ├── .env                # Variáveis de ambiente (ex: JWT_SECRET_KEY, DB_URL)
│   └── config.py
├── app.py                  # Inicialização e Configuração Principal do Flask
└── requirements.txt        # Dependências do Python


🔐 Regras de Segurança e Acesso

Autenticação (Obrigatória)

Todos os endpoints do sistema OBRIGATORIAMENTE exigem um token JWT válido, exceto o endpoint de autenticação (/auth). O token deve ser enviado no cabeçalho da requisição (Authorization: Bearer <token>).

Tipos de Usuário

O sistema possui dois níveis de acesso que definem as permissões:

Tipo

Descrição

admin

Acesso total. Pode criar/remover usuários e procedimentos, além de gerir dados de pacientes e atendimentos.

default

Acesso restrito. Pode gerir pacientes e atendimentos, e consultar seus próprios dados.

Paginação em Disco

Todos os endpoints que retornam uma lista de objetos implementam paginação em disco. As requisições devem incluir os seguintes parâmetros de consulta:

page: Número da página a ser recuperada (padrão: 1).

per_page: Quantidade de itens por página (padrão: 10 ou 20, dependendo da configuração).