"""
Testes TDD para o extrator de sentenças.

Foco: identificar quem foi condenado e os encargos de custas/honorários.
"""
import pytest
from unittest.mock import patch


# ========================================================================
# FIXTURES
# ========================================================================

@pytest.fixture
def sumario_tjdft_civel():
    return [
        {"doc_id": "206423284", "tipo": "Petição Inicial", "nome": "Petição Inicial"},
        {"doc_id": "207553631", "tipo": "Mandado", "nome": "Mandado"},
        {"doc_id": "213349177", "tipo": "Diligência", "nome": "Diligência"},
        {"doc_id": "268016633", "tipo": "Sentença", "nome": "Sentença"},
        {"doc_id": "275442991", "tipo": "Certidão", "nome": "Comprovante de Pagamento das Custas"},
    ]


@pytest.fixture
def dispositivo_civel():
    """Dispositivo real da sentença do processo 0732384-63.2024.8.07.0001."""
    return """ANTE O EXPOSTO, com fundamento no art. 487, inciso I, do CPC, resolvo o mérito e
julgo os pedidos iniciais PROCEDENTES.
Por conseguinte, condeno MARIA APARECIDA HERUNDINA DOS SANTOS SOUZA
ao cumprimento da obrigação de pagar à autora, a título de indenização por danos materiais, o
montante de R$ 10.158,00 (dez mil, cento e cinquenta e oito reais), a ser corrigido e acrescido de
juros de mora desde 26/06/2024, observados a sistemática de cálculo e os índices previstos nos
artigos 389 e 406 do CC, em sua nova redação, dada pela Lei nº 14.905/2024.
Em razão da sucumbência (art. 82, § 2º, do CPC) na lide principal, condeno a ré MARIA
SOUZA ao pagamento das custas processuais e dos honorários advocatícios, estes fixados em
10% (dez por cento) sobre o valor da condenação (art. 85, §§ 2º e 6º-A, do CPC). Suspensa,
porém, a exigibilidade dos encargos em questão, conforme artigo 98, § 3.º do Código de Processo
Civil."""


@pytest.fixture
def dispositivo_trabalhista():
    return """Vistos, relatados e discutidos os presentes autos.
ACORDAM os Magistrados integrantes da 1ª Turma do TRT-DF, por unanimidade de votos,
em CONHECER do recurso e, no mérito, DAR-LHE PROVIMENTO PARCIAL.
Assim, CONDENO a reclamada EMPRESA XYZ LTDA ao pagamento das seguintes verbas:
- Saldo de salário: R$ 3.500,00
- 13º salário proporcional: R$ 1.458,33
- Férias vencidas + 1/3: R$ 4.666,67
- Indenização por dispensa imotivada: R$ 14.000,00
- Horas extras: R$ 8.420,00
TOTAL DA CONDENAÇÃO: R$ 32.045,00 (trinta e dois mil e quarenta e cinco reais).
Sobre o total da condenação, fixo os honorários sucumbenciais em 15% (quinze por cento),
nos termos do art. 791-A da CLT.
Custas pela reclamada, observada a gratuidade de justiça."""


# ========================================================================
# TESTES - Sumário
# ========================================================================

class TestExtrairSumario:

    def test_ids_mandados(self, sumario_tjdft_civel):
        from modulos.extrator_sentenca import extrair_ids_por_tipo
        assert extrair_ids_por_tipo(sumario_tjdft_civel, ["Mandado"]) == "207553631"

    def test_ids_diligencias(self, sumario_tjdft_civel):
        from modulos.extrator_sentenca import extrair_ids_por_tipo
        assert extrair_ids_por_tipo(sumario_tjdft_civel, ["Diligência"]) == "213349177"

    def test_ids_sentenca(self, sumario_tjdft_civel):
        from modulos.extrator_sentenca import extrair_ids_por_tipo
        assert extrair_ids_por_tipo(sumario_tjdft_civel, ["Sentença"]) == "268016633"

    def test_ids_comprovante_custas(self, sumario_tjdft_civel):
        from modulos.extrator_sentenca import extrair_ids_por_tipo
        assert extrair_ids_por_tipo(sumario_tjdft_civel, ["Comprovante de Pagamento das Custas"]) == "275442991"


# ========================================================================
# TESTES - Sentença Cível
# ========================================================================

class TestSentencaCivel:

    def test_sucumbente_nome(self, dispositivo_civel):
        from modulos.extrator_sentenca import extrair_sentenca_regex
        r = extrair_sentenca_regex(dispositivo_civel, area="civel")
        assert r["sucumbente_nome"] == "MARIA APARECIDA HERUNDINA DOS SANTOS SOUZA"

    def test_sucumbente_tipo(self, dispositivo_civel):
        from modulos.extrator_sentenca import extrair_sentenca_regex
        r = extrair_sentenca_regex(dispositivo_civel, area="civel")
        # No dispositivo não há "réu" antes do nome, mas inferimos que é réu
        assert r["sucumbente_tipo"] == "réu"

    def test_valor_condenacao(self, dispositivo_civel):
        from modulos.extrator_sentenca import extrair_sentenca_regex
        r = extrair_sentenca_regex(dispositivo_civel, area="civel")
        assert r["valor_condenacao"] == "10.158,00"

    def test_honorarios_percentual(self, dispositivo_civel):
        from modulos.extrator_sentenca import extrair_sentenca_regex
        r = extrair_sentenca_regex(dispositivo_civel, area="civel")
        assert r["honorarios_percentual"] == "10"

    def test_suspensao_exigibilidade(self, dispositivo_civel):
        from modulos.extrator_sentenca import extrair_sentenca_regex
        r = extrair_sentenca_regex(dispositivo_civel, area="civel")
        assert r["suspensao_exigibilidade"] is True

    def test_score_alto(self, dispositivo_civel):
        from modulos.extrator_sentenca import extrair_sentenca_regex
        r = extrair_sentenca_regex(dispositivo_civel, area="civel")
        assert r["_score"] >= 0.8
        assert r["_metodo"] == "regex"


