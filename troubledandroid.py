#!/usr/bin/python

import datetime
from threading import Thread
import os

from subcommands import cleanup, adbIsDirectory, adbIsFile
from scanjobhandler import ScanJobHandler
from lsjobhandler import LsJobHandler, ListJob, FsItem
from scanfeedjobhandler import ScanFeedJob, ScanFeedJobHandler
from utils import Unclog
import cliparse

"""
                                         ListJob
                   +------------------------------------------------+
                   |                                                | dir?
                   |                                                |
                   |                                        +-------+------+
                   |   +-+-+--------------+-+-+             |              |
        ListJob    V   | | |              | | |   FsItem    |              |  file?
+--------------------->+ | | LsJobHandler | | +------------>+  filerouter  +------------------+
                       | | |              | | |             |              |                  |
                       +-+-+--------------+-+-+             |              |     ScanFeedJob  |
                            adb shell ls                    +--------------+                  |
                                                                                              |
                                                                                              |
                                                                                              |
                +-+-+----------------+-+-+                +-+-+--------------------+-+-+      |
  ScanCompleted | | |                | | |  TransferDone  | | |                    | | |      |
<---------------+ | | ScanJobHandler | | +<---------------+ | | ScanFeedJobHandler | | +<-----+
                | | |                | | |                | | |                    | | |
                +-+-+----------------+-+-+                +-+-+--------------------+-+-+
                         clamdscan                                    adb pull
"""


dirs_to_visit = {}


def filerouter(lister, scanfeeder, scanner, cli, localpath):
    global dirs_to_visit
    for fs in lister.genResults():
        if not isinstance(fs, Unclog):
            assert isinstance(fs, FsItem)
            #  this part is to keep track of the visited directories, so that we can actually decide
            #  when to stop the program
            if fs.parent in list(dirs_to_visit.keys()):
                old_sibl_num = dirs_to_visit[fs.parent]
                if fs.folderWasEmpty:
                    del dirs_to_visit[fs.parent]
                else:
                    if old_sibl_num == -1:
                        dirs_to_visit[fs.parent] = fs.file_entry["num_siblings"] - 1
                    else:
                        dirs_to_visit[fs.parent] = old_sibl_num - 1

                    if dirs_to_visit[fs.parent] == 0:
                        del dirs_to_visit[fs.parent]
            # actual jobs routing done here
            if not fs.folderWasEmpty:
                if fs.is_dir:
                    dirs_to_visit[fs.fullpath] = -1
                    lister.addJob(fs.listjob)
                else:
                    scanfeeder.addJob(ScanFeedJob((cli.id, fs.fullpath, localpath, cli.debug)))

        if len(dirs_to_visit) == 0:
            lister.finished()
        if cli.debug:
            print("DEBUG (filerouter): %d folders left to visit" % len(dirs_to_visit))
    print("Finished directory-tree traversal")
    scanfeeder.finished(callback=lambda: scanner.finished())


def logToFile(file, result):
    file.write("%s\n" % (result.resultstring))


def makeQuarantineFolder(folder):
    if not os.path.isdir(folder):
        os.makedirs(folder)


if __name__ == "__main__":
    cli = cliparse.parsecli()
    totalinfect = 0
    quarantine_folder = "quarantine/"
    makeQuarantineFolder(quarantine_folder)
    andr_files = cli.android_path.split(",")
    started = datetime.datetime.now()

    # careful: too many scanfeed jobs can cause adb to crash
    scanner = ScanJobHandler(keepfiles=cli.keep_files, debug=cli.debug)
    scanfeeder = ScanFeedJobHandler(scanner, maxjobs=4, debug=cli.debug)
    lister = LsJobHandler(cli.id, maxjobs=4, debug=True)
    router_thread = Thread(target=filerouter, args=(lister, scanfeeder, scanner, cli, quarantine_folder))

    router_thread.start()
    for file in andr_files:
        if adbIsDirectory(file, cli.id):
            dirs_to_visit[file] = -1
            lister.addJob(ListJob(file))
        elif adbIsFile(file, cli.id):
            scanfeeder.addJob(ScanFeedJob((cli.id, file, quarantine_folder, cli.debug)))

    #  if we only scanned single file, the main for loop inside filerouter was never used, so we have to awake it so that it can terminate
    lister.addJob(Unclog())

    #  loop to fetch the scan results as they are generated
    repfile = open(cli.report, "w")
    for r in scanner.genResults():
        if r.infected: totalinfect += 1
        print(r.resultstring)
        logToFile(repfile, r)

    cleanup(quarantine_folder)
    finished = datetime.datetime.now()

    finalmsg = "Total infected files: %d\nTotal time: %s" % (totalinfect, str(finished - started))
    print(finalmsg)
    repfile.write(finalmsg + "\n")
    repfile.close()