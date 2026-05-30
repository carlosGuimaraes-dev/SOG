import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useProcesso } from '../hooks/useProcesso'
import { useAprovar } from '../hooks/useAprovar'
import { useRejeitar } from '../hooks/useRejeitar'
import { useReprocessar } from '../hooks/useReprocessar'
import Button from '../components/ui/Button'
import Skeleton from '../components/ui/Skeleton'
import LinkPje from '../components/detalhe/LinkPje'
import ErroBanner from '../components/detalhe/ErroBanner'
import ResumoPreenchimento from '../components/detalhe/ResumoPreenchimento'
import LogsTimeline from '../components/detalhe/LogsTimeline'
import DocumentosPje from '../components/detalhe/DocumentosPje'
import CompensacaoTable from '../components/detalhe/CompensacaoTable'
import EmissaoStatus from '../components/detalhe/EmissaoStatus'
import DemonstrativoLink from '../components/detalhe/DemonstrativoLink'
import DadosProcessoCard from '../components/detalhe/DadosProcessoCard'
import SucumbentesTable from '../components/detalhe/SucumbentesTable'
import PecasProcessuaisCard from '../components/detalhe/PecasProcessuaisCard'
import OutrosItensTable from '../components/detalhe/OutrosItensTable'
import CustasPagasTable from '../components/detalhe/CustasPagasTable'
import ScreenshotCard from '../components/detalhe/ScreenshotCard'
import AvisosAlert from '../components/detalhe/AvisosAlert'
import AcoesPanel from '../components/detalhe/AcoesPanel'
import ValorTotal from '../components/detalhe/ValorTotal'

export default function Detalhe() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data, loading, refetch } = useProcesso(id)
  const { aprovar, actionLoading: aprovando } = useAprovar(id)
  const { rejeitar, actionLoading: rejeitando } = useRejeitar(id)
  const { reprocessar, actionLoading: reprocessando } = useReprocessar(id, refetch)
  const [obs, setObs] = useState(data?.dados?.obs_operador || '')

  useEffect(() => {
    if (data?.dados?.obs_operador !== undefined) {
      setObs(data.dados.obs_operador)
    }
  }, [data?.dados?.obs_operador])

  if (loading || !data) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  const p = data.processo
  const d = data.dados || {}
  const actionLoading = aprovando || rejeitando

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Processo {p.numero}</h2>
        <div className="flex items-center gap-2">
          <LinkPje numero={p.numero} />
          <Button variant="outline" onClick={() => navigate('/')} aria-label="Voltar para fila">
            ← Voltar
          </Button>
        </div>
      </div>

      {p.erro_msg && <ErroBanner mensagem={p.erro_msg} />}

      <ResumoPreenchimento dados={d} />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <DadosProcessoCard dados={d} />

          {d.sucumbentes && d.sucumbentes.length > 0 && (
            <SucumbentesTable sucumbentes={d.sucumbentes} />
          )}

          <PecasProcessuaisCard
            idsOficios={d.ids_oficios}
            idsAlvaras={d.ids_alvaras}
            idsTraslados={d.ids_traslados}
            idsMandados={d.ids_mandados}
            idsCartasSentenca={d.ids_cartas_sentenca}
            idsAr={d.ids_ar}
            idsArmp={d.ids_armp}
          />

          {d.outros_itens && d.outros_itens.length > 0 && (
            <OutrosItensTable items={d.outros_itens} />
          )}

          {d.custas_pagas && d.custas_pagas.length > 0 && (
            <CustasPagasTable items={d.custas_pagas} />
          )}

          <ValorTotal valor={d.valor_total_recolher} />

          <LogsTimeline logs={data.logs} />
        </div>

        <div className="space-y-6">
          <ScreenshotCard processoId={p.id} screenshotPath={d.screenshot_path} />

          <AvisosAlert
            areaDireito={d.area_direito}
            suspensao={d.suspensao_exigibilidade}
            sucumbenteNome={d.sucumbente_nome}
            valorTotalRecolher={d.valor_total_recolher}
          />

          {p.status === 'aprovado' && <EmissaoStatus processoId={p.id} />}

          <AcoesPanel
            observacao={obs}
            onObservacaoChange={setObs}
            onAprovar={aprovar}
            onRejeitar={() => rejeitar(obs)}
            onReprocessar={() => reprocessar(obs)}
            actionLoading={actionLoading}
            reprocessarLoading={reprocessando}
            statusProcesso={p.status}
            reprocessarSolicitadoEm={p.reprocessar_solicitado_em}
          />

          <DocumentosPje documentos={data.documentos} />

          <CompensacaoTable items={d.compensacao} />

          <DemonstrativoLink numero={p.numero} />
        </div>
      </div>
    </div>
  )
}
