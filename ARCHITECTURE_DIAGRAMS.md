# Architecture Diagrams & Visual Workflow Guide

## System Architecture Overview

### 🏗️ Complete System Architecture

```mermaid
graph TB
    subgraph "GitHub Ecosystem"
        A[GitHub Repository]
        B[Pull Request Created]
        C[Developer Comments]
        D[PR Comments/Reviews]
    end
    
    subgraph "External Infrastructure"  
        E[ngrok Tunnel]
        F[Public Internet]
    end
    
    subgraph "Core Application Layer"
        G[FastAPI Web Server]
        H[Webhook Endpoints]
        I[REST API Endpoints]
        J[Background Tasks]
    end
    
    subgraph "AI Agent Orchestration"
        K[Main Agent Controller]
        L[Agent Task Queue]
        M[Agent Result Aggregator]
    end
    
    subgraph "Specialized AI Agents"
        N1[Code Summarizer Agent]
        N2[Diff Analysis Agent]
        N3[Code Type Classifier]
        N4[Review Generator Agent]
        N5[Feedback Analyzer Agent]
    end
    
    subgraph "Dynamic Prompt System"
        O1[Prompt Manager]
        O2[Frontend Prompts v1.x]
        O3[Backend Prompts v1.x]
        O4[Generic Prompts v1.x]
        O5[Prompt Evolution Tracker]
    end
    
    subgraph "External AI Services"
        P[Groq LLM API]
        Q[Rate Limiting & Retry Logic]
    end
    
    subgraph "Data Persistence Layer"
        R[(SQLite Database)]
        S[Review Storage]
        T[Feedback Storage]  
        U[Prompt History]
        V[Analytics Data]
    end
    
    subgraph "Integration Layer"
        W[GitHub API Client]
        X[Webhook Security]
        Y[API Authentication]
    end
    
    %% Data Flow Connections
    A --> B
    B -->|Webhook Event| E
    C -->|Feedback Event| E
    E --> F
    F --> G
    
    G --> H
    H --> J
    J --> K
    
    K --> L
    L --> N1
    L --> N2  
    L --> N3
    L --> N4
    L --> N5
    
    N1 --> M
    N2 --> M
    N3 --> M
    N4 --> M
    N5 --> M
    
    M --> K
    
    K --> O1
    O1 --> O2
    O1 --> O3
    O1 --> O4
    O1 --> O5
    
    N1 -.->|LLM Calls| P
    N2 -.->|LLM Calls| P
    N4 -.->|LLM Calls| P
    N5 -.->|LLM Calls| P
    
    P --> Q
    
    K --> R
    R --> S
    R --> T
    R --> U
    R --> V
    
    K --> W
    W -->|Post Review| A
    
    G --> I
    I -.->|Admin API| O1
    I -.->|Analytics| V
```

### 🔄 Agent Workflow Sequence

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant GH as GitHub
    participant WH as Webhook System
    participant API as FastAPI App
    participant MA as Main Agent
    participant CS as Code Summarizer
    participant DA as Diff Analyzer
    participant CT as Code Classifier  
    participant PM as Prompt Manager
    participant RG as Review Generator
    participant LLM as Groq LLM
    participant DB as Database
    participant FA as Feedback Analyzer

    Note over Dev,FA: PR Creation & Initial Review
    Dev->>GH: Create Pull Request
    GH->>WH: Send PR webhook event
    WH->>API: Forward webhook payload
    API->>MA: Initialize PR processing
    
    Note over MA,LLM: Parallel Agent Processing
    MA->>CS: Summarize PR changes
    MA->>DA: Analyze diff complexity
    MA->>CT: Classify code type
    
    par Code Summarization
        CS->>LLM: Generate summary prompt
        LLM-->>CS: Return summary
    and Diff Analysis
        DA->>LLM: Analyze complexity prompt  
        LLM-->>DA: Return analysis
    and Type Classification
        CT->>LLM: Classification prompt
        LLM-->>CT: Return code type
    end
    
    CS-->>MA: Summary results
    DA-->>MA: Analysis results
    CT-->>MA: Classification results
    
    Note over MA,DB: Review Generation
    MA->>PM: Get prompt for code type
    PM-->>MA: Return current best prompt
    MA->>RG: Generate review
    RG->>LLM: Review generation prompt
    LLM-->>RG: Generated review
    RG-->>MA: Formatted review
    
    MA->>DB: Store review data
    MA->>GH: Post review comment
    
    Note over Dev,FA: Feedback Learning Loop
    Dev->>GH: Comment with feedback
    GH->>WH: Send comment webhook
    WH->>API: Forward comment data
    API->>MA: Process feedback
    MA->>FA: Analyze feedback content
    FA->>LLM: Feedback analysis prompt
    LLM-->>FA: Feedback analysis
    FA-->>MA: Improvement suggestions
    MA->>PM: Update prompts if needed
    PM->>DB: Store prompt evolution
    MA->>GH: Acknowledge feedback
