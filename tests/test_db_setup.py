import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
import chromadb
import uuid
import numpy as np

from app.config import settings
from app.db.models import Base, Game, Rulebook, User, ChatHistory, GameSubmission

# --- Fixtures ---

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    """Provides a clean, transaction-rolled-back session for each test function."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        async with session.begin():
            # Optional: If you need tables created for tests that run independently of alembic
            # async with engine.begin() as conn:
            #     await conn.run_sync(Base.metadata.create_all)
            yield session
        # Transaction is automatically rolled back here

    await engine.dispose()

@pytest.fixture(scope="function")
def chroma_client() -> chromadb.HttpClient:
    """Provides a ChromaDB client connected to the test server."""
    client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    # Ensure connection works before yielding
    try:
        client.heartbeat()
    except Exception as e:
        pytest.skip(f"ChromaDB server not reachable at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}: {e}")
    return client

@pytest.fixture(scope="function")
def test_chroma_collection(chroma_client: chromadb.HttpClient) -> chromadb.Collection:
    """Provides a temporary ChromaDB collection for testing, ensuring cleanup."""
    collection_name = f"test_collection_{uuid.uuid4().hex}"
    collection = chroma_client.get_or_create_collection(name=collection_name)
    yield collection
    # Cleanup: delete the collection after the test
    chroma_client.delete_collection(name=collection_name)

# --- Existing Tests ---

def test_settings_loaded():
    assert settings.DATABASE_URL is not None
    assert settings.CHROMA_HOST is not None
    assert settings.CHROMA_PORT is not None

def test_model_instantiation():
    try:
        # Create a game instance first
        game = Game(game_id=99, title="Test Game", description="A test description") # Assign temporary ID for testing
        user = User(username="testuser", email="test@example.com", password_hash="hashed")
        # Now instantiate Rulebook using game_id or the relationship
        rulebook = Rulebook(game_id=game.game_id, storage_path="/path/test.pdf", original_filename="test.pdf")
        # Or link via relationship (if Game object were persisted/added to session):
        # rulebook = Rulebook(game=game, storage_path="/path/test.pdf", original_filename="test.pdf")

        chat = ChatHistory(session_id="sess1", role="user", content="Hello")
        # Need a user instance for the submission
        # Use the correct keyword 'submitted_by_user_id'
        submission = GameSubmission(game_title="Submit Game", submitted_by_user_id=user.user_id if user.user_id else 1) # Use user ID if available

    except Exception as e:
        pytest.fail(f"Model instantiation failed: {e}")

@pytest.mark.asyncio
async def test_postgresql_connection(db_session: AsyncSession):
    """Tests if a connection can be established and a simple query run."""
    try:
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
        print(f"Successfully connected to PostgreSQL and executed query.")
    except Exception as e:
        pytest.fail(f"Failed to connect/query PostgreSQL: {e}")

@pytest.mark.asyncio
async def test_chromadb_connection(chroma_client: chromadb.HttpClient):
    """Tests if a connection can be established with the ChromaDB server."""
    try:
        heartbeat = chroma_client.heartbeat()
        assert isinstance(heartbeat, int)
        print(f"Successfully connected to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
        collections = chroma_client.list_collections()
        assert isinstance(collections, list)
    except Exception as e:
        pytest.fail(f"Failed to connect to ChromaDB: {e}")

# --- New CRUD Tests ---

# PostgreSQL CRUD Example (Game Model)
@pytest.mark.asyncio
async def test_game_crud_operations(db_session: AsyncSession):
    """Tests Create, Read, Update, Delete for the Game model."""
    # CREATE
    new_game = Game(title="Catan", description="Trade, build, settle!")
    db_session.add(new_game)
    await db_session.flush() # Assigns ID without full commit
    await db_session.refresh(new_game)
    game_id = new_game.game_id
    assert game_id is not None
    print(f"Created Game ID: {game_id}")

    # READ
    # Note: We use the same session, relying on rollback for isolation
    retrieved_game = await db_session.get(Game, game_id)
    assert retrieved_game is not None
    assert retrieved_game.title == "Catan"
    assert retrieved_game.description == "Trade, build, settle!"
    print(f"Read Game: {retrieved_game.title}")

    # UPDATE
    retrieved_game.description = "An updated description for Catan."
    db_session.add(retrieved_game) # Add again to mark dirty (though often SQLAlchemy tracks it)
    await db_session.flush()
    await db_session.refresh(retrieved_game)

    updated_game = await db_session.get(Game, game_id)
    assert updated_game.description == "An updated description for Catan."
    print(f"Updated Game Description: {updated_game.description}")

    # DELETE
    await db_session.delete(updated_game)
    await db_session.flush()

    deleted_game = await db_session.get(Game, game_id)
    assert deleted_game is None
    print(f"Deleted Game ID: {game_id}")

# ChromaDB CRUD Example
def test_chromadb_crud_operations(test_chroma_collection: chromadb.Collection):
    """Tests basic Add, Get, Query, Delete for ChromaDB."""
    collection = test_chroma_collection
    test_id_1 = "test_doc_1"
    # Create a dummy embedding of the correct dimension (384 for all-MiniLM-L6-v2)
    test_embedding_1 = [0.1] * 384
    test_metadata_1 = {"source": "rulebook_a", "page": 1}
    test_document_1 = "This is the first test document."

    # ADD (Upsert)
    collection.add(
        ids=[test_id_1],
        embeddings=[test_embedding_1],
        metadatas=[test_metadata_1],
        documents=[test_document_1]
    )
    print(f"Added doc ID: {test_id_1}")

    # GET
    results = collection.get(ids=[test_id_1], include=['metadatas', 'documents', 'embeddings'])
    assert results['ids'] == [test_id_1]
    # Use np.allclose for comparing float arrays/embeddings
    assert np.allclose(results['embeddings'][0], test_embedding_1)
    assert results['metadatas'][0] == test_metadata_1
    assert results['documents'][0] == test_document_1
    print(f"Got doc: {results['documents'][0]}")

    # QUERY (by embedding - simple nearest neighbor)
    query_results = collection.query(
        query_embeddings=[test_embedding_1], # Query with the same embedding
        n_results=1,
        include=['metadatas', 'documents']
    )
    assert query_results['ids'][0] == [test_id_1]
    assert query_results['documents'][0][0] == test_document_1
    print(f"Queried doc: {query_results['documents'][0][0]}")

    # UPDATE (Chroma uses upsert for updates - add with the same ID)
    updated_document_1 = "This is the updated test document."
    collection.update(
        ids=[test_id_1],
        documents=[updated_document_1]
    )
    results_after_update = collection.get(ids=[test_id_1], include=['documents'])
    assert results_after_update['documents'][0] == updated_document_1
    print(f"Updated doc: {results_after_update['documents'][0]}")

    # DELETE
    collection.delete(ids=[test_id_1])
    results_after_delete = collection.get(ids=[test_id_1])
    assert not results_after_delete['ids'] # Should be empty
    print(f"Deleted doc ID: {test_id_1}")

    # Verify count is zero after delete
    assert collection.count() == 0
