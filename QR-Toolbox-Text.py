import argparse
import csv
import sys
import datetime
import os
import os.path
import shutil
import time
import socket
import select
import urllib3
import RPi.GPIO as GPIO
from omxplayer.player import OMXPlayer, logger
from gpiozero import LED
from datetime import timedelta
from tkinter import *
from tkinter import filedialog

from arcgis.gis import GIS
from arcgis import features
from arcgis.geometry import Point

# Import csv packages
import cv2
import imutils
import numpy as np
from PIL import Image
from PIL import ImageDraw
from imutils.video import VideoStream
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol

import threading

from Setup.settings import settings

"""
    Known issues:
        disconnect upload from scanning, upload every 1-5 minutes + camera close
        redo documentation
"""

logger.propagate = False

url = settings['url']
gis_query = settings['query']
latitude = settings['latitude']
longitude = settings['longitude']
localQRBatchFile = settings['localQRBatchFile']

# System variables
qr_storage_file = "System_Data/qr-data.txt"  # file that contains saved session information
backup_file = "System_Data/backup.txt"  # file that contains data that couldn't be uploaded, to later be uploaded
archive_folder = "Archive"
pass_sound = "Library/sounds/passed.mp3"
fail_sound = "Library/sounds/failed.mp3"
alert_sound = "Library/sounds/alarm.mp3"
wait_sound = "Library/sounds/waiting.mp3"

# load variables
# set store folder default, assign system ID, and wait time
storagePath = ""  # the path to the local storage directory if chosen
checkStorage = False  # whether system should check if there is any backed up data or previous session data
uploadBackup = False
user_chose_storage = False  # tracks whether user chose a storage method or not
display_video = False  # whether the video feed should be displayed or not
system_id = socket.gethostname()  # this is used when checking qr codes in or out
t_value = timedelta(seconds=10)  # time between scans for the same qr code
upload_value = timedelta(minutes=5)
cameraSource = "Integrated"  # the camera source, defaults to integrated (so source 0)
storageChoice = ""  # users choice of local ('a') or online ('b') mode
vs = None  # global video stream variable, to ensure only 1 instance of it exists at a time
video_on = False
play_sound = False
play_light = False
red: LED = None
yellow: LED = None
green: LED = None
player = None

GPIO.setmode(GPIO.BCM)

# Lists and Dictionaries used for special character handling and conversion
trouble_characters = ['\t', '\n', '\r']  # characters that cause issues
# can't be used in a filename
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

"""
This function converts the passed data based on the other parameters, and returns the converted data
These conversions fall under 3 cases:
    1. Data has Special Characters that need to be converted to Code Characters (used in the video() function)
    2. Data has Code Characters that need to be converted to Special Characters (used for printing the data)
    3. Data has Special Characters that need to be converted to '-' so that it can be used as a file name
@param data_to_convert the data that is to be converted
@param character_list the list of characters that if found are to be converted
@param conversion_dict the dictionary of characters used for conversion
@param is_for_file_name if True, the code executes differently by replacing with '-' and printing text. Default is False

Note: For the logic to work when replacing \t,\n, \r with a space, both is_for_file_name and is_for_trouble must be 
True so that the logic results in the replacement of those chars with space rather than using a dictionary char

@return data_to_convert the changed or unchanged data
"""


def convert(data_to_convert, character_list, conversion_dict, is_for_file_name=False,
            is_for_trouble=False):
    old_data = data_to_convert  # saving original data before variable is modified

    for char in character_list:  # iterate through chars in character_list and convert if necessary
        if char in data_to_convert:
            data_to_convert = data_to_convert.replace(char, conversion_dict[
                char]) if not is_for_file_name else data_to_convert.replace(char, "-") \
                if not is_for_trouble else data_to_convert.replace(char,
                                                                   " ")
            # data is converted to the appropriate character(s) depending on if the conversion is for a bad file name,
            # or to remove trouble characters, or simply to convert special chars to code chars
    if old_data != data_to_convert and is_for_file_name and is_for_trouble is not True:
        # if the data was converted and it was for a bad file name and not only for a trouble character,
        # print this to user
        print("Error saving file with name %s, saved as %s instead." % (old_data, data_to_convert))
    return data_to_convert


"""
This function handles HTTP requests, and also handles errors that occur during those attempted connections
    - If there is an error, then system tries again after 10sec, then 30sec, and then stores the data
    that was to be uploaded in a file (backup.txt), to be attempted to upload again later on
@param connection_type the type of connection/request to make (depends on the method caller)
@param sys_id the id of the system
@param date_str the date of the data
@param time_str the time of the data
@param barcode the data itself
@param status the status of the data ('IN' or 'OUT')
@param time_elapsed the time between when data was checked 'IN' and checked 'OUT', only applies when status == 'OUT'
@param duplicate whether the file/data being uploaded already exists in the backup.txt or not

@return True if connection is successful, False if not
"""


