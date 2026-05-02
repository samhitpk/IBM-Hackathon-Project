# Skill: React Component Development

## Purpose
Build reusable, type-safe React components for DataContractIQ frontend using TypeScript and modern React patterns.

## When to Use
- Creating UI components for contract viewing and editing
- Building interactive forms and question cards
- Implementing data visualization
- Managing component state and API interactions

## Process

### 1. Component Structure

```
frontend/src/
├── components/
│   ├── contracts/
│   │   ├── ContractViewer.tsx
│   │   ├── ContractEditor.tsx
│   │   ├── ContractList.tsx
│   ├── schema/
│   │   ├── SchemaViewer.tsx
│   │   ├── TableCard.tsx
│   │   ├── ColumnList.tsx
│   ├── drift/
│   │   ├── DriftAlert.tsx
│   │   ├── DriftDashboard.tsx
│   │   ├── ChangeComparison.tsx
│   ├── review/
│   │   ├── QuestionCard.tsx
│   │   ├── ApprovalButton.tsx
│   │   ├── ReviewPanel.tsx
│   ├── common/
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Loading.tsx
│   │   ├── ErrorBoundary.tsx
├── hooks/
│   ├── useContract.ts
│   ├── useDrift.ts
│   ├── useSchema.ts
├── types/
│   ├── contract.ts
│   ├── schema.ts
│   ├── alert.ts
├── utils/
│   ├── api.ts
│   ├── formatting.ts
```

### 2. TypeScript Types

```typescript
// types/contract.ts
export interface Column {
  name: string;
  dataType: string;
  nullable: boolean;
  defaultValue?: string;
  description?: string;
  primaryKey: boolean;
  foreignKey?: string;
}

export interface BusinessRule {
  id: string;
  description: string;
  type: 'constraint' | 'validation' | 'calculation';
  expression?: string;
}

export interface Question {
  id: string;
  text: string;
  columnName?: string;
  options: string[];
  answer?: string;
}

export interface Contract {
  id: string;
  tableName: string;
  purpose: string;
  owner?: string;
  columns: Column[];
  businessRules: BusinessRule[];
  relationships: Relationship[];
  questions: Question[];
  status: 'draft' | 'approved' | 'rejected';
  createdAt: string;
  approvedAt?: string;
  approvedBy?: string;
}

// types/alert.ts
export interface DriftAlert {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  tableName: string;
  changeType: string;
  details: Record<string, any>;
  detectedAt: string;
  acknowledged: boolean;
  impactAnalysis: {
    affectedQueries: number;
    affectedPipelines: string[];
    breakingChange: boolean;
    riskLevel: string;
  };
}
```

### 3. Contract Viewer Component

```typescript
// components/contracts/ContractViewer.tsx
import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Contract } from '@/types/contract';

interface ContractViewerProps {
  contract: Contract;
  onEdit?: () => void;
  onApprove?: () => void;
}

export const ContractViewer: React.FC<ContractViewerProps> = ({
  contract,
  onEdit,
  onApprove
}) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="border-b pb-4 mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Data Contract: {contract.tableName}
            </h1>
            <p className="text-gray-600 mt-2">{contract.purpose}</p>
          </div>
          <div className="flex gap-2">
            {contract.status === 'draft' && (
              <>
                {onEdit && (
                  <button
                    onClick={onEdit}
                    className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded"
                  >
                    Edit
                  </button>
                )}
                {onApprove && (
                  <button
                    onClick={onApprove}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
                  >
                    Approve
                  </button>
                )}
              </>
            )}
            {contract.status === 'approved' && (
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                ✓ Approved
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Schema Definition */}
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Schema Definition</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Column
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Nullable
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Default
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Description
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {contract.columns.map((column) => (
                <tr key={column.name} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="font-medium text-gray-900">
                        {column.name}
                      </span>
                      {column.primaryKey && (
                        <span className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                          PK
                        </span>
                      )}
                      {column.foreignKey && (
                        <span className="ml-2 px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded">
                          FK
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {column.dataType}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {column.nullable ? (
                      <span className="text-gray-500">Yes</span>
                    ) : (
                      <span className="text-red-600 font-medium">No</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {column.defaultValue || '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    {column.description || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Business Rules */}
      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Business Rules</h2>
        <div className="space-y-3">
          {contract.businessRules.map((rule, index) => (
            <div key={rule.id} className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-start">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  {index + 1}
                </span>
                <div className="ml-3 flex-1">
                  <p className="text-gray-900">{rule.description}</p>
                  {rule.expression && (
                    <code className="mt-2 block text-sm text-gray-600 bg-white p-2 rounded">
                      {rule.expression}
                    </code>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Questions (if any) */}
      {contract.questions.length > 0 && (
        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">
            Questions for Review
          </h2>
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <p className="text-sm text-yellow-700">
              {contract.questions.length} question(s) need your attention
            </p>
          </div>
        </section>
      )}
    </div>
  );
};
```

