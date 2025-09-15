from typing import Any, Optional
import threading, redis, json, os
import redis.asyncio
import redis.cluster
import redis.asyncio.cluster
from redis.cluster import ClusterNode 
import joblib
import base64
import io

# Redis queue configuration
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT"))
REDIS_DB = int(os.environ.get("REDIS_DB"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_SSL = os.environ.get("REDIS_SSL")

REDIS_HOST="a2-pairs-5-a2-pairs-redis-cache-0001-001.a2-pairs-5-a2-pairs-redis-cache.km2jzi.apse2.cache.amazonaws.com"
REDIS_PORT=6379
REDIS_SSL=True

REDIS_QUEUE_KEY = "ml_training_queue"
MAX_CONCURRENT_TRAININGS = int(os.environ.get("MAX_CONCURRENT_TRAININGS", 2))
MAX_QUEUE_SIZE = int(os.environ.get("MAX_QUEUE_SIZE", 1000))

class RedisJobQueue:
    """
    Redis-based job queue for ML training tasks.
    Provides persistent queuing across application restarts.
    """

    def __init__(self):
        try:
            print("Connecting to Redis:", REDIS_HOST, REDIS_PORT, REDIS_SSL)
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                ssl=REDIS_SSL,
                # password=REDIS_PASSWORD,
                decode_responses=True
            )
            
            # startup_nodes = [ClusterNode(REDIS_HOST, REDIS_PORT)]
            # self.redis_client = redis.cluster.RedisCluster(
            #     startup_nodes=startup_nodes,
            #     ssl=REDIS_SSL,
            #     password=REDIS_PASSWORD,
            #     decode_responses=True
            # )
            self.redis_client.ping()
            self.redis_concurrency_cap = MAX_CONCURRENT_TRAININGS
            print("Redis job queue connected successfully")
        except Exception as e:
            print(f"Redis job queue connection failed: {e}")
            self.redis_client = None

    def enqueue(self, job_data):
        """Add a job to the queue."""
        if not self.redis_client:
            raise RuntimeError("Redis connection not available")
        
        # Check queue size
        queue_length = self.redis_client.llen(REDIS_QUEUE_KEY)
        if queue_length >= MAX_QUEUE_SIZE:
            raise RuntimeError(f"Queue is full (max {MAX_QUEUE_SIZE} jobs). Please try again later.")
        
        try:
            self.redis_client.lpush(REDIS_QUEUE_KEY, json.dumps(job_data))
            return True
        except Exception as e:
            print(f"Failed to enqueue job: {e}")
            return False

    def dequeue(self):
        """Remove and return a job from the queue."""
        if not self.redis_client:
            return None

        try:
            result = self.redis_client.brpop(REDIS_QUEUE_KEY, timeout=1)
            if result:
                _, job_data = result
                return json.loads(job_data)
            return None
        except Exception as e:
            print(f"Failed to dequeue job: {e}")
            return None

    def _get_active_job_count(self):
        """Get current number of active training jobs."""
        if not self.redis_client:
            return 0
        try:
            count = self.redis_client.get("active_training_jobs")
            return int(count) if count else 0
        except Exception as e:
            print(f"Error getting active job count: {e}")
            return 0

    def redis_queue_worker(self, cls):
        while True:
            # Check if we can start a new job
            active_count = self._get_active_job_count()
            if active_count >= MAX_CONCURRENT_TRAININGS:
                threading.Event().wait(5)  # Wait before checking again
                continue
            
            job_data = self.dequeue()
            if job_data:
                try:
                    # Increment active jobs
                    self.redis_client.incr("active_training_jobs")
                    
                    try:
                        # Process job (existing logic)
                        func_name = job_data.get("func")
                        args = job_data.get("args", [])
                        kwargs = job_data.get("kwargs", {})
                        job_id = job_data.get("job_id")
                        
                        if func_name == "_train_and_eval_actual":
                            user_id, username, item_id, item_name, raw_prices = args
                            instance = cls(user_id, username, item_id, item_name)
                            pipe, scaler, df, metrics = instance._train_and_eval_actual(raw_prices)
                            
                            # Serialize result
                            pipe_buffer = io.BytesIO()
                            joblib.dump(pipe, pipe_buffer)
                            pipe_bytes = pipe_buffer.getvalue()

                            scaler_buffer = io.BytesIO()
                            joblib.dump(scaler, scaler_buffer)
                            scaler_bytes = scaler_buffer.getvalue()

                            df_json = df.to_json()
                            metrics_json = json.dumps(metrics)
                            result_dict = {
                                "pipe": base64.b64encode(pipe_bytes).decode(),
                                "scaler": base64.b64encode(scaler_bytes).decode(),
                                "df": df_json,
                                "metrics": metrics_json
                            }
                            self.redis_client.set(f"job_result:{job_id}", json.dumps(result_dict))
                            print(f"Training completed for job {job_id}")
                        else:
                            print(f"Unknown job type: {func_name}")
                    
                    finally:
                        # Decrement active jobs
                        self.redis_client.decr("active_training_jobs")
                        # Note: QUEUE_STATUS_PATH is not accessible here, so skipping write_queue_status
                        
                except Exception as e:
                    print(f"Error processing job: {e}")
                    job_id = job_data.get("job_id")
                    if job_id:
                        self.redis_client.set(f"job_result:{job_id}", json.dumps({"error": str(e)}))
                    self.redis_client.decr("active_training_jobs")
            else:
                threading.Event().wait(1)

class RedisCache:
    """
    Async Redis-based caching service using redis-py 4.2.0+ native async support.
    """
    
    def __init__(self):
        self.host = REDIS_HOST
        self.port = REDIS_PORT
        self.db = REDIS_DB
        self.password = REDIS_PASSWORD
        self.ssl = REDIS_SSL
        self.client = None
        self.connected = False
    
    async def _ensure_connected(self):
        """Ensure the client is connected (lazy connection)."""
        if not self.connected and self.client is None:
            await self._connect()
            self.connected = True

    async def _connect(self):
        """Initialize async Redis client."""
        try:
            print("Connecting to Redis:", REDIS_HOST, REDIS_PORT, REDIS_SSL)
            self.client = redis.asyncio.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                # password=self.password,
                ssl=self.ssl,
                decode_responses=True
            )
            
            # startup_nodes = [ClusterNode(self.host, self.port)]
            # self.client = redis.asyncio.cluster.RedisCluster(
            #     startup_nodes=startup_nodes,
            #     ssl=self.ssl,
            #     password=self.password,
            #     decode_responses=True
            # )
            await self.client.ping()
            print("Async Redis cache connected successfully")
        except Exception as e:
            print(f"Async Redis connection failed: {e}")
            self.client = None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in cache with optional TTL (time to live in seconds).
        """
        await self._ensure_connected()
        if not self.client:
            return False

        try:
            serialized_value = json.dumps(value)
            if ttl:
                return await self.client.setex(key, ttl, serialized_value)
            else:
                return await self.client.set(key, serialized_value)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        """
        await self._ensure_connected()
        if not self.client:
            return None

        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        """
        await self._ensure_connected()
        if not self.client:
            return False

        try:
            return bool(await self.client.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

print("Initializing Redis cache...")
redis_cache = RedisCache()