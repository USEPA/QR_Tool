# -*- coding: windows-1252 -*-
"""
Name: QR Toolbox v1.3
Description: The QR Toolbox is a suite a tools for creating and reading QR codes. See the About screen for more
information
Author(s): Code integration, minor enhancements, & platform development - Timothy Boe boe.timothy@epa.gov;
    qrcode - Lincoln Loop info@lincolnloop.com; pyzbar - Lawrence Hudson quicklizard@googlemail.com;
    OpenCV code - Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/;
Contact: Timothy Boe boe.timothy@epa.gov
Requirements: Python 3.7+, pyzbar, imutils, opencv-python, qrcode[pil]
"""

# import the necessary packages
import pkg_resources  # this one and platform are built-in, as are some others (and so don't need to be checked)
import platform
import argparse
import csv
import datetime
import os
import os.path
import shutil
import time
from datetime import timedelta
from time import strftime
from tkinter import *
from tkinter import filedialog
import ctypes

"""
This function enables VT100 emulation, a Windows 10 setting that allows the color codes used above to actually
work and show the different colors. Otherwise, the colors would not work on the majority of terminals.
"""


def colors():
    kernel32 = ctypes.WinDLL('kernel32')
    hStdOut = kernel32.GetStdHandle(-11)
    mode = ctypes.c_ulong()
    kernel32.GetConsoleMode(hStdOut, ctypes.byref(mode))
    mode.value |= 4
    kernel32.SetConsoleMode(hStdOut, mode)


# colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[32m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


"""
This function checks the Python version and the Python module versions to ensure they are accurate.
If they are not exactly the versions the QR Tool was built for, a warning message will be printed.
(System can still run, but issues may arise because the packages/Python version code may have changed)
"""


def check_versions():
    pkg_array = ["pyzbar", "imutils", "qrcode", "Pillow", "opencv-python", "Office365-REST-Python-Client"]
    pkg_version = {"pyzbar": "0.1.8", "imutils": "0.5.3", "qrcode": "6.1", "Pillow": "7.0.0", "opencv-python": "4.2.0.32",
                   "Office365-REST-Python-Client": "2.1.7.post1"}
    pkgs_to_install = []
    i = 0
    while i < len(pkg_array):  # check which packages need to be installed or updated
        try:
            if pkg_resources.get_distribution(pkg_array[i]).version != pkg_version[pkg_array[i]]:
                pkgs_to_install.append(pkg_array[i])
        except:  # this catches errors thrown by a not-installed pkg resource, so we know to install it
            pkgs_to_install.append(pkg_array[i])
        i += 1

    if len(pkgs_to_install) > 0:
        print(f"{bcolors.WARNING}[WARNING] Some Python module versions are not accurate or installed, they will be installed "
              f"now.{bcolors.ENDC}\n")
    for pkg in pkgs_to_install:  # install the packages
        os.system(f"pip install {pkg}=={pkg_version[pkg]}")

    if os.environ.get('OPENCV_VIDEOIO_PRIORITY_MSMF') is None or os.environ.get('OPENCV_VIDEOIO_PRIORITY_MSMF') != '0':
        print(f"{bcolors.WARNING}[WARNING] OPENCV_VIDEOIO_PRIORITY_MSMF also not set. Setting now.{bcolors.ENDC}")
        os.system("setx OPENCV_VIDEOIO_PRIORITY_MSMF 0")

    if platform.python_version() != '3.7.4':
        print(f"{bcolors.WARNING}[WARNING] Your Python version is not 3.7.4. For the most stable build, install Python"
              f" version 3.7.4.{bcolors.ENDC}")


# call to function to turn on colors (enable VT100 emulation for Windows 10, works for Windows 10 only I believe)
colors()

# Check Python and module versions
check_versions()

# import csv packages
import cv2
import imutils
import numpy as np
import qrcode
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from imutils.video import VideoStream
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.file import File
from office365.sharepoint.file_creation_information import FileCreationInformation
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol

from Setup.settings import settings

# Sharepoint related variables
listTitle = "QR Timestamps"
qrfolder = "QRCodes"
bkcsvfolder = "HXWTEST"
remoteQRBatchFile = "System_Data/names-remote.csv"
localQRBatchFile = "names.csv"
relative_url = "/sites/Emergency%20Response/EOCIncident/EOC%20Documents/QRCodes/names.csv"
qr_storage_file = "System_Data/qr-data.txt"  # file that contains saved session information
backup_file = "System_Data/backup.txt"  # file that contains data that couldn't be uploaded, to later be uploaded

context_auth = AuthenticationContext(url=settings['url'])
context_auth.acquire_token_for_app(client_id=settings['client_id'], client_secret=settings['client_secret'])
ctx = ClientContext(settings['url'], context_auth)

# load variables
# set store folder default, assign system ID, and wait time
storagePath = "None"
checkStorage = False  # whether system should check if there is any backed up data or previous session data
system_id = os.environ['COMPUTERNAME']
t_value = timedelta(seconds=10)
cameraSource = "a"
storageChoice = ""

# Lists and Dictionaries used for special character handling and conversion
trouble_characters = ['\t', '\n', '\r']
bad_file_name_list = ['*', ':', '"', '<', '>', ',', '/', '|', '?', '\t', '\r', '\n', '\\']
special_characters = ["à", "á", "â", "ã", "ä", "å", "æ", "ç", "è", "é", "ê", "ë", "ì", "í", "î", "ï", "ð", "ñ", "ò",
                      "ó", "ô", "õ", "ö", "ø", "ù", "ú", "û", "ü", "ý", "þ", "ÿ", "À", "Á", "Â", "Ã", "Ä", "Å", "Æ",
                      "Ç", "È", "É", "Ê", "Ë", "Ì", "Í", "Î", "Ï", "Ð", "Ñ", "Ò", "Ó", "Ô", "Õ", "Ö", "Ø", "Ù", "Ú",
                      "Û", "Ü", "Ý", "Þ", "ß"]