# noinspection PyBroadException
def connect(main_screen, connection_type, sys_id, date_str, time_str, barcode, status, time_elapsed=None,
            duplicate=False):
    i = 0
    content = None
    while i < 3:
        try:
            return_val = True
            if connection_type == 'upload':  # if a record needs to be uploaded to arcgis
                if status == "IN":
                    content = f"{sys_id},{date_str},{time_str},{barcode},{status},NONE"
                if status == "OUT":
                    content = f"{sys_id},{date_str},{time_str},{barcode},{status},{time_elapsed}"
                main_screen.update_arcgis(sys_id, date_str, time_str, barcode, status, time_elapsed)
            else:  # if for some reason connection type is not one of the above
                print("Invalid connection type.")
                return_val = False
            if i > 0:  # if a connection retry occurred and was successful
                print("Connection successful.")
            return return_val  # so that calling method can use the results accordingly
        except:
            global yellow
            e = sys.exc_info()[0]  # used for error checking
            print(e)
            if i == 0:  # if first try failed
                print("Connection lost. Trying again in 10 seconds.")
                if play_sound:
                    threading.Thread(target=playsound, args=[wait_sound], daemon=True).start()
                if play_light:
                    threading.Thread(target=blink, args=[10, 2, 2], daemon=True).start()
                    # blink yellow
                time.sleep(10)
            elif i == 1:  # if second try failed
                print("Reconnect failed. Trying again in 30 seconds.")
                if play_sound:
                    threading.Thread(target=playsound, args=[wait_sound], daemon=True).start()
                if play_light:
                    threading.Thread(target=blink, args=[10, 2, 3], daemon=True).start()
                    # blink yellow
                time.sleep(30)
            elif i > 1 and not duplicate:  # if failed thrice, write to backup.txt
                print("Reconnect failed again. Data will be stored locally and uploaded at the next upload point, "
                      "or if triggered from the menu.")
                if connection_type == 'upload':
                    with open(backup_file, "a") as backup:  # write the data to the backup.txt file
                        backup.write(f"{content}\n")
                return False  # return a connection failure
        i += 1


"""
This function uploads the data that was stored/backed up in the backup.txt file

@param main_screen_widget a reference to the main screen so that info can be printed to it
@param from_menu True if this method was triggered/called from the main menu, False otherwise

@return True if re-upload was successful, False otherwise (or if there was no data to upload)
"""


def upload_backup(main_screen, from_menu=False):
    if os.path.exists(backup_file):  # check if file exists, if not then return
        with open(backup_file, "r") as backup:
            if from_menu:
                print("Uploading backed up data...")
            time_elapsed = None  # assume it's IN status so no elapsed time
            for line in backup:  # for each line, take the appropriate action according to what is read in
                if line == '\n' or line == "":
                    continue
                content = (line.rstrip('\n')).split(
                    ',')  # if not empty or newline, then strip newline chars and split line
                if content[5] != "NONE":  # if time_elapsed is not none then get time_elapsed
                    time_elapsed = content[5]
                successful = connect(main_screen, 'upload', content[0], content[1], content[2], content[3],
                                     content[4], time_elapsed=time_elapsed, duplicate=True)  # submit data for upload
                if not successful:  # if upload failed print info to user
                    print("Upload of backed up data failed. Program will try again at next upload, or you can trigger "
                          "upload manually from the menu.")
                    return False
            if from_menu:
                print("Upload complete!")
        os.remove(backup_file)  # file removed if upload is successful
    elif from_menu:
        print("No backed-up data to upload.")


#
# """
# This function creates QR codes in batches from a CSV file (defined in the global variables)
#     -The function always checks and performs the QR code creation in its root folder first, and the generated codes
#     are then stored in the Archive folder.
#     -A storage directory must have been chosen, the codes are then also stored in that location
#     -No difference between online and local mode for this
#
# @param main_screen_widget a reference to the main screen so that info can be printed to it
# """
#
#
# def qr_batch():
#     print("\nThe batch QR code function is used to quickly create multiple QR codes by referencing a .csv file."
#         "\n-There is no difference between online and local mode for this function, it only works as described below."
#           "\n-The CSV file must be stored in the root folder of the program (where it was installed), and named "
#           "'names.csv'.\n    * The file name can be changed, but this change must also be reflected in the "
#         "Setup/settings.py file for the \n       variable 'localQRBatchFile'.\n    * The Tool will then automatically"
#           " create QR codes for each line in the csv, and save each QR Code image to the\n       Tools root folder "
#           "(this folder is usually called 'QR-Toolbox', and should be found in\n       "
#          "C:/Users/<user>/AppData/Local/Programs), where <user> refers to your user name on your computer.\n    * \n-"
#           "'names.csv' may consist of two columns 'first' & 'second'. The 'first' and 'second' columns could be\n    "
#         "populated with participant's first and last names, or other information, and will be joined together with a "
#           "space in\n    between.\n")
#
#     # this code creates a batch of QR codes from a csv file stored in the local directory
#     # QR code image size and input filename can be modified below
#
#     success = True
#     # This one creates the batch of QR codes in the same folder as this file
#     with open(localQRBatchFile) as csvfile:
#         reader = csv.reader(csvfile)  # reader for the csv file
#
#         for row in reader:
#             labeldata = row[0] if len(row) == 1 else row[0] + " " + row[1] if row[1] != '' else row[
#                 0]  # combine the data in the first 2 cols depending on which is empty and which isn't
#
#             # convert special char to code character
#             code_label_data = convert(labeldata, special_characters, char_dict_special_to_code)
#
#             qr = qrcode.QRCode(  # this and below are to create the QR code
#                 version=1,
#                 error_correction=qrcode.constants.ERROR_CORRECT_L,
#                 box_size=10,
#                 border=4)
#
#             qr.add_data(code_label_data)
#             qr.make(fit=True)
#             print("Creating QR code: " + labeldata)
#
#             # make QR image
#             img = qr.make_image()
#             qr_file = labeldata + ".jpg"
#             qr_file = convert(qr_file, bad_file_name_list, None,
#                               True)  # remove special chars that can't be in filename
#             img.save(archive_folder + "/" + qr_file)
#
#             # open QR image and add qr data as name
#             img = Image.open(archive_folder + "/" + qr_file)
#             draw = ImageDraw.Draw(img)
#             font = ImageFont.truetype("arial.ttf", 24)
#             color = 0
#             draw.text((37, 10), labeldata, font=font, fill=color)
#             img.save(archive_folder + "/" + qr_file)
#             try:
#                 img.save(storagePath + "/" + qr_file)
#             except:
#                 success = False  # if any failures occur, set this to success so user knows a failure occurred
#                 print("\nQR Code %s not created.\n" % labeldata)
#
#     if success:
#         print("\nSuccess!\n")
#     else:
#         print("Some or no files were saved in %s, only in Archive folder." % storagePath)
#
#
# """
# This function creates a single QR code based on the text inserted by the user, which is then stored in the Archive
# folder.
#     - The QR code is also stored in the location entered by the user, regardless of the mode they are in
#
# @param main_screen_widget reference to main screen to print info
# @param text the text from the TextInput field
# """
#
#
# def qr_single(text):
#     if text is None or text == "":  # if no text is entered into the text box
#         print("Skipped because no text was entered.")
#         return
#
#     text_copy = text  # this line is probably not needed
#     print("Creating QR code: " + text)
#
#     # convert special char to code character
#     text_copy = convert(text_copy, special_characters, char_dict_special_to_code)
#
#     # this code creates a single QR code based on information entered into the command line.
#     # The resulting QR code is stored in the current (the programs') directory
#     # QR code image size and input filename can be modified below
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=4)
#
#     qr.add_data(text_copy)
#     qr.make(fit=True)
#
#     # draw label
#     img = qr.make_image()
#     file_name = text + ".jpg"
#     file_name = convert(file_name, bad_file_name_list, None,
#                         True)  # convert chars that can't be in a file name
#     img.save(archive_folder + "/" + file_name)
#
#     # Open QR image and add QR data as name
#     img = Image.open(archive_folder + "/" + file_name)
#     draw = ImageDraw.Draw(img)
#     font = ImageFont.truetype("arial.ttf", 24)
#     color = 0
#     draw.text((37, 10), text, font=font, fill=color)
#     img.save(archive_folder + "/" + file_name)
#
#     succeed = True
#     # Store QR code locally
#     try:  # try to save, if it fails then let user know
#         img.save(storagePath + "/" + file_name)
#     except:
#         succeed = False
#         print("\nQR Code %s not created.\n" % text)
#
#     if succeed:
#         print("Success!")
#     else:
#         print("File not saved in %s, only in Archive folder." % storagePath)


