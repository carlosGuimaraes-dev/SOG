import { describe, it, expect } from 'vitest'
import { parseValorMonetario } from './formatters'

describe('parseValorMonetario', () => {
  it('converte "R$ 10.000,00" para 10000', () => {
    expect(parseValorMonetario('R$ 10.000,00')).toBe(10000)
  })

  it('converte "10000,00" para 10000', () => {
    expect(parseValorMonetario('10000,00')).toBe(10000)
  })

  it('converte "R$ 50.000,00" para 50000', () => {
    expect(parseValorMonetario('R$ 50.000,00')).toBe(50000)
  })

  it('converte "R$ 1.234,56" para 1234.56', () => {
    expect(parseValorMonetario('R$ 1.234,56')).toBe(1234.56)
  })

  it('retorna 0 para string vazia', () => {
    expect(parseValorMonetario('')).toBe(0)
  })

  it('retorna 0 para undefined', () => {
    expect(parseValorMonetario(undefined)).toBe(0)
  })

  it('retorna 0 para valor inválido', () => {
    expect(parseValorMonetario('inválido')).toBe(0)
  })
})
