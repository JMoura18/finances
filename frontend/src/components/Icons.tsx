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
export const BellIcon = (p: P) => (
  <svg {...base} {...p}><path d="M6 8a6 6 0 0 1 12 0c0 7 3 8 3 8H3s3-1 3-8" /><path d="M10 21a2 2 0 0 0 4 0" /></svg>
)
export const CalibrationIcon = (p: P) => (
  <svg {...base} {...p}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /><path d="M3 12a9 9 0 0 1 9-9" stroke="currentColor" strokeOpacity="0.5" /></svg>
)
export const NewsIcon = (p: P) => (
  <svg {...base} {...p}><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M7 9h7" /><path d="M7 13h7" /><path d="M7 17h4" /></svg>
)
export const SearchIcon = (p: P) => (
  <svg {...base} {...p}><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.5-4.5" /></svg>
)
export const LinkIcon = (p: P) => (
  <svg {...base} {...p}><path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" /><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" /></svg>
)
