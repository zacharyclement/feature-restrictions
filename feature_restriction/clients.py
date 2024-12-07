import redis


class RedisConnectionBase:
    """Base class for Redis connections."""

    def __init__(self, host: str, port: int, db: int, decode_responses: bool = True):
        self.host = host
        self.port = port
        self.db = db
        self.decode_responses = decode_responses
        self.connection = None

    def connect(self):
        """Establish a Redis connection."""
        if not self.connection:
            self.connection = redis.StrictRedis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=self.decode_responses,
            )
        return self.connection


class RedisStreamClient(RedisConnectionBase):
    """Redis connection class for stream operations."""

    def __init__(self, host: str, port: int, db: int, decode_responses: bool = True):
        super().__init__(host, port, db, decode_responses)


class RedisUserClient(RedisConnectionBase):
    """Redis connection class for user operations."""

    def __init__(self, host: str, port: int, db: int, decode_responses: bool = True):
        super().__init__(host, port, db, decode_responses)


class RedisTripwireClient(RedisConnectionBase):
    """Redis connection class for tripwire operations."""

    def __init__(self, host: str, port: int, db: int, decode_responses: bool = True):
        super().__init__(host, port, db, decode_responses)
