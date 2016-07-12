import argparse
import constants


def parsecli():
    parser = argparse.ArgumentParser(description="Android malware scanner, based on adb and clamv")
    parser.add_argument('--android-path', '-a', metavar='path',
                        help='Path of the android folder/file to scan. You may specify multiple ones, in a'
                             'comma-separated list', type=str, default=constants.scanlocations)
    parser.add_argument('--keep-files', '-k', help='Enables fullscreen mode', action="store_true")
    parser.add_argument('--debug', '-d', help='Enables debug messages', action="store_true")
    parser.add_argument('id', help='Android device id (run adb devices to discover it)', type=str)
    parser.add_argument('--report', metavar='filename', help='Location to write the scan report to', type=str,
                        default="report.txt")
    return parser.parse_args()
