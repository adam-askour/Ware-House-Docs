from celery import shared_task

from .services import process_ocr_job


@shared_task
def process_ocr_job_task(job_id):
    return process_ocr_job(job_id).status