"""
This function consolidates QR csv results into a single file. This function looks for files with QRT in the first part 
of their name. If true, all csvs within the storage directory that also fit this condition. A number of error
checks are built in to prevent bad things from happening
"""


def cons():
    time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))  # get current date and time
    cons_filename = os.path.join(storagePath, 'Consolidated_Record_' + time_header + '.csv')
    if os.path.exists(storagePath):  # if storage directory has been set
        qrt_files = [fn for fn in os.listdir(storagePath) if
                     fn.startswith('QRT-R-') and fn.endswith('.csv') and fn.__contains__("_")]
        # above: get all csv files that start with QRT-R- and end with .csv and have  a '_' in them
        if not qrt_files:  # if its empty then print this
            print("No entries to combine. Check the storage directory and try again")
        else:  # if not empty then go through them and copy them into one file
            try:
                with open(cons_filename, 'wb') as outfile:
                    for i, fname in enumerate(qrt_files):
                        fname = os.path.join(storagePath, fname)
                        with open(fname, 'rb') as infile:
                            shutil.copyfileobj(infile, outfile)  # copy data from each file to the consolidated file
                            print("%s has been imported." % fname)
                print("\nConsolidated file created in the specified storage directory under the "
                      "filename %s\n" % cons_filename)
            except:
                print("[WARNING] Either the system was unable to write the consolidated file to the "
                      "specified storage directory or the file %s is currently in use or unavailable. "
                      "The consolidated record may be incomplete.\n" % cons_filename)
    else:  # if no storage location chosen yet
        print("A storage location has not been established. Specify a storage folder using the "
              "'Choose Storage Location' option before continuing\n")


"""
This function allows the user to select a storage directory. If user escapes, a storage directory is not created
    - Note: the Tkinter code can be finicky when displayed in IDE i.e., the file window will not show when operated in
    IDE while the root.withdraw command is turned on. Commenting out the root.withdraw command will fix, but root
    window remains; destroy() can be used to remove this. May need to search for a better solution in the future
"""


def store():
    global user_chose_storage
    try:
        root = Tk()
        root.title('Storage Directory')
        root.withdraw()
        store_path = filedialog.askdirectory(title='Select a Storage Directory')  # ask user to choose a directory
        if os.path.exists(store_path):  # if they chose one
            print("Storage directory established: %s" % store_path)
            user_chose_storage = True
        else:
            print("Storage directory NOT established")
            user_chose_storage = False
    except:
        store_path = os.getcwd()
        print("Unable to open window, Storage directory established: %s" % store_path)
        user_chose_storage = True
    return store_path


""" This function provides more information on the purpose and development of this software """


def about():
    # displays the about screen
    print("\n\nQR Toolbox v1.5\n"
          "About: The QR Toolbox is a suite a tools for creating and reading QR codes. \n"
          "The toolbox is lightweight, open source, and written in Python and Kivy.\n"
          "This toolbox may be used to track resources, serve as a check-in capability for personnel, \n"
          "or customized to meet other operational needs. \n\n"
          "Credits: The QR Toolbox consists of a number of python packages, namely: "
          "\n qrcode - Lincoln Loop info@lincolnloop.com; "
          "\n pyzbar - Lawrence Hudson quicklizard@googlemail.com; "
          "\n OpenCV code - Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/; "
          "\n Code integration, minor enhancements, & platform development - Timothy Boe boe.timothy@epa.gov, "
          "\nMuhammad Karimi karimi.muhammad@epa.gov, and Jordan Deagan jordan.deagan@epa.gov"
          "\nContact: Timothy Boe: boe.timothy@epa.gov; or Paul Lemieux: lemieux.paul@epa.gov; USEPA Homeland Security "
          "Research Program\n")
    time.sleep(5.0)


""" 
This class represents the displayed when you select "Choose Camera Source" from the Setup menu, 
and is text with 3 buttons 
"""


def set_camera(camera_choice):
    global cameraSource
    cameraSource = camera_choice  # set camera source based on user choice
    print("Camera source set to '%s'." % camera_choice)