# ========================================================================
# TESTES - Sentença Trabalhista
# ========================================================================

class TestSentencaTrabalhista:

    def test_sucumbente(self, dispositivo_trabalhista):
        from modulos.extrator_sentenca import extrair_sentenca_regex
        r = extrair_sentenca_regex(dispositivo_trabalhista, area="trabalhista")
        assert r["sucumbente_nome"] == "EMPRESA XYZ LTDA"
        assert r["sucumbente_tipo"] == "reclamada"

    def test_valor_total(self, dispositivo_trabalhista):
        from modulos.extrator_sentenca import extrair_sentenca_regex
        r = extrair_sentenca_regex(dispositivo_trabalhista, area="trabalhista")
        # Deve pegar o TOTAL, não o primeiro valor individual
        assert r["valor_condenacao"] == "32.045,00"

    def test_honorarios(self, dispositivo_trabalhista):
        from modulos.extrator_sentenca import extrair_sentenca_regex
        r = extrair_sentenca_regex(dispositivo_trabalhista, area="trabalhista")
        assert r["honorarios_percentual"] == "15"

    def test_gratuidade(self, dispositivo_trabalhista):
        from modulos.extrator_sentenca import extrair_sentenca_regex
        r = extrair_sentenca_regex(dispositivo_trabalhista, area="trabalhista")
        assert r["suspensao_exigibilidade"] is True


# ========================================================================
# TESTES - LLM Fallback
# ========================================================================

class TestLLMFallback:

    @patch("modulos.extrator_sentenca._chamar_llm")
    def test_llm_usado_quando_regex_fraco(self, mock_llm):
        from modulos.extrator_sentenca import extrair_sentenca
        mock_llm.return_value = {
            "sucumbente_nome": "FULANO",
            "valor_condenacao": "5.000,00",
            "honorarios_percentual": "10",
        }
        r = extrair_sentenca("Texto incompleto sem padrão.", area="civel")
        assert r["sucumbente_nome"] == "FULANO"
        assert r["_metodo"] == "llm"

    def test_regex_usado_quando_score_alto(self, dispositivo_civel):
        from modulos.extrator_sentenca import extrair_sentenca
        r = extrair_sentenca(dispositivo_civel, area="civel")
        assert r["_metodo"] == "regex"


# ========================================================================
# TESTES - Cache / Aprendizado
# ========================================================================

class TestCache:

    def test_salvar_e_buscar_padrao(self, dispositivo_civel):
        from modulos.extrator_sentenca import salvar_padrao, buscar_padrao
        resultado = {"sucumbente_nome": "MARIA SOUZA", "honorarios_percentual": "10"}
        salvar_padrao(dispositivo_civel, resultado, "regex", 0.95)
        encontrado = buscar_padrao(dispositivo_civel)
        assert encontrado is not None
        assert encontrado["score"] == 0.95

    def test_correcao_usuario(self, dispositivo_civel):
        from modulos.extrator_sentenca import salvar_padrao, aplicar_correcao, buscar_padrao
        salvar_padrao(dispositivo_civel, {"sucumbente_nome": "ERRADO"}, "regex", 0.3)
        aplicar_correcao(dispositivo_civel, {"sucumbente_nome": "MARIA SOUZA"})
        encontrado = buscar_padrao(dispositivo_civel)
        assert encontrado["resultado"]["sucumbente_nome"] == "MARIA SOUZA"
        assert encontrado["score"] == 1.0


# ========================================================================
# TESTES - Integração Completa
# ========================================================================

class TestExtracaoCompleta:

    def test_civel(self, sumario_tjdft_civel, dispositivo_civel):
        from modulos.extrator_sentenca import extrair_completo
        r = extrair_completo(sumario_tjdft_civel, dispositivo_civel, area="civel")

        # Do sumário
        assert r["ids_mandados"] == "207553631"
        assert r["ids_diligencias"] == "213349177"
        assert r["ids_sentenca"] == "268016633"
        assert r["ids_comprovante_custas"] == "275442991"

        # Da sentença
        assert r["sucumbente_nome"] == "MARIA APARECIDA HERUNDINA DOS SANTOS SOUZA"
        assert r["sucumbente_tipo"] == "réu"
        assert r["valor_condenacao"] == "10.158,00"
        assert r["honorarios_percentual"] == "10"
        assert r["suspensao_exigibilidade"] is True
        assert r["_score"] >= 0.8

    def test_trabalhista(self, dispositivo_trabalhista):
        from modulos.extrator_sentenca import extrair_completo
        sumario = [
            {"doc_id": "999001", "tipo": "Petição Inicial", "nome": "Reclamação"},
            {"doc_id": "999002", "tipo": "Sentença", "nome": "Sentença"},
        ]
        r = extrair_completo(sumario, dispositivo_trabalhista, area="trabalhista")

        assert r["sucumbente_nome"] == "EMPRESA XYZ LTDA"
        assert r["valor_condenacao"] == "32.045,00"
        assert r["honorarios_percentual"] == "15"
        assert r["ids_sentenca"] == "999002"
