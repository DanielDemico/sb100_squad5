# SmartB100 Architecture

This document describes the interfaces that exist in the current codebase. It is
not a roadmap.

## Architectural Style

SmartB100 is a modular monolith. The FastAPI process imports the internal
modules directly and calls Python functions in-process. Qdrant, Ollama, Groq,
OpenRouter and SQLite are external dependencies; they are not internal services.

## Public Contract Source

`core/schemas.py` is the single source of truth for public request, response and
cross-layer contracts:

- `ChatRequest`: API request for `POST /chat`.
- `ChatResponse`: API response for `POST /chat` and verification output.
- `RetrievalSource`: source item exposed in `ChatResponse.sources`.
- `RetrievalChunk`: retrieval-layer chunk exchanged from `retrieval` to `api`.
- `ConversationResponse`: API response item for `GET /conversations`.
- `UserCreate`: API request for `POST /auth/register`.
- `RegisterResponse`: API response for `POST /auth/register`.
- `Token`: API response for `POST /auth/token`.
- `UserProfile`: internal user profile passed to generation, verification and
  agent layers.
- `ExpertiseLevel`: allowed expertise levels.
- `ChatMessage`: shared message shape for history passed between API,
  generation, verification and agent layers.
- `AgentGraph`: minimal protocol consumed by the agent runner for graph
  invocation.

API routes must import these schemas from `core.schemas`; they must not define
duplicate Pydantic request or response models.

## Layer Interfaces

### API -> Auth / Database

`api/routes/auth.py` exposes:

- `POST /auth/register`
  - request: `UserCreate`
  - response: `RegisterResponse`
  - persistence: creates `database.models.User`

- `POST /auth/token`
  - request: `OAuth2PasswordRequestForm`
  - response: `Token`
  - persistence: reads `database.models.User`

`api/dependencies.py::verify_token` validates a bearer JWT and returns the
matching `database.models.User`.

### API -> Chat Pipeline

`api/routes/chat.py::chat` exposes:

- request: `ChatRequest`
- response: `ChatResponse`

The route resolves or creates a `database.models.Conversation`, persists
`Message`, `RagResponse` and `RagSource` rows, builds a `list[ChatMessage]`
history and dispatches to either the standard RAG path or the agent path.

### API -> Retrieval

The standard RAG path calls:

- `retrieval.embedder.generate_embedding(question) -> list[float]`
- `retrieval.vector_store.search_context_rich(embedding) -> list[RetrievalChunk]`

The API converts `RetrievalChunk` values into persisted `RagSource` rows and
into `RetrievalSource` response values.

### API -> Generation / Verification

When verification is disabled, the API calls:

- `generation.llm.generate(question, context, history, profile) -> str`

When verification is enabled, the API calls:

- `verification.gate.evaluate(question, context, history, profile) -> ChatResponse`

Both functions receive `history: list[ChatMessage]` and `profile: UserProfile`.

### API -> Agent

When `settings.agent_enabled` is true, the API may call:

- `agent.intent.classify_domain(question) -> DomainDecision`
- `agent.runner.invoke_agent(question, history, profile, graph=None) -> AgentOutcome`
- `verification.gate.score_context(question, context) -> float`

`invoke_agent` consumes `history: list[ChatMessage]` and a `UserProfile`. The
optional graph argument follows `AgentGraph`.

### Conversations API

`api/routes/conversations.py::list_conversations` exposes:

- response: `list[ConversationResponse]`

The route reads `database.models.Conversation` rows owned by the authenticated
user and returns central schemas, not ORM instances.

## Dependency Direction

The intended dependency direction is:

`api -> core`, `api -> database`, `api -> retrieval`, `api -> generation`,
`api -> verification`, `api -> agent`

`retrieval`, `generation`, `verification` and `agent` may depend on `core`.
`core` must not depend on API routes, database models or infrastructure modules.

