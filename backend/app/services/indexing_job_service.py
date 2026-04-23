"""Simple in-memory indexing job tracker."""

from datetime import datetime
from typing import Dict


class IndexingJobService:
    def __init__(self):
        self.jobs: Dict[str, dict] = {}

    def create_job(self, job_id: str, filename: str):
        self.jobs[job_id] = {
            "job_id": job_id,
            "filename": filename,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "document_id": None,
            "error": None,
        }

    def mark_running(self, job_id: str):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "running"

    def mark_completed(self, job_id: str, document_id: str):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "completed"
            self.jobs[job_id]["document_id"] = document_id

    def mark_failed(self, job_id: str, error: str):
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = "failed"
            self.jobs[job_id]["error"] = error

    def get(self, job_id: str):
        return self.jobs.get(job_id)


indexing_job_service = IndexingJobService()
