# Implementation Plan: Contract Review & Approval System (MVP)

## 📋 Overview

This plan addresses three key enhancements to DataContractIQ:

1. **Ambiguity Detection**: Enhance MCP contract generation to identify and flag ambiguities as questions
2. **Review Interface**: Build a clean frontend UI for users to review contracts and answer questions
3. **Approval Workflow**: Implement API endpoints to handle question answers and contract approval

## 🎯 MVP Scope

**Simplified Requirements**:
- ✅ Questions are **optional** - users can approve with unanswered questions
- ✅ **No role-based access** - anyone can approve
- ✅ **No version history** - keep only latest version
- ✅ **Two statuses only**: DRAFT and APPROVED (no rejection workflow)
- ✅ **No notifications** system
- ✅ **No bulk operations** - one contract at a time
- ✅ **Export formats**: JSON and Markdown only (no PDF)

---

## 🎯 Requirements Summary

### 1. MCP Enhancement - Ambiguity Detection
**Current State**: Contract generation creates basic contracts without identifying ambiguities  
**Target State**: AI identifies unclear aspects and generates specific questions for human review

**Key Ambiguities to Detect**:
- Columns with generic names (e.g., "data", "value", "info") → Ask for business meaning
- Nullable columns without clear business reason → Ask if NULL has special meaning
- Columns without constraints that might need them → Ask about validation rules
- Foreign keys without clear relationship purpose → Ask about business relationship
- Columns with technical names → Ask for user-friendly descriptions
- Missing business rules that should exist → Ask about expected behaviors
- Data sensitivity unclear → Ask about PII/confidential data

### 2. Frontend Review Interface
**Current State**: Basic status page  
**Target State**: Full contract review and approval interface

**Key Features**:
- List all draft contracts awaiting review
- Display contract details in readable format
- Show flagged questions with context
- Allow users to answer questions inline
- Provide approval/rejection workflow
- Show contract history and status

### 3. Backend API Endpoints
**Current State**: Basic health check and schema endpoints  
**Target State**: Complete contract management API

**Required Endpoints**:
- `GET /api/contracts` - List all contracts with filtering
- `GET /api/contracts/{id}` - Get specific contract details
- `POST /api/contracts/{id}/answers` - Submit answers to questions
- `POST /api/contracts/{id}/approve` - Approve contract
- `POST /api/contracts/{id}/reject` - Reject contract with feedback
- `GET /api/contracts/{id}/history` - Get contract version history

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         IBM Bob (MCP)                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │  1. Introspect Schema                               │    │
│  │  2. Generate Contract with AI Analysis              │    │
│  │  3. Identify Ambiguities → Create Questions         │    │
│  │  4. Save Draft Contract to data/contracts/          │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Contract Management API                            │    │
│  │  - Read contracts from data/contracts/             │    │
│  │  - Serve to frontend                                │    │
│  │  - Accept answers & approval                        │    │
│  │  - Update contract status                           │    │
│  │  - Merge AI + Human insights                        │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Contract Review Interface                          │    │
│  │  - Dashboard: List pending contracts               │    │
│  │  - Review Page: Show contract + questions          │    │
│  │  - Answer Form: Inline question responses          │    │
│  │  - Approval Action: Approve/Reject workflow        │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Phase 1: Enhance MCP Contract Generation

### 1.1 Create Ambiguity Detection Module

**File**: `backend/app/core/ambiguity_detector.py`

**Purpose**: Analyze schema and identify areas needing human clarification

**Key Functions**:
```python
def detect_column_ambiguities(column: ColumnSchema) -> List[ContractQuestion]
def detect_relationship_ambiguities(fk: ForeignKey, table: TableSchema) -> List[ContractQuestion]
def detect_business_rule_gaps(table: TableSchema) -> List[ContractQuestion]
def detect_data_sensitivity_questions(column: ColumnSchema) -> List[ContractQuestion]
```

**Detection Rules**:
- Generic column names → "What does this column represent in business terms?"
- Nullable without reason → "What does NULL mean for this field?"
- No constraints on important fields → "Should this field have validation rules?"
- Foreign key without context → "What business relationship does this represent?"
- Potential PII fields → "Does this contain sensitive/personal data?"

### 1.2 Update Contract Generation Logic

**File**: `backend/mcp_server.py` - Function `_generate_contract_from_schema()`