```

### 🧠 Agent Intelligence Architecture

```mermaid
graph TD
    subgraph "Agent Intelligence Layer"
        A1[Main Orchestrator]
        A1 --> B1{Task Distribution}
        
        B1 --> C1[Summarization Task]
        B1 --> C2[Analysis Task]  
        B1 --> C3[Classification Task]
        B1 --> C4[Generation Task]
        B1 --> C5[Learning Task]
        
        C1 --> D1[Code Summarizer<br/>- Extract key changes<br/>- Identify impact areas<br/>- Context understanding]
        
        C2 --> D2[Diff Analyzer<br/>- Complexity assessment<br/>- Risk identification<br/>- Quality indicators]
        
        C3 --> D3[Type Classifier<br/>- File pattern analysis<br/>- Code structure detection<br/>- Domain classification]
        
        C4 --> D4[Review Generator<br/>- Template selection<br/>- Content generation<br/>- Quality formatting]
        
        C5 --> D5[Feedback Processor<br/>- Sentiment analysis<br/>- Improvement extraction<br/>- Prompt optimization]
        
        D1 --> E1[Result Synthesis]
        D2 --> E1
        D3 --> E1
        D4 --> E1
        D5 --> E1
        
        E1 --> F1[Output Optimization]
        F1 --> G1[Quality Assurance]
        G1 --> H1[Delivery & Learning]
    end
    
    subgraph "Knowledge Base"
        I1[(Dynamic Prompts)]
        I2[(Historical Data)]
        I3[(Feedback Patterns)]
        I4[(Best Practices)]
    end
    
    D1 -.-> I1
    D2 -.-> I1
    D3 -.-> I1
    D4 -.-> I1
    D5 -.-> I1
    
    D5 --> I1
    E1 -.-> I2
    D5 -.-> I3
    F1 -.-> I4
```

## Data Flow Architecture

### 📊 Information Processing Pipeline

```mermaid
flowchart LR
    subgraph "Input Processing"
        A[GitHub PR Event] --> B[Webhook Validation]
        B --> C[Data Extraction]
        C --> D[Context Enrichment]
    end
    
    subgraph "AI Processing Pipeline"  
        D --> E[Agent Orchestration]
        E --> F[Parallel Processing]
        
        F --> G1[Summary Generation]
        F --> G2[Technical Analysis]
        F --> G3[Type Classification]
        
        G1 --> H[Result Aggregation]
        G2 --> H
        G3 --> H
        
        H --> I[Prompt Selection]
        I --> J[Review Generation]
        J --> K[Quality Enhancement]
    end
    
    subgraph "Output & Learning"
        K --> L[Review Formatting]
        L --> M[GitHub Integration]
        L --> N[Data Storage]
        
        M --> O[PR Comment Posted]
        N --> P[Analytics Update]
        
        O --> Q[User Feedback Collection]
        Q --> R[Feedback Analysis]
        R --> S[System Improvement]
        S --> I
    end
    
    style A fill:#e1f5fe
    style O fill:#c8e6c9
    style S fill:#fff3e0
