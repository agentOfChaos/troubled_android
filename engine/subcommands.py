import subprocess
import re
import os
import shutil
import time


adb = "/opt/android-sdk/platform-tools/adb"


class TransferDone:

    def __init__(self, andr, local):
        self.andr = andr
        self.local = local

class TransferFailed:

    def __init__(self, andr):
        self.andr = andr


def adbPullOneShot(deviceid, andr_file, destination, debug=False):
    """
    Tries to adb pull a mobile file onto the destination folder.
    In case of success, return a TrasnferDone object,
    in case of failure, return TrasnferFailed.

    Note: requires unbuffer to be installed
    """
    local_andr_name = andr_file
    if local_andr_name[0] == "/":
        local_andr_name = str(local_andr_name[1:])
    specific_dest = os.path.join(destination, local_andr_name)
    command = " ".join(["unbuffer", adb, "-s", deviceid, "pull", andr_file, specific_dest])
    raw = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE)
    if raw.decode("utf-8").lower().startswith("failed"):
        return TransferFailed(andr_file)
    return TransferDone(andr_file, specific_dest)


def device_list_files_parsed(device_dir, deviceid):

    """
    slightly modified from the source https://github.com/sole/aafm
    returns a list of dict, representing the listing of device_dir
    symbolic links are ignored
    """

    command = ['ls', '-l', '-a', "\"" + device_dir + "\""]
    pattern = re.compile(r"^(?P<permissions>[sdl\-][rwsxt\-]+) (?P<owner>\w+)\W+(?P<group>[\w_]+)\W*(?P<size>\d+)?\W+(?P<datetime>\d{4}-\d{2}-\d{2} \d{2}:\d{2}) (?P<name>.+)$")

    entries = []

    def execute(*args):
        cmd = [adb, "-s", deviceid, "shell"] + list(args)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        return filter(None, [line.decode("utf-8").rstrip('\r\n') for line in proc.stdout])

    for line in execute(*command):
        line = line.rstrip()
        match = pattern.match(line)

        if match:
            permissions = match.group('permissions')
            owner = match.group('owner')
            group = match.group('group')
            fsize = match.group('size')
            if fsize is None:
                fsize = 0
            filename = match.group('name')

            date_format = "%Y-%m-%d %H:%M"
            timestamp = time.mktime((time.strptime(match.group('datetime'), date_format)))

            is_directory = permissions.startswith('d')

            if permissions.startswith('l'):  # ignore symlinks
                continue

            entries.append({
                'filename': filename,
                'is_directory': is_directory,
                'size': fsize,
                'timestamp': timestamp,
                'permissions': permissions,
                'owner': owner,
                'group': group
            })

        else:
            print(line, "wasn't matched, please report to the developer!")

    for entry in entries:  # we need that for the directory-tracking mechanism used in troubledandroid.py
        entry["num_siblings"] = len(entries)

    return entries

def adbTestFile(candidate, test, deviceid):
    """
    perform a test on a mobile-file
    """
    command = [adb, "-s", deviceid, "shell", "test %s \"%s\"; echo $?" % (test, candidate)]
    raw = subprocess.check_output(command, shell=False)
    return raw

def adbIsDirectory(candidate, deviceid):
    """
    test -d a mobile file
    """
    raw = adbTestFile(candidate, "-d", deviceid)
    return int(raw.decode("utf-8")) == 0

def adbIsFile(candidate, deviceid):
    """
    test -f a mobile file
    """
    raw = adbTestFile(candidate, "-f", deviceid)
    return int(raw.decode("utf-8")) == 0

def clamScanOneShot(file):
    """
    runs an AV scan on a local file. Needs clamd to be running
    """
    command = "clamdscan --fdpass \"%s\"" % file
    rawoutput = subprocess.check_output(command, shell=True)
    lines = rawoutput.decode("utf-8").split("\n")
    result = lines[0]
    infected = result.endswith("FOUND")
    return result, infected

def cleanup(destination):
    """
    deletes quarantined files and directories
    """
    for innerfile in os.listdir(destination):
        name = os.path.join(destination, innerfile)
        if os.path.isdir(name):
            shutil.rmtree(name)
        else:
            os.remove(name)