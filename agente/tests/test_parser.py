"""
Testes unitários para o módulo parser.py
"""
from modulos.parser import (
    extrair_ids,
    parse_sentenca,
    parse_comprovante_pagamento,
    processar_documentos,
)


class TestExtrairIds:
    def test_extrai_ids_por_tipo(self):
        docs = [
            {"doc_id": "123", "tipo": "Mandado"},
            {"doc_id": "456", "tipo": "Ofício"},
            {"doc_id": "789", "tipo": "Mandado"},
        ]
        assert extrair_ids(docs, "Mandado") == "123,789"
        assert extrair_ids(docs, "Ofício") == "456"

    def test_retorna_vazio_se_nao_houver(self):
        docs = [{"doc_id": "123", "tipo": "Sentença"}]
        assert extrair_ids(docs, "Ofício") == ""


class TestParseSentenca:
    def test_sucumbente_simples(self):
        texto = "condeno a EMPRESA XYZ ao pagamento das custas"
        resultado = parse_sentenca(texto)
        assert resultado["sucumbente_nome"] == "EMPRESA XYZ"

    def test_honorarios(self):
        texto = "fixo os honorários advocatícios em 10% sobre o valor da condenação"
        resultado = parse_sentenca(texto)
        assert resultado["honorarios_percentual"] == "10"

    def test_suspensao_exigibilidade(self):
        texto = "aplico o art. 98, § 3º do CPC"
        resultado = parse_sentenca(texto)
        assert resultado["suspensao_exigibilidade"] is True

    def test_valor_condenacao(self):
        texto = "fixo o valor da condenação de R$ 50.000,00"
        resultado = parse_sentenca(texto)
        assert resultado["valor_condenacao"] == "50.000,00"

    def test_sentenca_completa(self):
        texto = (
            "condeno JOÃO DA SILVA ao pagamento das custas processuais. "
            "fixo os honorários em 15% sobre o valor da condenação de R$ 100.000,00. "
            "aplico o art. 98 § 3"
        )
        resultado = parse_sentenca(texto)
        assert resultado["sucumbente_nome"] == "JOÃO DA SILVA"
        assert resultado["honorarios_percentual"] == "15"
        assert resultado["suspensao_exigibilidade"] is True
        assert resultado["valor_condenacao"] == "100.000,00"


class TestParseComprovantePagamento:
    def test_data_pagamento(self):
        texto = "data do pagamento: 15/03/2024"
        resultado = parse_comprovante_pagamento(texto)
        assert resultado["data"] == "15/03/2024"

    def test_valor_pago(self):
        texto = "valor pago: R$ 1.234,56"
        resultado = parse_comprovante_pagamento(texto)
        assert resultado["valor"] == "1.234,56"

    def test_numero_guia(self):
        texto = "guia nº 123456789"
        resultado = parse_comprovante_pagamento(texto)
        assert resultado["numero_guia"] == "123456789"

    def test_comprovante_completo(self):
        texto = (
            "comprovante de pagamento de custas\n"
            "data do pagamento: 20/05/2024\n"
            "valor das custas pagas: R$ 500,00\n"
            "número da guia: 987654321"
        )
        resultado = parse_comprovante_pagamento(texto)
        assert resultado["data"] == "20/05/2024"
        assert resultado["valor"] == "500,00"
        assert resultado["numero_guia"] == "987654321"


class TestProcessarDocumentos:
    def test_processa_documentos_variados(self):
        docs = [
            {"doc_id": "111", "tipo": "Mandado", "data_assinatura": "01/01/2024", "nome": "Mandado 1"},
            {"doc_id": "222", "tipo": "Ofício", "data_assinatura": "02/01/2024", "nome": "Ofício 1"},
            {"doc_id": "333", "tipo": "Sentença", "data_assinatura": "03/01/2024", "nome": "Sentença 1"},
            {"doc_id": "444", "tipo": "Comprovante de Pagamento de Custas", "data_assinatura": "04/01/2024", "nome": "Comprovante 1"},
        ]
        textos = {
            "333": "condeno MARIA ao pagamento. honorários 12%. art 98 § 3",
            "444": "data do pagamento: 10/04/2024. valor pago: R$ 250,00. guia nº 111222333",
        }

        resultado = processar_documentos(docs, textos)

        assert resultado["ids_mandados"] == "111"
        assert resultado["ids_oficios"] == "222"
        assert resultado["sucumbente_nome"] == "MARIA"
        assert resultado["honorarios_percentual"] == "12"
        assert resultado["suspensao_exigibilidade"] is True
        assert len(resultado["custas_pagas"]) == 1
        assert resultado["custas_pagas"][0]["data"] == "10/04/2024"

    def test_processar_documentos_com_custas_iniciais(self):
        docs = [{"doc_id": "111", "tipo": "Guia", "data_assinatura": "01/01/2024", "nome": "Guia 1"}]
        textos = {}
        custas_pdf = [{"data": "11/08/2024", "valor": "266,95", "numero_guia": "001-9"}]

        resultado = processar_documentos(docs, textos, custas_iniciais=custas_pdf)

        assert len(resultado["custas_pagas"]) == 1
        assert resultado["custas_pagas"][0] == {"data": "11/08/2024", "valor": "266,95", "numero_guia": "001-9"}

    def test_processar_documentos_deduplica_custas_por_guia(self):
        docs = [
            {"doc_id": "444", "tipo": "Comprovante de Pagamento de Custas", "data_assinatura": "04/01/2024", "nome": "Comprovante 1"},
        ]
        textos = {
            "444": "data do pagamento: 10/04/2024. valor pago: R$ 250,00. guia nº 111222333",
        }
        custas_pdf = [{"data": "10/04/2024", "valor": "250,00", "numero_guia": "111222333"}]

        resultado = processar_documentos(docs, textos, custas_iniciais=custas_pdf)

        assert len(resultado["custas_pagas"]) == 1
        assert resultado["custas_pagas"][0]["data"] == "10/04/2024"

    def test_processar_documentos_custas_iniciais_sem_numero_guia(self):
        docs = []
        textos = {}
        custas_pdf = [
            {"data": "11/08/2024", "valor": "100,00", "numero_guia": ""},
            {"data": "12/08/2024", "valor": "200,00", "numero_guia": ""},
        ]

        resultado = processar_documentos(docs, textos, custas_iniciais=custas_pdf)

        assert len(resultado["custas_pagas"]) == 2