code_characters = ["!@!a1!", "!@!a2!", "!@!a3!", "!@!a4!", "!@!a5!", "!@!a6!", "!@!a7!", "!@!c1!", "!@!e1!", "!@!e2!",
                   "!@!e3!", "!@!e4!", "!@!i1!", "!@!i2!", "!@!i3!", "!@!i4!", "!@!o1!", "!@!n1!", "!@!o2!", "!@!o3!",
                   "!@!o4!", "!@!o5!", "!@!o6!", "!@!o7!", "!@!u1!", "!@!u2!", "!@!u3!", "!@!u4!", "!@!y1!", "!@!b1!",
                   "!@!y2!", "!@!A1!", "!@!A2!", "!@!A3!", "!@!A4!", "!@!A5!", "!@!A6!", "!@!A7!", "!@!C1!", "!@!E1!",
                   "!@!E2!", "!@!E3!", "!@!E4!", "!@!I1!", "!@!I2!", "!@!I3!", "!@!I4!", "!@!O1!", "!@!N1!", "!@!O2!",
                   "!@!O3!", "!@!O4!", "!@!O5!", "!@!O6!", "!@!O7!", "!@!U1!", "!@!U2!", "!@!U3!", "!@!U4!", "!@!Y1!",
                   "!@!B1!", "!@!Y2!"]
char_dict_special_to_code = {"à": "!@!a1!", "á": "!@!a2!", "â": "!@!a3!", "ã": "!@!a4!", "ä": "!@!a5!", "å": "!@!a6!",
                             "æ": "!@!a7!", "ç": "!@!c1!", "è": "!@!e1!", "é": "!@!e1!", "ê": "!@!e3!", "ë": "!@!e4!",
                             "ì": "!@!i1!", "í": "!@!i2!", "î": "!@!i3!", "ï": "!@!i4!", "ð": "!@!o1!", "ñ": "!@!n1!",
                             "ò": "!@!o2!", "ó": "!@!o3!", "ô": "!@!o4!", "õ": "!@!o5!", "ö": "!@!o6!", "ø": "!@!o7!",
                             "ù": "!@!u1!", "ú": "!@!u2!", "û": "!@!u3!", "ü": "!@!u4!", "ý": "!@!y1!", "þ": "!@!b1!",
                             "ÿ": "!@!y2!", "À": "!@!A1!", "Á": "!@!A2!", "Â": "!@!A3!", "Ã": "!@!A4!", "Ä": "!@!A5!",
                             "Å": "!@!A6!", "Æ": "!@!A7!", "Ç": "!@!C1!", "È": "!@!E1!", "É": "!@!E2!", "Ê": "!@!E3!",
                             "Ë": "!@!E4!", "Ì": "!@!I1!", "Í": "!@!I2!", "Î": "!@!I3!", "Ï": "!@!I4!", "Ð": "!@!O1!",
                             "Ñ": "!@!N1!", "Ò": "!@!O2!", "Ó": "!@!O3!", "Ô": "!@!O4!", "Õ": "!@!O5!", "Ö": "!@!O6!",
                             "Ø": "!@!O7!", "Ù": "!@!U1!", "Ú": "!@!U2!", "Û": "!@!U3!", "Ü": "!@!U4!", "Ý": "!@!Y1!",
                             "Þ": "!@!B1!", "ß": "!@!Y2!"}
char_dict_code_to_special = {"!@!a1!": "à", "!@!a2!": "á", "!@!a3!": "â", "!@!a4!": "ã", "!@!a5!": "ä", "!@!a6!": "å",
                             "!@!a7!": "æ", "!@!c1!": "ç", "!@!e1!": "è", "!@!e2!": "é", "!@!e3!": "ê", "!@!e4!": "ë",
                             "!@!i1!": "ì", "!@!i2!": "í", "!@!i3!": "î", "!@!i4!": "ï", "!@!o1!": "ð", "!@!n1!": "ñ",
                             "!@!o2!": "ò", "!@!o3!": "ó", "!@!o4!": "ô", "!@!o5!": "õ", "!@!o6!": "ö", "!@!o7!": "ø",
                             "!@!u1!": "ù", "!@!u2!": "ú", "!@!u3!": "û", "!@!u4!": "ü", "!@!y1!": "ý", "!@!b1!": "þ",
                             "!@!y2!": "ÿ", "!@!A1!": "À", "!@!A2!": "Á", "!@!A3!": "Â", "!@!A4!": "Ã", "!@!A5!": "Ä",
                             "!@!A6!": "Å", "!@!A7!": "Æ", "!@!C1!": "Ç", "!@!E1!": "È", "!@!E2!": "É", "!@!E3!": "Ê",
                             "!@!E4!": "Ë", "!@!I1!": "Ì", "!@!I2!": "Í", "!@!I3!": "Î", "!@!I4!": "Ï", "!@!O1!": "Ð",
                             "!@!N1!": "Ñ", "!@!O2!": "Ò", "!@!O3!": "Ó", "!@!O4!": "Ô", "!@!O5!": "Õ", "!@!O6!": "Ö",
                             "!@!O7!": "Ø", "!@!U1!": "Ù", "!@!U2!": "Ú", "!@!U3!": "Û", "!@!U4!": "Ü", "!@!Y1!": "Ý",
                             "!@!B1!": "Þ", "!@!Y2!": "ß"}
char_dict_special_to_reg = {"à": "a", "á": "a", "â": "a", "ã": "a", "ä": "a", "å": "a", "æ": "a", "ç": "c", "è": "e",
                            "é": "e", "ê": "e", "ë": "e", "ì": "i", "í": "i", "î": "i", "ï": "i", "ð": "o", "ñ": "n",
                            "ò": "o", "ó": "o", "ô": "o", "õ": "o", "ö": "o", "ø": "o", "ù": "u", "ú": "u", "û": "u",
                            "ü": "u", "ý": "y", "þ": "b", "ÿ": "y", "À": "A", "Á": "A", "Â": "A", "Ã": "A", "Ä": "A",
                            "Å": "A", "Æ": "A", "Ç": "C", "È": "E", "É": "E", "Ê": "E", "Ë": "E", "Ì": "I", "Í": "I",
                            "Î": "I", "Ï": "I", "Ð": "O", "Ñ": "N", "Ò": "O", "Ó": "O", "Ô": "O", "Õ": "O", "Ö": "O",
                            "Ø": "O", "Ù": "U", "Ú": "U", "Û": "U", "Ü": "U", "Ý": "Y", "Þ": "B", "ß": "Y"}