**Changes**:
1. Import ambiguity detector
2. Run detection after basic contract creation
3. Add detected questions to contract.questions list
4. Increase confidence score when fewer ambiguities found
5. Add summary of questions to contract metadata

### 1.3 Update Contract Model

**File**: `backend/app/models/contract.py`

**Changes**:
- Ensure `ContractQuestion` model has all needed fields
- Add `question_category` field (e.g., "column_meaning", "business_rule", "data_sensitivity")
- Add `priority` field (high, medium, low)

---

## 🔧 Phase 2: Create FastAPI Endpoints

### 2.1 Create Contract Router

**File**: `backend/app/api/contracts.py`

**Endpoints**:

```python
@router.get("/contracts")
async def list_contracts(
    status: Optional[str] = None,
    table_name: Optional[str] = None
) -> List[ContractSummary]

@router.get("/contracts/{contract_id}")
async def get_contract(contract_id: str) -> ContractDetail

@router.post("/contracts/{contract_id}/answers")
async def submit_answers(
    contract_id: str,
    answers: List[QuestionAnswer]
) -> ContractDetail

@router.post("/contracts/{contract_id}/approve")
async def approve_contract(
    contract_id: str,
    approval: ApprovalRequest
) -> ContractDetail

@router.post("/contracts/{contract_id}/reject")
async def reject_contract(
    contract_id: str,
    rejection: RejectionRequest
) -> ContractDetail

@router.get("/contracts/{contract_id}/markdown")
async def get_contract_markdown(contract_id: str) -> str
```

### 2.2 Create Request/Response Models

**File**: `backend/app/api/models.py`

```python
class ContractSummary(BaseModel):
    contract_id: str
    table_name: str
    status: str
    created_at: datetime
    unanswered_questions: int
    
class QuestionAnswer(BaseModel):
    question_id: str
    answer: str
    answered_by: str
    
class ApprovalRequest(BaseModel):
    approved_by: str
    notes: Optional[str]
    
class RejectionRequest(BaseModel):
    rejected_by: str
    reason: str
```

### 2.3 Create Contract Service Layer

**File**: `backend/app/services/contract_service.py`

**Purpose**: Business logic for contract operations

**Key Functions**:
```python
def get_contracts_from_storage(status: Optional[str]) -> List[Dict]
def load_contract_with_details(contract_id: str) -> DataContract
def update_contract_answers(contract_id: str, answers: List[QuestionAnswer]) -> DataContract
def approve_contract_with_merge(contract_id: str, approval: ApprovalRequest) -> DataContract
def merge_ai_and_human_insights(contract: DataContract) -> DataContract
```

### 2.4 Update Main App

**File**: `backend/app/main.py`

**Changes**:
- Import and include contracts router
- Add CORS for contract endpoints

---

## 🔧 Phase 3: Build Frontend Review Interface

### 3.1 Create Type Definitions

**File**: `frontend/src/types/contract.ts`

```typescript
export interface Contract {
  contract_id: string
  table_name: string
  schema_name: string
  status: 'draft' | 'approved'  // MVP: Only two statuses
  columns: Column[]
  relationships: Relationship[]
  questions: Question[]
  metadata: ContractMetadata
}

export interface Question {
  question_id: string
  question: string
  context: string
  category: string
  priority: 'high' | 'medium' | 'low'
  suggested_answers: string[]
  answer?: string
  answered_by?: string
}
```

### 3.2 Create API Client

**File**: `frontend/src/utils/api.ts`

```typescript
export const contractAPI = {
  listContracts: (status?: string) => fetch(...),
  getContract: (id: string) => fetch(...),
  submitAnswers: (id: string, answers: QuestionAnswer[]) => fetch(...),
  approveContract: (id: string, approval: ApprovalRequest) => fetch(...)
  // MVP: No rejection workflow
}
```

### 3.3 Create Contract Dashboard Page

**File**: `frontend/src/pages/ContractDashboard.tsx`

**Features**:
- List all contracts with status badges
- Filter by status (draft, approved, rejected)
- Show key metrics (total questions, unanswered, etc.)
- Click to navigate to review page
- Visual indicators for priority

