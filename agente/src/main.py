"""
Orquestrador principal do pipeline de custas processuais TJDFT.

Fluxo:
1. Coleta lista de processos no PJE por etiqueta
2. Para cada novo processo:
   a. Consulta Datajud
   b. Coleta documentos no PJE
   c. Parse dos documentos
   d. Preenche SISTJWEB
   e. Notifica operador
3. Logs em JSON estruturado
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import MAX_TENTATIVAS
from banco import db
from modulos.pje import PjeClient
from modulos.datajud import consultar as datajud_consultar
from modulos.parser import processar_documentos
from modulos.sistjweb import SistjClient
from modulos.emissor import emitir_e_anexar
from regras import detectar_area, obter_regras_outros_itens
from utils.logger import info, erro, aviso
from utils.notificador import enviar_alerta


def processar_processo(numero: str, numero_sem_mascara: str, pje: PjeClient, sistj: SistjClient):
    """Executa o pipeline completo para um único processo."""
    processo_id = None
    try:
        existente = db.processo_existe(numero)
        if existente:
            if existente["status"] != "erro":
                info(f"Processo {numero} já existe com status '{existente['status']}'. Pulando.")
                return
            processo_id = existente["id"]
            db.atualizar_status(processo_id, "pendente", erro_msg="", incrementar_tentativa=True)
        else:
            processo_id = db.inserir_processo(numero, numero_sem_mascara)
            info(f"Novo processo inserido: {numero} (id={processo_id})")

        db.registrar_log(processo_id, "inicio", "ok", "Iniciando pipeline")

        # 1. Datajud
        info(f"[{numero}] Consultando Datajud...", processo_id=processo_id, etapa="datajud")
        dados_datajud = datajud_consultar(numero_sem_mascara)
        db.registrar_log(processo_id, "datajud", "ok" if dados_datajud else "aviso", str(dados_datajud))

        # 2. Documentos PJE
        info(f"[{numero}] Coletando documentos no PJE...", processo_id=processo_id, etapa="pje")
        docs, textos = pje.coletar_documentos(numero)
        for doc in docs:
            db.salvar_documento(
                processo_id, doc["doc_id"], doc["tipo"], doc["data_assinatura"], doc["nome"]
            )
        db.registrar_log(processo_id, "pje_documentos", "ok", f"{len(docs)} documentos")

        # 3. Parser
        info(f"[{numero}] Analisando documentos...", processo_id=processo_id, etapa="parser")
        dados_parser = processar_documentos(docs, textos)
        db.registrar_log(processo_id, "parser", "ok", str(dados_parser))

        # 4. Detecta área e regras
        area = detectar_area(dados_datajud.get("classe", ""), "")
        regras = obter_regras_outros_itens(area)

        if not regras and area == "default":
            aviso(f"Área não mapeada para {numero}. Status: pendente_manual.", processo_id=processo_id)
            db.atualizar_status(processo_id, "pendente_manual")
            db.registrar_log(processo_id, "regras", "aviso", "Área não mapeada")
            return

        payload = {
            "numero_sem_mascara": numero_sem_mascara,
            "numero": numero,
            "instancia": dados_datajud.get("instancia", "1ª Instância"),
            "processo_eletronico": 1,
            "circunscricao": "",
            "competencia": "",
            "feito": "",
            "classe": dados_datajud.get("classe", ""),
            "valor_causa": dados_datajud.get("valor_causa", ""),
            "data_distribuicao": dados_datajud.get("data_distribuicao", ""),
            "polo_ativo": dados_datajud.get("polo_ativo", ""),
            "polo_passivo": dados_datajud.get("polo_passivo", "Não Há"),
            "tipo_guia": "",
            "pro_rata": 1 if len(dados_parser.get("sucumbentes", [])) > 1 else 0,
            "sucumbentes": [
                {
                    "nome": dados_parser.get("sucumbente_nome", ""),
                    "cpf_cnpj": dados_parser.get("sucumbente_cpf_cnpj", ""),
                    "tipo": dados_parser.get("sucumbente_tipo", "Requerido"),
                    "is_autor": False,
                    "percentual": dados_parser.get("honorarios_percentual", "100"),
                }
            ],
            **dados_parser,
            "area_direito": area,
        }

        # 5. SISTJWEB
        info(f"[{numero}] Preenchendo SISTJWEB...", processo_id=processo_id, etapa="sistjweb")
        if not sistj.login():
            raise RuntimeError("Falha no login SISTJWEB")

        resultado_sistj = sistj.preencher(payload, numero)

        db.salvar_dados_processo(processo_id, {**payload, **resultado_sistj})
        db.atualizar_status(processo_id, "aguardando_aprovacao")
        db.registrar_log(processo_id, "sistjweb", "ok", f"Screenshot: {resultado_sistj.get('screenshot_path', '')}")

        info(f"[{numero}] Pipeline concluído. Aguardando aprovação.", processo_id=processo_id)

    except Exception as e:
        erro_msg = str(e)
        erro(f"[{numero}] Erro no pipeline: {erro_msg}", processo_id=processo_id)
        if processo_id:
            db.atualizar_status(processo_id, "erro", erro_msg, incrementar_tentativa=True)
            db.registrar_log(processo_id, "pipeline", "erro", erro_msg)
            proc = db.processo_existe(numero)
            if proc and proc.get("tentativas", 0) >= MAX_TENTATIVAS:
                enviar_alerta([{"numero": numero, "status": "erro"}])


def rodar():
    """Execução principal do orquestrador."""
    info("Iniciando pipeline de custas TJDFT...")

    pje = PjeClient()
    sistj = SistjClient()

    try:
        if not pje.login():
            erro("Falha no login PJE. Abortando.")
            return

        numeros = pje.coletar_lista_processos()
        info(f"Total de processos na etiqueta: {len(numeros)}")

        if not numeros:
            info("Nenhum processo novo encontrado.")
            return

        sistj.login()

        for numero in numeros:
            numero_sem_mascara = re.sub(r"\D", "", numero)
            try:
                processar_processo(numero, numero_sem_mascara, pje, sistj)
            except Exception as e:
                erro(f"Erro inesperado processando {numero}: {e}")
                continue

        pendentes = db.listar_aguardando_aprovacao()
        if pendentes:
            enviar_alerta(pendentes)

    finally:
        pje.fechar()
        sistj.fechar()
        info("Pipeline finalizado.")


if __name__ == "__main__":
    rodar()
