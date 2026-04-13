"""
Scheduler Service - APScheduler-based background monitoring

Implements periodic detection jobs for the Sensing & Intelligence Layer.
"""
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from services.sensing_service import SensingService
from services.decision_service import DecisionService
from services.signal_service import SignalService
from api.config import settings
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Background scheduler for periodic detection and monitoring.
    
    Jobs:
    - Low stock detection (every 30 seconds)
    - Stockout detection (every 30 seconds)
    - Delivery delay detection (every 60 seconds)
    - Demand analysis (every 5 minutes)
    - Warehouse utilization (every 2 minutes)
    - Signal processing (every 60 seconds)
    - Stale signal cleanup (every hour)
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.sensing_service = SensingService()
        self.decision_service = DecisionService()
        self.signal_service = SignalService()
        self._is_running = False
        self._job_stats = {}
        
        # Add event listeners
        self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)
    
    def _on_job_executed(self, event):
        """Callback when a job executes successfully"""
        job_id = event.job_id
        if job_id not in self._job_stats:
            self._job_stats[job_id] = {"runs": 0, "errors": 0, "last_run": None}
        
        self._job_stats[job_id]["runs"] += 1
        self._job_stats[job_id]["last_run"] = datetime.utcnow()
    
    def _on_job_error(self, event):
        """Callback when a job errors"""
        job_id = event.job_id
        if job_id not in self._job_stats:
            self._job_stats[job_id] = {"runs": 0, "errors": 0, "last_run": None}
        
        self._job_stats[job_id]["errors"] += 1
        logger.error(f"Job {job_id} failed: {event.exception}")
    
    def _wrap_job(self, func: Callable, job_name: str) -> Callable:
        """Wrap a job function with logging and error handling"""
        def wrapped():
            try:
                logger.debug(f"Running scheduled job: {job_name}")
                result = func()
                logger.debug(f"Job {job_name} completed: {result}")
                return result
            except Exception as e:
                logger.error(f"Error in scheduled job {job_name}: {e}")
                raise
        return wrapped
    
    def _job_detect_low_stock(self):
        """Job: Detect low stock items"""
        return self.sensing_service.detect_low_stock(source="scheduler")
    
    def _job_detect_stockout(self):
        """Job: Detect stockout items"""
        return self.sensing_service.detect_stockout(source="scheduler")
    
    def _job_detect_delivery_delay(self):
        """Job: Detect delivery delays"""
        return self.sensing_service.detect_delivery_delay(source="scheduler")
    
    def _job_detect_demand_spike(self):
        """Job: Detect demand spikes"""
        return self.sensing_service.detect_demand_spike(source="scheduler")
    
    def _job_detect_demand_drop(self):
        """Job: Detect demand drops"""
        return self.sensing_service.detect_demand_drop(source="scheduler")
    
    def _job_detect_utilization(self):
        """Job: Detect warehouse utilization issues"""
        over = self.sensing_service.detect_over_utilization(source="scheduler")
        under = self.sensing_service.detect_under_utilization(source="scheduler")
        return {"over_utilization": over, "under_utilization": under}
    
    def _job_process_signals(self):
        """Job: Process active signals through decision engine"""
        return self.decision_service.process_active_signals(auto_only=True)
    
    def _job_expire_stale_signals(self):
        """Job: Expire stale signals"""
        return self.signal_service.expire_stale_signals()
    
    def setup_jobs(self):
        """Set up all scheduled jobs"""
        
        # Low stock detection - every 30 seconds
        self.scheduler.add_job(
            self._wrap_job(self._job_detect_low_stock, "detect_low_stock"),
            trigger=IntervalTrigger(seconds=settings.scheduler_low_stock_interval),
            id="detect_low_stock",
            name="Detect Low Stock",
            replace_existing=True
        )
        
        # Stockout detection - every 30 seconds
        self.scheduler.add_job(
            self._wrap_job(self._job_detect_stockout, "detect_stockout"),
            trigger=IntervalTrigger(seconds=settings.scheduler_stockout_interval),
            id="detect_stockout",
            name="Detect Stockout",
            replace_existing=True
        )
        
        # Delivery delay detection - every 60 seconds
        self.scheduler.add_job(
            self._wrap_job(self._job_detect_delivery_delay, "detect_delivery_delay"),
            trigger=IntervalTrigger(seconds=settings.scheduler_delivery_delay_interval),
            id="detect_delivery_delay",
            name="Detect Delivery Delays",
            replace_existing=True
        )
        
        # Demand analysis - every 5 minutes
        self.scheduler.add_job(
            self._wrap_job(self._job_detect_demand_spike, "detect_demand_spike"),
            trigger=IntervalTrigger(seconds=settings.scheduler_demand_analysis_interval),
            id="detect_demand_spike",
            name="Detect Demand Spike",
            replace_existing=True
        )
        
        self.scheduler.add_job(
            self._wrap_job(self._job_detect_demand_drop, "detect_demand_drop"),
            trigger=IntervalTrigger(seconds=settings.scheduler_demand_analysis_interval),
            id="detect_demand_drop",
            name="Detect Demand Drop",
            replace_existing=True
        )
        
        # Warehouse utilization - every 2 minutes
        self.scheduler.add_job(
            self._wrap_job(self._job_detect_utilization, "detect_utilization"),
            trigger=IntervalTrigger(seconds=settings.scheduler_utilization_interval),
            id="detect_utilization",
            name="Detect Utilization Issues",
            replace_existing=True
        )
        
        # Process signals - every 60 seconds
        self.scheduler.add_job(
            self._wrap_job(self._job_process_signals, "process_signals"),
            trigger=IntervalTrigger(seconds=60),
            id="process_signals",
            name="Process Active Signals",
            replace_existing=True
        )
        
        # Expire stale signals - every hour
        self.scheduler.add_job(
            self._wrap_job(self._job_expire_stale_signals, "expire_signals"),
            trigger=IntervalTrigger(hours=1),
            id="expire_signals",
            name="Expire Stale Signals",
            replace_existing=True
        )
        
        logger.info("Scheduler jobs configured")
    
    def start(self):
        """Start the scheduler"""
        if not self._is_running:
            self.setup_jobs()
            self.scheduler.start()
            self._is_running = True
            logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("Scheduler stopped")
    
    def pause(self):
        """Pause all jobs"""
        self.scheduler.pause()
        logger.info("Scheduler paused")
    
    def resume(self):
        """Resume all jobs"""
        self.scheduler.resume()
        logger.info("Scheduler resumed")
    
    def pause_job(self, job_id: str):
        """Pause a specific job"""
        self.scheduler.pause_job(job_id)
        logger.info(f"Job {job_id} paused")
    
    def resume_job(self, job_id: str):
        """Resume a specific job"""
        self.scheduler.resume_job(job_id)
        logger.info(f"Job {job_id} resumed")
    
    def run_job_now(self, job_id: str) -> Dict[str, Any]:
        """Run a specific job immediately"""
        job = self.scheduler.get_job(job_id)
        if job:
            try:
                result = job.func()
                return {"success": True, "job_id": job_id, "result": result}
            except Exception as e:
                return {"success": False, "job_id": job_id, "error": str(e)}
        return {"success": False, "error": f"Job {job_id} not found"}
    
    def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific job"""
        job = self.scheduler.get_job(job_id)
        if job:
            stats = self._job_stats.get(job_id, {"runs": 0, "errors": 0, "last_run": None})
            return {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "runs": stats["runs"],
                "errors": stats["errors"],
                "last_run": stats["last_run"].isoformat() if stats["last_run"] else None
            }
        return None
    
    def get_all_jobs(self) -> list:
        """Get information about all jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            stats = self._job_stats.get(job.id, {"runs": 0, "errors": 0, "last_run": None})
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "runs": stats["runs"],
                "errors": stats["errors"],
                "last_run": stats["last_run"].isoformat() if stats["last_run"] else None
            })
        return jobs
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            "is_running": self._is_running,
            "state": str(self.scheduler.state),
            "job_count": len(self.scheduler.get_jobs()),
            "jobs": self.get_all_jobs()
        }
    
    def update_job_interval(self, job_id: str, seconds: int):
        """Update the interval of a job"""
        job = self.scheduler.get_job(job_id)
        if job:
            self.scheduler.reschedule_job(
                job_id,
                trigger=IntervalTrigger(seconds=seconds)
            )
            logger.info(f"Job {job_id} interval updated to {seconds} seconds")
            return True
        return False


# Global scheduler instance
scheduler_service = SchedulerService()


def start_scheduler():
    """Start the global scheduler"""
    scheduler_service.start()


def stop_scheduler():
    """Stop the global scheduler"""
    scheduler_service.stop()
