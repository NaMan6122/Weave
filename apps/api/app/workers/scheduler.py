"""Main scheduler — runs all workers on their configured intervals via APScheduler."""

import asyncio
import logging
import signal

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.workers import crawl_worker, digest_worker, embedding_worker, expiry_worker, metrics_worker, sla_worker, triangle_worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(crawl_worker.run, "interval", hours=24, id="crawl_worker")
    scheduler.add_job(embedding_worker.run_embedding_worker, "interval", hours=6, id="embedding_worker")
    scheduler.add_job(metrics_worker.run, "interval", days=7, id="metrics_worker")
    scheduler.add_job(expiry_worker.run, "interval", hours=24, id="expiry_worker")
    scheduler.add_job(triangle_worker.run, "interval", hours=1, id="triangle_worker")
    scheduler.add_job(sla_worker.run, "interval", hours=24, id="sla_worker")
    scheduler.add_job(digest_worker.run, "interval", days=7, id="digest_worker")

    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, scheduler.shutdown)
    loop.add_signal_handler(signal.SIGTERM, scheduler.shutdown)

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()
