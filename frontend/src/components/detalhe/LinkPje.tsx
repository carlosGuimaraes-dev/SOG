interface Props {
  numero: string
}

export default function LinkPje({ numero }: Props) {
  const url = `https://pje.tjdft.jus.br/pje/Processo/ConsultaProcesso/listView.seam?nrProcesso=${encodeURIComponent(numero)}`

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2"
      aria-label="Abrir processo no PJE em nova aba"
    >
      <span className="mr-2" aria-hidden="true">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>
      </span>
      Abrir no PJE
    </a>
  )
}
