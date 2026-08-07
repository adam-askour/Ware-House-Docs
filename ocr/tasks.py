from celery import shared_task

from .services import process_ocr_job


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_ocr_job_task(self, job_id):
    job = process_ocr_job(job_id)
    if job.status == job.Status.FAILED and self.request.retries < self.max_retries:
        raise self.retry()
    return job.status
