import { SVGProps } from 'react'

type P = SVGProps<SVGSVGElement>
const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  viewBox: '0 0 24 24',
} as const

export const HomeIcon = (p: P) => (
  <svg {...base} {...p}><path d="M3 11 12 4l9 7" /><path d="M5 10v10h14V10" /></svg>
)
export const WalletIcon = (p: P) => (
  <svg {...base} {...p}><rect x="3" y="6" width="18" height="13" rx="2" /><path d="M16 13h2" /><path d="M3 9h13a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2H3" /></svg>
)
export const PieIcon = (p: P) => (
  <svg {...base} {...p}><path d="M12 3v9h9a9 9 0 1 1-9-9Z" /><path d="M21 12A9 9 0 0 0 12 3" /></svg>
)
export const ListIcon = (p: P) => (
  <svg {...base} {...p}><path d="M4 6h16" /><path d="M4 12h16" /><path d="M4 18h10" /></svg>
)
export const TrendingIcon = (p: P) => (
  <svg {...base} {...p}><path d="M3 17l6-6 4 4 8-8" /><path d="M14 7h7v7" /></svg>
)
export const ShieldIcon = (p: P) => (
  <svg {...base} {...p}><path d="M12 3 4 6v6c0 5 3.5 8.5 8 9 4.5-.5 8-4 8-9V6l-8-3Z" /></svg>
)
export const TaxIcon = (p: P) => (
  <svg {...base} {...p}><circle cx="12" cy="12" r="9" /><path d="M8 14l8-8" /><circle cx="9" cy="9" r="1" fill="currentColor" /><circle cx="15" cy="15" r="1" fill="currentColor" /></svg>
)
export const ScaleIcon = (p: P) => (
  <svg {...base} {...p}><path d="M12 4v16" /><path d="M5 20h14" /><path d="M3 10l3-6 3 6a3 3 0 1 1-6 0Z" /><path d="M15 12l3-6 3 6a3 3 0 1 1-6 0Z" /></svg>
)
export const PlusIcon = (p: P) => (
  <svg {...base} {...p}><path d="M12 5v14" /><path d="M5 12h14" /></svg>
)
export const SparkleIcon = (p: P) => (
  <svg {...base} {...p}><path d="M12 3v4" /><path d="M12 17v4" /><path d="M3 12h4" /><path d="M17 12h4" /><path d="M6 6l2.5 2.5" /><path d="M15.5 15.5 18 18" /><path d="M6 18l2.5-2.5" /><path d="M15.5 8.5 18 6" /></svg>
)
export const ArrowUpRight = (p: P) => (
  <svg {...base} {...p}><path d="M7 17 17 7" /><path d="M8 7h9v9" /></svg>
)