### 4. Question Card Component

```typescript
// components/review/QuestionCard.tsx
import React, { useState } from 'react';
import { Question } from '@/types/contract';

interface QuestionCardProps {
  question: Question;
  onAnswer: (questionId: string, answer: string) => void;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  onAnswer
}) => {
  const [selectedOption, setSelectedOption] = useState<string>(
    question.answer || ''
  );
  const [customAnswer, setCustomAnswer] = useState('');

  const handleSelect = (option: string) => {
    setSelectedOption(option);
    if (option !== 'Other') {
      onAnswer(question.id, option);
    }
  };

  const handleCustomSubmit = () => {
    if (customAnswer.trim()) {
      onAnswer(question.id, customAnswer);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      {/* Question Header */}
      <div className="flex items-start mb-4">
        <div className="flex-shrink-0 w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
          <span className="text-yellow-600 text-lg">?</span>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-lg font-medium text-gray-900">
            {question.text}
          </h3>
          {question.columnName && (
            <p className="text-sm text-gray-500 mt-1">
              Related to column: <code className="bg-gray-100 px-2 py-1 rounded">{question.columnName}</code>
            </p>
          )}
        </div>
      </div>

      {/* Options */}
      <div className="space-y-2">
        {question.options.map((option) => (
          <label
            key={option}
            className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
              selectedOption === option
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:bg-gray-50'
            }`}
          >
            <input
              type="radio"
              name={`question-${question.id}`}
              value={option}
              checked={selectedOption === option}
              onChange={() => handleSelect(option)}
              className="w-4 h-4 text-blue-600"
            />
            <span className="ml-3 text-gray-900">{option}</span>
          </label>
        ))}
      </div>

      {/* Custom Answer Input */}
      {selectedOption === 'Other' && (
        <div className="mt-4">
          <textarea
            value={customAnswer}
            onChange={(e) => setCustomAnswer(e.target.value)}
            placeholder="Please specify..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={3}
          />
          <button
            onClick={handleCustomSubmit}
            disabled={!customAnswer.trim()}
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Submit Answer
          </button>
        </div>
      )}
    </div>
  );
};
```

### 5. Drift Alert Component

```typescript
// components/drift/DriftAlert.tsx
import React from 'react';
import { DriftAlert as Alert } from '@/types/alert';

interface DriftAlertProps {
  alert: Alert;
  onAcknowledge?: (alertId: string) => void;
}