""" 
This class represents the Exit alert box that pops up when you click the 'Exit' button, confirming that you want 
to exit 
"""


def confirm_exit():
    print("\nAre you sure you want to quit?\n(unsaved data, such as from an open QR Reader, will be lost)")
    option = input("(Y/N): ")
    if option.lower() == 'y' or option.lower() == 'yes':
        GPIO.cleanup()
        sys.exit()
    return True


#
# """ This function checks if storage path is set, calls it if not, otherwise/and then calls the qr_batch function """
#
#
# def setup_qr_single():
#     global storagePath
#     if storagePath == "":
#         storagePath = store()  # set storage path if it hasn't been set already
#
#     if storagePath != "":  # then ask user for the text for the new qr code
#         print("Enter text to generate a single QR Code and click OK. The resulting image will be saved in the "
#               "tool's origin folder, and selected storage location.")
#         text = input("QR Text: ")
#         qr_single(text)
#
#
# """
#     This function creates a popup widget to prompt the user for text for the QR code, can be multi-line
#     It also first checks if storage path is set, and if not then it triggers the user to select that
# """
#
#
# def setup_qr_batch():
#     global storagePath
#     if storagePath == "":
#         storagePath = store()
#     if storagePath != "":
#         qr_batch()

""" 
This class represents the information shown when the online button is pressed and a username/password is requested, 
has text, an input box, and 2 buttons 
"""


def sign_in(main_screen):
    global user_chose_storage

    global url, gis_query
    try:
        main_screen.gis = GIS(url, client_id='vpeanPqMcHdq7G6z')  # Get ArcGIS access and save it

        # check that query works and there's a layer to get
        search_results = main_screen.gis.content.search(query=gis_query,
                                                        max_items=15)
        # print(search_results)
        data = search_results[0]  # Get the layer we'll be using, so user can see it

        print("Storage location set to online (ArcGIS).\nLayer: %s" % data.title)
        # provides more info on the exact layer chosen
        user_chose_storage = True
    except Exception as e:  # if error in trying to access ArcGIS or run the query
        # e = sys.exc_info()[0]  # used for error checking
        print("Error: %s" % e)
        user_chose_storage = False
    except:  # in case the above except clause doesn't catch everything
        print("An error has occurred.")
        user_chose_storage = False


""" 
This function Checks to see if there is any previous sessions and session data, and if there is it will pull that 
back in @param check is to see if we should checkStorage or not
"""


def set_check_storage(main_screen, check):
    global video_on
    if check:  # if user wants to check for previous session/session data
        global checkStorage
        checkStorage = True
        print("Previous session will be restarted, if one exists.")
    video_on = True
    threading.Thread(target=main_screen.video, daemon=True).start()  # starts video method on its own thread


def blink(led, length, count):
    GPIO.output(10, False)
    GPIO.output(led, True)
    time.sleep(length)
    GPIO.output(led, False)
    for i in range(count-1):
        time.sleep(1)
        GPIO.output(led, True)
        time.sleep(length)
        GPIO.output(led, False)
    GPIO.output(10, True)


def set_media():
    global play_sound, play_light, red, yellow, green, player, pass_sound
    print("Which media devices are connected to the Pi?\n1) Audio speaker\n2) Light display\n3) Both\n4) Neither")
    choice = input("Choice: ")
    if choice == '1':
        play_sound = True
        play_light = False
    elif choice == '2':
        play_sound = False
        play_light = True
    elif choice == '3':
        play_sound = True
        play_light = True
    elif choice == '4':
        play_sound = False
        play_light = False
    else:
        print("Selection entered was not of an available option")
    if play_light:
        # red = LED(9)
        # yellow = LED(10)
        # green = LED(11)
        GPIO.setup(9, GPIO.OUT)
        GPIO.setup(10, GPIO.OUT)
        GPIO.setup(11, GPIO.OUT)
    if play_sound:
        try:
            player = OMXPlayer(pass_sound, args="-o local")
        except SystemError as e:
            print("Error: %s" % e)


def playsound(path):
    global player
    try:
        player.load(path)
    except SystemError as e:
        print("Error: %s" % e)



""" This function is triggered when a user goes over the time limit, and it triggers an alert popup and sound """


def timer_alert(user):
    global play_sound
    print("ALERT: %s has exceeded the time limit." % user)
    if play_sound:
        threading.Thread(target=playsound, args=[alert_sound], daemon=True).start()

    return True


"""
This class is the main class for the GUI, it is the main screen within which all other screens/widgets/buttons are 
located
"""


