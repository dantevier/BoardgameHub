import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
import chromadb
import uuid

from app.config import settings
from app.db.models import Base, Game, Rulebook, User, ChatHistory, GameSubmission

# --- Fixtures ---

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    """Provides a transactional SQLAlchemy session for tests."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()
        await engine.dispose()

@pytest.fixture(scope="function")
def chroma_client():
    """Provides a ChromaDB client for tests."""
    client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    yield client

# --- Basic Setup Tests ---

# Basic test to check if config is loaded
def test_settings_loaded():
    assert settings.DATABASE_URL is not None
    assert settings.CHROMA_HOST is not None
    assert settings.CHROMA_PORT is not None

# Test model instantiation (doesn't require DB connection)
def test_model_instantiation():
    try:
        game = Game(title="Test Game", description="A test description")
        user = User(username="testuser", email="test@example.com", password_hash="somehash")
    except Exception as e:
        pytest.fail(f"Model instantiation failed: {e}")

# --- Async Tests for Connections ---

@pytest.mark.asyncio
async def test_postgresql_connection():
    """Tests if a connection can be established with the PostgreSQL DB."""
    engine = None
    try:
        engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
        print(f"Successfully connected to PostgreSQL: {settings.DATABASE_URL}")
    except Exception as e:
        pytest.fail(f"Failed to connect to PostgreSQL at {settings.DATABASE_URL}: {e}")
    finally:
        if engine:
            await engine.dispose()

@pytest.mark.asyncio
async def test_chromadb_connection():
    """Tests if a connection can be established with the ChromaDB server."""
    try:
        client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        heartbeat = client.heartbeat()
        assert isinstance(heartbeat, int)
        print(f"Successfully connected to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
        collections = client.list_collections()
        assert isinstance(collections, list)
    except Exception as e:
        pytest.fail(f"Failed to connect to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}: {e}")

# --- CRUD Tests ---

@pytest.mark.asyncio
async def test_postgresql_crud_game(db_session: AsyncSession):
    """Tests Create, Read, Update, Delete for the Game model in PostgreSQL."""
    new_game = Game(title="Test Game CRUD", description="Initial Desc")
    db_session.add(new_game)
    await db_session.commit()
    await db_session.refresh(new_game)
    assert new_game.game_id is not None
    assert new_game.title == "Test Game CRUD"
    game_id = new_game.game_id

    result = await db_session.execute(select(Game).where(Game.game_id == game_id))
    read_game = result.scalar_one_or_none()
    assert read_game is not None
    assert read_game.title == "Test Game CRUD"

    read_game.description = "Updated Desc"
    db_session.add(read_game)
    await db_session.commit()
    await db_session.refresh(read_game)

    result_updated = await db_session.execute(select(Game).where(Game.game_id == game_id))
    updated_game = result_updated.scalar_one()
    assert updated_game.description == "Updated Desc"

    await db_session.delete(updated_game)
    await db_session.commit()

    result_deleted = await db_session.execute(select(Game).where(Game.game_id == game_id))
    deleted_game = result_deleted.scalar_one_or_none()
    assert deleted_game is None

@pytest.mark.asyncio
async def test_chromadb_crud(chroma_client: chromadb.Client):
    """Tests basic CRUD operations for ChromaDB."""
    collection_name = f"test_collection_{uuid.uuid4().hex[:8]}"
    test_id = "test_doc_1"
    test_embedding = [0.1, 0.2, 0.3]
    test_metadata = {"source": "test"}

    try:
        try:
            chroma_client.delete_collection(collection_name)
        except:
            pass

        collection = chroma_client.create_collection(collection_name)
        assert collection.name == collection_name

        collection.add(
            ids=[test_id],
            embeddings=[test_embedding],
            metadatas=[test_metadata]
        )

        results = collection.get(ids=[test_id], include=["metadatas", "embeddings"])
        assert results is not None
        assert len(results['ids']) == 1
        assert results['ids'][0] == test_id
        assert results['metadatas'][0] == test_metadata
        assert len(results['embeddings'][0]) == len(test_embedding)

        updated_metadata = {"source": "updated_test"}
        collection.upsert(
            ids=[test_id],
            embeddings=[test_embedding],
            metadatas=[updated_metadata]
        )
        results_updated = collection.get(ids=[test_id], include=["metadatas", "embeddings"])
        assert results_updated['metadatas'][0] == updated_metadata

        collection.delete(ids=[test_id])
        results_deleted = collection.get(ids=[test_id])
        assert len(results_deleted['ids']) == 0

    finally:
        try:
            chroma_client.delete_collection(collection_name)
            print(f"Cleaned up ChromaDB collection: {collection_name}")
        except Exception as e:
            print(f"Could not clean up ChromaDB collection {collection_name}: {e}")

# We need sqlalchemy.text for the DB connection test
from sqlalchemy import text
