import { useState, useEffect } from 'react'

// ============================================================================
// TypeScript Types (inline for MVP)
// ============================================================================

interface ContractQuestion {
  question_id: string
  question: string
  context: string
  suggested_answers: string[]
  answer?: string
  answered_by?: string
  answered_at?: string
}

interface ContractColumn {
  name: string
  description: string
  data_type: string
  nullable: boolean
  constraints: string[]
}

interface ContractRelationship {
  type: string
  column: string
  references_table: string
  references_column: string
  description: string
}

interface ContractMetadata {
  contract_id: string
  status: 'draft' | 'approved'
  created_at: string
  approved_by?: string
  approved_at?: string
  confidence_score?: number
}

interface Contract {
  table_name: string
  schema_name: string
  description: string
  purpose: string
  columns: ContractColumn[]
  relationships: ContractRelationship[]
  questions: ContractQuestion[]
  metadata: ContractMetadata
  row_count?: number
}

interface ContractSummary {
  contract_id: string
  table_name: string
  schema_name: string
  status: 'draft' | 'approved'
  created_at: string
  total_questions: number
  unanswered_questions: number
  confidence_score?: number
}

interface SchemaChange {
  change_type: string
  table_name: string
  column_name?: string
  severity: 'critical' | 'warning' | 'info'
  description: string
  breaking_change: boolean
}

interface DriftSummary {
  total_tables_monitored: number
  tables_with_drift: number
  total_changes: number
  by_severity: {
    critical: number
    warning: number
    info: number
  }
  tables: Array<{
    table_name: string
    drift_detected: boolean
    change_count: number
  }>
}

// ============================================================================
// Main App Component
// ============================================================================