**Layout**:
```
┌─────────────────────────────────────────────────┐
│  📊 Contract Dashboard                          │
├─────────────────────────────────────────────────┤
│  Filters: [All] [Draft] [Approved]  │  // MVP: No rejected status
├─────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────┐ │
│  │ 📄 film (public)                    DRAFT │ │
│  │ Created: 2026-05-02                       │ │
│  │ Questions: 5 unanswered                   │ │
│  │ [Review →]                                │ │
│  └───────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────┐ │
│  │ 📄 customer (public)            APPROVED  │ │
│  │ Approved: 2026-05-01 by Sam               │ │
│  │ [View →]                                  │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 3.4 Create Contract Review Page

**File**: `frontend/src/pages/ContractReview.tsx`

**Features**:
- Display contract metadata and status
- Show all columns with descriptions
- Show relationships
- Display questions grouped by category
- Inline answer forms for each question
- Save answers button
- Approve button (always enabled - questions optional for MVP)

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│  📝 Review Contract: film                               │
│  Status: DRAFT | Created: 2026-05-02 | AI Confidence: 70% │
├─────────────────────────────────────────────────────────┤
│  📊 Table Overview                                      │
│  Schema: public | Rows: 1,000 | Columns: 14            │
├─────────────────────────────────────────────────────────┤
│  ❓ Questions Requiring Your Input (5)                  │
│  ┌───────────────────────────────────────────────────┐ │
│  │ 🔴 HIGH PRIORITY                                  │ │
│  │ Q1: What does the 'special_features' column       │ │
│  │     represent in business terms?                  │ │
│  │                                                   │ │
│  │ Context: This ARRAY column has a generic name... │ │
│  │                                                   │ │
│  │ Your Answer:                                      │ │
│  │ [Text area for answer]                            │ │
│  │                                                   │ │
│  │ Suggested: [Behind the scenes] [Deleted scenes]  │ │
│  └───────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────┐ │
│  │ ⚠️ MEDIUM PRIORITY                                │ │
│  │ Q2: Does 'description' contain sensitive data?   │ │
│  │ ...                                               │ │
│  └───────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  📋 Column Details (14 columns)                         │
│  [Expandable sections for each column]                  │
├─────────────────────────────────────────────────────────┤
│  🔗 Relationships (2)                                   │
│  [Foreign key details]                                  │
├─────────────────────────────────────────────────────────┤
│  [Save Answers] [Approve Contract]                     │
└─────────────────────────────────────────────────────────┘
```

### 3.5 Create Reusable Components

**Files**:
- `frontend/src/components/ContractCard.tsx` - Contract summary card
- `frontend/src/components/QuestionCard.tsx` - Individual question with answer form
- `frontend/src/components/ColumnDetails.tsx` - Column information display
- `frontend/src/components/StatusBadge.tsx` - Status indicator
- `frontend/src/components/ApprovalModal.tsx` - Approval confirmation dialog

### 3.6 Update App Router

**File**: `frontend/src/App.tsx`

**Changes**:
- Add React Router
- Create routes for dashboard and review pages
- Add navigation

---

## 🔧 Phase 4: Implement Approval Workflow

### 4.1 Answer Submission Flow

**Backend** (`backend/app/services/contract_service.py`):
```python
def update_contract_answers(contract_id: str, answers: List[QuestionAnswer]):
    1. Load contract from storage
    2. Find each question by ID
    3. Update question.answer, answered_by, answered_at
    4. Recalculate confidence score based on answers
    5. Save updated contract
    6. Return updated contract
```

**Frontend** (`frontend/src/pages/ContractReview.tsx`):
```typescript
const handleSaveAnswers = async () => {
    1. Collect all answered questions
    2. No validation needed - questions are optional for MVP
    3. Submit to API
    4. Show success message
    5. Refresh contract data
}
```

### 4.2 Contract Approval Flow

**Backend** (`backend/app/services/contract_service.py`):
```python
def approve_contract_with_merge(contract_id: str, approval: ApprovalRequest):
    1. Load contract from storage
    2. Skip validation - questions are optional for MVP
    3. Merge AI-generated content with human answers:
       - Update column descriptions with human context
       - Add business rules from answers
       - Update data sensitivity based on answers
       - Enhance relationship descriptions
    4. Update status to APPROVED
    5. Set approved_by, approved_at, approval_notes
    6. No version increment - MVP keeps only latest version
    7. Save approved contract (both JSON and Markdown)
    8. Return approved contract
```

**Frontend** (`frontend/src/components/ApprovalModal.tsx`):
```typescript
const handleApprove = async () => {
    1. Show confirmation modal
    2. Collect approval notes
    3. Submit approval request
    4. Show success message
    5. Navigate to dashboard
}
```

### 4.3 Merge Logic Details