class MainScreen:
    sys_id = socket.gethostname()  # this may be a repeat
    gis = None  # contains the access to arcgis online to upload data
    timer = None  # used to time how long users are checked in and alert any who exceed this amount of elapsed time

    """
    This function starts a VideoStream, and captures any QR Codes it sees (in a certain distance)
    Those codes are decoded, and written to a local CSV file along with the Computer Name, date, time, and IN/OUT
    The local CSV file is always saved in the Archive folder by default
        -If local was chosen, the CSV file is also saved at the storage location entered by the user
        -If online was chosen, the records (not the CSV) are also saved on the ArcGIS site
    """

    def video(self):
        global user_chose_storage, vs, video_on, display_video, uploadBackup, checkStorage, t_value, upload_value, \
            backup_file

        if user_chose_storage:

            print("[ALERT] Starting video stream...")
            print("To exit, enter \'q\'")
            if not display_video:
                print("[Alert] Not displaying camera feed, this can be changed in settings")

            # construct the argument parser and parse the arguments
            ap = argparse.ArgumentParser()
            ap.add_argument("-o", "--output", type=str, default="System_Data/barcodes.txt",
                            help="path to output CSV file containing barcodes")
            args = vars(ap.parse_args())
            # initialize time and date and make filename friendly
            time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            file_name = "QRT-R-" + system_id + "_" + time_header + ".csv"
            txt = None

            # initialize the video stream and allow the camera sensor to warm up
            try:
                if cameraSource == 'Integrated':  # start correct camera based on user choice at beginning
                    vs = VideoStream(src=0).start()  # for integrated/built in webcam
                elif cameraSource == 'Separate':
                    vs = VideoStream(src=1, ).start()  # for separate webcam (usually USB connected)
                elif cameraSource == 'PiCamera':
                    vs = VideoStream(usePiCamera=True).start()  # for mobile solution like Raspberry Pi Camera
                else:
                    print("An error has occurred.")
                    return
            except:  # if an error occurs in creating video stream, print to user and return
                print("An error occurred starting the QR Reader. Check your cameras and try again.")
                vs = None
                return

            time.sleep(2.0)  # give camera time

            # open the output txt file for writing and initialize the set of barcodes found thus far

            if os.path.isfile(args["output"]) and checkStorage:  # check if user wanted to restart prev session
                if storageChoice.lower() == 'b' and uploadBackup:  # do this only if QR Toolbox is in online-mode
                    # Write previous records back to contentStrings
                    with open(args["output"], "r", encoding='utf-8') as txt:
                        print("Restoring records (online mode)...")
                        for line in txt:  # get each record from the file by line
                            if line == '\n':
                                continue  # if line is newline only then skip it
                            line_array = line.split(",")
                            last_system_id = line_array[0]
                            # get date from file
                            file_date = datetime.datetime.strptime(line_array[1], "%m/%d/%Y").date()
                            file_time = datetime.datetime.strptime(line_array[2], "%H:%M:%S.%f").time()
                            file_time_online = file_time

                            barcode_data_special = line_array[3]  # get the QR Code from the file
                            status = line_array[4]  # get the status from the file
                            if "OUT" in status:  # if the status is OUT, also get the QRCodes' duration from the file
                                duration = line_array[5][:len(line_array[5]) - 1:]  # also remove newline char
                            else:
                                status = status[:len(status) - 1]  # else just remove the newline char from the status

                            if status == "IN":  # if status is IN, no duration
                                success = connect(self, "upload", last_system_id, file_date, file_time_online,
                                                  barcode_data_special, status)
                            else:  # if status is OUT, add duration of qr code being checked in
                                success = connect(self, "upload", last_system_id, file_date, file_time_online,
                                                  barcode_data_special, status, duration)
                            if not success:
                                break  # if upload failed, break loop and let user know it failed
                elif storageChoice.lower() == 'b' and not uploadBackup:
                    print("Restoring records (online mode)...")
                    print(open(args['output'], 'r', encoding='utf-8').read())
                if storageChoice.lower() == 'a':
                    # if in local mode, just open barcodes.txt for appending to restorerecords
                    print("Restoring records (local mode)...")
                    print(open(args['output'], 'r', encoding='utf-8').read())
                try:
                    # reopen txt file for appending (to continue records)
                    txt = open(args["output"], "a", encoding="utf-8")
                    success = True
                except:
                    success = False
                if success:
                    print("Previous records restored.")
                else:
                    print("Previous records NOT restored.")
            else:  # if no previous records and user wanted to restart/restore them then print that none exist
                txt = open(args["output"], "w", encoding="utf-8")  # else open new file/overwrite previous
                if checkStorage:
                    print("No previous records found. CSV file will not include past records.")

            # time track variables. These are used to keep track of QR codes as they enter the screen
            found = []
            found_time = []
            found_status = []
            thread_started = []  # tracks if a thread for the item in the given position has been started already, bool

            # Check if there are any stored QR codes that were scanned-in in an earlier instance of the system
            if checkStorage:
                if os.path.exists(qr_storage_file) and os.stat(qr_storage_file).st_size != 0:
                    with open(qr_storage_file, "r") as qr_data_file:
                        print("Restarting session...")
                        for line in qr_data_file:  # if yes, read them in line by line
                            if line == '\n':
                                continue
                            line_array = line.split(",")
                            found.append(line_array[0])  # append file data to the found arrays
                            found_time.append(datetime.datetime.strptime(line_array[1], "%Y-%m-%d %H:%M:%S.%f"))
                            found_status.append(line_array[2][:len(line_array[2]) - 1:])
                            thread_started.append(False)
                        print("Previous session restarted.")
                elif not os.path.exists(qr_storage_file) or os.stat(qr_storage_file).st_size == 0:
                    print("No previous session found [qr-data.txt not found or is empty].")
            if play_light:
                GPIO.output(10, True)
            # loop over the frames from the video stream
            upload_time = datetime.datetime.now()
            while True:
                # grab the frame from the threaded video stream and resize it to have a maximum width of 400 pixels
                # frame = None
                try:  # if the video stream stops working or is changed
                    frame = vs.read()
                    frame = imutils.resize(frame, width=400)
                except:  # then catch and break the loop, and do clean up
                    print("Video stream lost. Check your cameras. Proceeding to clean up.")
                    break

                # find the barcodes in the frame and decode each of the barcodes
                barcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.QRCODE])
                timestr = datetime.datetime.now()
                datestr = timestr.strftime("%m/%d/%Y")
                timestr = timestr.strftime("%H:%M:%S.%f")
                if storageChoice.lower() == 'b':
                    time_since = timestr - upload_time

                    if time_since > upload_value:
                        upload_time = timestr
                        threading.Thread(target=upload_backup, args=[self, False], daemon=True).start()

                # loop over the detected barcodes
                for barcode in barcodes:

                    # extract the bounding box location of the barcode and draw the bounding box surrounding the
                    # barcode on the image
                    (x, y, w, h) = barcode.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                    # the barcode data is a bytes object so if we want to draw it on our output image we need to
                    # convert it to a string first
                    barcode_data = barcode.data.decode("utf-8")
                    barcode_type = barcode.type

                    # Convert barcodeData code chars back to special chars
                    barcode_data = convert(barcode_data, code_characters, char_dict_code_to_special)

                    # Draw the barcode data and barcode type on the image
                    img = Image.new('RGB', (400, 15), color='white')
                    img.putalpha(0)
                    d = ImageDraw.Draw(img)
                    text_to_print = convert(barcode_data, trouble_characters, None, True,
                                            True)  # replace \t,\n,\r with ' '
                    try:  # if code was not generated by qr tool or doesn't meet its conditions, let user know
                        d.text((0, 0), text_to_print + ' (' + barcode_type + ')', fill='blue')
                    except UnicodeEncodeError:
                        print("[ERROR] Can't use QR Codes not generated by the system.")
                        continue

                    pil_image = Image.fromarray(frame)  # convert frame to pil image format, then to numpy array
                    pil_image.paste(img, box=(x, y - 15), mask=img)
                    frame = np.array(pil_image)

                    # if the barcode text is currently not in our CSV file, write the timestamp + barcode to disk and
                    # update the set of barcode data has never been seen, check the user in and record id, date,
                    # and time information
                    if barcode_data not in found:
                        datetime_scanned = datetime.datetime.now()  # this one appended to found_time arr
                        date_scanned = datetime.datetime.now().strftime("%m/%d/%Y")  # this one prints to csv
                        time_scanned = datetime.datetime.now().strftime("%H:%M:%S.%f")  # this one prints to csv

                        try:
                            txt.write("{},{},{},{},{}\n".format(system_id, date_scanned, time_scanned,
                                                                barcode_data, "IN"))  # write scanned data to the text file
                            txt.flush()

                            # add the scanned data to the found arrays so status/times can be managed
                            found.append(barcode_data)
                            found_time.append(datetime_scanned)
                            found_status.append("IN")
                            thread_started.append(False)
                            # added so that it corresponds to the actual data in the found arrays

                            # Write updated found arrays to qr_data_file so that it is up to date with the latest scan
                            # ins
                            with open(qr_storage_file, "w") as qr_data_file:
                                for i in range(len(found)):
                                    code = found[i]
                                    tyme = found_time[i]
                                    status = found_status[i]
                                    qr_data_file.write("{0},{1},{2}\n".format(code, tyme, status))

                            if storageChoice.lower() == 'b':  # if user chose online/arcgis
                                # success = connect(self, "upload", system_id, datestr, timestr, barcode_data, "IN")
                                content = f"{system_id},{datestr},{timestr},{barcode_data},IN,NONE"
                                with open(backup_file, "a") as backup:  # write the data to the backup.txt file
                                    backup.write(f"{content}\n")
                            success = True
                        except:
                            success = False

                        if success:
                            print("%s checking IN at %s at location: %s" % (barcode_data, datetime_scanned, system_id))
                            if play_light:
                                threading.Thread(target=blink, args=[11, 3, 1], daemon=True).start()
                                # blink green
                            if play_sound:
                                threading.Thread(target=playsound, args=[pass_sound], daemon=True).start()
                                # makes a beeping sound on scan in
                        elif not success:
                            print("%s NOT checked IN" % barcode_data)
                            if play_light:
                                threading.Thread(target=blink, args=[9, 3, 1], daemon=True).start()
                                # blink red
                            if play_sound:
                                threading.Thread(target=playsound, args=[fail_sound], daemon=True).start()
                                # makes a slightly deeper beeping sound on failed scan in

                    # if barcode information is found...
                    elif barcode_data in found:
                        # get current time and also total time passed since user checked in
                        datetime_scanned = datetime.datetime.now()  # this one appended to found_time arr
                        date_scanned = datetime.datetime.now().strftime("%m/%d/%Y")  # this one prints to csv
                        time_scanned = datetime.datetime.now().strftime("%H:%M:%S.%f")  # this one prints to csv
                        time_check = datetime_scanned - found_time[found.index(barcode_data)]
                        status_check = found_status[found.index(barcode_data)]

                        # if time exceeds wait period and user is checked in then check them out
                        if time_check > t_value and status_check == "IN":
                            index_loc = found.index(barcode_data)
                            found_status[index_loc] = "OUT"
                            found_time[index_loc] = datetime_scanned
                            # write to local txt file
                            try:
                                txt.write("{},{},{},{},{},{}\n".format(system_id, date_scanned, time_scanned,
                                                                       barcode_data, "OUT", time_check))

                                txt.flush()

                                if storageChoice.lower() == 'b':  # if user chose online/arcgis version
                                    # success = connect(self, "upload", system_id, datestr, timestr, barcode_data,
                                    #                   "OUT", time_check)
                                    content = f"{system_id},{datestr},{timestr},{barcode_data},OUT,{time_check}"
                                    with open(backup_file, "a") as backup:  # write the data to the backup.txt file
                                        backup.write(f"{content}\n")
                                success = True
                            except:
                                success = False

                            if success:
                                print("%s checking OUT at %s at location: %s for duration of %s" %
                                      (barcode_data, datetime_scanned, system_id, time_check))
                                if play_light:
                                    threading.Thread(target=blink, args=[11, 3, 1], daemon=True).start()
                                    # blink green
                                if play_sound:
                                    threading.Thread(target=playsound, args=[pass_sound], daemon=True).start()
                                    # makes a beeping sound on scan
                            elif not success:
                                print("%s NOT checked OUT" % barcode_data)
                                if play_light:
                                    threading.Thread(target=blink, args=[9, 3, 1], daemon=True).start()
                                    # blink red
                                if play_sound:
                                    threading.Thread(target=playsound, args=[fail_sound], daemon=True).start()
                                    # makes a slightly deeper beeping sound on failed scan out
                        # if found and check-in time is less than the specified wait time then wait
                        elif time_check < t_value and status_check == "OUT":
                            pass
                        # if found and time check exceeds specified wait time and user is checked out, delete ID and
                        # affiliated data from the list. This resets everything for said user and allows the user to
                        # check back in at a later time.
                        elif time_check > t_value and status_check == "OUT":
                            index_loc = found.index(barcode_data)
                            del found_status[index_loc]
                            del found_time[index_loc]
                            del found[index_loc]
                            del thread_started[index_loc]

                        # Write updated found arrays to qr_data_file so that it is up to date with the latest scan ins
                        with open(qr_storage_file, "w") as qr_data_file:  # that file is used when restarting sessions
                            for i in range(len(found)):
                                code = found[i]
                                tyme = found_time[i]
                                status = found_status[i]
                                qr_data_file.write("{0},{1},{2}\n".format(code, tyme, status))
                    else:
                        print("[Error] Barcode data issue in video() function.")

                # If timer is active, check to see if any user has gone over the timer
                if self.timer is not None:
                    datetime_scanned = datetime.datetime.now()  # get current time
                    for i in range(len(found)):  # below: total time passed since user checked in
                        time_check = \
                            (datetime_scanned.hour * 60 + datetime_scanned.minute + datetime_scanned.second / 60) - \
                            (found_time[i].hour * 60 + found_time[i].minute + found_time[i].second / 60)
                        if time_check > self.timer and thread_started[i] is not True:
                            # if they're beyond the timer limit
                            # print(found[i])
                            timer_alert(found[i])
                            # alert user
                            thread_started[i] = True  # mark this code/item/user as having an alert already run for
                            # them, so that it doesn't happen again
                # future: it should probably also not have the potential to trigger multiple threads/alerts/sounds
                # overlayed

                # show the output frame
                if display_video:
                    cv2.imshow("QR Toolbox", frame)
                    key = cv2.waitKey(1)
                    if key == 113 or key == 81:
                        break
                else:
                    key = select.select([sys.stdin], [], [], 1)[0]
                    if key:
                        value = sys.stdin.readline().rstrip()
                        if value == 'q':
                            break
                # if the user closes the window, close the window (lol)

            # close the output CSV file and do a bit of cleanup
            print("[ALERT] Cleaning up... \n")
            txt.close()
            if play_light:
                GPIO.output(10, False)

            if os.path.exists(qr_storage_file) and os.stat(qr_storage_file).st_size == 0:
                os.remove(qr_storage_file)  # if the file is empty, delete it
            checkStorage = False  # Reset the global variable that tells code to check the qr_storage_file
            uploadBackup = False
            data = ""
            # This part is necessary to show special characters properly on any of the local CSVs
            if os.path.exists(args["output"]) and os.stat(args["output"]).st_size != 0:
                barcodes_txt = open(args["output"], 'r', encoding="utf-8")
                new_csv = open(archive_folder + "/" + file_name, 'w', encoding="utf-8")

                data = barcodes_txt.read()
                new_csv.write(data)

                barcodes_txt.close()
                new_csv.close()
            elif not os.path.exists(args["output"]):
                data = "[ERROR] barcodes.txt not found as expected."
                print(data)

            if storageChoice == 'a' and os.stat(args["output"]).st_size != 0:
                # if local was chosen, also store barcodes file at the location given
                if os.path.exists(storagePath):  # check if file path exists
                    with open(os.path.join(storagePath, file_name), "w", encoding="utf-8") as csv2:
                        csv2.write(data)
                else:
                    print("[ALERT]: Storage folder not established or is unavailable. Files will only be saved to the "
                          "root/working directory")

            if os.path.exists(args["output"]) and os.stat(args["output"]).st_size == 0:  # delete barcodes.txt if empty
                os.remove(args["output"])
                # not removed until the end in case something goes wrong above and it's needed
            if vs is not None:
                vs.stop()  # reset and close everything related to the videostream
                vs.stream.release()
                vs = None

            cv2.destroyAllWindows()  # close all cv windows
            video_on = False
        else:  # if user did not choose storage
            print("Storage location not chosen, please choose a storage location")
            video_on = False

    """
    This function prepares the program and then runs the video() function to read QR Codes
        - The preparation involves setting up and starting the popup, and checking if a video stream already exists
        - It also runs the video stream on a different thread, so that the user can do 2 things at once with the program
    """

    def qr_reader(self):

        global vs, uploadBackup
        if vs is not None:
            # if vs already exists let user know (this code will likely never be run due to disabled btn)
            print("[ALERT] A video stream already exists.")
            return

        print("\nDo you want to:\n1) start a new session (all previous data will be deleted)\n"
              "2) restart the previous LOCAL session (if one exists)\n"
              "3) restart the previous ONLINE session (if one exists)\n"
              "Note: CSV files are not created nor uploaded until after the QR Reader is closed.")
        answer = input("Choice: ")
        if answer == '1':
            uploadBackup = False
            set_check_storage(self, False)
        elif answer == '2':
            uploadBackup = True
            set_check_storage(self, True)
        elif answer == '3':
            uploadBackup = False
            set_check_storage(self, True)
        else:
            print("Selection entered was not of an available option")

    """ 
        This function sends the scanned-in/out data to arcgis as a feature, along with the coordinates defined by the
        user in the settings.py file
        - If an error occurs, it lets the user know
    """

    def update_arcgis(self, sys_id, date_str, time_str, barcode_data, status, time_elapsed=None):
        search_results = self.gis.content.search(query=gis_query, max_items=15)  # query is set in the settings.py file
        data = search_results[0]  # code auto chooses the first option on the list

        # Add data to layer
        feature_layers = data.layers
        layer = feature_layers[0]

        # Get the geo coordinates
        point = Point({"x": longitude, "y": latitude, "spatialReference": {"wkid": 4326}})  # other is 3857
        feature = None
        try:
            if status == "IN":  # create the feature (slightly diff if status is IN vs OUT)
                feature = features.Feature(
                    geometry=point,
                    attributes={
                        'Source': sys_id,
                        'ScanDateTime': f"{date_str} {time_str}",
                        'CodeText': barcode_data,
                        'Status': 'IN'
                    }
                )
            elif status == "OUT":
                feature = features.Feature(
                    geometry=point,
                    attributes={
                        'Source': sys_id,
                        'ScanDateTime': f"{date_str} {time_str}",
                        'CodeText': barcode_data,
                        'Status': 'OUT',
                        'ElapsedTime': f"{time_elapsed}"
                    }
                )
            layer.edit_features(adds=[feature])  # add feature to the layer, get results
        except Exception as e:  # if failed, print error to user and return False so not successful
            print("Error: Couldn't create the feature: %s" % e)
            return False

    """ This function shows the setup menu as a popup widget w/4 buttons """

    def setup(self):
        setup = SetupElement()
        setup.main_screen = self
        print("\nChoose an option:\n"
              "1) Upload/Consolidate\n2) Change storage location\n3) Change camera source\n4) Change camera display\n"
              "5) Change attached media\n6) Set Timer")
        # "\n4) Set timer")
        option = input("Choice: ")
        if option == '1':
            setup.upload_consolidate()
        elif option == '2':
            setup.change_storage_location()
        elif option == '3':
            setup.change_camera_source()
        elif option == '4':
            setup.change_display_feed()
        elif option == '5':
            set_media()
        elif option == '6':
            setup.set_timer_popup()
        else:
            print("Selection entered was not of an available option")

    """ This function is triggered when the user clicks the Menu 'Exit' button """

    def menu(self):
        global video_on
        while True:
            if video_on:
                continue
            print("\nPlease select which option you would like:\n1) QR Reader\n2) Settings\n3) About\n4) Exit")
            choice = input("Choice: ")
            if choice == '1':
                self.qr_reader()
            elif choice == '2':
                self.setup()
            elif choice == '3':
                about()
            elif choice == '4':
                confirm_exit()
            else:
                print("Please enter one of the available selections")