export const DriftAlert: React.FC<DriftAlertProps> = ({
  alert,
  onAcknowledge
}) => {
  const severityColors = {
    low: 'bg-blue-50 border-blue-200 text-blue-800',
    medium: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    high: 'bg-orange-50 border-orange-200 text-orange-800',
    critical: 'bg-red-50 border-red-200 text-red-800'
  };

  const severityIcons = {
    low: 'ℹ️',
    medium: '⚠️',
    high: '⚠️',
    critical: '🚨'
  };

  return (
    <div className={`border-l-4 p-4 rounded-r-lg ${severityColors[alert.severity]}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start flex-1">
          <span className="text-2xl mr-3">{severityIcons[alert.severity]}</span>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold text-lg">
                Schema Drift Detected: {alert.tableName}
              </h3>
              <span className="px-2 py-1 text-xs font-medium rounded uppercase">
                {alert.severity}
              </span>
            </div>
            
            <p className="text-sm mb-3">
              <strong>Change Type:</strong> {alert.changeType}
            </p>

            {/* Change Details */}
            <div className="bg-white bg-opacity-50 p-3 rounded mb-3">
              <pre className="text-sm overflow-x-auto">
                {JSON.stringify(alert.details, null, 2)}
              </pre>
            </div>

            {/* Impact Analysis */}
            {alert.impactAnalysis && (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="font-medium">Impact:</span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    alert.impactAnalysis.breakingChange
                      ? 'bg-red-100 text-red-800'
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {alert.impactAnalysis.breakingChange ? 'Breaking' : 'Non-Breaking'}
                  </span>
                </div>
                
                {alert.impactAnalysis.affectedPipelines.length > 0 && (
                  <div>
                    <span className="font-medium">Affected Pipelines:</span>
                    <ul className="list-disc list-inside ml-4">
                      {alert.impactAnalysis.affectedPipelines.map((pipeline) => (
                        <li key={pipeline}>{pipeline}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            <p className="text-xs mt-3 opacity-75">
              Detected: {new Date(alert.detectedAt).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Actions */}
        {!alert.acknowledged && onAcknowledge && (
          <button
            onClick={() => onAcknowledge(alert.id)}
            className="ml-4 px-3 py-1 bg-white hover:bg-gray-100 border border-gray-300 rounded text-sm"
          >
            Acknowledge
          </button>
        )}
      </div>
    </div>
  );
};
```

### 6. Custom Hooks for API Integration

```typescript
// hooks/useContract.ts
import { useState, useEffect } from 'react';
import { Contract } from '@/types/contract';
import { api } from '@/utils/api';

export const useContract = (contractId: string) => {
  const [contract, setContract] = useState<Contract | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContract = async () => {
      try {
        setLoading(true);
        const data = await api.get<Contract>(`/api/contracts/${contractId}`);
        setContract(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load contract');
      } finally {
        setLoading(false);
      }
    };

    fetchContract();
  }, [contractId]);

  const updateContract = async (updates: Partial<Contract>) => {
    try {
      const updated = await api.put<Contract>(
        `/api/contracts/${contractId}`,
        updates
      );
      setContract(updated);
      return updated;
    } catch (err) {
      throw new Error('Failed to update contract');
    }
  };

  const approveContract = async (approver: string) => {
    try {
      const approved = await api.post<Contract>(
        `/api/contracts/${contractId}/approve`,
        { approver }
      );
      setContract(approved);
      return approved;
    } catch (err) {
      throw new Error('Failed to approve contract');
    }
  };

  return {
    contract,
    loading,
    error,
    updateContract,
    approveContract
  };
};
```

### 7. API Utility

```typescript
// utils/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }
}

export const api = new ApiClient(API_BASE_URL);
```

## Best Practices

- Use TypeScript for type safety
- Implement proper error boundaries
- Use React Query for API state management
- Keep components small and focused
- Use composition over inheritance
- Implement loading and error states
- Make components accessible (ARIA labels)
- Use TailwindCSS for consistent styling
- Implement proper form validation
- Use React.memo for performance optimization

## Integration with Other Skills
- Consumes APIs from **API_DEVELOPMENT** skill
- Displays contracts from **CONTRACT_GENERATION**
- Shows alerts from **DRIFT_DETECTION**
- Provides UI for contract review workflow