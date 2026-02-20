import { useState, useMemo, useEffect, createContext, useContext, lazy, Suspense } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import { applyRouteInstrumentation } from './lib/siteInstrumentation'

const Upload = lazy(() => import('./pages/Upload'))
const Overview = lazy(() => import('./pages/Overview'))
const AtRisk = lazy(() => import('./pages/AtRisk'))
const GapAnalysis = lazy(() => import('./pages/GapAnalysis'))
const SubjectAnalysis = lazy(() => import('./pages/SubjectAnalysis'))
const StudentProfile = lazy(() => import('./pages/StudentProfile'))
const Reports = lazy(() => import('./pages/Reports'))
const TermComparison = lazy(() => import('./pages/TermComparison'))

// Global data context
export const DataContext = createContext(null)

export function useData() {
  return useContext(DataContext)
}

export default function App() {
  const location = useLocation()
  const currentYear = new Date().getFullYear()
  const [rawData, setRawData] = useState(null)          // full cleaned data records
  const [sessionId, setSessionId] = useState(null) // upload session_id
  const [fileName, setFileName] = useState('')
  const [selectedClass, setSelectedClass] = useState('')

  const classOptions = useMemo(() => {
    if (!Array.isArray(rawData) || rawData.length === 0) return []
    const values = new Set()
    rawData.forEach((row) => {
      const v = row?.class ?? row?.grade ?? row?.form ?? null
      if (v !== null && v !== undefined && String(v).trim() !== '') {
        values.add(String(v))
      }
    })
    return Array.from(values).sort()
  }, [rawData])

  const schoolName = useMemo(() => {
    if (!Array.isArray(rawData) || rawData.length === 0) return ''
    const keys = ['school_name', 'school', 'institution']
    const counts = new Map()

    rawData.forEach((row) => {
      let value = ''
      for (const key of keys) {
        const candidate = row?.[key]
        if (candidate !== null && candidate !== undefined && String(candidate).trim() !== '') {
          value = String(candidate).trim()
          break
        }
      }
      if (!value) return
      counts.set(value, (counts.get(value) || 0) + 1)
    })

    let best = ''
    let bestCount = 0
    counts.forEach((count, value) => {
      if (count > bestCount) {
        best = value
        bestCount = count
      }
    })
    return best
  }, [rawData])

  useEffect(() => {
    if (!classOptions.length) {
      setSelectedClass('')
      return
    }
    if (!selectedClass || !classOptions.includes(selectedClass)) {
      setSelectedClass(classOptions[0])
    }
  }, [classOptions, selectedClass])

  // All analytics in the app run on selected class only.
  const data = useMemo(() => {
    if (!Array.isArray(rawData)) return null
    if (!selectedClass) return rawData
    return rawData.filter((row) => {
      const v = row?.class ?? row?.grade ?? row?.form ?? null
      return v !== null && String(v) === selectedClass
    })
  }, [rawData, selectedClass])

  useEffect(() => {
    applyRouteInstrumentation(location.pathname)
  }, [location.pathname])

  return (
    <DataContext.Provider value={{
      data,
      rawData,
      setData: setRawData,
      schoolName,
      sessionId,
      setSessionId,
      fileName,
      setFileName,
      classOptions,
      selectedClass,
      setSelectedClass,
    }}>
      <div className="flex h-screen overflow-hidden bg-surface">
        <Sidebar
          hasData={!!data}
          schoolName={schoolName}
          classOptions={classOptions}
          selectedClass={selectedClass}
          setSelectedClass={setSelectedClass}
        />
        <main className="flex-1 min-w-0 flex flex-col">
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
              <Suspense fallback={<div className="py-24 text-center text-sm text-gray-500">Loading page...</div>}>
                <Routes>
                  <Route path="/" element={<Upload />} />
                  <Route path="/overview" element={data ? <Overview /> : <Navigate to="/" />} />
                  <Route path="/at-risk" element={data ? <AtRisk /> : <Navigate to="/" />} />
                  <Route path="/gaps" element={data ? <GapAnalysis /> : <Navigate to="/" />} />
                  <Route path="/subjects" element={data ? <SubjectAnalysis /> : <Navigate to="/" />} />
                  <Route path="/student/:id" element={data ? <StudentProfile /> : <Navigate to="/" />} />
                  <Route path="/reports" element={data ? <Reports /> : <Navigate to="/" />} />
                  <Route path="/term-comparison" element={data ? <TermComparison /> : <Navigate to="/" />} />
                </Routes>
              </Suspense>
            </div>
          </div>
          <footer className="shrink-0 border-t border-gray-200 bg-white/80">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-xs text-gray-600 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div className="flex flex-wrap items-center gap-4">
                <a href="https://www.linkedin.com/in/pcodesdev/" target="_blank" rel="noopener noreferrer" className="hover:text-brand-accent">LinkedIn</a>
                <a href="https://github.com/pcodesdev" target="_blank" rel="noopener noreferrer" className="hover:text-brand-accent">GitHub</a>
                <a href="https://medium.com/@pcodesdev" target="_blank" rel="noopener noreferrer" className="hover:text-brand-accent">Medium</a>
                <a href="mailto:pcodesdev@gmail.com" className="hover:text-brand-accent">pcodesdev@gmail.com</a>
              </div>
              <div className="text-left md:text-right md:max-w-3xl">
                <p>
                  © {currentYear} EduMetrics. Open-source software provided "as is", without warranty of any kind.
                </p>
                <p className="mt-1">
                  Contributions are welcome. Support, bug reports, and feature requests can be shared via GitHub or email.
                </p>
              </div>
            </div>
          </footer>
        </main>
      </div>
    </DataContext.Provider>
  )
}
