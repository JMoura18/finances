import { Routes, Route, Navigate } from 'react-router-dom'
import { Shell } from './components/Shell'
import { DashboardPage } from './pages/Dashboard'
import { HoldingsPage } from './pages/Holdings'
import { HoldingDetailPage } from './pages/HoldingDetail'
import { AccountsPage } from './pages/Accounts'
import { ForecastPage } from './pages/Forecast'
import { RiskPage } from './pages/Risk'
import { TaxPage } from './pages/Tax'
import { RebalancePage } from './pages/Rebalance'
import { TransactionsPage } from './pages/Transactions'
import { AlertsPage } from './pages/Alerts'
import { CalibrationPage } from './pages/Calibration'

export default function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/accounts" element={<AccountsPage />} />
        <Route path="/holdings" element={<HoldingsPage />} />
        <Route path="/holdings/:id" element={<HoldingDetailPage />} />
        <Route path="/transactions" element={<TransactionsPage />} />
        <Route path="/forecast" element={<ForecastPage />} />
        <Route path="/risk" element={<RiskPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/tax" element={<TaxPage />} />
        <Route path="/rebalance" element={<RebalancePage />} />
        <Route path="/calibration" element={<CalibrationPage />} />
      </Routes>
    </Shell>
  )
}
