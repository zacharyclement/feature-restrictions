

# Feature Restriction Service

## Overview

The **Feature Restriction Service** is a high-performance system designed to manage user-based feature restrictions. It leverages FastAPI for the backend, Redis for real-time data storage, and a consumer to process Redis streams. The system can scale to handle high request rates and supports various rules with a tripwire mechanism to manage rule thresholds.

### Components

1. **FastAPI Application**: Handles REST API requests for event posting and feature restriction queries.
2. **Redis Database**: Stores user data, tripwire states, and events for real-time processing.
3. **Stream Consumer**: Reads events from Redis streams and processes them with business logic and rules.
4. **Locust Load Testing**: Simulates high-load scenarios to test system scalability and performance.

---

## Data Flow Description

1. **Event Ingestion**:
   - Events are posted to the FastAPI `/event` endpoint.
   - Events are stored in a Redis stream.

2. **Stream Processing**:
   - The Stream Consumer reads events from the Redis stream.
   - Applies business rules based on event data.
   - Updates user data and tripwire states in Redis.

3. **Feature Restriction Queries**:
   - Clients query endpoints such as `/canmessage` or `/canpurchase` to check feature availability for users.
   - Responses are determined by the processed user data in Redis.

---
## Project Structure


```text
.
├── app.py                       # FastAPI application entry point
├── stream_consumer.py           # Redis Stream Consumer script
├── feature_restriction/         # Application modules
│   ├── config.py                # Configuration settings (e.g., Redis DBs)
│   ├── models.py                # Pydantic models for events and user data
│   ├── redis_user_manager.py    # User data management logic
│   ├── tripwire_manager.py      # Tripwire management logic
│   ├── rules.py                 # Business rules for events
│   ├── utils.py                 # Utility functions and helpers
│   ├── registry.py              # Event handler registry
│   ├── publisher.py             # EventPublisher class
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── load/                    # Load testing scripts
│   │   ├── locustfile.py        # Locust configuration for load testing
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Dockerfile for the FastAPI app
├── docker-compose.yml           # Docker Compose file for all services
```

---
## Setup and Starting the System

### Prerequisites
1. **Docker**: Ensure Docker and Docker Compose are installed.
   - [Install Docker](https://docs.docker.com/get-docker/)
   - [Install Docker Compose](https://docs.docker.com/compose/install/)

2. **Python Environment** (optional, for local development):
   - Python 3.10+
   - Install dependencies with `pip install -r requirements.txt`.

### Start the System with Docker Compose

1. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

2. Verify that the services are running:
   - FastAPI app: [http://localhost:8000](http://localhost:8000)
   - Redis database: Running internally within the Docker network.

3. Stop the containers:
   ```bash
   docker-compose down
   ```

---

## Running Tests

### Integration Tests
Run the integration tests to verify system functionality:
```bash
pytest tests/integration
```

### Load Tests with Locust
1. Start the Docker containers (`docker-compose up`).
2. Run Locust for load testing:
   ```bash
   locust -f tests/load/locustfile.py
   ```
3. Access the Locust web interface at [http://localhost:8089](http://localhost:8089).

---

## Environment Variables

The following environment variables are used in the system. These are set in the `docker-compose.yml` file:

| Variable       | Default Value | Description                              |
|----------------|---------------|------------------------------------------|
| `REDIS_HOST`   | `redis`       | Redis hostname within the Docker network. |
| `REDIS_PORT`   | `6379`        | Redis port.                             |
| `REDIS_DB_USER`| `0`           | Redis database for user data.           |
| `REDIS_DB_STREAM`| `1`         | Redis database for streams.             |
| `REDIS_DB_TRIPWIRE`| `2`       | Redis database for tripwire data.       |

---

## API Endpoints

### Event Endpoints
- **POST /event**: Add an event to the system.
  - Example payload for a `scam_message_flagged` event:
    ```json
    {
      "name": "scam_message_flagged",
      "event_properties": {
        "user_id": "12345"
      }
    }
    ```

### Feature Restriction Endpoints
- **GET /canmessage?user_id={user_id}**
- **GET /canpurchase?user_id={user_id}**

These endpoints return a boolean value indicating whether the feature is available.

---

## Development Workflow

### Run Locally Without Docker
1. Start Redis manually:
   ```bash
   redis-server
   ```
2. Run the FastAPI app:
   ```bash
   uvicorn app:app --reload
   ```
3. Start the Stream Consumer:
   ```bash
   python stream_consumer.py
   ```

### Logs
To view logs for each service in Docker:
```bash
docker logs <container_name>
```

---

#