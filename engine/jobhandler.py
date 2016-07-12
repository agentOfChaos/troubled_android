from threading import Thread, Semaphore
from queue import Queue
import time


class JobHandler:
    """
        Base class to handle job dispatching:
        * when addJob(job) is called, job is appended to the task queue
        * when a slot is available, an indipendent thread is dispatched to execute the job
        * when the job finishes, the result is put in the results queue (this behaviour must be
          implemented by the sub-class)
        * genResults() is the generator of the results
    """

    def __init__(self, maxjobs=50, debug=False):
        self.maxjobs = maxjobs
        self.debug = debug
        self.semaphore = Semaphore(self.maxjobs)
        self.results = Queue()
        self.tasks = Queue()  # glorious twin-queues!
        self.running = 0
        self.acceptJobs = True

        self.feederthread = Thread(target=self.selfFeeder)
        self.feederthread.start()

    def worker(self, jobdata):

        self.running -= 1
        self.semaphore.release()

    def finished(self, callback=None):
        self.acceptJobs = False
        while self.running > 0 or self.tasks.qsize() > 0:
            time.sleep(1.0)
        self.results.put(None)
        self.tasks.put(None)
        if callback is not None:
            callback()

    def spawnJob(self, jobdata):
        t = Thread(target=self.worker, args=(jobdata,))
        t.start()

    def selfFeeder(self):
        while True:
            job = self.tasks.get()
            if job is None:
                break
            self.semaphore.acquire()
            self.running += 1
            self.spawnJob(job)

    def addJob(self, jobdata):
        if self.acceptJobs:
            self.tasks.put(jobdata)
        elif self.debug:
            print("refusing new job")

    def genResults(self):
        while True:
            val = self.results.get()
            if val == None:
                return
            yield val