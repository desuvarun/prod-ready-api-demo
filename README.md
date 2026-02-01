# Production-Ready API

A well-architected FastAPI application demonstrating production best practices.

## Features

- **Connection Pooling**: Explicitly configured database pool (min=5, max=20)
- **Rate Limiting**: Token bucket algorithm (100 req/min per client)
- **Pagination**: All list endpoints paginated (max 100 per page)
- **Global Exception Handler**: Catches and logs all unhandled errors
- **Health Checks**: Liveness, readiness, and comprehensive health endpoints
- **Structured Logging**: Request logging with timing
- **Input Validation**: Pydantic models with field constraints
- **Clean Architecture**: Service layer separates business logic
- **Metrics Endpoint**: Prometheus-compatible metrics

## Running

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Testing

```bash
pytest test_main.py -v
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Comprehensive health check |
| `/health/live` | GET | Kubernetes liveness probe |
| `/health/ready` | GET | Kubernetes readiness probe |
| `/api/v1/items` | GET | List items (paginated) |
| `/api/v1/items` | POST | Create item |
| `/api/v1/items/{id}` | GET | Get item by ID |
| `/api/v1/items/{id}` | DELETE | Delete item |
| `/metrics` | GET | Application metrics |

## Production Patterns Implemented

1. **Scalability**: Connection pooling, rate limiting
2. **Security**: Input validation, CORS configuration
3. **Reliability**: Global exception handler, health checks
4. **Performance**: Async handlers, connection pooling
5. **Observability**: Structured logging, metrics endpoint
6. **Testability**: Comprehensive test suite
7. **Architecture**: Clean service layer separation
8. **Maintainability**: Type hints, documentation
