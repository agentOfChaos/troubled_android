from subcommands import TransferDone, clamScanOneShot
from jobhandler import JobHandler
import os
import time


class ScanCompleted:

    def __init__(self, andr, local, clamline, infected):
        self.andr = andr
        self.local = local
        self.clamline = clamline
        self.infected = infected

    @property
    def resultstring(self):
        zero = self.clamline.index(self.andr)
        return str(self.clamline[zero:])


class ScanJobHandler(JobHandler):

    """
        Accepts jobs in the form of a TrasnferDone obect.
        Scans a single file with an antivirus program (clamAV), and then
        puts the corresponding ScanCompleted object into the results queue
    """

    def __init__(self, maxjobs=50, keepfiles=False, debug=False):
        super().__init__(maxjobs, debug=debug)
        self.keepfiles = keepfiles

    def waitStableFile(self, file):
        while not os.path.isfile(file):
            time.sleep(0.5)

    def worker(self, jobdata):
        assert isinstance(jobdata, TransferDone)
        self.waitStableFile(jobdata.local)
        result, infected = clamScanOneShot(jobdata.local)
        self.results.put(ScanCompleted(jobdata.andr, jobdata.local, result, infected))
        if not self.keepfiles:
            os.remove(jobdata.local)
            
        super().worker(jobdata)