function App() {
  const [contracts, setContracts] = useState<ContractSummary[]>([])
  const [selectedContract, setSelectedContract] = useState<Contract | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [approverName, setApproverName] = useState('')
  const [driftSummary, setDriftSummary] = useState<DriftSummary | null>(null)
  const [showDriftAlert, setShowDriftAlert] = useState(false)

  const API_BASE = 'http://localhost:8000/api'

  // Load contracts on mount
  useEffect(() => {
    loadContracts()
  }, [])

  // Polling service: Check for drift every 30 seconds
  useEffect(() => {
    const checkDrift = async () => {
      try {
        const response = await fetch(`${API_BASE}/drift/summary/all`)
        if (response.ok) {
          const summary: DriftSummary = await response.json()
          setDriftSummary(summary)
          
          // Show alert if drift detected
          if (summary.tables_with_drift > 0) {
            setShowDriftAlert(true)
          } else {
            setShowDriftAlert(false)
          }
        }
      } catch (err) {
        console.error('Failed to check drift:', err)
      }
    }

    // Check immediately on mount
    checkDrift()

    // Then check every 30 seconds
    const interval = setInterval(checkDrift, 30000)

    return () => clearInterval(interval)
  }, [])

  const loadContracts = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/contracts`)
      if (!response.ok) throw new Error('Failed to load contracts')
      const data = await response.json()
      setContracts(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load contracts')
    } finally {
      setLoading(false)
    }
  }

  const loadContractDetails = async (contractId: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/contracts/${contractId}`)
      if (!response.ok) throw new Error('Failed to load contract details')
      const data = await response.json()
      setSelectedContract(data)
      
      // Initialize answers from existing answers
      const existingAnswers: Record<string, string> = {}
      data.questions.forEach((q: ContractQuestion) => {
        if (q.answer) {
          existingAnswers[q.question_id] = q.answer
        }
      })
      setAnswers(existingAnswers)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load contract')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    if (!selectedContract || !approverName.trim()) {
      setError('Please enter your name to approve')
      return
    }

    setLoading(true)
    setError(null)
    try {
      // Build answers array from the answers state
      const answersArray = Object.entries(answers)
        .filter(([_, answer]) => answer.trim())
        .map(([question_id, answer]) => ({
          question_id,
          answer,
          answered_by: approverName
        }))

      const response = await fetch(
        `${API_BASE}/contracts/${selectedContract.metadata.contract_id}/approve`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            approved_by: approverName,
            notes: `Approved with ${answersArray.length} answers`,
            answers: answersArray.length > 0 ? answersArray : undefined
          })
        }
      )

      if (!response.ok) throw new Error('Failed to approve contract')
      
      // Success! Reload contracts and clear selection
      await loadContracts()
      setSelectedContract(null)
      setAnswers({})
      setApproverName('')
      alert('Contract approved successfully!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve contract')
    } finally {
      setLoading(false)
    }
  }

  const handleAnswerChange = (questionId: string, value: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }))
  }

  // ============================================================================
  // Render: Contract List View
  // ============================================================================

  if (!selectedContract) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <header className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              DataContractIQ
            </h1>
            <p className="text-xl text-gray-600">
              Contract Review & Approval
            </p>
          </header>
          {/* Drift Alert Banner */}
          {showDriftAlert && driftSummary && driftSummary.tables_with_drift > 0 && (
            <div className="max-w-4xl mx-auto mb-4">
              <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg shadow-md">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div className="ml-3 flex-1">
                    <h3 className="text-lg font-medium text-red-800">
                      ⚠️ Schema Drift Detected
                    </h3>
                    <div className="mt-2 text-sm text-red-700">
                      <p className="mb-2">
                        <strong>{driftSummary.tables_with_drift}</strong> table(s) have schema changes that violate approved contracts:
                      </p>
                      <ul className="list-disc list-inside space-y-1">
                        {driftSummary.tables.filter(t => t.drift_detected).map(table => (
                          <li key={table.table_name}>
                            <strong>{table.table_name}</strong>: {table.change_count} change(s)
                          </li>
                        ))}
                      </ul>
                      {driftSummary.by_severity.critical > 0 && (
                        <p className="mt-2 font-semibold">
                          🔴 {driftSummary.by_severity.critical} CRITICAL change(s) detected
                        </p>
                      )}
                    </div>
                    <div className="mt-3 flex gap-2">
                      <button
                        onClick={() => setShowDriftAlert(false)}
                        className="text-sm px-3 py-1 bg-red-100 hover:bg-red-200 text-red-800 rounded"
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}


          {error && (
            <div className="max-w-4xl mx-auto mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          <div className="max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold">Contracts</h2>
              <button
                onClick={loadContracts}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Loading...' : 'Refresh'}
              </button>
            </div>

            {loading && contracts.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                Loading contracts...
              </div>
            ) : contracts.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No contracts found. Generate one using the MCP tools.
              </div>
            ) : (
              <div className="space-y-4">
                {contracts.map(contract => (
                  <div
                    key={contract.contract_id}
                    className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
                    onClick={() => loadContractDetails(contract.contract_id)}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-2">
                        <div>
                          <h3 className="text-xl font-semibold text-gray-900">
                            {contract.table_name}
                          </h3>
                          <p className="text-sm text-gray-500">
                            Schema: {contract.schema_name}
                          </p>
                        </div>
                        {/* Drift Status Indicator */}
                        {contract.status === 'approved' && driftSummary && (
                          <>
                            {driftSummary.tables.find(t => t.table_name === contract.table_name)?.drift_detected ? (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800" title="Schema drift detected">
                                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                </svg>
                                Drift
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800" title="No drift detected">
                                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                OK
                              </span>
                            )}
                          </>
                        )}
                      </div>
                      <StatusBadge status={contract.status} />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Questions:</span>
                        <span className="ml-2 font-medium">
                          {contract.total_questions} total
                          {contract.unanswered_questions > 0 && (
                            <span className="text-amber-600">
                              {' '}({contract.unanswered_questions} unanswered)
                            </span>
                          )}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Created:</span>
                        <span className="ml-2 font-medium">
                          {new Date(contract.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>

                    {contract.confidence_score && (
                      <div className="mt-3 text-sm">
                        <span className="text-gray-600">AI Confidence:</span>
                        <span className="ml-2 font-medium">
                          {Math.round(contract.confidence_score * 100)}%
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // ============================================================================
  // Render: Contract Detail & Review View
  // ============================================================================

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <button
              onClick={() => {
                setSelectedContract(null)
                setAnswers({})
              }}
              className="text-blue-600 hover:text-blue-800 mb-4"
            >
              ← Back to Contracts
            </button>
            
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  {selectedContract.table_name}
                </h1>
                <p className="text-gray-600">{selectedContract.description}</p>
              </div>
              <StatusBadge status={selectedContract.metadata.status} />
            </div>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          {/* Contract Overview */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Overview</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Schema:</span>
                <span className="ml-2 font-medium">{selectedContract.schema_name}</span>
              </div>
              <div>
                <span className="text-gray-600">Columns:</span>
                <span className="ml-2 font-medium">{selectedContract.columns.length}</span>
              </div>
              <div>
                <span className="text-gray-600">Relationships:</span>
                <span className="ml-2 font-medium">{selectedContract.relationships.length}</span>
              </div>
              {selectedContract.row_count && (
                <div>
                  <span className="text-gray-600">Rows:</span>
                  <span className="ml-2 font-medium">{selectedContract.row_count.toLocaleString()}</span>
                </div>
              )}
            </div>
            <div className="mt-4">
              <p className="text-sm text-gray-700">
                <span className="font-medium">Purpose:</span> {selectedContract.purpose}
              </p>
            </div>
          </div>

          {/* Questions Section */}
          {selectedContract.questions.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4">
                Questions ({selectedContract.questions.length})
              </h2>
              <p className="text-sm text-gray-600 mb-4">
                Answer questions to improve contract quality (optional for approval)
              </p>
              
              <div className="space-y-6">
                {selectedContract.questions.map((question, idx) => (
                  <div key={question.question_id} className="border-l-4 border-blue-500 pl-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-medium text-gray-900">
                        Q{idx + 1}: {question.question}
                      </h3>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-3">
                      {question.context}
                    </p>

                    {question.suggested_answers.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs text-gray-500 mb-1">Suggestions:</p>
                        <div className="flex flex-wrap gap-2">
                          {question.suggested_answers.map((suggestion, i) => (
                            <button
                              key={i}
                              onClick={() => handleAnswerChange(question.question_id, suggestion)}
                              className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded"
                            >
                              {suggestion}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    <textarea
                      value={answers[question.question_id] || ''}
                      onChange={(e) => handleAnswerChange(question.question_id, e.target.value)}
                      placeholder="Your answer (optional)..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                      rows={2}
                      disabled={selectedContract.metadata.status === 'approved'}
                    />

                    {question.answer && question.answered_by && (
                      <p className="text-xs text-green-600 mt-2">
                        ✓ Answered by {question.answered_by}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Columns Section */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">
              Columns ({selectedContract.columns.length})
            </h2>
            <div className="space-y-3">
              {selectedContract.columns.map(column => (
                <div key={column.name} className="border-l-2 border-gray-300 pl-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">
                        {column.name}
                        <span className="ml-2 text-sm text-gray-500">
                          {column.data_type}
                        </span>
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">{column.description}</p>
                      {column.constraints.length > 0 && (
                        <div className="flex gap-2 mt-2">
                          {column.constraints.map((constraint, i) => (
                            <span key={i} className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                              {constraint}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    {column.nullable && (
                      <span className="text-xs text-gray-500">nullable</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Relationships Section */}
          {selectedContract.relationships.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4">
                Relationships ({selectedContract.relationships.length})
              </h2>
              <div className="space-y-3">
                {selectedContract.relationships.map((rel, idx) => (
                  <div key={idx} className="border-l-2 border-purple-300 pl-3">
                    <h3 className="font-medium text-gray-900">
                      {rel.column} → {rel.references_table}.{rel.references_column}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">{rel.description}</p>
                    <p className="text-xs text-gray-500 mt-1">Type: {rel.type}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Approval Section */}
          {selectedContract.metadata.status === 'draft' && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Approve Contract</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Your Name *
                  </label>
                  <input
                    type="text"
                    value={approverName}
                    onChange={(e) => setApproverName(e.target.value)}
                    placeholder="Enter your name"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
                  />
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={handleApprove}
                    disabled={loading || !approverName.trim()}
                    className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    {loading ? 'Approving...' : 'Approve Contract'}
                  </button>
                </div>

                <p className="text-xs text-gray-500">
                  Note: Questions are optional. You can approve without answering all questions.
                </p>
              </div>
            </div>
          )}

          {selectedContract.metadata.status === 'approved' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-green-800 mb-2">
                ✓ Contract Approved
              </h2>
              <p className="text-sm text-green-700">
                Approved by {selectedContract.metadata.approved_by} on{' '}
                {selectedContract.metadata.approved_at && 
                  new Date(selectedContract.metadata.approved_at).toLocaleString()}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Helper Components
// ============================================================================

function StatusBadge({ status }: { status: 'draft' | 'approved' }) {
  const styles = {
    draft: 'bg-amber-100 text-amber-800',
    approved: 'bg-green-100 text-green-800'
  }

  const labels = {
    draft: 'Draft',
    approved: 'Approved'
  }

  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${styles[status]}`}>
      {labels[status]}
    </span>
  )
}

export default App

// Made with Bob
