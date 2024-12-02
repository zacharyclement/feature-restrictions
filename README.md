Here’s the revised README with your specifications:

---

# Feature Restriction Service

## Overview

The **Feature Restriction Service** is a high-performance system designed to manage user-based feature restrictions. It leverages FastAPI for the backend, Redis for real-time data storage, and a consumer to process Redis streams. The system can scale to handle high request rates and supports various rules with a tripwire mechanism to manage rule thresholds. It is able to ingest 100 to 1K (valley to peak) new events per second & respond to 100 to 1K requests for feature restrictions.

![Architecture Diagram](images/architecture.png)


---

## Data Flow Description

1. **Event Ingestion**:
   - Events are posted to the FastAPI `/event` endpoint.
   - Events are stored in a Redis stream.

2. **Stream Processing**:
   - The Stream Consumer reads events from the Redis stream.
   - Applies business rules based on event data.
   - Updates user data and tripwire states in Redis.

3. **Event Handling, Rules, and Tripwires**:
    - Events are processed based on their `name` field, updating user data.
    - User data is assessed against various rules. If a rule is violated, feature access is restricted.
    - Rules are evaluated for potential tripwire activation. Tripwires disable rules when thresholds are exceeded.

4. **Feature Restriction Queries**:
   - Clients query endpoints such as `/canmessage` or `/canpurchase` to check feature availability for users.
   - Responses are determined by processed user data in Redis.

---


## Setup, Starting, and Using the System

### Prerequisites

1. **Docker**: Ensure Docker and Docker Compose are installed.
   - [Install Docker](https://docs.docker.com/get-docker/)
   - [Install Docker Compose](https://docs.docker.com/compose/install/)

2. **Postman or Curl**: For testing API endpoints.

---

### Starting the System

1. **Start Services**:
   ```bash
   docker-compose up --build
   ```

2. **Verify Running Services**:
   - FastAPI app: [http://localhost:8000](http://localhost:8000)
   - Redis: Runs internally within the Docker network.

3. **Stop Services**:
   ```bash
   docker-compose down
   ```

---

### Using the System

#### Available Endpoints

1. **POST /event**: Add an event to the system.
   - Example payload for `scam_message_flagged`:
     ```json
     {
       "name": "scam_message_flagged",
       "event_properties": {
         "user_id": "12345"
       }
     }
     ```

2. **GET /canmessage?user_id={user_id}**: Check if the user can send messages.

3. **GET /canpurchase?user_id={user_id}**: Check if the user can make purchases.

**note**: with container running, see link for swagger docs: http://127.0.0.1:8000/docs#/

---

## Running Tests

### Prerequisites

1. **Python Environment**:
   - Install Conda: [Miniconda Installation](https://docs.conda.io/en/latest/miniconda.html).
   - Create a Conda environment:
     ```bash
     conda create -n feature-restriction python=3.10
     conda activate feature-restriction
     ```
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```

2. **Redis Server**: Ensure a Redis instance is running locally:
   ```bash
   redis-server
   ```

---

### Integration Tests

1. Start the required services (Redis and FastAPI).
2. Run the integration tests:
   ```bash
   pytest tests/integration
   ```

---

### Load Tests with Locust

1. Start the Docker containers:
   ```bash
   docker-compose up
   ```

2. Run Locust:
   ```bash
   locust -f tests/load/locustfile.py
   ```

3. Open the Locust web interface: [http://localhost:8089](http://localhost:8089).  **Note**: tests run with 100 users and 50 ramp up for 30 seconds.

---

## Environment Variables

### Required Environment Variables

| Variable       | Default Value | Description                              |
|----------------|---------------|------------------------------------------|
| `REDIS_HOST`   | `redis`       | Redis hostname within the Docker network.|

All other settings (Redis ports and DB indexes) are defined in `feature_restriction/config.py`.

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