```

### 🔄 Learning & Adaptation Flow

```mermaid
graph TB
    subgraph "Feedback Collection"
        A[PR Comments Monitoring]
        B[Feedback Detection]
        C[Feedback Classification]
    end
    
    subgraph "Analysis Phase"
        D[Sentiment Analysis]
        E[Issue Identification] 
        F[Improvement Categorization]
        G[Priority Assessment]
    end
    
    subgraph "Learning Integration"
        H{Priority Level?}
        H -->|High| I[Immediate Prompt Update]
        H -->|Medium| J[Batch Learning Queue]
        H -->|Low| K[Pattern Analysis Store]
        
        I --> L[Prompt Versioning]
        J --> M[Weekly Learning Cycle]
        K --> N[Trend Analysis]
        
        L --> O[A/B Testing Setup]
        M --> O
        N --> P[Long-term Optimization]
    end
    
    subgraph "Validation & Deployment"
        O --> Q[Performance Validation]
        Q --> R{Improvement Verified?}
        R -->|Yes| S[Deploy Updated Prompts]
        R -->|No| T[Rollback & Analyze]
        
        S --> U[Monitor Performance]
        T --> V[Refinement Process]
        U --> W[Success Metrics Update]
        V --> O
    end
    
    A --> B --> C
    C --> D --> E --> F --> G
    G --> H
```

## Component Architecture

### 🏗️ Microservices-Style Component Design

```mermaid
graph TB
    subgraph "API Gateway Layer"
        A[FastAPI Application]
        B[Request Routing]
        C[Authentication & Rate Limiting]
        D[Response Formatting]
    end
    
    subgraph "Core Business Logic"
        E[Webhook Service]
        F[Review Service] 
        G[Feedback Service]
        H[Analytics Service]
    end
    
    subgraph "Agent Services"
        I[Agent Orchestrator]
        J[Summarization Service]
        K[Analysis Service]
        L[Classification Service]
        M[Generation Service]
        N[Learning Service]
    end
    
    subgraph "Infrastructure Services"
        O[Prompt Management]
        P[Database Service]
        Q[External API Service]
        R[Cache Service]
        S[Queue Service]
    end
    
    subgraph "Integration Layer"
        T[GitHub Integration]
        U[LLM Integration]
        V[Webhook Security]
        W[Monitoring & Logging]
    end
    
    A --> B --> C --> D
    B --> E --> I
    B --> F --> I
    B --> G --> N
    B --> H --> P
    
    I --> J --> U
    I --> K --> U
    I --> L --> U
    I --> M --> U
    N --> O --> P
    
    E --> T
    I --> Q
    F --> P
    G --> P
    H --> P
    
    T --> V
    U --> Q
    all --> W
```

### 🎯 Agent Interaction Model

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing: PR Event Received
    
    state Processing {
        [*] --> Validation
        Validation --> DataCollection
        DataCollection --> AgentDispatch
        
        state AgentDispatch {
            [*] --> ParallelExecution
            ParallelExecution --> Summarization
            ParallelExecution --> Analysis  
            ParallelExecution --> Classification
            
            Summarization --> ResultCollection
            Analysis --> ResultCollection
            Classification --> ResultCollection
            
            ResultCollection --> [*]
        }
        
        AgentDispatch --> ReviewGeneration
        ReviewGeneration --> QualityCheck
        QualityCheck --> OutputFormatting
        OutputFormatting --> [*]
    }
    
    Processing --> Publishing: Review Ready
    Publishing --> Storing: GitHub API Success
    Storing --> Monitoring: Database Success
    Monitoring --> Idle: Complete
    
    Processing --> Error: Any Failure
    Error --> Retry: Recoverable
    Error --> Failed: Non-recoverable
    Retry --> Processing
    Failed --> Idle
    
    Idle --> Learning: Feedback Received
    Learning --> PromptUpdate: High Priority
    Learning --> QueuedLearning: Low Priority
    PromptUpdate --> Idle
    QueuedLearning --> Idle
```

## Technology Integration Architecture

### 🔌 External Service Integration

```mermaid
graph LR
    subgraph "PR Review System Core"
        A[FastAPI Application]
    end
    
    subgraph "GitHub Integration"
        B[GitHub API Client]
        C[Webhook Handler]
        D[OAuth Authentication]
        E[Rate Limit Manager]
    end
    
    subgraph "AI/LLM Integration"
        F[Groq API Client]
        G[Prompt Templates]
        H[Response Parser]
        I[Token Manager]
        J[Retry Logic]
    end
    
    subgraph "Data Persistence"
        K[(SQLite Database)]
        L[Review Repository]
        M[Feedback Repository] 
        N[Prompt Repository]
        O[Analytics Repository]
    end
    
    subgraph "Infrastructure"
        P[ngrok Tunnel]
        Q[Environment Config]
        R[Logging System]
        S[Health Monitoring]
    end
    
    A <--> B
    A <--> C
    A <--> F
    A <--> K
    A <--> P
    
    B --> D
    B --> E
    C --> D
    
    F --> G
    F --> H
    F --> I
    F --> J
    
    K --> L
    K --> M
    K --> N
    K --> O
    
    A --> Q
    A --> R
    A --> S
    
    style A fill:#2196F3,color:#fff
    style K fill:#4CAF50,color:#fff
    style F fill:#FF9800,color:#fff
    style B fill:#9C27B0,color:#fff
```

