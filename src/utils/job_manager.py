import time
import schedule
from typing import Callable


class JobManager:
    def __init__(self) -> None:
        self.queue: list[Callable[[], None]] = []
        self.running = True


    def __enqueue(self, job_func) -> None:
        self.queue.append(job_func)


    def __run_pending_sequential(self) -> None:
        if self.queue:
            job_func = self.queue.pop(0)
            job_func()


    def add_job(self, job_method: Callable[[], None], interval_hours: int) -> None:
        schedule.every(interval_hours).hours.do(self.__enqueue, job_method)


    def start_blocking_scheduler(self) -> None:
        while True:
            if not self.running:
                break
            schedule.run_pending()
            self.__run_pending_sequential()
            time.sleep(1)
