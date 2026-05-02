import { useState } from 'react'

function App() {
  const [apiStatus, setApiStatus] = useState<string>('Checking...')

  // Check API health on mount
  const checkAPI = async () => {
    try {
      const response = await fetch('http://localhost:8000/health')
      const data = await response.json()
      setApiStatus(`✓ Connected - ${data.service} v${data.version}`)
    } catch (error) {
      setApiStatus('✗ API not available')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            DataContractIQ
          </h1>
          <p className="text-xl text-gray-600">
            AI-Powered Data Contract Generation & Drift Detection
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Using IBM Bob for Context-Aware Analysis
          </p>
        </header>

        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-2xl font-semibold mb-4">System Status</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="font-medium">Frontend</span>
                <span className="text-green-600">✓ Running on port 5173</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="font-medium">Backend API</span>
                <button 
                  onClick={checkAPI}
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  {apiStatus}
                </button>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold mb-4">Implementation Phases</h2>
            <div className="space-y-3">
              <PhaseCard 
                phase="1" 
                title="Project Foundation & Database Setup" 
                status="in-progress"
              />
              <PhaseCard 
                phase="2" 
                title="Schema Introspection Engine" 
                status="pending"
              />
              <PhaseCard 
                phase="3" 
                title="AI Contract Generation (Stage 1)" 
                status="pending"
              />
              <PhaseCard 
                phase="4" 
                title="Review Interface (Stage 2)" 
                status="pending"
              />
              <PhaseCard 
                phase="5" 
                title="Drift Detection System (Stage 3)" 
                status="pending"
              />
              <PhaseCard 
                phase="6" 
                title="Demo Integration & Testing" 
                status="pending"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

interface PhaseCardProps {
  phase: string
  title: string
  status: 'pending' | 'in-progress' | 'complete'
}

function PhaseCard({ phase, title, status }: PhaseCardProps) {
  const statusColors = {
    pending: 'bg-gray-100 text-gray-600',
    'in-progress': 'bg-yellow-100 text-yellow-800',
    complete: 'bg-green-100 text-green-800'
  }

  const statusLabels = {
    pending: 'Pending',
    'in-progress': 'In Progress',
    complete: 'Complete'
  }

  return (
    <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
      <div className="flex items-center gap-3">
        <span className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-semibold">
          {phase}
        </span>
        <span className="font-medium text-gray-900">{title}</span>
      </div>
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[status]}`}>
        {statusLabels[status]}
      </span>
    </div>
  )
}

export default App

// Made with Bob