**Purpose**: Combine AI-extracted technical details with human business context

**Merge Strategy**:
```python
def merge_ai_and_human_insights(contract: DataContract) -> DataContract:
    for question in contract.questions:
        if question.category == "column_meaning":
            # Update column description with human answer
            column = find_column(question.context)
            column.description = f"{question.answer} (Technical: {column.description})"
            
        elif question.category == "business_rule":
            # Add new business rule
            rule = BusinessRule(
                rule_id=generate_id(),
                description=question.answer,
                rule_type="business_logic",
                enforcement="application",
                examples=[]
            )
            contract.business_rules.append(rule)
            
        elif question.category == "data_sensitivity":
            # Update column sensitivity
            column = find_column(question.context)
            column.sensitivity = question.answer
            
    return contract
```

---

## 🔧 Phase 5: Testing & Integration

### 5.1 Backend Testing

**File**: `backend/tests/test_contract_workflow.py`

**Test Cases**:
- Test ambiguity detection generates appropriate questions
- Test contract creation with questions
- Test answer submission updates contract correctly
- Test approval merges AI + human insights
- Test rejection workflow
- Test contract listing and filtering

### 5.2 Frontend Testing

**Files**: `frontend/src/__tests__/`

**Test Cases**:
- Test contract list renders correctly
- Test question answering flow
- Test form validation
- Test approval/rejection actions
- Test navigation between pages

### 5.3 Integration Testing

**Scenarios**:
1. End-to-end: Generate contract → Review → Answer → Approve
2. Verify merged contract contains both AI and human insights
3. Test contract status transitions
4. Verify file system updates (JSON + Markdown)

### 5.4 UI/UX Polish

- Add loading states
- Add error handling and user feedback
- Add animations for smooth transitions
- Ensure responsive design
- Add keyboard shortcuts
- Add tooltips for guidance

---

## 📊 Data Flow Example

### Complete Workflow:

```
1. MCP Generates Contract
   ├─ Introspects 'film' table
   ├─ Creates basic contract
   ├─ Detects ambiguities:
   │  ├─ "What does 'special_features' mean?"
   │  ├─ "Does 'description' contain PII?"
   │  └─ "What business rule governs 'rental_rate'?"
   └─ Saves draft contract with questions

2. User Opens Frontend
   ├─ Sees 'film' contract in dashboard (DRAFT status)
   ├─ Clicks "Review"
   └─ Sees contract details + 3 questions

3. User Answers Questions
   ├─ Q1: "Array of special features like deleted scenes, trailers"
   ├─ Q2: "No, just movie synopsis"
   ├─ Q3: "Must be between $0.99 and $9.99"
   └─ Clicks "Save Answers"

4. Backend Updates Contract
   ├─ Loads contract
   ├─ Updates questions with answers
   └─ Saves updated contract

5. User Approves Contract
   ├─ Clicks "Approve Contract"
   ├─ Adds note: "Reviewed with product team"
   └─ Submits approval

6. Backend Merges & Finalizes
   ├─ Updates column descriptions with business context
   ├─ Adds business rule: "rental_rate range: $0.99-$9.99"
   ├─ Sets sensitivity: description = "public"
   ├─ Changes status to APPROVED
   ├─ Saves final contract (JSON + Markdown)
   └─ Returns approved contract

7. Result: Comprehensive Contract
   ├─ AI-extracted: Technical schema details
   ├─ Human-provided: Business context and rules
   └─ Combined: Complete, approved data contract
```

---

## 🎨 UI Design Principles