# display landing screen
print()
print("     _/_/      _/_/_/        _/_/_/_/_/                    _/  _/                   ")
print("  _/    _/    _/    _/          _/      _/_/      _/_/    _/  _/_/_/      _/_/    _/    _/")
print(" _/  _/_/    _/_/_/            _/    _/    _/  _/    _/  _/  _/    _/  _/    _/    _/_/  ")
print("_/    _/    _/    _/          _/    _/    _/  _/    _/  _/  _/    _/  _/    _/  _/    _/  ")
print(" _/_/  _/  _/    _/          _/      _/_/      _/_/    _/  _/_/_/      _/_/    _/    _/ \n")
print("QR Toolbox v1.3 \n")
print("The QR Toolbox is a suite a tools for creating and reading QR codes.\n")
print("USEPA Homeland Security Research Program \n")
print("System ID: " + system_id + "\n")

"""
This function starts a VideoStream, and captures any QR Codes it sees (in a certain distance)
Those codes are decoded, and written to a local CSV file along with the Computer Name, date, time, and IN/OUT
    -If local was chosen, the CSV file is also saved at the location entered by the user
    -If online was chosen, the CSV file is also saved on the SharePoint site
"""


def video():
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", type=str, default="System_Data/barcodes.txt",
                    help="path to output CSV file containing barcodes")
    # ap.add_argument("-o1", "--output2", type=str, default=files_name,
    #        help="path to output CSV file containing barcodes")
    args = vars(ap.parse_args())
    # initialize time and date and make filename friendly
    time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    file_name = "QRT" + "-" + system_id + "_" + time_header + ".csv"

    # initialize the video stream and allow the camera sensor to warm up
    print(f"{bcolors.OKBLUE}[ALERT] starting video stream...{bcolors.ENDC}")
    print(f"{bcolors.OKBLUE}Press 'Q' to exit{bcolors.ENDC}")

    if cameraSource == 'a':  # start correct camera based on user choice at beginning
        vs = VideoStream(src=0).start()  # for integrated/built in webcam
    elif cameraSource == 'b':
        vs = VideoStream(src=1).start()  # for separate webcam (usually USB connected)
    elif cameraSource == 'c':
        vs = VideoStream(usePiCamera=True).start()  # for mobile solution like Raspberry Pi Camera
    else:
        print(f"{bcolors.FAIL}An error has occurred.{bcolors.ENDC}")
        return

    time.sleep(5.0)  # give camera time

    # open the output txt file for writing and initialize the set of barcodes found thus far
    global checkStorage
    contentStrings = ""  # used to contain data recorded from qr codes, to save in files
    if os.path.isfile(args["output"]) and checkStorage:  # check if user wanted to restart prev session
        if storageChoice.lower() == 'b':  # do this only if QR Toolbox is in online-mode
            # Write previous records back to contentStrings
            with open(args["output"], "r") as txt:
                print(f"{bcolors.OKBLUE}Restoring records...{bcolors.ENDC}")
                for line in txt:  # get each record from the file by line
                    if line == '\n': continue  # if line is newline only then skip it
                    line_array = line.split(",")
                    last_system_id = line_array[0]
                    date_time = datetime.datetime.strptime(line_array[1], "%Y-%m-%d %H:%M:%S.%f")  # get date from file
                    date_time_online = f"{date_time.month}/{date_time.day}/{date_time.year} " \
                                       f"{date_time.hour}:{date_time.minute}"  # store in this format: "%m/%d/%Y %H:%M"

                    barcodeDataSpecial = line_array[2]  # get the QR Code from the file
                    status = line_array[3]  # get the status from the file
                    if "OUT" in status:  # if the status is OUT, also get the QRCodes' duration from the file
                        duration = line_array[4][:len(line_array[4]) - 1:]  # also remove newline char
                    else:
                        status = status[:len(status) - 1]  # else just remove the newline char from the status

                    # Convert barcodeDataSpecial's special chars to regular chars
                    barcodeDataReg = convert(barcodeDataSpecial, special_characters, char_dict_special_to_reg)

                    if status == "IN":  # if status is IN, use 4 params
                        contentstr = "{},{},{},{}\n".format(last_system_id, date_time_online,
                                                            barcodeDataReg, status)  # for online CSV file
                        contentstr2 = '{},{},{},{}\n'.format(last_system_id, date_time,
                                                             barcodeDataSpecial, status)  # for list item
                    else:  # if status is OUT, use 5 params
                        contentstr = "{},{},{},{},{}\n".format(last_system_id, date_time_online, barcodeDataReg,
                                                            status, duration)  # for online CSV file
                        contentstr2 = '{},{},{},{},{}\n'.format(last_system_id, date_time,
                                                             barcodeDataSpecial, status, duration)  # for list item
                    create_list_item(ctx, contentstr2)
                    contentStrings = contentStrings + contentstr

        txt = open(args["output"], "a", encoding="utf-8")  # reopen txt file for appending (to continue records)
        print(f"{bcolors.OKBLUE}Previous records restored.{bcolors.ENDC}")
    else:
        txt = open(args["output"], "w", encoding="utf-8")  # else open new file/overwrite previous
        if checkStorage:
            print(f"{bcolors.WARNING}No previous records found. CSV file will not include past records.{bcolors.ENDC}")

    # time track variables. These are used to keep track of QR codes as they enter the screen
    found = []
    found_time = []
    found_status = []
    # ctxAuth = AuthenticationContext(url=settings['url'])

    # Check if there are any stored QR codes that were scanned in in an earlier instance of the system
    if checkStorage:
        if os.path.exists(qr_storage_file):
            with open(qr_storage_file, "r") as qr_data_file:
                for line in qr_data_file:  # if yes, read them in line by line
                    if line == '\n': continue
                    line_array = line.split(",")
                    found.append(line_array[0])  # append file data to the found arrays
                    found_time.append(datetime.datetime.strptime(line_array[1], "%Y-%m-%d %H:%M:%S.%f"))
                    found_status.append(line_array[2][:len(line_array[2]) - 1:])
                print(f"{bcolors.OKBLUE}Previous session restarted.{bcolors.ENDC}")
        else:
            print(f"{bcolors.WARNING}No previous session found [qr-data.txt not found].{bcolors.ENDC}")

    # loop over the frames from the video stream
    while True:
        # grab the frame from the threaded video stream and resize it to
        # have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        # find the barcodes in the frame and decode each of the barcodes
        barcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.QRCODE])
        timestr = strftime("%m/%d/%Y %H:%M")

        # loop over the detected barcodes
        for barcode in barcodes:
            # extract the bounding box location of the barcode and draw
            # the bounding box surrounding the barcode on the image
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

            # the barcode data is a bytes object so if we want to draw it
            # on our output image we need to convert it to a string first
            barcodeData = barcode.data.decode("utf-8")
            barcodeType = barcode.type

            # Convert barcodeData code chars back to special chars
            barcodeData = convert(barcodeData, code_characters, char_dict_code_to_special)

            # Draw the barcode data and barcode type on the image
            img = Image.new('RGB', (400, 15), color='white')
            img.putalpha(0)
            d = ImageDraw.Draw(img)
            textToPrint = convert(barcodeData, trouble_characters, None, True, True)  # replace \t,\n,\r with ' '
            try:
                d.text((0, 0), textToPrint + ' (' + barcodeType + ')', fill='blue')
            except UnicodeEncodeError:
                print(f"{bcolors.FAIL}[ERROR] Can't use QR Codes not generated by the system.{bcolors.ENDC}")
                continue

            pil_image = Image.fromarray(frame)
            pil_image.paste(img, box=(x, y - 15), mask=img)
            frame = np.array(pil_image)

            # if the barcode text is currently not in our CSV file, write
            # the timestamp + barcode to disk and update the set
            # of barcode data has never been seen, check the user in and record id, date, and time information
            if barcodeData not in found:
                datetime_scanned = datetime.datetime.now()
                txt.write("{},{},{},{}\n".format(system_id, datetime_scanned,
                                                 barcodeData, "IN"))
                txt.flush()

                found.append(barcodeData)
                found_time.append(datetime_scanned)
                found_status.append("IN")

                # Write updated found arrays to qr_data_file so that it is up to date with the latest scan ins
                with open(qr_storage_file, "w") as qr_data_file:
                    for i in range(len(found)):
                        code = found[i]
                        tyme = found_time[i]
                        status = found_status[i]
                        qr_data_file.write("{0},{1},{2}\n".format(code, tyme, status))

                checked_in = True
                if storageChoice.lower() == 'b':  # if user chose online/Sharepoint
                    # Convert barcodeData's special chars to regular chars
                    barcodeDataNew = convert(barcodeData, special_characters, char_dict_special_to_reg)

                    contentstr = "{},{},{},{}\n".format(system_id, timestr, barcodeDataNew, "IN")  # for online CSV file
                    contentstr2 = '{},{},{},{}\n'.format(system_id, timestr, barcodeData, "IN")  # for list item
                    checked_in = create_list_item(ctx, contentstr2)
                    contentStrings = contentStrings + contentstr

                sys.stdout.write('\a')  # beeping sound
                sys.stdout.flush()
                if checked_in:
                    print(barcodeData + " checking IN at " + str(datetime_scanned) + " at location: " + system_id)

            # if barcode information is found...
            elif barcodeData in found:
                # get current time and also total time passed since user checked in
                datetime_scanned = datetime.datetime.now()
                time_check = datetime_scanned - found_time[found.index(barcodeData)]
                status_check = found_status[found.index(barcodeData)]

                # if time exceeds wait period and user is checked in then check them out
                if time_check > t_value and status_check == "IN":
                    index_loc = found.index(barcodeData)
                    found_status[index_loc] = "OUT"
                    found_time[index_loc] = datetime_scanned
                    txt.write("{},{},{},{},{}\n".format(system_id, datetime_scanned,
                                                        barcodeData, "OUT", time_check))  # write to local CSV file
                    txt.flush()

                    checked_out = True
                    if storageChoice.lower() == 'b':  # if user chose online/Sharepoint version
                        barcodeDataNew = convert(barcodeData, special_characters, char_dict_special_to_reg)
                        # (above) convert qr code text special chars to reg chars
                        contentstr = "{},{},{},{},{}\n".format(system_id, timestr, barcodeDataNew, "OUT", time_check)
                        contentstr2 = "{},{},{},{},{}\n".format(system_id, timestr, barcodeData, "OUT",
                                                                time_check)

                        checked_out = create_list_item(ctx, contentstr2)
                        contentStrings = contentStrings + contentstr

                    sys.stdout.write('\a')  # When this letter is sent to terminal, a beep sound is emitted but no text
                    sys.stdout.flush()
                    if checked_out:
                        print(barcodeData + " checking OUT at " + str(datetime_scanned)
                              + " at location: " + system_id + " for duration of " + str(time_check))
                # if found and check-in time is less than the specified wait time then wait
                elif time_check < t_value and status_check == "OUT":
                    pass
                # if found and time check exceeds specified wait time and user is checked out, delete ID and affiliated
                # data from the list. This resets everything for said user and allows the user to check back in at a
                # later time.
                elif time_check > t_value and status_check == "OUT":
                    index_loc = found.index(barcodeData)
                    del found_status[index_loc]
                    del found_time[index_loc]
                    del found[index_loc]

                # Write updated found arrays to qr_data_file so that it is up to date with the latest scan ins
                with open(qr_storage_file, "w") as qr_data_file:
                    for i in range(len(found)):
                        code = found[i]
                        tyme = found_time[i]
                        status = found_status[i]
                        qr_data_file.write("{0},{1},{2}\n".format(code, tyme, status))
            else:
                print(f"{bcolors.FAIL}[Error] Barcode data issue in video() function.{bcolors.ENDC}")

        # show the output frame
        cv2.imshow("QR Toolbox", frame)
        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q") or key == ord("Q"):
            break

    # close the output CSV file do a bit of cleanup
    print(f"{bcolors.OKBLUE}[ALERT] Cleaning up... \n{bcolors.ENDC}")
    txt.close()

    if os.path.exists(qr_storage_file) and os.stat(qr_storage_file).st_size == 0:
        os.remove(qr_storage_file)  # if the file is empty, delete it
    checkStorage = False  # Reset the global variable that tells code to check the qr_storage_file

    # This part is necessary to show special characters properly on any of the local CSVs
    if os.path.exists(args["output"]):
        barcodesTxt = open(args["output"], 'r', encoding="utf-8")
        newCSV = open(file_name, 'w', encoding="ANSI")

        data = barcodesTxt.read()
        newCSV.write(data)

        barcodesTxt.close()
        newCSV.close()
    else:
        data = f"{bcolors.FAIL}[ERROR] barcodes.txt not found as expected.{bcolors.ENDC}"
        print(data)

    if storageChoice == 'a':  # if local was chosen, also store barcodes file at the location given
        if os.path.exists(storagePath):  # check if file path exists
            with open(os.path.join(storagePath, file_name), "w", encoding="ANSI") as csv2:
                csv2.write(data)
        else:
            print(f"{bcolors.WARNING}[ALERT]: Storage folder not established or is unavailable. "
                  f"Files will only be saved to the working directory\n{bcolors.ENDC}")
    elif storageChoice.lower() == 'b':  # if online was chosen, upload data to SharePoint as well
        success = connect(ctx, 'upload', contentStrings, file_name, bkcsvfolder)
        if success:
            upload_backup(ctx)

    if os.path.exists(args["output"]) and os.stat(args["output"]).st_size == 0:  # delete barcodes.txt if empty
        os.remove(args["output"])  # not removed until the end in case something goes wrong above and it's needed
    vs.stop()
    vs.stream.release()
    cv2.destroyAllWindows()


