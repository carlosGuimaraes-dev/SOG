export function parseValorMonetario(valor: string | undefined): number {
  if (!valor) return 0
  const limpo = valor
    .replace(/R\$\s?/g, '')
    .replace(/\./g, '')
    .replace(/,/g, '.')
  const numero = parseFloat(limpo)
  return isNaN(numero) ? 0 : numero
}