### Color Scheme
- **Draft**: Yellow/Amber (#F59E0B)
- **Approved**: Green (#10B981)
- **Rejected**: Red (#EF4444)
- **High Priority**: Red badge
- **Medium Priority**: Orange badge
- **Low Priority**: Blue badge

### Typography
- Headers: Bold, clear hierarchy
- Questions: Prominent, easy to read
- Context: Smaller, gray text
- Answers: Highlighted when filled

### Layout
- Clean, spacious design
- Card-based components
- Clear visual separation
- Responsive grid layout
- Sticky action buttons

---

## 📝 Implementation Checklist

### Phase 1: MCP Enhancement
- [ ] Create `ambiguity_detector.py` module
- [ ] Implement column ambiguity detection
- [ ] Implement relationship ambiguity detection
- [ ] Implement business rule gap detection
- [ ] Implement data sensitivity detection
- [ ] Update `_generate_contract_from_schema()` function
- [ ] Test contract generation with questions
- [ ] Verify questions are saved correctly

### Phase 2: Backend API (MVP Simplified)
- [ ] Create `contracts.py` router
- [ ] Create API request/response models (no rejection models)
- [ ] Implement list contracts endpoint (filter: draft/approved only)
- [ ] Implement get contract endpoint
- [ ] Implement submit answers endpoint (no validation)
- [ ] Implement approve contract endpoint (no question validation)
- [ ] Create `contract_service.py` with business logic
- [ ] Implement merge logic for AI + human insights
- [ ] Update `main.py` to include router
- [ ] Test all endpoints with Postman/curl

### Phase 3: Frontend UI (MVP Simplified)
- [ ] Create TypeScript type definitions (draft/approved only)
- [ ] Create API client utility (no reject endpoint)
- [ ] Install React Router
- [ ] Create ContractDashboard page (filter: draft/approved)
- [ ] Create ContractReview page (approve always enabled)
- [ ] Create ContractCard component
- [ ] Create QuestionCard component (optional answers)
- [ ] Create ColumnDetails component
- [ ] Create StatusBadge component (draft/approved only)
- [ ] Create ApprovalModal component (simple confirmation)
- [ ] Update App.tsx with routing
- [ ] Style with Tailwind CSS
- [ ] Add loading states
- [ ] Add error handling

### Phase 4: Approval Workflow (MVP Simplified)
- [ ] Implement answer submission in frontend (optional)
- [ ] Implement answer update in backend (no validation)
- [ ] Implement approval flow in frontend (no question check)
- [ ] Implement approval logic in backend (no validation)
- [ ] Implement merge logic (handle unanswered questions)
- [ ] Test complete workflow
- [ ] Verify merged contracts are correct

### Phase 5: Testing & Polish
- [ ] Write backend unit tests
- [ ] Write frontend component tests
- [ ] Perform integration testing
- [ ] Test edge cases
- [ ] Add UI polish and animations
- [ ] Ensure responsive design
- [ ] Add user feedback messages
- [ ] Create user documentation

---

## 🚀 Deployment Considerations

### Environment Variables
```env
# Backend
DATABASE_URL=postgresql://...
CONTRACTS_DIR=../data/contracts
FRONTEND_URL=http://localhost:5173

# Frontend
VITE_API_URL=http://localhost:8000
```

### File Storage
- Contracts stored in `data/contracts/`
- Both JSON (machine-readable) and Markdown (human-readable)
- Ensure directory permissions are correct
- Consider backup strategy

### Performance
- Lazy load contract details
- Paginate contract lists if many contracts
- Cache frequently accessed contracts
- Optimize markdown rendering

---

## 📚 Questions for Clarification

Before implementation, please confirm:

1. **Question Priority**: Should users be required to answer all questions, or only high-priority ones?

2. **Approval Authority**: Can anyone approve, or should there be role-based access control?

3. **Version History**: Should we keep old versions when contracts are updated, or just the latest?

4. **Rejection Workflow**: When a contract is rejected, should it go back to draft for re-generation?

5. **Notification System**: Should users be notified when new contracts need review?

6. **Bulk Operations**: Should users be able to approve multiple contracts at once?

7. **Export Options**: Besides JSON and Markdown, do you need PDF or other formats?

---

## 🎯 Success Criteria

The implementation will be considered successful when:

1. ✅ MCP generates contracts with 3-7 relevant questions per table
2. ✅ Frontend displays contracts in a clean, intuitive interface
3. ✅ Users can answer questions inline with good UX
4. ✅ Approval workflow merges AI + human insights correctly
5. ✅ Approved contracts contain both technical and business context
6. ✅ All contracts are saved in both JSON and Markdown formats
7. ✅ System handles errors gracefully with user feedback
8. ✅ UI is responsive and works on different screen sizes

---

## 📅 Estimated Timeline

- **Phase 1** (MCP Enhancement): 4-6 hours
- **Phase 2** (Backend API): 6-8 hours
- **Phase 3** (Frontend UI): 8-10 hours
- **Phase 4** (Approval Workflow): 4-6 hours
- **Phase 5** (Testing & Polish): 4-6 hours

**Total Estimated Time**: 26-36 hours

---

*This plan provides a comprehensive roadmap for implementing the contract review and approval system. Each phase builds on the previous one, ensuring a solid foundation for the complete workflow.*