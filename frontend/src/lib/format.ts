const CAD = new Intl.NumberFormat('en-CA', {
  style: 'currency',
  currency: 'CAD',
  maximumFractionDigits: 0,
})
const CAD2 = new Intl.NumberFormat('en-CA', {
  style: 'currency',
  currency: 'CAD',
  maximumFractionDigits: 2,
})
const PCT = new Intl.NumberFormat('en-CA', { style: 'percent', maximumFractionDigits: 1 })
const NUM = new Intl.NumberFormat('en-CA', { maximumFractionDigits: 2 })

export const fmt = {
  cad: (n: number) => CAD.format(n),
  cad2: (n: number) => CAD2.format(n),
  pct: (n: number) => PCT.format(n),
  num: (n: number) => NUM.format(n),
  signed: (n: number) => (n >= 0 ? '+' : '') + CAD.format(n),
  signedPct: (n: number) => (n >= 0 ? '+' : '') + PCT.format(n),
}

export const accountTypeLabel: Record<string, string> = {
  tfsa: 'TFSA',
  rrsp: 'RRSP',
  fhsa: 'FHSA',
  non_reg: 'Non-Reg',
  rrif: 'RRIF',
  lira: 'LIRA',
  resp: 'RESP',
  corporate: 'Corp',
}
