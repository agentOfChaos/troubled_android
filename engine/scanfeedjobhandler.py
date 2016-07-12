from engine.subcommands import TransferDone
from engine.jobhandler import JobHandler
from engine.subcommands import adbPullOneShot


class ScanFeedJob:

    def __init__(self, params):
        self.params = params


class ScanFeedJobHandler(JobHandler):

    """
        Accepts jobs in the form of a ScanFeedJob object
        Adb pull a single file from the mobile,
        puts the corresponding TrasnferDone object into the results queue
    """

    def __init__(self, scanner, maxjobs=50, debug=False):
        super().__init__(maxjobs, debug=debug)
        self.scanner = scanner

    def worker(self, jobdata):
        assert isinstance(jobdata, ScanFeedJob)
        transferdone = adbPullOneShot(*jobdata.params)
        if isinstance(transferdone, TransferDone):
            self.scanner.addJob(transferdone)
        else:
            if self.debug:
                print("DEBUG (scan feeder): failed transfer of %s" % transferdone.andr)
        super().worker(jobdata)
