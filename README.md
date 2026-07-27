# Sistema de Avaliação de Técnicos

Aplicação web (FastAPI) para avaliação mensal de desempenho dos técnicos,
com dois perfis de acesso: **supervisor** e **coordenador geral**.

## Acesso em produção

- Sistema: https://avaliacao-tecnicos.onrender.com/login
- Ranking Geral (painel Streamlit, à parte): https://ranking-ateg-kczdjv73nkfmrq7w2nvfmn.streamlit.app/ — **acesso protegido por senha**, peça à coordenação

## Funcionalidades

**Perfil supervisor**
- Login individual, com troca de senha obrigatória no primeiro acesso
- Enxerga e avalia somente os técnicos vinculados a ele (`vinculo_tecnico`)
- Questionário de 10 perguntas, cada uma com nota de 5 a 10 — nota final é a média simples das 10
- Trava contra avaliação duplicada do mesmo técnico no mesmo mês
- Prazo mensal para lançar a avaliação — depois do prazo, o lançamento é bloqueado automaticamente (só o coordenador pode reabrir)

**Perfil coordenador geral**
- Cadastro e gestão de supervisores e técnicos, e dos vínculos entre eles
- Acompanhamento, tela "Avaliação do Supervisor", de quem já lançou (ou ainda não) as avaliações do mês, com pendências e média
- Ranking dos Técnicos e Relatório de técnicos
- Acesso ao Ranking Geral (link acima, agora protegido por senha)

## Como rodar localmente (Docker — forma padrão deste projeto)

```bash
cp .env.example .env             # depois edite o .env com os dados reais do banco
docker compose up --build
```

A aplicação sobe em http://localhost:8000 (porta definida no `docker-compose.yml`).
O `volumes: .:/app` já espelha o código local dentro do container, então
mudanças em templates/CSS aparecem só dando refresh no navegador — mudanças
em arquivos Python exigem `docker compose restart web` (ou rodar com `--reload`,
já configurado no `Dockerfile`).

Para rodar comandos dentro do container (ex: os scripts utilitários abaixo):

```bash
docker compose exec web python cadastrar_coordenador.py "Nome do Coordenador" login_desejado senha_provisoria
```

Para parar:

```bash
docker compose down
```

Crie as tabelas no Postgres (sem mexer nas tabelas existentes) — pode ser
direto do seu computador, com `psql`, sem precisar entrar no container:

```bash
psql "postgresql://usuario:senha@host:5432/banco" -f sql/schema.sql
psql "postgresql://usuario:senha@host:5432/banco" -f sql/schema_vinculo_tecnico.sql
psql "postgresql://usuario:senha@host:5432/banco" -f sql/migracao_supervisores_tecnicos.sql
psql "postgresql://usuario:senha@host:5432/banco" -f sql/migracao_prazo_avaliacao.sql
psql "postgresql://usuario:senha@host:5432/banco" -f sql/migracao_nao_avaliar_tecnico.sql
```

Cadastre os primeiros usuários (senha provisória, troca obrigatória no primeiro acesso):

```bash
# Supervisor — liste antes os nomes exatos cadastrados no banco:
docker compose exec web python cadastrar_supervisor.py listar
docker compose exec web python cadastrar_supervisor.py criar "Nome Exato Do Supervisor" login_desejado senha_provisoria

# Coordenador geral (acesso a tudo):
docker compose exec web python cadastrar_coordenador.py "Nome do Coordenador" login_desejado senha_provisoria
```

### Alternativa sem Docker (venv)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Estrutura

