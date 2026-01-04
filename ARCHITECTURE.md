# Architecture Documentation

## Overview

This application is built using FastAPI with SQLAlchemy 2.0 (async) for database operations. The architecture emphasizes:

1. **Dependency Injection** - All dependencies are injected via FastAPI's dependency injection system
2. **Lazy Initialization** - Database connections are created only when needed
3. **Testability** - Components can be easily mocked and tested in isolation
4. **Async/Await** - Full async support for scalable performance

## Key Components

### 1. API Layer (`src/powonline/`)

#### Main Application (`main.py`)
- Creates the FastAPI application
- Registers routers and middleware
- Can be instantiated without database connection (important for testing)

#### Routers (`routers/`)
- `app.py` - General application routes
- `auth.py` - Authentication endpoints

#### Resources (`resources/`)
- RESTful API endpoints for domain entities:
  - `team.py` - Team management
  - `station.py` - Station management
  - `route.py` - Route management
  - `user.py` - User management
  - `assignment.py` - Team/station assignments
  - `questionnaire.py` - Questionnaire management
  - And more...

### 2. Data Layer

#### Models (`model.py`)
- SQLAlchemy ORM models
- Database schema definition
- Uses async SQLAlchemy 2.0 style

#### Core Business Logic (`core.py`)
- Business logic layer between API and database
- Async functions for data operations
- Domain logic implementation

#### Dependencies (`dependencies.py`)
**Key Design:** Lazy initialization for better testability

```python
# Database engine and session maker are created lazily
def get_engine() -> AsyncEngine:
    """Lazy initialization - only creates engine when first called"""
    
def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    """Lazy initialization - only creates session maker when first called"""

async def get_db():
    """FastAPI dependency - provides database session"""
```

**Benefits:**
- App can be created without database connection
- Easy to override for testing
- Supports different databases for different environments

### 3. Testing Strategy

#### Test Setup (`tests/conftest.py`)
The test configuration uses the lazy initialization pattern:

```python
@fixture
async def dbsession():
    from powonline.dependencies import get_async_session_maker
    
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        # Setup and cleanup test data
        yield session
```

#### Test Database
Tests use a PostgreSQL test database configured via environment variable:
```bash
POWONLINE_DSN=postgresql://postgres:postgres@test-db/powonline
```

#### Dependency Override Pattern
For unit tests that need to mock the database:

```python
from powonline.dependencies import set_engine
from sqlalchemy.ext.asyncio import create_async_engine

# Create a test engine
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")

# Override the global engine
set_engine(test_engine)

# Now all code using get_db() will use the test engine
```

### 4. Authentication & Authorization

#### Authentication (`auth.py`)
- JWT-based authentication
- OAuth2 integration (Google, Facebook)
- Local development user support

#### Authorization
- Role-based access control
- Permission checks via `User.require_permission()`

### 5. Schema Validation

#### Pydantic Schemas (`schema.py`)
- Request/response validation
- Type safety
- Automatic API documentation

### 6. Database Migrations

#### Alembic (`database/alembic/`)
- Version-controlled schema changes
- Migration scripts in `database/alembic/versions/`
- Run migrations: `alembic upgrade head`

## Data Flow

1. **Request** → FastAPI router endpoint
2. **Dependency Injection** → `get_db()` provides database session
3. **Business Logic** → Core functions process the request
4. **Database** → SQLAlchemy ORM operations
5. **Response** → Pydantic schema validation and serialization

## Configuration

### Environment Variables

- `POWONLINE_DSN` - Database connection string (required)
  - Format: `postgresql+psycopg://user:password@host/dbname`
  - Example: `postgresql+psycopg://postgres:postgres@localhost/powonline`

### Configuration Files
- Config files managed via `config-resolver` library
- Looks for config in standard locations
- Can be overridden in tests

## Running the Application

### Development
```bash
# Set database URL
export POWONLINE_DSN="postgresql+psycopg://user:pass@localhost/powonline"

# Run with uvicorn
uvicorn powonline.main:create_app --reload --factory
```

### Testing
```bash
# Tests use environment variable from pytest.ini
pytest
```

### Production
```bash
# Use production WSGI server
uvicorn powonline.main:create_app --factory --host 0.0.0.0 --port 8000
```

## Key Improvements from Flask

1. **Async/Await Support** - Better performance and scalability
2. **Type Safety** - Pydantic schemas provide runtime validation
3. **Automatic API Documentation** - OpenAPI/Swagger built-in
4. **Lazy Initialization** - Better testability and flexibility
5. **Modern Python** - Type hints, async/await, modern patterns

## Testing Best Practices

1. **Use fixtures** - Leverage pytest fixtures for setup/teardown
2. **Override dependencies** - Use `set_engine()` for test databases
3. **Async tests** - Use `pytest-asyncio` for async test functions
4. **Seed data** - Use SQL seed files for consistent test data
5. **Cleanup** - Always clean up test data in fixtures

## Security Considerations

1. **JWT Tokens** - Secure token-based authentication
2. **Password Hashing** - bcrypt for password storage
3. **CORS** - Configured via middleware
4. **SQL Injection** - Prevented by SQLAlchemy ORM
5. **Input Validation** - Pydantic schemas validate all input

## Future Improvements

1. **API Versioning** - Add version prefix to endpoints
2. **Caching** - Add Redis caching layer
3. **Rate Limiting** - Implement rate limiting middleware
4. **Monitoring** - Add application performance monitoring
5. **Documentation** - Expand inline documentation
