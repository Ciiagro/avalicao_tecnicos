"""
Diagnostica por que um técnico NÃO aparece (ou aparece indevidamente) na
tela "Avaliação dos técnicos" de um supervisor, para um mês específico.

Reproduz exatamente a mesma lógica de app/repositorio.py:
  - tecnicos_do_supervisor_no_mes()  (visitas do mês + vinculo_tecnico do mês)
  - tecnicos_com_status_para_mes()   (união com quem já tem avaliação lançada)

Rode assim, na raiz do projeto (onde tem o .env):
    python diagnosticar_avaliacao_mes.py "KATIA ARAUJO RIBEIRO" 2026-07-01
    python diagnosticar_avaliacao_mes.py "KATIA ARAUJO RIBEIRO" 2026-07-01 "MARIA LORENA BRAGA CARNEIRO"
"""
import sys
from datetime import date
from sqlalchemy import text
from app.database import get_engine
from app.repositorio import normalizar, tecnicos_do_supervisor_no_mes, tecnicos_com_status_para_mes

if len(sys.argv) < 3:
    print('Uso: python diagnosticar_avaliacao_mes.py "NOME DO SUPERVISOR" AAAA-MM-01 ["NOME DO TECNICO" opcional]')
    sys.exit(1)

supervisor_busca = sys.argv[1]
mes_ref = date.fromisoformat(sys.argv[2])
tecnico_filtro = normalizar(sys.argv[3]) if len(sys.argv) > 3 else None
alvo_supervisor = normalizar(supervisor_busca)

engine = get_engine()

print("=" * 70)
print(f"Supervisor: {supervisor_busca}   |   Mês de referência: {mes_ref.strftime('%m/%Y')}")
print("=" * 70)

# 1) O que a função oficial do sistema devolve hoje
tecnicos_mes = tecnicos_do_supervisor_no_mes(supervisor_busca, mes_ref)
print(f"\n[1] tecnicos_do_supervisor_no_mes() devolveu {len(tecnicos_mes)} técnico(s):")
for t in tecnicos_mes:
    print(f"     - {t}")

status = tecnicos_com_status_para_mes(supervisor_busca, mes_ref)
print(f"\n[2] tecnicos_com_status_para_mes() (o que a tela realmente lista) devolveu {len(status)}:")
for t in status:
    print(f"     - {t['tecnico']} | avaliado={t['avaliado']} | nao_avaliar={t['nao_avaliar']}")

# 2) Detalhe cru: visitas dentro do mês, comparando o supervisor_atual gravado
with engine.connect() as conn:
    rows_visitas = conn.execute(
        text("""
            SELECT tecnico_responsavel AS tecnico, supervisor_atual, dt_visita_v::date AS dt_visita
            FROM acompanhamento_mensal_visitas
            WHERE dt_visita_v::date >= :mes_ref
              AND dt_visita_v::date < (:mes_ref + INTERVAL '1 month')
              AND tecnico_responsavel IS NOT NULL
            ORDER BY tecnico_responsavel;
        """),
        {"mes_ref": mes_ref},
    ).fetchall()

print(f"\n[3] Visitas registradas em {mes_ref.strftime('%m/%Y')} (todas, de qualquer supervisor):")
if not rows_visitas:
    print("     Nenhuma visita encontrada nesse mês em toda a base.")
for r in rows_visitas:
    if tecnico_filtro and normalizar(r.tecnico) != tecnico_filtro:
        continue
    bate = normalizar(r.supervisor_atual or "") == alvo_supervisor
    marca = "✅ bate com o supervisor buscado" if bate else "❌ NÃO bate com o supervisor buscado"
    print(f"     - {r.tecnico} | supervisor_atual='{r.supervisor_atual}' | {r.dt_visita} | {marca}")

# 3) Detalhe cru: vinculo_tecnico ativo/encerrado que cobre esse mês
with engine.connect() as conn:
    rows_vinculo = conn.execute(
        text("""
            SELECT tecnico, supervisor, data_inicio, data_desvinculacao, motivo_desvinculacao
            FROM vinculo_tecnico
            WHERE supervisor = :supervisor
            ORDER BY tecnico, data_inicio DESC;
        """),
        {"supervisor": supervisor_busca},
    ).fetchall()

print(f"\n[4] Vínculos cadastrados com supervisor = '{supervisor_busca}' (string exata, sem normalizar):")
if not rows_vinculo:
    print("     Nenhum vínculo encontrado com esse texto exato de supervisor.")
for r in rows_vinculo:
    if tecnico_filtro and normalizar(r.tecnico) != tecnico_filtro:
        continue
    cobre_o_mes = (r.data_inicio < date(mes_ref.year + (mes_ref.month // 12), (mes_ref.month % 12) + 1, 1)) and (
        r.data_desvinculacao is None or r.data_desvinculacao >= mes_ref
    )
    marca = "✅ cobre esse mês" if cobre_o_mes else "❌ NÃO cobre esse mês"
    print(f"     - {r.tecnico} | data_inicio={r.data_inicio} | data_desvinculacao={r.data_desvinculacao} | {marca}")

# 4) Se foi passado um técnico específico, também mostra TODOS os vínculos dele
#    (em qualquer supervisor) — ajuda a ver se ele estava com outro supervisor no mês.
if tecnico_filtro:
    with engine.connect() as conn:
        rows_todos = conn.execute(
            text("SELECT tecnico, supervisor, data_inicio, data_desvinculacao FROM vinculo_tecnico ORDER BY data_inicio DESC;")
        ).fetchall()
    print(f"\n[5] TODOS os vínculos (qualquer supervisor) do técnico buscado:")
    achou = False
    for r in rows_todos:
        if normalizar(r.tecnico) == tecnico_filtro:
            achou = True
            print(f"     - supervisor='{r.supervisor}' | data_inicio={r.data_inicio} | data_desvinculacao={r.data_desvinculacao}")
    if not achou:
        print("     Nenhum vínculo encontrado para esse técnico em nenhum supervisor.")

print("\n" + "=" * 70)
print("Como ler o resultado:")
print(" - Se o técnico aparece em [3] com ❌, o problema é o campo supervisor_atual")
print("   da visita não bater com o nome do supervisor (o filtro usa esse campo).")
print(" - Se o técnico aparece em [4] com ❌, o vinculo_tecnico dele com esse")
print("   supervisor tem data_inicio POSTERIOR ao mês avaliado (ou desvinculação")
print("   ANTERIOR a ele) — por isso o sistema entende que ele não era dela naquele mês.")
print(" - Se em [5] aparece um vínculo com OUTRO supervisor cobrindo esse mês, é aí")
print("   que o técnico 'pertencia' no mês avaliado, mesmo estando na equipe da")
print("   Katia hoje.")
print("=" * 70)
