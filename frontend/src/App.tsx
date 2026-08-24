import { Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './hooks/useTheme'
import Header from './components/Header'
import ErrorBoundary from './components/ErrorBoundary'
import LandingPage from './pages/LandingPage'
import AnalysisProgressPage from './pages/AnalysisProgressPage'
import DashboardPage from './pages/DashboardPage'

function App() {
  return (
    <ThemeProvider>
      <ErrorBoundary>
        <div className="min-h-screen bg-white dark:bg-[#0d1117] text-gray-900 dark:text-[#e6edf3] flex flex-col font-sans transition-colors duration-150">
          <Header />
          <main className="flex-1 flex flex-col">
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/analysis/:jobId" element={<AnalysisProgressPage />} />
              <Route path="/repo/:repoId" element={<DashboardPage />} />
            </Routes>
          </main>
        </div>
      </ErrorBoundary>
    </ThemeProvider>
  )
}

export default App