```
app/
  main.py                          -> rotas (login, painéis, formulário, ranking, relatórios)
  database.py                      -> conexão com o Postgres
  repositorio.py                   -> consultas de supervisor/técnico
  repositorio_tecnico_empresa.py   -> vínculo técnico ↔ empresa
  repositorio_tecnico_supervisor.py-> vínculo supervisor ↔ técnico (legado)
  repositorio_vinculo_tecnico.py   -> vínculo único técnico (atual)
  auth.py                          -> login, hash de senha, troca de senha, criação de usuário
  avaliacoes.py                    -> questionário, gravação das respostas e cálculo da nota final
  templates/                       -> páginas HTML
  static/                          -> CSS e logo
sql/
  schema.sql                       -> usuarios_supervisores, avaliacoes_tecnicos
  schema_vinculo_tecnico.sql       -> vinculo_tecnico
  migracao_supervisores_tecnicos.sql -> tabelas supervisores, tecnicos, tecnico_atividades
  migracao_prazo_avaliacao.sql     -> prazo de avaliação e autorizações de atraso
  migracao_nao_avaliar_tecnico.sql -> marcação "não avaliar este técnico neste mês"
```

## Tabelas utilizadas (Postgres)

| Tabela | O que guarda | Criada em |
|---|---|---|
| `usuarios_supervisores` | Login de cada usuário (supervisor ou coordenador), senha (hash) e se precisa trocar no próximo acesso | `sql/schema.sql` |
| `avaliacoes_tecnicos` | Avaliação mensal de cada técnico (10 perguntas, nota 5–10, nota final) | `sql/schema.sql` |
| `supervisores` | Cadastro de supervisores (ativo/inativo, dados complementares) | `sql/migracao_supervisores_tecnicos.sql` |
| `tecnicos` | Cadastro de técnicos (ativo/inativo, dados complementares) | `sql/migracao_supervisores_tecnicos.sql` |
| `tecnico_atividades` | Projeto(s)/atividade(s) e propriedades atendidas por técnico | `sql/migracao_supervisores_tecnicos.sql` |
| `vinculo_tecnico` | Vínculo único do técnico: empresa, supervisor responsável, datas de início/fim, motivo de desvinculação | `sql/schema_vinculo_tecnico.sql` |
| `configuracao_prazo_avaliacao` | Dia-limite padrão do mês para lançar avaliação | `sql/migracao_prazo_avaliacao.sql` |
| `prazos_avaliacao_mes` | Prazo específico definido pelo coordenador para um mês de referência | `sql/migracao_prazo_avaliacao.sql` |
| `autorizacoes_avaliacao_atrasada` | Liberação do coordenador para um supervisor lançar avaliação fora do prazo | `sql/migracao_prazo_avaliacao.sql` |
| `solicitacoes_prazo_avaliacao` | Pedido do supervisor ao coordenador para reabrir o prazo de um mês | `sql/migracao_prazo_avaliacao.sql` |
| `nao_avaliar_tecnico_mes` | Marcação "não avaliar este técnico neste mês" + motivo | `sql/migracao_nao_avaliar_tecnico.sql` |
| `tecnico_empresa_legado`, `tecnico_supervisor_legado` | Tabelas antigas de vínculo (renomeadas, mantidas só como histórico/backup) | `sql/migracao_vinculo_unico.sql` |
| `acompanhamento_mensal_visitas` | Base de visitas/orientações/propriedades — **não é criada por este projeto**, já existe no banco (`painel_ateg`) e alimenta o Ranking Geral e o Ranking dos Técnicos | (externa, pré-existente) |

## Scripts utilitários (raiz do projeto)

Rodando com Docker, execute com `docker compose exec web python <script>.py ...`
(sem Docker, é só `python <script>.py ...` normalmente, com a venv ativada):

- `cadastrar_supervisor.py` — lista supervisores do banco e cadastra login de supervisor
- `cadastrar_coordenador.py` — cadastra login de coordenador geral
- `resetar_avaliacoes.py` — faz backup em CSV e zera as tabelas de avaliação (uso: ambiente de teste antes de ir para produção)

## Próximos passos (ainda não incluídos aqui)

- Validação/homologação dos vínculos pelo coordenador antes de valerem
- Avaliação e ranking de supervisores dentro do próprio sistema (hoje o Ranking Geral vive em painel separado)
