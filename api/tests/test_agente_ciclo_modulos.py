def test_modulos_dedicados_snapshot_e_contadores_preservam_totais(mock_db):
    from sog_shared import agente_ciclo_contadores, agente_ciclo_snapshot, agente_ciclos
    from sog_shared import processos_aprovacao

    erro_id = processos_aprovacao.inserir_processo(
        "0000010-00.0000.0.00.0000", "000001000000000000000"
    )
    concluido_id = processos_aprovacao.inserir_processo(
        "0000011-00.0000.0.00.0000", "000001100000000000000"
    )
    processos_aprovacao.atualizar_status(erro_id, "erro", "Falha anterior")
    processos_aprovacao.atualizar_status(concluido_id, "emitido")
    processos_aprovacao.solicitar_reprocessamento(erro_id, "operador", "nova tentativa")

    inicio = agente_ciclos.solicitar_inicio_agente()
    ciclo_uuid = inicio["ciclo_uuid"]
    agente_ciclo_snapshot.fechar_snapshot_ciclo(
        ciclo_uuid,
        ["0000012-00.0000.0.00.0000"],
    )

    membros = agente_ciclo_snapshot.listar_membros_ciclo(ciclo_uuid)
    novo_id = next(m["processo_id"] for m in membros if m["origem"] == "novo_pje")
    processos_aprovacao.atualizar_status(novo_id, "aguardando_aprovacao")

    agente_ciclo_contadores.atualizar_contadores_ciclo(ciclo_uuid)

    ciclo = agente_ciclos.obter_ciclo(ciclo_uuid)
    assert ciclo is not None
    assert ciclo["total_membros"] == 2
    assert ciclo["total_novos"] == 1
    assert ciclo["total_rearmados"] == 1
    assert ciclo["total_concluidos"] == 1
    assert ciclo["total_erros"] == 1

    agente_ciclo_contadores.finalizar_ciclo(ciclo_uuid)
    finalizado = agente_ciclos.obter_ciclo(ciclo_uuid)
    assert finalizado is not None
    assert finalizado["status"] == "concluido"
    assert finalizado["finalizado_em"] is not None
