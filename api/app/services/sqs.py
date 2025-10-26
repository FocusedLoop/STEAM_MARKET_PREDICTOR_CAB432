import boto3
import json
import os
import logging
from typing import Dict, Any
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class SQSClient:
    """
    SQS client for sending ML training and prediction jobs to the queue.
    """
    
    def __init__(self):
        self.queue_url = os.getenv("SQS_QUEUE_URL")
        self.dlq_url = os.getenv("SQS_DLQ_URL")
        self.region = os.getenv("AWS_REGION", "ap-southeast-2")
        self.endpoint_url = os.getenv("AWS_ENDPOINT_URL")
        
        try:
            client_kwargs = {'region_name': self.region}
            if self.endpoint_url:
                client_kwargs['endpoint_url'] = self.endpoint_url
            
            self.sqs = boto3.client('sqs', **client_kwargs)
            logger.info(f"SQS client initialized for queue: {self.queue_url}")
        except Exception as e:
            logger.error(f"Failed to initialize SQS client: {e}")
            self.sqs = None
    
    def send_training_job(self, user_id: int, username: str, item_id: int, 
                         item_name: str, price_history: Dict[str, Any]) -> bool:
        """
        Send a training job to the SQS queue.
        
        Args:
            user_id: User ID
            username: Username
            item_id: Item ID
            item_name: Item name
            price_history: Price history data
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self.sqs or not self.queue_url:
            logger.error("SQS client or queue URL not configured")
            return False
        
        message_body = {
            "job_type": "train",
            "user_id": user_id,
            "username": username,
            "item_id": item_id,
            "item_name": item_name,
            "price_history": price_history,
            "timestamp": str(os.getenv("TIMESTAMP", ""))
        }
        
        try:
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body),
                MessageAttributes={
                    'JobType': {
                        'StringValue': 'train',
                        'DataType': 'String'
                    },
                    'ItemId': {
                        'StringValue': str(item_id),
                        'DataType': 'Number'
                    },
                    'UserId': {
                        'StringValue': str(user_id),
                        'DataType': 'Number'
                    }
                }
            )
            logger.info(f"Training job sent to SQS for item {item_id} (user {username})")
            logger.info(f"MessageId: {response['MessageId']}")
            return True
        except ClientError as e:
            logger.error(f"Failed to send training job to SQS: {e}")
            return False
    
    def send_prediction_job(self, user_id: int, username: str, item_id: int,
                           item_name: str, data_hash: str, start_time: str, 
                           end_time: str) -> bool:
        """
        Send a prediction job to the SQS queue.
        
        Args:
            user_id: User ID
            username: Username
            item_id: Item ID
            item_name: Item name
            data_hash: Model data hash
            start_time: Prediction start time
            end_time: Prediction end time
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self.sqs or not self.queue_url:
            logger.error("SQS client or queue URL not configured")
            return False
        
        message_body = {
            "job_type": "predict",
            "user_id": user_id,
            "username": username,
            "item_id": item_id,
            "item_name": item_name,
            "data_hash": data_hash,
            "start_time": start_time,
            "end_time": end_time
        }
        
        try:
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body),
                MessageAttributes={
                    'JobType': {
                        'StringValue': 'predict',
                        'DataType': 'String'
                    },
                    'ItemId': {
                        'StringValue': str(item_id),
                        'DataType': 'Number'
                    },
                    'UserId': {
                        'StringValue': str(user_id),
                        'DataType': 'Number'
                    }
                }
            )
            logger.info(f"Prediction job sent to SQS for item {item_id} (user {username})")
            logger.info(f"MessageId: {response['MessageId']}")
            return True
        except ClientError as e:
            logger.error(f"Failed to send prediction job to SQS: {e}")
            return False
    
    def get_queue_attributes(self) -> Dict[str, Any]:
        """
        Get queue attributes for monitoring.
        
        Returns:
            dict: Queue attributes including approximate number of messages
        """
        if not self.sqs or not self.queue_url:
            return {}
        
        try:
            response = self.sqs.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=['All']
            )
            return response.get('Attributes', {})
        except ClientError as e:
            logger.error(f"Failed to get queue attributes: {e}")
            return {}

sqs_client = SQSClient()

