import os

from engine.jobhandler import JobHandler
from engine.subcommands import device_list_files_parsed
from engine.utils import Unclog


class ListJob:

    def __init__(self, andr_folder):
        self.andr_folder = andr_folder


class FsItem:

    def __init__(self, file_entry, parent):
        self.file_entry = file_entry
        self.parent = parent
        if isinstance(file_entry, dict):
            self.is_dir = file_entry["is_directory"]
        else:
            self.is_dir = True

    @property
    def folderWasEmpty(self):
        return self.file_entry is None

    @property
    def fullpath(self):
        if not self.folderWasEmpty:
            return os.path.join(self.parent, self.file_entry["filename"])
        else:
            return self.parent

    @property
    def listjob(self):
        if not self.is_dir:
            return None
        return ListJob(self.fullpath)


class LsJobHandler(JobHandler):

    """
        Accepts jobs in the form of either a ListJob or Unclog object.
        The Unclog object is put into the results queue unmodified.
        Uses adb to list a single directory on the mobile, puts all the single FsItem entries
        in the result queue
    """

    def __init__(self, deviceid, maxjobs=50, debug=False):
        super().__init__(maxjobs, debug=debug)
        self.deviceid = deviceid

    def worker(self, jobdata):
        if isinstance(jobdata, Unclog):
            self.results.put(jobdata)
        else:
            assert isinstance(jobdata, ListJob)
            if self.debug:
                print("DEBUG (list dir): listing %s" % jobdata.andr_folder)
            files = device_list_files_parsed(jobdata.andr_folder, self.deviceid)
            if len(files) == 0:
                self.results.put(FsItem(None, jobdata.andr_folder))
            else:
                for file in files:
                    self.results.put(FsItem(file, jobdata.andr_folder))

        super().worker(jobdata)