"""
This function converts the passed data based on the other parameters, and returns the converted data
These conversions fall under 4 cases:
    1. Data has Special Characters that need to be converted to Code Characters (used in the video() function)
    2. Data has Special Characters that need to be converted to Regular Characters (only if uploading to SharePoint)
    3. Data has Code Characters that need to be converted to Special Characters (used for printing the data)
    4. Data has Special Characters that need to be converted to '-' so that it can be used as a file name
@param data_to_convert the data that is to be converted
@param character_list the list of characters that if found are to be converted
@param conversion_dict the dictionary of characters used for conversion
@param is_for_file_name if True, the code executes differently by replacing with '-' and printing text. Default is False

Note: For the logic to work when replacing \t,\n, \r with a space, both is_for_file_name and is_for_trouble must be 
True so that the logic results in the replacement of those chars with space rather than using a dictionary char

@return data_to_convert the changed or unchanged data
"""


def convert(data_to_convert, character_list, conversion_dict, is_for_file_name=False, is_for_trouble=False):
    old_data = data_to_convert

    for char in character_list:
        if char in data_to_convert:
            data_to_convert = data_to_convert.replace(char, conversion_dict[char]) if not \
                is_for_file_name else data_to_convert.replace(char, "-") if not is_for_trouble \
                else data_to_convert.replace(char, " ")
    if old_data != data_to_convert and is_for_file_name and is_for_trouble is not True:
        print(f"{bcolors.FAIL}Error saving file with name {old_data}, saved as {data_to_convert} instead.{bcolors.ENDC}")
    return data_to_convert


