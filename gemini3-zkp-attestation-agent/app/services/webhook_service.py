"""
Webhook Service
Handles callback notifications for attestation status changes
"""

import httpx
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from collections import deque

logger = logging.getLogger(__name__)


class WebhookRetryQueue:
    """Queue for retrying failed webhook deliveries"""
    
    def __init__(self, max_size: int = 1000):
        self.queue: deque = deque(maxlen=max_size)
    
    def add(self, claim_id: str, payload: dict):
        """Add failed webhook to retry queue"""
        self.queue.append({
            "claim_id": claim_id,
            "payload": payload,
            "attempts": 0,
            "added_at": datetime.utcnow()
        })
        logger.info(f"Added webhook to retry queue: {claim_id}")
    
    def get_pending(self, max_items: int = 10) -> list:
        """Get pending webhooks for retry"""
        return list(self.queue)[:max_items]


# Global retry queue
webhook_retry_queue = WebhookRetryQueue()


class WebhookService:
    """Service for sending webhook notifications"""
    
    def __init__(self, timeout: float = 10.0, max_retries: int = 3):
        """
        Initialize webhook service
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
    
    async def trigger_webhook(
        self,
        callback_url: str,
        event: str,
        claim_id: str,
        status: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send webhook notification
        
        Args:
            callback_url: Webhook URL to call
            event: Event type (e.g., "attestation.status_changed")
            claim_id: Attestation claim ID
            status: Current status
            data: Additional event data
            
        Returns:
            True if webhook sent successfully
        """
        payload = {
            "event": event,
            "claim_id": claim_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    callback_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "ZKPA-Webhook/1.0"
                    }
                )
                
                if response.status_code in [200, 201, 202, 204]:
                    logger.info(
                        f"Webhook sent successfully: {callback_url} "
                        f"(status: {response.status_code})"
                    )
                    return True
                else:
                    logger.warning(
                        f"Webhook returned error status: {response.status_code} "
                        f"(url: {callback_url})"
                    )
                    webhook_retry_queue.add(claim_id, payload)
                    return False
                    
        except httpx.TimeoutException:
            logger.error(f"Webhook timeout: {callback_url}")
            webhook_retry_queue.add(claim_id, payload)
            return False
            
        except httpx.RequestError as e:
            logger.error(f"Webhook request error: {e} (url: {callback_url})")
            webhook_retry_queue.add(claim_id, payload)
            return False
            
        except Exception as e:
            logger.error(f"Unexpected webhook error: {e} (url: {callback_url})")
            webhook_retry_queue.add(claim_id, payload)
            return False
    
    async def trigger_status_change(
        self,
        attestation: dict
    ) -> bool:
        """
        Trigger webhook for attestation status change
        
        Args:
            attestation: Attestation data dict
            
        Returns:
            True if webhook sent successfully
        """
        callback_url = attestation.get("callback_url")
        if not callback_url:
            return True  # No webhook configured
        
        return await self.trigger_webhook(
            callback_url=callback_url,
            event="attestation.status_changed",
            claim_id=attestation["claim_id"],
            status=attestation["status"],
            data={
                "completed_at": attestation.get("completed_at"),
                "package_uri": attestation.get("package", {}).get("package_uri"),
                "anchor_tx": attestation.get("anchor", {}).get("transaction_id")
            }
        )
    
    async def trigger_completion(
        self,
        attestation: dict
    ) -> bool:
        """
        Trigger webhook for attestation completion
        
        Args:
            attestation: Attestation data dict
            
        Returns:
            True if webhook sent successfully
        """
        callback_url = attestation.get("callback_url")
        if not callback_url:
            return True  # No webhook configured
        
        return await self.trigger_webhook(
            callback_url=callback_url,
            event="attestation.completed",
            claim_id=attestation["claim_id"],
            status=attestation["status"],
            data={
                "completed_at": attestation.get("completed_at"),
                "proof_hash": attestation.get("proof", {}).get("proof_hash"),
                "package_hash": attestation.get("package", {}).get("package_hash"),
                "package_uri": attestation.get("package", {}).get("package_uri"),
                "anchor_tx": attestation.get("anchor", {}).get("transaction_id"),
                "anchor_explorer": attestation.get("anchor", {}).get("explorer_url")
            }
        )
    
    async def trigger_failure(
        self,
        attestation: dict,
        error_message: str
    ) -> bool:
        """
        Trigger webhook for attestation failure
        
        Args:
            attestation: Attestation data dict
            error_message: Error description
            
        Returns:
            True if webhook sent successfully
        """
        callback_url = attestation.get("callback_url")
        if not callback_url:
            return True  # No webhook configured
        
        return await self.trigger_webhook(
            callback_url=callback_url,
            event="attestation.failed",
            claim_id=attestation["claim_id"],
            status=attestation["status"],
            data={
                "error": error_message,
                "failed_at": datetime.utcnow().isoformat()
            }
        )


# Global webhook service instance
webhook_service = WebhookService()