""" 
This class represents the information displayed when you want to set the storage location (text and 2 buttons, local 
or online) 
"""


class Storage:
    main_screen = None

    """ This function sets the storage based on the users selection (local or online) """

    def set_storage(self, storage):
        global storageChoice
        if storage:  # Local button was pressed
            global storagePath
            storageChoice = "a"
            storagePath = store()
        elif not storage:  # online btn was pressed
            storageChoice = "b"

            sign_in(self.main_screen)


""" This class represents the information displayed when you click the Setup menu """


class SetupElement:
    main_screen = None

    """ 
    Redirects program to either the consolidate() method or the upload_backup() method above, 
    based on users choice 
    """

    def upload_consolidate(self):
        if storageChoice == 'a':  # if local mode, call cons() func, otherwise call upload_backup()
            cons()
        else:
            upload_backup(self.main_screen, True)  # since it comes only from menu, send True

    """ Creates and starts the popup for changing the storage location """

    def change_storage_location(self):
        storage_location = Storage()
        storage_location.main_screen = self.main_screen
        print("\nSelect a storage location\nNote: Files are also saved in the QR-Toolbox Archive folder regardless."
              "\n1) ArcGIS (online)\n2) Local ")
        choice = input("Choice: ")
        if choice == '1':
            storage_location.set_storage(False)
        elif choice == '2':
            storage_location.set_storage(True)
        else:
            print("Selection entered was not of an available option")

    """  Creates and starts the popup for changing the camera source """

    @staticmethod
    def change_camera_source():
        print("\nWhich camera do you want to use?\n1) Integrated Webcam\n2) Separate Webcam\n3) PiCamera")
        choice = input("Choice: ")
        if choice == '1':
            set_camera("Integrated")
        elif choice == '2':
            set_camera("Separate")
        elif choice == '3':
            set_camera("PiCamera")
        else:
            print("Selection entered was not of an available option")

    """ Method to turn on and off the camera feed display """

    @staticmethod
    def change_display_feed():
        global display_video
        print("\nDo you want to display the camera feed?")
        choice = input("(Y/N): ")
        if choice.lower() == 'y' or choice.lower() == 'yes':
            display_video = True
        elif choice.lower() == 'n' or choice.lower() == 'no':
            display_video = False
        else:
            print("Selection entered was not of an available option")

    """Creates and starts the popup for setting a timer for how long users can be checked in"""

    def set_timer_popup(self):
        timer = Timer()
        timer.main_screen = self.main_screen
        print("Enter the time (in minutes) for the timer.")
        choice = input("Time: ")
        if choice.isnumeric():
            timer.set_timer(choice)
        else:
            print("Value entered was not in the proper format")


