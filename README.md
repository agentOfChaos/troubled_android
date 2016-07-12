# troubled_android
Experimental android malware scanner based on adb and clamAV

## Abstract
The key concept here is that android apps are isolated from each other; this is a security feature, but it also makes it very hard for an antivirus app to be actually effective.

This program attempts to circumvent this by using adb to pull the files onto your desktop, and then scan them with your pc antivirus.

I use clamAV for this job, since it's open-source and it has signatures for android malware.

I know, a concerned android user could just disable "unknown source" and enable "Verify apps", but where's the fun in that? :)

## Requirements

Programs:

    adb
    clamav
    unbuffer

Environment:
* adb daemon must be running, and have the permissions to access the files to be scanned.  
Ideally, a rooted device and `adb root` whould be make it possible to scan anything
* clamd daemon must be running
* mobile device plugged into the pc

## Running
You can find the id of your device by executing:

    adb devices

Then simply running

    ./troubledandroid.py <device id>

will have the program scan the content of the /data directory on your mobile.  
To specify a different folder/file:

    ./troubledandroid.py -a <directory> <device id>

## Help

    ./troubledandroid.py -h

for more info on additional command parameters

## Testing

I did say "experimental" up there, didn't I? :)

I tested it on an Android 5.1.1 device (with Cyanogenmod and Busybox); the dektop was an arch linux machine.

As of now, only the linux operating system is supported.