"""
This function first checks if passed data has a Special Character, then asks the user if they want to convert it.
    -If no, the user is returned to the main menu
    -If yes, the prior operation is continued and the data is converted as needed
@param label the text to check to see if it has Special Characters

@return True if it does and user answers Yes, or if no Special Character is found. False if no.
"""


def ask_special_char_conversion(label):
    for special_char in special_characters:
        if special_char in label:
            # Has special char, so ask if they want to convert or return to main menu
            while True:
                print("\nYour text has a special character(s), do you want to convert it to a regular character(s)?")
                print("A. Yes (Only for the SharePoint version)")
                print("B. No (This one will be skipped)")
                answer = input("Enter your selection: ")
                answer = answer.lower()
                if answer == 'a':
                    return True
                elif answer == 'b':
                    return False
                else:
                    print("Invalid choice \n")
    return True


"""
This function handles HTTP requests, and also handles errors that occur during those attempted connections
    - If there is an error, then system tries again after 10sec, then 30sec, and then stores the data
    that was to be uploaded in a file (backup.txt), to be attempted to upload again later on
@param context the URL/HTTP request
@param connection_type the type of connection/request to make (depends on the method caller)
@param content the content of the upload
@param file_name the name of the file to be uploaded
@param location the location that the file should be uploaded to
@param duplicate whether the file/data being uploaded already exists in the backup.txt or not

@return True if connection is successful, False if not
    - Returns binary file in the case of the 'qr_batch' connection_type
"""


def connect(context, connection_type, content=None, file_name=None, location=None, duplicate=False):
    i = 0
    while i < 3:
        # noinspection PyBroadException
        try:
            return_val = True
            if connection_type == 'upload':  # if a file needs to be uploaded
                upload_file(ctx, content, file_name, location)
            elif connection_type == 'execute_query':  # if list item needs to be created and added
                context.execute_query()
            elif connection_type == 'qr_batch':  # if a file from the SharePoint needs to be retrieved (names.csv)
                return_val = File.open_binary(context, relative_url)
            else:
                print(f"{bcolors.WARNING}Invalid connection type.{bcolors.ENDC}")  # connection_type not one of above
                return_val = False
            if i > 0:
                print(f"{bcolors.OKGREEN}Connection successful.{bcolors.ENDC}")
            return return_val
        except:
            # e = sys.exc_info()[0] used for error checking
            if i == 0:
                print(f"{bcolors.FAIL}Connection lost. Trying again in 10 seconds.{bcolors.ENDC}")
                time.sleep(10)
            elif i == 1:
                print(f"{bcolors.FAIL}Reconnect failed. Trying again in 30 seconds.{bcolors.ENDC}")
                time.sleep(30)
            elif i > 1 and not duplicate and connection_type != 'qr_batch':  # if failed thrice, write to backup.txt
                print(f"{bcolors.FAIL}Reconnect failed again.{bcolors.OKBLUE} Data will be stored locally and "
                      f"uploaded at the next upload point, or if triggered from the menu.{bcolors.ENDC}")
                if os.path.exists(backup_file) and connection_type == 'upload':
                    with open(backup_file, "a") as backup:
                        backup.write(f"{content}\n@@@@@\n{file_name}\n@@@@@\n{location}\n----------\n")
                elif connection_type == 'upload':
                    with open(backup_file, "w") as backup:
                        backup.write(f"{content}\n@@@@@\n{file_name}\n@@@@@\n{location}\n----------\n")
                elif connection_type == 'execute_query':
                    with open(backup_file, "a") as backup:
                        backup.write(f"$$$$$\n{content}\n----------\n")
                return False
            elif i > 1 and connection_type == 'qr_batch':
                print(f"{bcolors.FAIL}Reconnect failed again.{bcolors.OKBLUE} Try again when you have "
                      f"internet connection.{bcolors.ENDC}")
                return False
        i += 1


