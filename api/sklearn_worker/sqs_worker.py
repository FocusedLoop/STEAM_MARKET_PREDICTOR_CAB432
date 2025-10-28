import boto3
import json
import os
import logging
import time
import threading
from botocore.exceptions import ClientError
from utils_ml import PriceModel, validate_price_history
from fastapi.responses import JSONResponse
from db import model_save_ml_index

logger = logging.getLogger(__name__)

class SQSWorker:
    """
    Background worker that polls SQS queue and processes ML jobs.
    """
    
    def __init__(self):
        self.queue_url = os.getenv("SQS_QUEUE_URL")
        self.dlq_url = os.getenv("SQS_DLQ_URL")
        self.region = os.getenv("AWS_REGION", "ap-southeast-2")
        self.worker_thread = None
        self.running = False
        
        try:
            self.endpoint_url = os.getenv("AWS_ENDPOINT_URL")
            client_kwargs = {'region_name': self.region}
            if self.endpoint_url:
                client_kwargs['endpoint_url'] = self.endpoint_url
            
            self.sqs = boto3.client('sqs', **client_kwargs)
            logger.info(f"SQS worker initialized for queue: {self.queue_url}")
        except Exception as e:
            logger.error(f"Failed to initialize SQS worker: {e}")
            self.sqs = None
    
    def process_message(self, message: dict) -> bool:
        """
        Process a single message from the queue.
        
        Args:
            message: SQS message
            
        Returns:
            bool: True if message was processed successfully
        """
        try:
            body = json.loads(message['Body'])
            job_type = body.get('job_type')
            
            logger.info(f"Processing {job_type} job for item {body.get('item_id')}")
            
            if job_type == 'train':
                return self._process_training_job(body, message)
            elif job_type == 'predict':
                return self._process_prediction_job(body, message)
            else:
                logger.error(f"Unknown job type: {job_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return False
    
    def _process_training_job(self, job_data: dict, message: dict) -> bool:
        """Process a training job."""
        try:
            user_id = job_data.get('user_id')
            username = job_data.get('username')
            item_id = job_data.get('item_id')
            group_id = job_data.get('group_id')
            item_name = job_data.get('item_name')
            price_history = job_data.get('price_history')
            
            logger.info(f"Training model for {item_name} (group_id: {group_id},item_id: {item_id}, user: {username})")
            
            is_valid, error_msg = validate_price_history(price_history)
            if not is_valid:
                logger.error(f"Invalid price history: {error_msg}")
                return False
            
            model = PriceModel(user_id, username, item_id, item_name)
            result = model.create_model(price_history.get('prices'))

            model_save_ml_index(
                user_id,
                group_id,
                item_id,
                result["data_hash"]
            )
            
            logger.info(f"Model training completed for item {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in training job: {e}")
            return False
    
    def _process_prediction_job(self, job_data: dict, message: dict) -> bool:
        """Process a prediction job."""
        try:
            user_id = job_data.get('user_id')
            username = job_data.get('username')
            item_id = job_data.get('item_id')
            item_name = job_data.get('item_name')
            data_hash = job_data.get('data_hash')
            start_time = job_data.get('start_time')
            end_time = job_data.get('end_time')
            
            logger.info(f"Generating prediction for {item_name} (item_id: {item_id})")
            
            model = PriceModel(user_id, username, item_id, item_name)
            result = model.generate_prediction(start_time, end_time, data_hash)
            
            logger.info(f"Prediction generated for item {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in prediction job: {e}")
            return False
    
    def send_to_dlq(self, message: dict):
        """Send a failed message to the DLQ."""
        if not self.dlq_url:
            logger.warning("DLQ URL not configured, cannot send failed message to DLQ")
            return
        
        try:
            self.sqs.send_message(
                QueueUrl=self.dlq_url,
                MessageBody=message['Body']
            )
            logger.info("Message sent to DLQ")
        except ClientError as e:
            logger.error(f"Failed to send message to DLQ: {e}")
    
    def delete_message(self, receipt_handle: str):
        """Delete a message from the queue after successful processing."""
        try:
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
        except ClientError as e:
            logger.error(f"Failed to delete message: {e}")
    
    def _worker_loop(self):
        """Main worker loop that polls the SQS queue."""
        while self.running:
            try:
                if not self.sqs or not self.queue_url:
                    logger.error("SQS client or queue URL not configured")
                    time.sleep(10)
                    continue
                
                response = self.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=20,  # Long polling
                    MessageAttributeNames=['All']
                )
                
                messages = response.get('Messages', [])
                
                if messages:
                    for message in messages:
                        logger.info(f"Received message: {message['MessageId']}")
                        
                        success = self.process_message(message)
                        
                        if success:
                            self.delete_message(message['ReceiptHandle'])
                            logger.info(f"Successfully processed message: {message['MessageId']}")
                        else:
                            receive_count = int(message.get('Attributes', {}).get('ApproximateReceiveCount', 0))
                            logger.warning(f"Failed to process message: {message['MessageId']}, receive_count: {receive_count}")
                            
                            if receive_count >= 3:
                                logger.error(f"Message {message['MessageId']} exceeded max receive count, will be sent to DLQ")
                                self.send_to_dlq(message)
                                self.delete_message(message['ReceiptHandle'])
                            else:
                                self.sqs.change_message_visibility(
                                    QueueUrl=self.queue_url,
                                    ReceiptHandle=message['ReceiptHandle'],
                                    VisibilityTimeout=60  # 1 minute delay before retry
                                )
                else:
                    pass
                    
            except ClientError as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(10)
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {e}")
                time.sleep(10)
    
    def start(self):
        """Start the worker thread."""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("SQS worker started")
    
    def stop(self):
        """Stop the worker thread."""
        if self.running:
            self.running = False
            logger.info("SQS worker stopped")

sqs_worker = SQSWorker()

def start_sqs_worker():
    """Start the SQS worker."""
    sqs_worker.start()