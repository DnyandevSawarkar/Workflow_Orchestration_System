from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import random
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceResult:
    """Represents the result of a service operation"""
    def __init__(self, success: bool, data: Optional[Dict[str, Any]] = None, 
                 error_message: Optional[str] = None, retry_count: int = 0):
        self.success = success
        self.data = data or {}
        self.error_message = error_message
        self.retry_count = retry_count
        self.timestamp = datetime.now()

class BaseService(ABC):
    """Abstract base class for all services"""
    
    def __init__(self, name: str, failure_rate: float = 0.25):
        self.name = name
        self.failure_rate = failure_rate
        self.call_count = 0
        
    @abstractmethod
    def execute(self, **kwargs) -> ServiceResult:
        """Execute the service operation"""
        pass
    
    def _simulate_failure(self) -> bool:
        """Simulate random failures based on failure rate"""
        self.call_count += 1
        should_fail = random.random() < self.failure_rate
        
        if should_fail:
            logger.warning(f"{self.name} - Simulated failure on call #{self.call_count}")
        else:
            logger.info(f"{self.name} - Successful execution on call #{self.call_count}")
            
        return should_fail
    
    def _log_operation(self, operation: str, success: bool, details: str = ""):
        """Log service operations for observability"""
        status = "SUCCESS" if success else "FAILURE"
        logger.info(f"{self.name} - {operation} - {status} - {details}")

class RetryableService(BaseService):
    """Base class for services that support retry logic"""
    
    def __init__(self, name: str, failure_rate: float = 0.25, max_retries: int = 3):
        super().__init__(name, failure_rate)
        self.max_retries = max_retries
    
    def execute_with_retry(self, **kwargs) -> ServiceResult:
        """Execute service with retry logic"""
        for attempt in range(self.max_retries + 1):
            result = self.execute(**kwargs)
            result.retry_count = attempt
            
            if result.success:
                if attempt > 0:
                    logger.info(f"{self.name} - Succeeded after {attempt} retries")
                return result
            
            if attempt < self.max_retries:
                logger.warning(f"{self.name} - Attempt {attempt + 1} failed, retrying...")
            else:
                logger.error(f"{self.name} - All {self.max_retries + 1} attempts failed")
                
        return result

