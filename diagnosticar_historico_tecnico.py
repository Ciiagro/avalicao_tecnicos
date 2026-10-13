"""
SOMENTE LEITURA. Mostra tudo que existe no banco sobre um técnico:
avaliações (qualquer status/supervisor/mês), marcações "não avaliar" e vínculos.

Rode na raiz do projeto (onde tem o .env):
    python diagnosticar_historico_tecnico.py "JOSIONE MATEUS DA FONSECA"
"""
import sys
from sqlalchemy import text
from app.database import get_engine

if len(sys.argv) != 2:
    print('Uso: python diagnosticar_historico_tecnico.py "NOME DO TECNICO"')
    sys.exit(1)

padrao = "%" + "%".join(sys.argv[1].split()) + "%"
engine = get_engine()

with engine.connect() as conn:
    print("\n[1] AVALIAÇÕES (avaliacoes_tecnicos)")
    for r in conn.execute(text("""
        SELECT id, supervisor, tecnico, mes_referencia, status, nota_final
        FROM avaliacoes_tecnicos WHERE tecnico ILIKE :p
        ORDER BY mes_referencia, supervisor"""), {"p": padrao}):
        print(f"   id={r.id} | {r.mes_referencia} | sup={r.supervisor} | {r.tecnico!r} | {r.status} | nota={r.nota_final}")

    print("\n[2] MARCAÇÕES 'NÃO AVALIAR' (nao_avaliar_tecnico_mes)")
    for r in conn.execute(text("""
        SELECT supervisor, tecnico, mes_referencia, observacao, criado_por, criado_em
        FROM nao_avaliar_tecnico_mes WHERE tecnico ILIKE :p
        ORDER BY mes_referencia"""), {"p": padrao}):
        print(f"   {r.mes_referencia} | sup={r.supervisor} | {r.tecnico!r} | por {r.criado_por} em {r.criado_em} | {r.observacao!r}")

    print("\n[3] VÍNCULOS (vinculo_tecnico)")
    for r in conn.execute(text("""
        SELECT id, supervisor, tecnico, data_inicio, data_desvinculacao, motivo_desvinculacao
        FROM vinculo_tecnico WHERE tecnico ILIKE :p
        ORDER BY data_inicio"""), {"p": padrao}):
        print(f"   id={r.id} | sup={r.supervisor} | {r.tecnico!r} | {r.data_inicio} -> {r.data_desvinculacao} | {r.motivo_desvinculacao}")