"""
This function uploads the data that was stored/backed up in the backup.txt file

@param context the URL/HTTP request information for uploading
@param from_menu True if this method was triggered/called from the main menu, False otherwise

@return True if re-upload was successful, False otherwise (or if there was no data to upload)
"""


def upload_backup(context, from_menu=False):
    if os.path.exists(backup_file):  # check if file exists, if not then return
        with open(backup_file, "r") as backup:
            print("Uploading backed up data...")
            content = ""  # the content of the file that will be uploaded
            file_name = ""  # the file name of the file to upload
            location = ""  # the location to upload the file to
            flag = 0  # this tells program whether we are looking at content, filename, or location information
            for line in backup:  # for each line, take the appropriate action according to what is read in
                if line == '\n': continue
                if line == '@@@@@\n': flag += 1; continue
                if line == '$$$$$\n': flag = 3; continue
                if line == '----------\n':
                    if flag == 3:  # means it was a list item
                        successful = create_list_item(context, content, True)
                    else:  # means it was a file to be uploaded
                        successful = connect(context, 'upload', content, file_name, location, True)
                    if not successful:
                        print(f"{bcolors.FAIL}Upload of backed up data failed.{bcolors.OKBLUE} Program will try again"
                              f" at next upload, or you can trigger upload manually from the menu.{bcolors.ENDC}")
                        return False
                    flag = 0
                    content = ""
                    file_name = ""
                    location = ""
                    continue
                if flag == 0 or flag == 3:
                    content = content + line
                elif flag == 1:
                    file_name = line.rstrip('\n')
                elif flag == 2:
                    location = line.rstrip('\n')
            print(f"{bcolors.OKGREEN}Upload complete!{bcolors.ENDC}")
        os.remove(backup_file)  # file removed if upload is successful
    elif from_menu:
        print(f"{bcolors.OKBLUE}No backed-up data to upload.{bcolors.ENDC}")


"""
This function Creates a list item, used with the SharePoint site and the Office365-REST-Python-Client
@param context the context of the site that is being communicated with/uploaded to
@param content the content to add as a list item
"""


def create_list_item(context, content, duplicate=False):
    print("Creating list item example...")
    list_object = context.web.lists.get_by_title(listTitle)
    values = content.split(",")
    sid = values[0]
    tstr = values[1]
    barstr = values[2]
    status = values[3]

    item_properties = {'__metadata': {'type': 'SP.Data.QR_x0020_TimestampsListItem'}, 'Title': barstr,
                       'QR_x0020_Terminal': sid, 'Time_x0020_Stamp': tstr, 'Info': status}
    item = list_object.add_item(item_properties)
    succeed = connect(context, 'execute_query', content, duplicate=duplicate)
    if succeed:
        print("List item '{0}' has been created.".format(item.properties["Title"]))
    else:
        print(f"{bcolors.WARNING}List item '{item.properties['Title']}' has NOT been created.{bcolors.ENDC}")
    return succeed


"""
This function uploads the passed data to the SharePoint site in the specified sub folder with the given file name
@param context the context of the site that is being communicated with/uploaded to (URL, authorization, etc.)
@param file_content the content of the file to be uploaded
@param filename the name of the file
@param sub_folder the folder to put the file in

@return returns the reference to the file that was uploaded
"""


def upload_file(context, file_content, filename, sub_folder):
    list_title = "EOC Documents"
    library = context.web.lists.get_by_title(list_title)

    file_context = library.context
    info = FileCreationInformation()
    info.content = file_content
    info.url = filename
    info.overwrite = True

    # upload file to sub folder 'eoctest'
    target_file = library.rootFolder.folders.get_by_url(sub_folder).files.add(info)
    file_context.execute_query()

    return target_file


"""
This function creates QR codes in batches from a CSV file (defined in the global variables)
    -The function always checks and performs the QR code creation in its root folder first, and the generated codes
    are then stored in that same folder.
    -If the local choice was chosen, the codes are also stored in the location entered by the user
    -If the online/SharePoint choice was chosen, the function then also reads a CSV file (defined in global variables) 
    on the SharePoint site and generates QR Codes from that, which are stored in the same location as that CSV file
"""


