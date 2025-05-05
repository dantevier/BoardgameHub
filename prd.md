# Board Game Rule Master - Product Requirements Document

## 1. Introduction

The Board Game Rule Master is a web application designed to provide users with a specialized chatbot interface for answering rule-specific questions about various board games. The application is primarily grounded in official rulebooks, with capabilities to integrate external knowledge sources and a generic chat mode for broader inquiries.

## 2. System Architecture

The application follows a client-server architecture with these key components:

### 2.1 Frontend (Client)
- Web-based interface using HTML, CSS, JavaScript (potentially React or Vue)
- Renders UI, handles user input, and communicates with backend via APIs

### 2.2 Backend (Server)
- Python-based application (Flask or FastAPI)
- Serves APIs for the frontend
- Handles business logic, authentication, database interactions
- Orchestrates chatbot functionalities

### 2.3 Database
- Stores persistent data including:
  - Game catalog
  - User information (if applicable)
  - Rulebook metadata and file references
  - Chat history for specific games
  - Potentially cached external data
- Recommended: PostgreSQL or MySQL for structured data
- May include dedicated vector database/store

### 2.4 RAG Pipeline
- Document Loader: Loads rulebook PDFs (e.g., using Langchain's PyPDFLoader)
- Text Splitter: Chunks rulebook text into manageable segments
- Embedding Model: Generates vector embeddings for text chunks
- Vector Store: Stores and indexes embeddings for efficient retrieval
- Retriever: Fetches relevant rulebook chunks based on user query embeddings
- LLM (Chat Model): Generates answers based on user query and retrieved context

### 2.5 External Knowledge Module
- Uses tools/agents to search specified external websites (BoardGameGeek, r/boardgames)
- Extracts relevant information via web scraping or APIs

### 2.6 Admin Interface
- Separate interface for administrators
- Manages game catalog
- Reviews submissions
- Monitors system performance

## 3. Data Flow

### 3.1 Game-Specific Chat (Rulebook Grounded)
1. User selects a game from the catalog
2. Frontend requests game-specific chat interface for selected game ID
3. Backend loads game details and prepares RAG pipeline specific to that game's rulebook embeddings
4. Backend retrieves persistent chat history for the user/game combination
5. User asks a rule question
6. Backend embeds the query, uses Retriever to find relevant rulebook chunks
7. (Optional) External Knowledge Module searches BGG/Reddit if needed
8. Backend sends query, retrieved rulebook context, and potentially external information to the LLM
9. LLM generates an answer grounded in the provided context
10. Backend formats response with citations for rulebook sections and external sources
11. Backend saves query and response to Chat History
12. Frontend displays response and updates chat history UI

### 3.2 Generic Chat (Ungrounded)
1. User selects "Generic Chat" option
2. Frontend initiates chat session without specific game ID
3. Backend initializes standard LLM chat session without specific rulebook context
4. User asks general board game question
5. Backend sends query directly to the LLM
6. LLM generates answer based on its general knowledge
7. Frontend displays response (chat history not persisted)

## 4. Core Features

### 4.1 Board Game Catalog
- **Landing Page UI/UX:**
  - Visually appealing grid or list layout
  - Each entry displays: Game Cover Image, Game Title, Brief Description
  - Prominent search bar
  - Filtering options (Genre, Player Count, Complexity)
- **Functionality:** Browse, search (by title, keywords), filter
- **Game Selection:** Clicking game entry redirects to dedicated game page
- **Rulebook Download:** Clear button/link for official PDF rulebook download

### 4.2 Rulebook Grounded Chatbot
- **Chat Interface:** Standard chat UI on dedicated game page
- **RAG Implementation:**
  - Document Loading: PyPDFLoader or similar
  - Chunking Strategy: RecursiveCharacterTextSplitter with appropriate parameters
  - Embedding Model: Sentence Transformer model via Langchain
  - Vector Store: Chroma or FAISS for development, managed service for production
  - Retrieval: Similarity search, potentially with MMR
  - Context Management: Maintain recent conversation history
- **Citation:** Every generated message must include source citations

### 4.3 External Knowledge Integration
- Triggered when RAG system retrieves insufficient context
- Target websites: boardgamegeek.com and reddit.com/r/boardgames/
- Extract relevant text snippets with clear citation in responses

### 4.4 Generic Chat Option
- Clear button/link labeled "Generic Board Game Chat"
- Chat interface without specific game context
- No rulebook grounding, no saved chat history
- Uses standard LLM interaction

### 4.5 Chat History Persistence
- Only applies to game-specific chats
- Requires user identification (session cookies or user accounts)
- Saves user queries and chatbot responses linked to user and game
- Retrieves and displays relevant history upon returning to a game's chat page

### 4.6 Adding New Games
- **Request Mechanism:** Button/link on catalog page
- **Submission Form:**
  - Game Title
  - Rulebook Upload (PDF)
  - Game Description
- **Admin Review Workflow:**
  - Submission saved with "Pending Review" status
  - Admin reviews submission
  - If Approved: PDF processed through RAG pipeline and added to catalog
  - If Rejected: Status updated with reason

## 5. Technical Specifications

### 5.1 Technologies
- **Backend:** Python 3.x with FastAPI or Flask
- **AI/LLM & RAG:** Langchain library ecosystem
- **Database:**
  - Primary Data: PostgreSQL or MySQL
  - Vector Embeddings: Chroma/FAISS or dedicated Vector Database
- **Frontend:** HTML5, CSS3 (Tailwind CSS recommended), JavaScript
- **Web Scraping:** requests, BeautifulSoup4
- **PDF Handling:** pypdf, potentially PyMuPDF
- **Deployment:** Docker, Serverless platform, or traditional VM/server hosting

### 5.2 Data Model
```sql
-- Games table
CREATE TABLE Games (
    game_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    cover_image_url VARCHAR(512),
    genre VARCHAR(100),
    min_players INT,
    max_players INT,
    complexity_rating FLOAT,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rulebook_id INT UNIQUE,
    FOREIGN KEY (rulebook_id) REFERENCES Rulebooks(rulebook_id)
);

-- Rulebooks table
CREATE TABLE Rulebooks (
    rulebook_id SERIAL PRIMARY KEY,
    game_title VARCHAR(255),
    original_filename VARCHAR(255),
    storage_path VARCHAR(512) NOT NULL,
    file_hash VARCHAR(64),
    processing_status VARCHAR(50) DEFAULT 'Processed',
    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    page_count INT
);

-- Users table (optional)
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ChatHistory table
CREATE TABLE ChatHistory (
    message_id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    game_id INT NOT NULL,
    is_user_message BOOLEAN NOT NULL,
    message_text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    citations TEXT,
    FOREIGN KEY (game_id) REFERENCES Games(game_id)
);

-- GameSubmissions table
CREATE TABLE GameSubmissions (
    submission_id SERIAL PRIMARY KEY,
    game_title VARCHAR(255) NOT NULL,
    user_description TEXT,
    submitted_rulebook_path VARCHAR(512),
    submission_status VARCHAR(50) DEFAULT 'Pending Review',
    submitted_by_user_id INT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    admin_notes TEXT
);
```

## 6. Scalability and Performance

- **Database:** Proper indexing on frequently queried columns; potential read replicas
- **Vector Search:** Scalable vector store with optimized indexing parameters
- **RAG Pipeline:** Asynchronous embedding generation during admin approval workflow
- **LLM Calls:** Timeouts and potential caching for identical queries
- **External Knowledge:** Timeouts, caching of scraped results, robust error handling
- **Backend:** Asynchronous capabilities for concurrent request handling
- **Frontend:** Optimized asset loading, minimized bundle size
- **Caching:** Multi-level caching strategy
- **Load Balancing:** Multiple backend instances behind a load balancer

## 7. UI/UX Considerations

### 7.1 User Journey
1. **Landing:** Game catalog, search/filter options, "Generic Chat" option
2. **Browsing/Searching:** Finding games with dynamic updates
3. **Game Selection:** Navigation to game-specific page
4. **Game Page:** Game info, rulebook download button, chat interface with history
5. **Chatting:** Question asking with cited answers
6. **Generic Chat:** Clean interface for general questions
7. **Requesting Game:** Form submission with rulebook upload

### 7.2 Design Requirements
- **Landing Page:** Clean, image-focused grid; intuitive search and filtering; responsive design
- **Game Page:** Clear distinction between game info and chat area
- **Chat Interface:** "Thinking" indicators, graceful error handling, copy functionality
- **Rulebook Download:** Obvious and accessible buttons/links
- **Generic Chat:** Visual differentiation from game-specific chats
- **Responsiveness:** Fully responsive for all screen sizes
- **Accessibility:** WCAG guidelines compliance

## 8. Admin Workflow

### 8.1 Access and Dashboard
- Secure login for administrators
- Overview dashboard with pending submissions, total games, system status

### 8.2 Submission Management
- List of pending games with relevant details
- Review interface for submissions
- Approval process with asynchronous background jobs
- Rejection process with feedback capability

### 8.3 Game Management
- Edit existing game details
- Replace rulebooks (triggering re-processing)
- Delete games if necessary

## 9. Future Considerations

- **User Accounts:** Full user accounts for personalized features
- **Community Features:** Rating answer quality, suggesting alternative interpretations
- **Multilingual Support:** Multiple languages for rulebooks and queries
- **Advanced RAG:** More sophisticated retrieval techniques
- **Visual Aids:** Diagram/image extraction from rulebooks
- **BGG Integration:** Direct metadata pull from BoardGameGeek API 