class Timer:
    main_screen = None

    """ Sets the timer variable to the user defined value """

    def set_timer(self, time_to_set):  # a time of 0min also counts as unsetting the timer
        if time_to_set != "" and time_to_set is not None and int(time_to_set) != 0:
            self.main_screen.timer = int(time_to_set)  # set the timer and print a message
            print("Timer set to %s minute(s)." % time_to_set)
        else:  # unset the timer
            self.main_screen.timer = None
            print("Timer unset.")


""" This class represents the app itself, and everything starts from and runs from this """


class QRToolboxApp:
    main_screen = None

    """ 
    Builds the QRToolboxApp instance by instantiating the MainScreenWidget and returning that as the 
    Main Widget for the app 
    """

    def __init__(self):
        self.main_screen = MainScreen()

    """ This function runs the storage selection popup at the start of the App, and sets some global vars """

    def start(self):
        storage_location = Storage()
        storage_location.main_screen = self.main_screen
        urllib3.disable_warnings()
        print("Select a storage location\nNote: Files are also saved in the QR-Toolbox Archive folder regardless."
              "\n1) ArcGIS (online)\n2) Local ")
        choice = input("Choice: ")
        if choice == '1':
            storage_location.set_storage(False)
        elif choice == '2':
            storage_location.set_storage(True)
        else:
            print("Selection entered was not of an available option")
        set_media()
        self.main_screen.menu()


if __name__ == '__main__':
    QRToolboxApp().start()  # runs and starts the whole program