def qr_batch():
    print("")
    print("The batch QR code function is used to automatically create multiple QR codes by referencing a .csv file."
          "\n-If QR Toolbox is in local mode, the csv file must be stored in the root/origin folder, named 'names.csv'."
          "\n The Tool will then automatically create QR codes for each line in the csv, and save each QR Code image to"
          "\n the Tools root/origin folder."
          "\n-If QR Toolbox is in online mode, the csv file must be stored on the SharePoint site where QR codes are"
          "\n located, and must be named 'names.csv'. The Tool will then do the same as above, but will also store each"
          "\n QR code image to the SharePoint site."
          "\n-'names.csv' may consist of two columns 'first' & 'second'. The 'first' and 'second' columns could be "
          "\n populated with participant's first and last names, or other information.")
    input("\nPress Enter to Continue \n")
    # this code creates a batch of QR codes from a csv file stored in the local directory
    # QR code image size and input filename can be modified below

    success = True
    # This one creates the batch of QR codes in the same folder as this file
    if storageChoice == 'a':
        with open(localQRBatchFile) as csvfile:
            reader = csv.reader(csvfile)

            for row in reader:
                labeldata = row[0] if len(row) == 1 else row[0] + " " + row[1] if row[1] != '' else row[0]

                # Check for special char, ask if user wants to convert
                if storageChoice == 'b' and not ask_special_char_conversion(labeldata):
                    continue  # if user doesn't want to convert (returns False), then this text/row is skipped

                # convert special char to code character
                codeLabelData = convert(labeldata, special_characters, char_dict_special_to_code)

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4)

                qr.add_data(codeLabelData)
                qr.make(fit=True)
                print("Creating QR code: " + labeldata)

                # draw QR image

                img = qr.make_image()
                qrFile = labeldata + ".jpg"
                qrFile = convert(qrFile, bad_file_name_list, None, True)  # remove special chars that can't be in filename
                img.save(qrFile)

                # open QR image and add qr data as name
                img = Image.open(qrFile)
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype("arial", 24)
                color = 0
                draw.text((37, 10), labeldata, font=font, fill=color)
                img.save(qrFile)
                if storageChoice == 'a':
                    try:
                        img.save(storagePath + "/" + qrFile)
                    except:
                        success = False
    elif storageChoice == 'b':  # For storing the new QR Codes online, if that was selected
        resp = connect(ctx, 'qr_batch')  # runs the retrieval of the names.csv file from SharePoint through connect()

        if type(resp) == bool:  # if a boolean value is returned, then the retrieval failed
            return False
        elif resp.status_code == 404:
            print(f"{bcolors.FAIL}The batch file '" + relative_url + "' doesn't exist. "
                f"Please copy 'names.csv' to the sharepoint site.{bcolors.ENDC}")
            return False

        with open(remoteQRBatchFile, 'wb') as output_file:
            output_file.write(resp.content)

        with open(remoteQRBatchFile) as csvfile:
            reader = csv.reader(csvfile)

            for row in reader:  # get each row from the CSV file
                labeldata = row[0] if len(row) == 1 else row[0] + " " + row[1] if row[1] != '' else row[0]
                # above: gets data from 1 row or 2 rows depending on what is in each
                if not ask_special_char_conversion(labeldata):  # Check if text has a special char, ask to convert
                    continue  # if False, skip this text (user doesn't want to convert special char)

                # convert special char to code character
                codeLabelData = convert(labeldata, special_characters, char_dict_special_to_code)

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4)

                qr.add_data(codeLabelData)
                qr.make(fit=True)
                print("Creating QR code: " + labeldata)

                # draw QR image

                img = qr.make_image()
                qrfile = labeldata + ".jpg"
                qrfile = convert(qrfile, bad_file_name_list, None, True)  # convert chars that can't be in filename
                img.save(qrfile)

                # open QR image and add qr data as name

                img = Image.open(qrfile)
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype("arial", 18)
                color = 0
                draw.text((37, 10), labeldata, font=font, fill=color)
                img.save(qrfile)

                with open(qrfile, 'rb') as content_file:  # upload file
                    file_content = content_file.read()
                success = connect(ctx, 'upload', file_content, qrfile, qrfolder)

        os.remove(remoteQRBatchFile)

    if success:
        print(f"{bcolors.OKGREEN}Success!{bcolors.ENDC}\n")
        if storageChoice == 'b':  # if the other upload was successful, also try to upload the backed-up data
            upload_backup(ctx)
    else:
        print(f"{bcolors.FAIL}Some or no files were saved in {storagePath}, only in root folder.{bcolors.ENDC}" if
              storageChoice == 'a' else f"{bcolors.WARNING}Successful locally, not online.{bcolors.ENDC}")


"""
This function creates a single QR code based on the text inserted by the user, which is then stored in the root folder.
    - If user chose the local option, the QR code is also stored in the location entered by the user
    - If user chose the online SharePoint option, the QR code is stored on the SharePoint site
"""


def qr_single():
    print("\nEnter text to generate a single QR code and press Enter. The resulting QR image will be saved in the "
          "tool's origin folder. \n")
    custom_labeldata = input("QR Text: ")

    if storageChoice == 'b' and not ask_special_char_conversion(custom_labeldata):  # Check if text has a special char
        return  # if False, return to main menu (user doesn't want to convert special char)

    copy_labeldata = custom_labeldata
    print("Creating QR code...")

    # convert special char to code character
    copy_labeldata = convert(copy_labeldata, special_characters, char_dict_special_to_code)

    # this code creates a single QR code based on information entered into the command line.
    # The resulting QR code is stored in the current (the programs') directory
    # QR code image size and input filename can be modified below
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4)

    qr.add_data(copy_labeldata)
    qr.make(fit=True)

    # draw label

    img = qr.make_image()
    fileName = custom_labeldata + ".jpg"
    fileName = convert(fileName, bad_file_name_list, None, True)  # convert chars that can't be in a file name
    img.save(fileName)

    # Open QR image and add QR data as name

    img = Image.open(fileName)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial", 24)
    color = 0
    draw.text((37, 10), custom_labeldata, font=font, fill=color)
    img.save(fileName)

    succeed = True
    # Store QR code locally, if that was chosen
    if storageChoice == 'a':
        try:
            img.save(storagePath + "/" + fileName)
        except:
            succeed = False
    elif storageChoice == 'b':  # Store QR code online, if chosen
        # upload file
        with open(fileName, 'rb') as content_file:
            file_content = content_file.read()
        succeed = connect(ctx, 'upload', file_content, fileName, qrfolder)

    if succeed:
        print(f"{bcolors.OKGREEN}Success!{bcolors.ENDC}\n")
        if storageChoice == 'b':
            upload_backup(ctx)  # if the other upload was successful, also try to upload the backed-up data
    else:
        print(f"{bcolors.FAIL}File not saved in {storagePath}, only in root folder.{bcolors.ENDC}" if
              storageChoice == 'a' else f"{bcolors.WARNING}Successful locally, not online.{bcolors.ENDC}")


"""
This function provides more information on the purpose and development of this software
"""