### 🚀 Deployment Architecture Options

```mermaid
graph TB
    subgraph "Development Environment"
        A1[Local Machine]
        B1[SQLite Database]
        C1[ngrok Tunnel]
        D1[File-based Logging]
    end
    
    subgraph "Staging Environment" 
        A2[Docker Container]
        B2[PostgreSQL Database]
        C2[Cloud Load Balancer]
        D2[Centralized Logging]
        E2[Monitoring Dashboard]
    end
    
    subgraph "Production Environment"
        A3[Kubernetes Cluster]
        B3[Managed Database]
        C3[API Gateway]
        D3[Log Aggregation]
        E3[Alert Management]
        F3[Auto-scaling]
        G3[Backup System]
        H3[Security Scanning]
    end
    
    A1 --> A2: Docker Build
    A2 --> A3: K8s Deploy
    
    B1 --> B2: Migration Scripts
    B2 --> B3: Database Upgrade
    
    C1 --> C2: DNS Configuration
    C2 --> C3: Production Gateway
    
    D1 --> D2: Log Standardization
    D2 --> D3: Enterprise Logging
    
    style A1 fill:#FFF9C4
    style A2 fill:#E8F5E8
    style A3 fill:#E3F2FD
```

## Performance & Scalability Architecture

### ⚡ Performance Optimization Strategy

```mermaid
graph TD
    subgraph "Request Processing Optimization"
        A[Async Request Handling]
        B[Background Task Queue] 
        C[Connection Pooling]
        D[Response Caching]
    end
    
    subgraph "AI Processing Optimization"
        E[Parallel Agent Execution]
        F[Prompt Caching]
        G[Response Streaming]
        H[Token Optimization]
    end
    
    subgraph "Database Optimization"
        I[Query Optimization]
        J[Index Strategy]
        K[Connection Pooling]
        L[Read Replicas]
    end
    
    subgraph "Infrastructure Scaling"
        M[Horizontal Pod Scaling]
        N[Load Balancing]
        O[CDN Integration]
        P[Resource Monitoring]
    end
    
    A --> B
    B --> E
    E --> F
    
    C --> I
    I --> J
    
    D --> G
    G --> H
    
    M --> N
    N --> O
    O --> P
    
    style A fill:#4CAF50
    style E fill:#2196F3  
    style I fill:#FF9800
    style M fill:#9C27B0
```

### 📈 Scalability Considerations

```mermaid
graph LR
    subgraph "Current State (MVP)"
        A[Single Instance]
        B[SQLite Database]
        C[Synchronous Processing]
        D[File Logging]
    end
    
    subgraph "Scale Level 1 (10-50 PRs/day)"
        E[Load Balanced Instances]
        F[PostgreSQL]
        G[Async Processing]
        H[Structured Logging]
    end
    
    subgraph "Scale Level 2 (100-500 PRs/day)"
        I[Microservices Architecture]
        J[Database Clustering]
        K[Message Queues]
        L[Distributed Logging]
    end
    
    subgraph "Scale Level 3 (1000+ PRs/day)"
        M[Container Orchestration]
        N[Managed Database Services]
        O[Event-Driven Architecture]
        P[Observability Platform]
    end
    
    A --> E: Traffic Increase
    E --> I: Feature Complexity
    I --> M: Enterprise Scale
    
    B --> F: Data Growth
    F --> J: Performance Needs
    J --> N: Operational Excellence
    
    C --> G: Response Time Requirements
    G --> K: Reliability Needs
    K --> O: Scalability Requirements
    
    D --> H: Debugging Needs
    H --> L: Operational Visibility
    L --> P: Full Observability
```

---

*Architecture Documentation Version: 1.0 | Last Updated: May 3, 2026*