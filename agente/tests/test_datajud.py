"""
Testes unitários para o módulo datajud.py
"""
import pytest
from unittest.mock import patch, MagicMock
from modulos.datajud import consultar


class TestConsultarDatajud:
    @patch("modulos.datajud.requests.post")
    def test_consulta_sucesso(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "dataAjuizamento": "2024-01-15",
                            "valorCausa": 50000.0,
                            "classe": {"nome": "Procedimento Comum"},
                            "partes": [
                                {"tipo": "AUTOR", "nome": "JOÃO SILVA"},
                                {"tipo": "REU", "nome": "EMPRESA XYZ"},
                            ],
                        }
                    }
                ]
            }
        }
        mock_post.return_value = mock_response

        resultado = consultar("07037299022068070007")

        assert resultado["classe"] == "Procedimento Comum"
        assert resultado["polo_ativo"] == "JOÃO SILVA"
        assert resultado["polo_passivo"] == "EMPRESA XYZ"
        assert resultado["data_distribuicao"] == "2024-01-15"
        assert resultado["instancia"] == "1ª Instância"  # segmento 07

    @patch("modulos.datajud.requests.post")
    def test_segunda_instancia(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "dataAjuizamento": "2024-01-15",
                            "valorCausa": 100000.0,
                            "classe": {"nome": "Apelação"},
                            "partes": [],
                        }
                    }
                ]
            }
        }
        mock_post.return_value = mock_response

        # Número CNJ com segmento 08 (2ª instância)
        resultado = consultar("07037299022068080007")
        assert resultado["instancia"] == "2ª Instância"

    @patch("modulos.datajud.requests.post")
    def test_sem_resultados(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"hits": {"hits": []}}
        mock_post.return_value = mock_response

        resultado = consultar("12345678901234567890")
        assert resultado == {}

    @patch("modulos.datajud.requests.post")
    def test_sem_polo_passivo(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "dataAjuizamento": "2024-01-15",
                            "valorCausa": 1000.0,
                            "classe": {"nome": "Procedimento Comum"},
                            "partes": [
                                {"tipo": "AUTOR", "nome": "MARIA"},
                            ],
                        }
                    }
                ]
            }
        }
        mock_post.return_value = mock_response

        resultado = consultar("070372990220268070007")
        assert resultado["polo_passivo"] == "Não Há"