def about():
    # displays the about screen
    print("\nQR Toolbox v1.3 \n")
    print("About: The QR Toolbox is a suite a tools for creating and reading QR codes. The toolbox is platform "
          "agnostic, lightweight, open source, and written in pure Python. This toolbox may be used to track resources,"
          " serve as a check-in capability for personnel, or customized to meet other operational needs. \n")
    print("Version: 1.3 \n")
    print("Credits: The QR Toolbox consists of a number of python packages, namely: \n qrcode - "
          "Lincoln Loop info@lincolnloop.com; \n pyzbar - Lawrence Hudson quicklizard@googlemail.com; \n OpenCV code - "
          "Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/; \n Code integration, minor enhancements, & "
          "platform development - Timothy Boe boe.timothy@epa.gov \n")
    print("Contact: Timothy Boe: boe.timothy@epa.gov; or Paul Lemieux: lemieux.paul@epa.gov; USEPA Homeland Security "
          "Research Program \n")


"""
This function allows the user to select a shared folder. If user escapes, a share folder is not created
    - Note: the Tkinter code can be finicky when displayed in IDE i.e., the file window will not show when operated in
    IDE while the root.withdraw command is turned on. Commenting out the root.withdraw command will fix, but root
    window remains; destroy() can be used to remove this. May need to search for a better solution in the future
"""


def store():
    print("")
    root = Tk()
    root.title('Storage Directory')
    root.withdraw()
    store_path = filedialog.askdirectory(title='Select a Network Storage Directory')
    if os.path.exists(store_path):
        print(f"{bcolors.OKGREEN}Storage directory established: " + store_path + f"{bcolors.ENDC}")
    else:
        print(f"{bcolors.WARNING}Storage directory NOT established{bcolors.ENDC}")
    print("")
    return store_path


"""
This function consolidates QR csv results into a single file. This function looks for files with QRT in the first part 
of their name. If true, all csvs within the shared folder directory that also fit this condition. A number of error
checks are built in to prevent bad things from happening
"""


def cons():
    time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    cons_filename = os.path.join(storagePath, 'Consolidated_Record_' + time_header + '.csv')
    if os.path.exists(storagePath):
        QRT_files = [fn for fn in os.listdir(storagePath) if fn.startswith('QRT')]

        if not QRT_files:
            print("No entries to combine. Check the shared directory and try again")
        else:
            try:
                with open(cons_filename, 'wb') as outfile:
                    for i, fname in enumerate(QRT_files):
                        fname = os.path.join(storagePath, fname)
                        with open(fname, 'rb') as infile:
                            shutil.copyfileobj(infile, outfile)
                            print(fname + " has been imported.")
                print(
                    f"{bcolors.OKGREEN}\nConsolidated file created in the specified shared drive under the filename " +
                    cons_filename + f"{bcolors.ENDC}\n")
            except:
                print(f"{bcolors.WARNING}\n[WARNING] Either the system was unable to write the consolidated file to the"
                      "specified shared directory or the file " + cons_filename + " is currently in use or unavailable."
                      f"The consolidated record may be incomplete.{bcolors.ENDC} \n")
    else:
        print(f"{bcolors.WARNING}\nA shared folder has not been established. Specify a shared folder using the "
              f"Establish Share Folder option before continuing \n{bcolors.ENDC}")
        pass


"""
This function asks the user whether they want to restart the previous session
    - This means that the system will read and add-in/append at the beginning the data in the qr-data.txt,
    as well as the data in the barcodes.txt, so that previous checkin/checkout data is maintained/carried over,
    and so that the CSV file to be created will have the lines/data from the last session
    - System knows to do this because this function sets the checkStorage global variable to True
"""


def ask_to_restart_session():
    while True:
        print("\nDo you want to start a new session or restart a previous one?")
        print("A. New session (all previous data will be deleted)")
        print("B. Restart previous session")
        sessionChoice = input("Enter your selection: ").lower()
        if sessionChoice == 'a':
            break
        elif sessionChoice == 'b':
            global checkStorage
            checkStorage = True
            print(f"{bcolors.OKBLUE}Previous session will be restarted, if one exists.{bcolors.ENDC}")
            break
        else:
            print("Invalid choice \n")


"""
This function asks the user what camera will be used to read QR Codes
Only 3 options
    1. A - integrated/built-in webcam (the default)
    2. B - USB or connected webcam
    3. C - PiCamera (from Raspberry Pi)
"""


def choose_camera_source():
    while True:
        print("Which camera do you want to use?")
        print("A. Integrated webcam")
        print("B. Separate webcam")
        print("C. PiCamera")
        cameraChoice = input("Enter your selection: ").lower()
        if cameraChoice != 'a' and cameraChoice != 'b' and cameraChoice != 'c':
            print("Invalid choice \n")
        else:
            print("\n")
            global cameraSource
            cameraSource = cameraChoice
            break


# Determine where to store data that is captured/recorded
def choose_storage_location():
    while True:
        print("Do you want data stored on Sharepoint (online) or locally?")
        print("Note: Files are also saved in the QR-Toolbox root folder regardless.")
        print("A. Local (Specify a location on the computer)")
        print("B. Sharepoint (Online)")
        global storageChoice
        storageChoice = input("Enter your selection: ").lower()
        if storageChoice == 'a':
            global storagePath
            storagePath = store()
            break
        elif storageChoice == 'b':
            break
        else:
            print("Invalid choice \n")


# MAIN PART OF PROGRAM STARTS HERE
choose_storage_location()  # ask user to choose the storage location
# main menu
while True:
    print("\n==============|  MENU  |===============")
    print("A. QR Reader")
    print("B. QR Creator - Batch")
    print("C. QR Creator - Single")
    print("D. Consolidate Records" if storageChoice == 'a' else "D. Upload Backed-Up Data")
    print("E. Change Camera Source")
    print("F. Change Storage (Local/Online)")
    print("G. About/Credits")
    print("H. Exit\n")
    choice = input("Enter your selection: ").lower()
    if choice == 'a':
        ask_to_restart_session()
        video()
    elif choice == 'b':
        qr_batch()
    elif choice == 'c':
        qr_single()
    elif choice == 'd':
        cons() if storageChoice == 'a' else upload_backup(ctx, True)
    elif choice == 'e':
        choose_camera_source()
    elif choice == 'f':
        choose_storage_location()
    elif choice == 'g':
        about()
    elif choice == 'h':
        break
    else:
        print("Invalid choice \n")
