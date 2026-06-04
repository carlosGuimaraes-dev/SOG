"""
Testes unitários para o módulo regras.py
"""
from regras import detectar_area, obter_regras_outros_itens


class TestDetectarArea:
    def test_familia(self):
        assert detectar_area("Ação de Divórcio", "") == "familia"
        assert detectar_area("", "alimentos") == "familia"
        assert detectar_area("Inventário e Partilha", "") == "familia"

    def test_fazenda_publica(self):
        assert detectar_area("Execução Fiscal", "") == "fazenda_publica"
        assert detectar_area("", "fazenda") == "fazenda_publica"

    def test_criminal(self):
        assert detectar_area("Ação Penal", "") == "criminal"
        assert detectar_area("", "crime") == "criminal"

    def test_civel_comum(self):
        assert detectar_area("Procedimento Comum", "") == "civel_comum"
        assert detectar_area("", "cobrança") == "civel_comum"

    def test_default(self):
        assert detectar_area("Área Desconhecida", "") == "default"


class TestObterRegras:
    def test_civel_comum_tem_regras(self):
        regras = obter_regras_outros_itens("civel_comum")
        assert len(regras) > 0
        assert any(r["item_guia"] == "Distribuidor" for r in regras)
        assert any(r["item_guia"] == "Custas" for r in regras)

    def test_familia_vazio(self):
        regras = obter_regras_outros_itens("familia")
        assert regras == []

    def test_default_vazio(self):
        regras = obter_regras_outros_itens("default")
        assert regras == []

    def test_area_inexistente_retorna_default(self):
        regras = obter_regras_outros_itens("nao_existe")
        assert regras == []
