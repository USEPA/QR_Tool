# -*- coding: windows-1252 -*-
"""
Name: QR Toolbox v1.7
Description: The QR Toolbox is a suite a tools for creating and reading QR codes. See the About screen for more
information
Author(s): Code integration, minor enhancements, & platform development - Timothy Boe boe.timothy@epa.gov;
    Muhammad Karimi karimi.muhammad@epa.gov; Jordan Deagan deagan.jordan@epa.gov
    qrcode - Lincoln Loop info@lincolnloop.com; pyzbar - Lawrence Hudson quicklizard@googlemail.com;
    OpenCV code - Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/;
    Sound effects obtained from https://www.zapsplat.com
Contact: Timothy Boe boe.timothy@epa.gov
Requirements: Python 3.7+, pyzbar, imutils, opencv-python, qrcode[pil], Pillow, Kivy, kivy-deps.angle,
kivy-deps.glew, kivy-deps.gstreamer, kivy-deps.sdl2, Kivy-Garden, arcgis, playsound

Specific versions:
{"pyzbar": "0.1.8", "imutils": "0.5.4", "qrcode": "6.1", "Pillow": "8.2.0", "opencv-python": "4.5.1.48",
"Kivy": "2.0.0", "kivy-deps.angle": "0.3.0", "kivy-deps.glew": "0.3.0", "kivy-deps.gstreamer": "0.3.2",
"kivy-deps.sdl2": "0.4.2", "Kivy-Garden": "0.1.4", "arcgis": "1.8.5.post3", "playsound": "1.2.2}
"""

# import the necessary packages
import argparse
import csv
import sys
import datetime
import os
import os.path
import shutil
import time
import pyodbc
from playsound import playsound
from datetime import timedelta
from time import strftime
from tkinter import *
from tkinter import filedialog

from arcgis.gis import GIS
from arcgis import features
from arcgis.geometry import Point

# Import csv packages
import cv2
import imutils
import numpy as np
import qrcode
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import math
from imutils.video import VideoStream
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol

import threading
from kivy.app import App

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.core.window import Window
from Library.garden.recyclelabel import RecycleLabel

# to do
"""
    Alter code to allow SQL access:
    Change connect to upload (name)
    upload sync fail message should be changed (838, 877)
    Auto upload during session start not triggering
    Read back from ArcGIS to track interactions across multiple devices
    restore log option
    Toggle tracking state option
    if no recent camera activity, test read data to check/maintain connection
    Plugging in camera while running doesn't detect
    Use new architecture to allow ArcGIS connection longer than 30 min
"""

# colors


class BaseColors:
    HEADER = ''
    OKBLUE = '[color=#009999]'
    OKGREEN = '[color=#66cc00]'
    WARNING = '[color=#e3e129]'
    FAIL = '[color=#a72618]'
    ENDC = '[/color]'
    BOLD = ''
    UNDERLINE = ''


# ArcGIS/IO related variables
arcgis_url = ""
gis_query = ""
latitude = ""
longitude = ""
sql_address = ""
sql_database = ""
localQRBatchFile = ""

# System variables
settings = "Setup/settings.csv"
qr_storage_file = "System_Data/qr-data.txt"  # file that contains saved session information
backup_file = "System_Data/backup.txt"  # file that contains data that couldn't be uploaded, to later be uploaded
archive_folder = "Archive"
fail_ding = "Library/sounds/failed.mp3"
pass_ding = "Library/sounds/passed.mp3"
timer_alarm = "Library/sounds/alarm.mp3"

# query_in = """
# INSERT INTO ? (?, ?, ?, ?)
# VALUES (?, ?, ?, 'IN');
query_in = ""
query_out = ""
headers = []

# load variables
# set store folder default, assign system ID, and wait time
storagePath = ""  # the path to the local storage directory if chosen
checkStorage = False  # whether system should check if there is any backed up data or previous session data
uploadBackup = False
user_chose_storage = False  # tracks whether user chose a storage method or not
system_id = os.environ['COMPUTERNAME']  # this is used when checking qr codes in or out
t_value = timedelta(seconds=10)  # time between scans for the same qr code
cameraSource = "Integrated"  # the camera source, defaults to integrated (so source 0)
storageChoice = ""  # users choice of local ('a'), ArcGIS ('b'), or SQL ('c') mode
vs = None  # global video stream variable, to ensure only 1 instance of it exists at a time
clear_screen = False  # if True, clear screen, else don't clear it (true only in 4 cases)
not_yet = False  # prevents the screen from being cleared immediately at the start (only used at the start)
connection_lost = False  # set if an upload fails
local_passed = False  # check source of connection error
sql_cursor = None

# Lists and Dictionaries used for special character handling and conversion
trouble_characters = ['\t', '\n', '\r']  # characters that cause issues
bad_file_name_list = ['*', ':', '"', '<', '>', ',', '/', '|', '?', '\t', '\r', '\n',
                      '\\']  # can't be used in a filename
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


def convert(main_screen, data_to_convert, character_list, conversion_dict, is_for_file_name=False,
            is_for_trouble=False):
    old_data = data_to_convert  # saving original data before variable is modified
    screen_label = main_screen.ids.screen_label
    setup_screen_label(screen_label)  # setup the screen label

    for char in character_list:  # iterate through chars in character_list and convert if necessary
        if char in data_to_convert:
            data_to_convert = data_to_convert.replace(char, conversion_dict[
                char]) if not is_for_file_name else data_to_convert.replace(char, "-") \
                if not is_for_trouble else data_to_convert.replace(char, " ")
            # data is converted to the appropriate character(s) depending on if the conversion is for a bad file
            # name, or to remove trouble characters, or simply to convert special chars to code chars
    if old_data != data_to_convert and is_for_file_name and is_for_trouble is not True:
        # if the data was converted and it was for a bad file name and not only for a trouble character, print this
        # to user
        screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Error saving file with name {old_data}, saved " \
                                                f"as {data_to_convert} instead.{BaseColors.ENDC} "
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


def upload(main_screen, connection_type, sys_id, date_str, time_str, barcode, status, time_elapsed=None,
           duplicate=False, from_backup=False):
    global connection_lost, query_out, query_in, sql_cursor, headers, storageChoice, local_passed
    if storageChoice == "b":
        screen_label = main_screen.ids.screen_label
        setup_screen_label(screen_label)
        if status == "IN":
            content = f"{sys_id},{date_str},{time_str},{barcode},{status},NONE"
        elif status == "OUT":
            content = f"{sys_id},{date_str},{time_str},{barcode},{status},{time_elapsed}"
        else:
            screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}Status not a valid value.{BaseColors.ENDC}"
            local_passed = False
            return False
        i = 0
        while i < 3:
            try:
                return_val = True
                local_passed = True
                if connection_type == 'upload':  # if a record needs to be uploaded to arcgis
                    main_screen.update_arcgis(sys_id, date_str, time_str, barcode, status, time_elapsed)
                    if not from_backup:
                        upload_backup(main_screen)
                else:  # if for some reason connection type is not one of the above
                    screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}Invalid connection type." \
                                                            f"{BaseColors.ENDC}"
                    local_passed = False
                    return_val = False
                if i > 0:  # if a connection retry occurred and was successful
                    screen_label.text = screen_label.text + f"\n{BaseColors.OKGREEN}Connection successful.{BaseColors.ENDC}"
                return return_val  # so that calling method can use the results accordingly
            except:
                e = sys.exc_info()[0]  # used for error checking
                print(e)
                if i == 0:  # if first try failed
                    if connection_lost:
                        screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}No Connection. {BaseColors.ENDC}" \
                                                                f"{BaseColors.OKBLUE}Data will be stored locally and " \
                                                                f"uploaded at the next {BaseColors.OKBLUE}upload point"\
                                                                f", or if triggered from the menu.{BaseColors.ENDC}"
                        if connection_type == 'upload':
                            with open(backup_file, "a") as backup:  # write the data to the backup.txt file
                                backup.write(f"{content}\n")
                        local_passed = True
                        return False  # return a connection failure
                    else:
                        screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Connection lost. Trying again in 10 " \
                                                                f"seconds.{BaseColors.ENDC}"
                        time.sleep(10)

                elif i == 1:  # if second try failed
                    screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Reconnect failed. Trying again in 30 " \
                                                            f"seconds.{BaseColors.ENDC}"
                    time.sleep(30)
                elif i > 1 and not duplicate:  # if failed thrice, write to backup.txt
                    connection_lost = True
                    screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Reconnect failed again. {BaseColors.ENDC}" \
                                                            f"{BaseColors.OKBLUE}Data will be stored locally and uploaded at" \
                                                            f" the {BaseColors.OKBLUE}next upload point, or if triggered " \
                                                            f"from the menu.{BaseColors.ENDC}"
                    if connection_type == 'upload':
                        with open(backup_file, "a") as backup:  # write the data to the backup.txt file
                            backup.write(f"{content}\n")
                        local_passed = True
                    return False  # return a connection failure
            i += 1
    elif storageChoice == "c":
        screen_label = main_screen.ids.screen_label
        setup_screen_label(screen_label)
        date_time = "%s %s" % (date_str, time_str);
        if status == "IN":
            # content = tuple(headers[0:5]) + (sys_id, date_time, barcode)
            content = f"{sys_id},{date_str},{time_str},{barcode},{status},NONE"
            sql_data = (sys_id, date_time, barcode)
            # print(content)
            query = query_in
        elif status == "OUT": #update needed
            content = f"{sys_id},{date_str},{time_str},{barcode},{status},{time_elapsed}"
            sql_data = (sys_id, date_time, barcode, time_elapsed)
            query = query_out
        else:
            screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}Status not a valid value.{BaseColors.ENDC}"
            local_passed = False
            return False
        i = 0
        # query_find = "SELECT * FROM Table_1;"
        #
        # sql_cursor.execute(query_find)
        # records = sql_cursor.fetchall()
        # for r in records:
        #     print(f"{r.Scan_Date_Time}\t{r.Scanned_Text}\t{r.Scan_Status}\t{r.Elapsed_Time}")
        while i < 3:
            try:
                return_val = True
                local_passed = True
                if connection_type == 'upload':  # if a record needs to be uploaded to arcgis
                    sql_cursor.execute(query, sql_data)
                    if not from_backup:
                        upload_backup(main_screen)
                    sql_cursor.commit()
                else:  # if for some reason connection type is not one of the above
                    screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}Invalid connection type.{BaseColors.ENDC}"
                    local_passed = False
                    return_val = False
                if i > 0:  # if a connection retry occurred and was successful
                    screen_label.text = screen_label.text + f"\n{BaseColors.OKGREEN}Connection successful.{BaseColors.ENDC}"
                return return_val  # so that calling method can use the results accordingly
            except:
                e = sys.exc_info()[0]  # used for error checking
                print(e)
                if i == 0:  # if first try failed
                    if connection_lost:
                        screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}No Connection. {BaseColors.ENDC}" \
                                                                f"{BaseColors.OKBLUE}Data will be stored locally and " \
                                                                f"uploaded at the next {BaseColors.OKBLUE}upload point, or " \
                                                                f"if triggered from the menu.{BaseColors.ENDC}"
                        if connection_type == 'upload':
                            with open(backup_file, "a") as backup:  # write the data to the backup.txt file
                                backup.write(f"{content}\n")
                        local_passed = True
                        return False  # return a connection failure
                    else:
                        screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Connection lost. Trying again in 10 " \
                                                                f"seconds.{BaseColors.ENDC}"
                        time.sleep(10)

                elif i == 1:  # if second try failed
                    screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Reconnect failed. Trying again in 30 " \
                                                            f"seconds.{BaseColors.ENDC}"
                    time.sleep(30)
                elif i > 1 and not duplicate:  # if failed thrice, write to backup.txt
                    connection_lost = True
                    screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Reconnect failed again. {BaseColors.ENDC}" \
                                                            f"{BaseColors.OKBLUE}Data will be stored locally and uploaded at" \
                                                            f" the {BaseColors.OKBLUE}next upload point, or if triggered " \
                                                            f"from the menu.{BaseColors.ENDC}"
                    if connection_type == 'upload':
                        with open(backup_file, "a") as backup:  # write the data to the backup.txt file
                            backup.write(f"{content}\n")
                        local_passed = True
                    return False  # return a connection failure
            i += 1
    local_passed = False
    return False


"""
This function uploads the data that was stored/backed up in the backup.txt file

@param main_screen_widget a reference to the main screen so that info can be printed to it
@param from_menu True if this method was triggered/called from the main menu, False otherwise

@return True if re-upload was successful, False otherwise (or if there was no data to upload)
"""


def upload_backup(main_screen_widget, from_menu=False):
    screen_label = main_screen_widget.ids.screen_label
    setup_screen_label(screen_label)
    if os.path.exists(backup_file):  # check if file exists, if not then return
        with open(backup_file, "r") as backup:
            screen_label.text = screen_label.text + "\nUploading backed up data..."
            time_elapsed = None  # assume its IN status so no elapsed time
            for line in backup:  # for each line, take the appropriate action according to what is read in
                if line == '\n' or line == "":
                    continue
                content = (line.rstrip('\n')).split(',')  # if not empty or newline, then strip newline chars and
                # split line
                if content[5] != "NONE":  # if time_elapsed is not none then get time_elapsed
                    time_elapsed = content[5]
                successful = upload(main_screen_widget, 'upload', content[0], content[1], content[2], content[3],
                                    content[4], time_elapsed=time_elapsed, duplicate=True, from_backup=True)
                # submit data for upload
                if not successful:  # if upload failed print info to user
                    screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Upload of backed up data failed." \
                                                            f"{BaseColors.ENDC}{BaseColors.OKBLUE} Program will try " \
                                                            f"again at next upload, {BaseColors.OKBLUE}or you can " \
                                                            f"trigger upload manually from the menu.{BaseColors.ENDC}"
                    return False
            screen_label.text = screen_label.text + f"\n{BaseColors.OKGREEN}Upload complete!{BaseColors.ENDC}"
        os.remove(backup_file)  # file removed if upload is successful
    elif from_menu:
        screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}No backed-up data to upload.{BaseColors.ENDC}"


"""
This function creates QR codes in batches from a CSV file (defined in the global variables)
    -The function always checks and performs the QR code creation in its root folder first, and the generated codes
    are then stored in the Archive folder.
    -A storage directory must have been chosen, the codes are then also stored in that location
    -No difference between online and local mode for this
    
@param main_screen_widget a reference to the main screen so that info can be printed to it
"""


def qr_batch(main_screen_widget):
    screen_label = main_screen_widget.ids.screen_label
    setup_screen_label(screen_label)
    screen_label.text = screen_label.text + "\n\nThe batch QR code function is used to quickly create multiple QR " \
                                            "codes by referencing a .csv file.\n-There is no difference between " \
                                            "online and local mode for this function, it only works as described " \
                                            "below.\n-The CSV file must be stored in the root folder of the program (" \
                                            "where it was installed), and named 'names.csv'.\n    * The file name " \
                                            "can be changed, but this change must also be reflected in the " \
                                            "Setup/settings.py file for the \n       variable 'localQRBatchFile'." \
                                            "\n    * The Tool will then automatically create QR codes for each line " \
                                            "in the csv, and save each QR Code image to the\n       Tools root folder" \
                                            "(this folder is usually called 'QR-Toolbox', and should be found in\n   " \
                                            "    C:/Users/<user>/AppData/Local/Programs), where <user> refers to your" \
                                            "user name on your computer.\n    * However, if you changed the install " \
                                            "location, it may not be at that file path.\n-'names.csv' may consist of " \
                                            "two columns 'first' & 'second'. The 'first' and 'second' columns could " \
                                            "be \n    populated with participant's first and last names, or other " \
                                            "information, and will be joined together with a space in\n    between.\n "

    # this code creates a batch of QR codes from a csv file stored in the local directory
    # QR code image size and input filename can be modified below

    success = True
    # This one creates the batch of QR codes in the same folder as this file
    with open(localQRBatchFile) as csvfile:
        reader = csv.reader(csvfile)  # reader for the csv file

        for row in reader:
            labeldata = row[0] if len(row) == 1 else row[0] + " " + row[1] if row[1] != '' else row[
                0]  # combine the data in the first 2 cols depending on which is empty and which isn't

            # convert special char to code character
            code_label_data = convert(main_screen_widget, labeldata, special_characters, char_dict_special_to_code)

            qr = qrcode.QRCode(  # this and below are to create the QR code
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4)

            qr.add_data(code_label_data)
            qr.make(fit=True)
            screen_label.text = screen_label.text + "\nCreating QR code: " + labeldata

            # make QR image
            img = qr.make_image()
            qr_file = labeldata + ".jpg"
            qr_file = convert(main_screen_widget, qr_file, bad_file_name_list, None,
                              True)  # remove special chars that can't be in filename
            img.save(archive_folder + "/" + qr_file)

            # open QR image and add qr data as name
            img = Image.open(archive_folder + "/" + qr_file)
            draw = ImageDraw.Draw(img)
            qr_font = ImageFont.truetype("arial", 24)
            color = 0
            draw.text((37, 10), labeldata, font=qr_font, fill=color)
            img.save(archive_folder + "/" + qr_file)
            try:
                img.save(storagePath + "/" + qr_file)
            except:
                success = False  # if any failures occur, set this to success so user knows a failure occurred
                screen_label.text = screen_label.text + f"\n\n{BaseColors.FAIL}QR Code {labeldata} not " \
                                                        f"created.{BaseColors.ENDC}\n "

    if success:
        screen_label.text = screen_label.text + f"\n\n{BaseColors.OKGREEN}Success!{BaseColors.ENDC}\n"
    else:
        screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Some or no files were saved in {storagePath}, " \
                                                f"only in Archive folder.{BaseColors.ENDC}"


"""
This function creates a single QR code based on the text inserted by the user, which is stored in the Archive folder.
    - The QR code is also stored in the location entered by the user, regardless of the mode they are in
    
@param main_screen_widget reference to main screen to print info
@param text the text from the TextInput field
"""


def qr_single(main_screen_widget, text):
    screen_label = main_screen_widget.ids.screen_label
    setup_screen_label(screen_label)

    if text == "":  # if no text is entered into the text box
        screen_label.text = screen_label.text + "\nSkipped because no text was entered."
        return

    text_copy = text  # this line is probably not needed
    screen_label.text = screen_label.text + "\nCreating QR code: " + text

    # convert special char to code character
    text_copy = convert(main_screen_widget, text_copy, special_characters, char_dict_special_to_code)

    # this code creates a single QR code based on information entered into the command line.
    # The resulting QR code is stored in the current (the programs') directory
    # QR code image size and input filename can be modified below
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4)

    qr.add_data(text_copy)
    qr.make(fit=True)

    # draw label
    img = qr.make_image()
    file_name = text + ".jpg"
    file_name = convert(main_screen_widget, file_name, bad_file_name_list, None,
                        True)  # convert chars that can't be in a file name
    img.save(archive_folder + "/" + file_name)

    # Open QR image and add QR data as name
    img = Image.open(archive_folder + "/" + file_name)
    draw = ImageDraw.Draw(img)
    qr_font = ImageFont.truetype("arial", 24)
    color = 0
    draw.text((37, 10), text, font=qr_font, fill=color)
    img.save(archive_folder + "/" + file_name)

    succeed = True
    # Store QR code locally
    try:  # try to save, if it fails then let user know
        img.save(storagePath + "/" + file_name)
    except:
        succeed = False
        screen_label.text = screen_label.text + f"\n\n{BaseColors.FAIL}QR Code {text} not created.{BaseColors.ENDC}\n"

    if succeed:
        screen_label.text = screen_label.text + f"\n{BaseColors.OKGREEN}Success!{BaseColors.ENDC}"
    else:
        screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}File not saved in {storagePath}, only in " \
                                                f"Archive folder.{BaseColors.ENDC}"


"""
This function consolidates QR csv results into a single file. This function looks for files with QRT in the first part 
of their name. If true, all csvs within the storage directory that also fit this condition. A number of error
checks are built in to prevent bad things from happening
"""


def cons(main_screen_widget):
    screen_label = main_screen_widget.ids.screen_label
    setup_screen_label(screen_label)

    time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))  # get current date and time
    cons_filename = os.path.join(storagePath, 'Consolidated_Record_' + time_header + '.csv')
    if os.path.exists(storagePath):  # if storage directory has been set
        qrt_files = [fn for fn in os.listdir(storagePath) if
                     fn.startswith('QRT-R-') and fn.endswith('.csv') and fn.__contains__("_")]
        # above: get all csv files that start with QRT-R- and end with .csv and have  a '_' in them
        if not qrt_files:  # if its empty then print this
            screen_label.text = screen_label.text + "\nNo entries to combine. Check the storage directory and try again"
        else:  # if not empty then go through them and copy them into one file
            try:
                with open(cons_filename, 'wb') as outfile:
                    for i, fname in enumerate(qrt_files):
                        fname = os.path.join(storagePath, fname)
                        with open(fname, 'rb') as infile:
                            shutil.copyfileobj(infile, outfile)  # copy data from each file to the consolidated file
                            screen_label.text = screen_label.text + f"\n{fname} has been imported."
                screen_label.text = screen_label.text + f"\n\n{BaseColors.OKGREEN}Consolidated file created in the " \
                                                        f"specified storage directory under {BaseColors.OKBLUE}" \
                                                        f"{BaseColors.OKGREEN}the filename " + cons_filename + \
                                                        f"{BaseColors.ENDC}\n"
            except:
                screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}[WARNING] Either the system was " \
                                                        f"unable to write the consolidated file {BaseColors.ENDC}" \
                                                        f"{BaseColors.WARNING}to the specified storage directory or " \
                                                        f"the file {BaseColors.ENDC}" + cons_filename + \
                                    f"{BaseColors.WARNING} is currently in use {BaseColors.ENDC}" \
                                    f"{BaseColors.WARNING}or unavailable. The consolidated record " \
                                    f"may be incomplete.{BaseColors.ENDC}\n"
    else:  # if no storage location chosen yet
        screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}A storage location has not been established. " \
                                                f"Specify a storage folder using the {BaseColors.ENDC}" \
                                                f"{BaseColors.WARNING}'Choose Storage Location' option before " \
                                                f"continuing\n{BaseColors.ENDC}"


# GUI PART OF PROGRAM STARTS HERE
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'  # not sure if its vital or not

"""
This function allows the user to select a storage directory. If user escapes, a storage directory is not created
    - Note: the Tkinter code can be finicky when displayed in IDE i.e., the file window will not show when operated in
    IDE while the root.withdraw command is turned on. Commenting out the root.withdraw command will fix, but root
    window remains; destroy() can be used to remove this. May need to search for a better solution in the future
"""


def store(main_screen):
    global user_chose_storage
    screen_label = main_screen.ids.screen_label
    setup_screen_label(screen_label)  # setup the screen label

    root = Tk()
    root.title('Storage Directory')
    root.withdraw()
    store_path = filedialog.askdirectory(title='Select a Storage Directory')  # ask user to choose a directory
    if os.path.exists(store_path):  # if they chose one
        screen_label.text = screen_label.text + f"\n{BaseColors.OKGREEN}Storage directory established: " \
                                                f"{store_path}{BaseColors.ENDC}"
        user_chose_storage = True
    else:
        screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}Storage directory NOT " \
                                                f"established{BaseColors.ENDC}"
        user_chose_storage = False
    return store_path


"""
This method allows the home screen and one command along with it, but when any other command is pressed it formats the 
screen
 - Formatted to the left and removing whatever was already there
 @param screen_label the reference to the scrollable label on the screen that text is put on
"""


def setup_screen_label(screen_label):
    global clear_screen, not_yet

    if clear_screen and not not_yet:
        screen_label.text = ""
        clear_screen = False  # i've forgotten how this works exactly, but its simple and shouldn't need to be changed
    # if a new function is created that prints to the screen, just call this function at the beginning of it
    if not not_yet:
        screen_label.halign = 'left'
    not_yet = False


"""
This class is the main class for the GUI, 
it is the main screen within which all other screens/widgets/buttons are located
"""


class MainScreenWidget(BoxLayout):
    sys_id = os.environ["COMPUTERNAME"]  # this may be a repeat
    gis = None  # contains the access to arcgis online to upload data
    timer = None  # used to time how long users are checked in and alert any who exceed this amount of elapsed time

    def __init__(self, **kwargs):  # start the program and bind the 'X' button the exit function
        super(MainScreenWidget, self).__init__(**kwargs)
        Window.bind(on_request_close=self.exit)

    """
    This function starts a VideoStream, and captures any QR Codes it sees (in a certain distance)
    Those codes are decoded, and written to a local CSV file along with the Computer Name, date, time, and IN/OUT
    The local CSV file is always saved in the Archive folder by default
        -If local was chosen, the CSV file is also saved at the storage location entered by the user
        -If online was chosen, the records (not the CSV) are also saved on the ArcGIS site
    """

    def video(self):
        global user_chose_storage, vs, uploadBackup, checkStorage, local_passed

        screen_label = self.ids.screen_label
        setup_screen_label(screen_label)

        if user_chose_storage:
            screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}[ALERT] Starting video stream..." \
                                                    f"{BaseColors.ENDC}\n"
            screen_label.text = screen_label.text + f"{BaseColors.OKBLUE}To exit, close the webcam " \
                                                    f"window.{BaseColors.ENDC}"

            # construct the argument parser and parse the arguments
            ap = argparse.ArgumentParser()
            ap.add_argument("-o", "--output", type=str, default="System_Data/barcodes.txt",
                            help="path to output CSV file containing barcodes")
            args = vars(ap.parse_args())
            # initialize time and date and make filename friendly
            time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            file_name = "QRT-R-" + system_id + "_" + time_header + ".csv"
            if storageChoice == 'a' and os.path.exists(storagePath):
                local_file = os.path.join(storagePath, file_name)
            else:
                local_file = ""
                if storageChoice == 'a':
                    screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}[ALERT]: Storage folder not " \
                                                            f"established or is unavailable.\n {BaseColors.ENDC}" \
                                                            f"{BaseColors.WARNING}Files will only be saved to the " \
                                                            f"root/working directory\n{BaseColors.ENDC} "

            # initialize the video stream and allow the camera sensor to warm up
            try:
                if cameraSource == 'Integrated':  # start correct camera based on user choice at beginning
                    vs = VideoStream(src=0).start()  # for integrated/built in webcam
                elif cameraSource == 'Separate':
                    vs = VideoStream(src=1).start()  # for separate webcam (usually USB connected)
                elif cameraSource == 'PiCamera':
                    vs = VideoStream(usePiCamera=True).start()  # for mobile solution like Raspberry Pi Camera
                else:
                    screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}An error has " \
                                                            f"occurred.{BaseColors.ENDC}"
                    return
            except:  # if an error occurs in creating video stream, print to user and return
                screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}An error occurred starting the QR " \
                                                        f"Reader. Check your cameras and try again.{BaseColors.ENDC}"
                vs = None
                self.ids.qrreader.disabled = False  # makes QR Reader btn enabled again
                return

            time.sleep(5.0)  # give camera time

            # open the output txt file for writing and initialize the set of barcodes found thus far
            if os.path.isfile(args["output"]) and checkStorage:  # check if user wanted to restart prev session
                if (storageChoice.lower() == 'b' or storageChoice.lower() == 'c') and uploadBackup:  # do this only if QR Toolbox is in online-mode
                    # Write previous records back to contentStrings
                    with open(args["output"], "r", encoding='utf-8') as txt:
                        screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Restoring records (online " \
                                                                f"mode)...{BaseColors.ENDC}"
                        for line in txt:  # get each record from the file by line
                            if line == '\n':
                                continue  # if line is newline only then skip it
                            line_array = line.split(",")
                            last_system_id = line_array[0]
                            file_date = datetime.datetime.strptime(line_array[1],
                                                                   "%m/%d/%Y").date()  # get date from file
                            file_time = datetime.datetime.strptime(line_array[2],
                                                                   "%H:%M:%S").time()  # get time from file
                            # hour = file_time.hour + 4
                            # this is to counter the weird arcgis effect where it auto subtracts 4 hrs
                            # if hour > 23:
                            # have to do this part for the cases where it goes over 2300 and isn't real time anymore
                            #     if hour == 24: hour = 0
                            #     if hour == 25: hour = 1
                            #     if hour == 26: hour = 2
                            #     if hour == 27: hour = 3
                            #     file_date.replace(file_date.year, file_date.month, file_date.day + 1)
                            # need to increment day by one, otherwise when time is set back 4hrs by arcgis, it'll
                            # decrement the day as well so the date would end up one day off (one day early)
                            file_time_online = file_time

                            barcode_data_special = line_array[3]  # get the QR Code from the file
                            status = line_array[4]  # get the status from the file
                            if "OUT" in status:  # if the status is OUT, also get the QRCodes' duration from the file
                                duration = line_array[5][:len(line_array[5]) - 1:]  # also remove newline char
                            else:
                                status = status[:len(status) - 1]  # else just remove the newline char from the status

                            if status == "IN":  # if status is IN, no duration
                                success = upload(self, "upload", last_system_id, file_date, file_time_online,
                                                 barcode_data_special, status)
                            else:  # if status is OUT, add duration of qr code being checked in
                                success = upload(self, "upload", last_system_id, file_date, file_time_online,
                                                 barcode_data_special, status, duration)
                            if not success:
                                break  # if upload failed, break loop and let user know it failed
                elif (storageChoice.lower() == 'b' or storageChoice.lower() == 'c') and not uploadBackup:
                    screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Restoring records (online mode)" \
                                                            f"...{BaseColors.ENDC}\n" \
                                                            f"{open(args['output'], 'r', encoding='utf-8').read()}"
                if storageChoice.lower() == 'a':
                    # if in local mode, just open barcodes.txt for appending to restorerecords
                    screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Restoring records (local mode)" \
                                                            f"...{BaseColors.ENDC}\n" \
                                                            f"{open(args['output'], 'r', encoding='utf-8').read()}"
                    if local_file != "":
                        with open(args["output"], "r", encoding='utf-8') as txt:
                            with open(local_file, "a", encoding="ANSI") as csv2:
                                for line in txt:
                                    csv2.write(line)

                try:
                    txt = open(args["output"], "a",
                               encoding="utf-8")  # reopen txt file for appending (to continue records)
                    success = True
                except:
                    success = False
                if success:
                    screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Previous records restored." \
                                                            f"{BaseColors.ENDC}"
                else:
                    screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Previous records NOT restored." \
                                                            f"{BaseColors.ENDC}"
            else:  # if no previous records and user wanted to restart/restore them then print that none exist
                txt = open(args["output"], "w", encoding="utf-8")  # else open new file/overwrite previous
                if checkStorage:
                    screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}No previous records found. CSV " \
                                                            f"file will not include {BaseColors.ENDC}" \
                                                            f"{BaseColors.WARNING}past records.{BaseColors.ENDC}"

            # time track variables. These are used to keep track of QR codes as they enter the screen
            found = []
            found_time = []
            found_status = []
            thread_started = []  # tracks if a thread for the item in the given position has been started already, bool

            # Check if there are any stored QR codes that were scanned-in in an earlier instance of the system
            if checkStorage:
                if os.path.exists(qr_storage_file) and os.stat(qr_storage_file).st_size != 0:
                    screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Restarting session" \
                                                            f"...{BaseColors.ENDC}"
                    with open(qr_storage_file, "r") as qr_data_file:
                        for line in qr_data_file:  # if yes, read them in line by line
                            if line == '\n':
                                continue
                            line_array = line.split(",")
                            found.append(line_array[0])  # append file data to the found arrays
                            found_time.append(datetime.datetime.strptime(line_array[1], "%Y-%m-%d %H:%M:%S"))
                            found_status.append(line_array[2][:len(line_array[2]) - 1:])
                            thread_started.append(False)
                    if storageChoice.lower() == 'b' or storageChoice.lower() == 'c':
                        upload_backup(self)
                    screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Previous session restarted." \
                                                            f"{BaseColors.ENDC}"
                elif not os.path.exists(qr_storage_file) or os.stat(qr_storage_file).st_size == 0:
                    screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}No previous session found " \
                                                            f"[qr-data.txt not found or is empty].{BaseColors.ENDC}"
            if storageChoice.lower() == 'a' and local_file != "":
                local_timer = datetime.datetime.now()
                local_temp = []
            # loop over the frames from the video stream
            while True:
                # grab the frame from the threaded video stream and resize it to have a maximum width of 400 pixels
                frame = None
                try:  # if the video stream stops working or is changed
                    frame = vs.read()
                    frame = imutils.resize(frame, width=400)
                except:  # then catch and break the loop, and do clean up
                    screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Video stream lost. Check your " \
                                                            f"cameras. Proceeding to clean up.{BaseColors.ENDC}"
                    break

                # find the barcodes in the frame and decode each of the barcodes
                barcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.QRCODE])
                timestr = datetime.datetime.now()
                # hour = timestr.hour + 4  # this is to counter the weird arcgis effect where it auto subtracts 4 hrs
                # if hour > 23:
                # have to do this part for the cases where it goes over 2300 and thus isn't real time anymore
                #     if hour == 24: hour = 0
                #     if hour == 25: hour = 1
                #     if hour == 26: hour = 2
                #     if hour == 27: hour = 3
                #     timestr = timestr.replace(timestr.year, timestr.month, timestr.day + 1, hour, timestr.minute,
                #                               timestr.second, timestr.microsecond)
                # need to increment day by one, otherwise when time is set back 4hrs by arcgis,
                # it'll decrement the day as well so the date would end up one day off (one day early)
                datestr = timestr.strftime("%m/%d/%Y")
                timestr = timestr.strftime("%H:%M:%S")

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

                    # Convert barcode_data code chars back to special chars
                    barcode_data = convert(self, barcode_data, code_characters, char_dict_code_to_special)

                    # Draw the barcode data and barcode type on the image
                    img = Image.new('RGB', (400, 15), color='white')
                    img.putalpha(0)
                    d = ImageDraw.Draw(img)
                    text_to_print = convert(self, barcode_data, trouble_characters, None, True,
                                            True)  # replace \t,\n,\r with ' '
                    try:  # if code was not generated by qr tool or doesn't meet its conditions, let user know
                        d.text((0, 0), text_to_print + ' (' + barcode_type + ')', fill='blue')
                    except UnicodeEncodeError:
                        screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}[ERROR] Can't use QR Codes not " \
                                                                f"generated by the system.{BaseColors.ENDC}"
                        continue

                    pil_image = Image.fromarray(frame)  # convert frame to pil image format, then to numpy array
                    pil_image.paste(img, box=(x, y - 15),
                                    mask=img)  # not sure exactly what's going on here, but it is vital I believe
                    frame = np.array(pil_image)

                    # if the barcode text is currently not in our CSV file, write the timestamp + barcode to disk
                    # and update the set of barcode data has never been seen, check the user in and record id, date,
                    # and time information
                    if barcode_data not in found:
                        datetime_scanned = datetime.datetime.now()  # this one appended to found_time arr
                        date_scanned = datetime.datetime.now().strftime("%m/%d/%Y")  # this one prints to csv
                        time_scanned = datetime.datetime.now().strftime("%H:%M:%S")  # this one prints to csv

                        txt.write("{},{},{},{},{}\n".format(system_id, date_scanned, time_scanned,
                                                            barcode_data, "IN"))  # write scanned data to the text file
                        txt.flush()

                        if storageChoice.lower() == 'a' and local_file != "":
                            local_temp.append(
                                "{},{},{},{},{}\n".format(system_id, date_scanned, time_scanned, barcode_data, "IN"))

                        found.append(
                            barcode_data)  # add the scanned data to the found arrays so status/times can be managed
                        found_time.append(datetime_scanned)
                        found_status.append("IN")
                        thread_started.append(
                            False)  # added so that it corresponds to the actual data in the found arrays

                        # Write updated found arrays to qr_data_file so that it is up to date with the latest scan ins
                        with open(qr_storage_file, "w") as qr_data_file:
                            for i in range(len(found)):
                                code = found[i]
                                tyme = found_time[i]
                                status = found_status[i]
                                qr_data_file.write("{0},{1},{2}\n".format(code, tyme, status))

                        success = True
                        if storageChoice.lower() == 'b' or storageChoice.lower() == 'c':  # if user chose online/arcgis
                            success = upload(self, "upload", system_id, datestr, timestr, barcode_data, "IN")

                        if success:
                            screen_label.text = screen_label.text + f"\n{barcode_data} checking IN at {date_scanned} " \
                                                                    f"{time_scanned} at location: {system_id}"
                            playsound(pass_ding)  # makes a beeping sound on scan in
                        elif local_passed and not success:
                            screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}Online login unavailable" \
                                                                    f" at current time, continuing local login" \
                                                                    f"\n{barcode_data} checking IN at " \
                                                                    f"{date_scanned} {time_scanned} at location: " \
                                                                    f"{system_id}"
                            playsound(pass_ding)
                        elif not success and not local_passed:
                            screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}{barcode_data} NOT " \
                                                                    f"CHECKED IN, SEE ABOVE ERROR{BaseColors.ENDC}"
                            playsound(fail_ding)  # makes a slightly deeper beeping sound on failed scan in

                    # if barcode information is found...
                    elif barcode_data in found:
                        # get current time and also total time passed since user checked in
                        datetime_scanned = datetime.datetime.now()  # this one appended to found_time arr
                        date_scanned = datetime.datetime.now().strftime("%m/%d/%Y")  # this one prints to csv
                        time_scanned = datetime.datetime.now().strftime("%H:%M:%S")  # this one prints to csv
                        time_check = datetime_scanned - found_time[found.index(barcode_data)]
                        status_check = found_status[found.index(barcode_data)]

                        # if time exceeds wait period and user is checked in then check them out
                        if time_check > t_value and status_check == "IN":
                            index_loc = found.index(barcode_data)
                            found_status[index_loc] = "OUT"
                            found_time[index_loc] = datetime_scanned
                            txt.write("{},{},{},{},{},{}\n".format(system_id, date_scanned, time_scanned,
                                                                   barcode_data, "OUT",
                                                                   time_check))  # write to local txt file

                            txt.flush()

                            if storageChoice.lower() == 'a' and local_file != "":
                                local_temp.append("{},{},{},{},{},{}\n".format(system_id, date_scanned, time_scanned,
                                                                               barcode_data, "OUT", time_check))

                            success = True
                            if storageChoice.lower() == 'b' or storageChoice.lower() == 'c':  # if user chose online/arcgis version
                                success = upload(self, "upload", system_id, datestr, timestr, barcode_data, "OUT",
                                                 str(time_check))

                            if success:
                                screen_label.text = screen_label.text + f"\n{barcode_data} checking OUT at " \
                                                                        f"{date_scanned} {time_scanned} at location: " \
                                                                        f"{system_id} for duration of {str(time_check)}"
                                playsound(pass_ding)  # makes a beeping sound on scan
                            elif local_passed and not success:
                                screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}Online logout " \
                                                                        f"unavailable at current time, continuing " \
                                                                        f"local logout\n{barcode_data} checking OUT " \
                                                                        f"at {date_scanned} {time_scanned} at " \
                                                                        f"location: {system_id} for duration of " \
                                                                        f"{str(time_check)}"
                                playsound(pass_ding)  # makes a beeping sound on scan
                            elif not local_passed and not success:
                                screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}{barcode_data} NOT " \
                                                                        f"checked OUT{BaseColors.ENDC}"
                                playsound(fail_ding)  # makes a slightly deeper beeping sound on failed scan out
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
                            del thread_started[
                                index_loc]  # has caused an error before, not sure why nor how to recreate

                        # Write updated found arrays to qr_data_file so that it is up to date with the latest scan ins
                        with open(qr_storage_file, "w") as qr_data_file:  # that file is used when restarting sessions
                            for i in range(len(found)):
                                code = found[i]
                                tyme = found_time[i]
                                status = found_status[i]
                                qr_data_file.write("{0},{1},{2}\n".format(code, tyme, status))
                    else:
                        screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}[Error] Barcode data issue in " \
                                                                f"video() function.{BaseColors.ENDC}"

                # If timer is active, check to see if any user has gone over the timer
                if self.timer is not None:
                    datetime_scanned = datetime.datetime.now()  # get current time
                    for i in range(len(found)):  # below: total time passed since user checked in
                        time_check = (datetime_scanned.hour * 60 + datetime_scanned.minute + datetime_scanned.second /
                                      60) - (found_time[i].hour * 60 + found_time[i].minute + found_time[i].second / 60)
                        if time_check > self.timer and thread_started[i] is not True:
                            # if they're beyond the timer limit
                            print(found[i])
                            threading.Thread(target=self.timer_alert, args=[found[i]],
                                             daemon=True).start()  # alert user
                            thread_started[i] = True
                            # mark this code/item/user as having an alert already run for them, so that it doesn't
                            # happen again
                # future: it should probably also not have the potential to trigger multiple threads/alerts/sounds
                # overlay

                if storageChoice.lower() == 'a' and local_file != "":
                    datetime_scanned = datetime.datetime.now()
                    time_check = (datetime_scanned.hour * 60 + datetime_scanned.minute + datetime_scanned.second /
                                  60) - (local_timer.hour * 60 + local_timer.minute + local_timer.second / 60)
                    if time_check > 5:
                        with open(local_file, "a", encoding="ANSI") as csv2:
                            for line in local_temp:
                                csv2.write(line)
                        local_timer = datetime_scanned
                        local_temp = []

                # show the output frame
                cv2.imshow("QR Toolbox", frame)
                cv2.waitKey(1)

                # if the user closes the window, close the window (lol)
                if cv2.getWindowProperty('QR Toolbox', cv2.WND_PROP_VISIBLE) < 1:
                    break

            # close the output CSV file and do a bit of cleanup
            screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}[ALERT] Cleaning up... \n{BaseColors.ENDC}"
            txt.close()
            if storageChoice.lower() == 'a' and local_file != "":
                with open(local_file, "a", encoding="ANSI") as csv2:
                    for line in local_temp:
                        csv2.write(line)

            if os.path.exists(qr_storage_file) and os.stat(qr_storage_file).st_size == 0:
                os.remove(qr_storage_file)  # if the file is empty, delete it
            checkStorage = False  # Reset the global variable that tells code to check the qr_storage_file
            uploadBackup = False
            # This part is necessary to show special characters properly on any of the local CSVs
            if os.path.exists(args["output"]) and os.stat(args["output"]).st_size != 0:
                barcodes_txt = open(args["output"], 'r', encoding="utf-8")
                new_csv = open(archive_folder + "/" + file_name, 'w', encoding="ANSI")

                data = barcodes_txt.read()
                new_csv.write(data)

                barcodes_txt.close()
                new_csv.close()
            elif not os.path.exists(args["output"]):
                data = f"\n{BaseColors.FAIL}[ERROR] barcodes.txt not found as expected.{BaseColors.ENDC}"
                screen_label.text = screen_label.text + data

            # if storageChoice == 'a' and os.stat(
            #         args["output"]).st_size != 0:
            #         # if local was chosen, also store barcodes file at the location given
            #     if os.path.exists(storagePath):  # check if file path exists
            #         with open(os.path.join(storagePath, file_name), "w", encoding="ANSI") as csv2:
            #             csv2.write(data)
            #     else:
            #         screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}[ALERT]: Storage folder not " \
            #                                                 f"established or is unavailable. {BaseColors.ENDC}" \
            #                                                 f"{BaseColors.WARNING}Files will only be saved to the " \
            #                                                 f"root/working directory\n{BaseColors.ENDC}"

            if os.path.exists(args["output"]) and os.stat(args["output"]).st_size == 0:  # delete barcodes.txt if empty
                os.remove(
                    args["output"])  # not removed until the end in case something goes wrong above and it's needed
            if vs is not None:
                vs.stop()  # reset and close everything related to the videostream
                vs.stream.release()
                vs = None

            cv2.destroyAllWindows()  # close all cv windows
        else:  # if user did not choose storage
            screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}Storage location not chosen, please " \
                                                    f"choose a storage location{BaseColors.ENDC}"
        self.ids.qrreader.disabled = False  # makes QR Reader btn enabled again

    """
    This function prepares the program and then runs the video() function to read QR Codes
        - The preparation involves setting up and starting the popup, and checking if a video stream already exists
        - It also runs the video stream on a different thread, so that the user can do 2 things at once with the program
    """

    def qr_reader(self):
        restart_session_popup = RestartSessionWidget()
        restart_session_popup.restart_popup = Popup(
            title="Do you want to start a new session or restart the previous one?\nNote: CSV files are not created "
                  "nor uploaded until after the QR Reader is closed.",
            content=restart_session_popup, size_hint=(None, None), size=(715, 183), auto_dismiss=True)

        global vs
        if vs is not None:
            # if vs already exists let user know (this code will likely never be run due to disabled btn)
            screen_label = self.ids.screen_label
            screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}[ALERT] A video stream already exists." \
                                                    f"{BaseColors.ENDC}"
            return

        restart_session_popup.restart_popup.open()
        restart_session_popup.main_screen = self

    """ 
        This function sends the scanned-in/out data to arcgis as a feature, along with the coordinates defined by the
        user in the settings.py file
        - If an error occurs, it lets the user know
    """

    def update_arcgis(self, sys_id, date_str, time_str, barcode_data, status, time_elapsed=None):
        screen_label = self.ids.screen_label
        try:
            search_results = self.gis.content.search(query=gis_query, max_items=15)
        except Exception as e:
            if e.__str__() == "Invalid token.\n(Error Code: 498)":
                self.gis._con.token = self.gis._con.relogin()
                search_results = self.gis.content.search(query=gis_query, max_items=15)  # query is set in the settings.csv file
            else:
                screen_label.text = screen_label.text + f"\n{e}"
                return False
        data = search_results[0]  # code auto chooses the first option on the list

        # Add data to layer
        feature_layers = data.layers
        layer = feature_layers[0]

        # Get the geo coordinates
        point = Point({"x": longitude, "y": latitude, "spatialReference": {"wkid": 4326}})  # other is 3857

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
            results = layer.edit_features(adds=[feature])  # add feature to the layer, get results
            # screen_label.text = screen_label.text + f"\n{results}"
            # this gives more info on the add if it was successful
        except Exception as e:  # if failed, print error to user and return False so not successful
            screen_label.text = screen_label.text + f"\nError: Couldn't create the feature: {str(e)}"
            return False

    """ 
    This function checks if storage path is set, calls it if not, otherwise/and then calls the qr_batch function 
    """

    def qr_batch(self):
        global storagePath
        if storagePath == "":
            storagePath = store(self)
        if storagePath != "":
            qr_batch(self)

    """ 
        This function creates a popup widget to prompt the user for text for the QR code, can be multi-line 
        It also first checks if storage path is set, and if not then it triggers the user to select that
    """

    def qr_single(self):
        global storagePath
        if storagePath == "":
            storagePath = store(self)  # set storage path if it hasn't been set already

        if storagePath != "":  # then ask user for the text for the new qr code
            qr_single_widget = QRSingleWidget()
            qr_single_widget.qr_single_popup = Popup(
                title="Enter text to generate a single QR Code and click OK. The resulting image will be saved in the "
                      "tool's origin folder, and selected storage location.", content=qr_single_widget,
                size_hint=(None, None), size=(327, 290), auto_dismiss=True)
            qr_single_widget.main_screen = self
            qr_single_widget.qr_single_popup.open()

    """ 
    This function shows the setup menu as a popup widget w/4 buttons 
    """

    def setup(self):
        setup_popup = SetupWidget()
        setup_popup.setup_popup = Popup(title="Choose an option", content=setup_popup, size_hint=(None, None),
                                        size=(251, 470),
                                        auto_dismiss=True)
        setup_popup.main_screen = self
        setup_popup.setup_popup.open()

    """ 
    This function provides more information on the purpose and development of this software 
    """

    def about(self):
        # displays the about screen
        text = "[u]QR Toolbox v1.6[/u]\n"
        text = text + "About: The QR Toolbox is a suite a tools for creating and reading QR codes. The toolbox is " \
                      "lightweight, open source, and written in Python and Kivy. This toolbox may be used to track " \
                      "resources, serve as a check-in capability for personnel, or customized to meet other " \
                      "operational needs. \n"
        text = text + "Version: 1.6 \n\n"
        text = text + "Credits: The QR Toolbox consists of a number of python packages, namely: \n qrcode - " \
                      "Lincoln Loop info@lincolnloop.com; \n pyzbar - Lawrence Hudson quicklizard@googlemail.com; \n " \
                      "OpenCV code - Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/; \n Sound effects " \
                      "obtained from https://www.zapsplat.com; \n Code integration, minor enhancements, & platform " \
                      "development - Timothy Boe boe.timothy@epa.gov, Muhammad Karimi karimi.muhammad@epa.gov, \nand " \
                      "Jordan Deagan deagan.jordan@epa.gov\n"
        text = text + "Contact: Timothy Boe: boe.timothy@epa.gov; or Paul Lemieux: lemieux.paul@epa.gov; USEPA " \
                      "Homeland Security Research Program \n"
        screen_label = self.ids.screen_label
        screen_label.text = text
        screen_label.font_size = 18
        screen_label.valign = 'middle'
        screen_label.halign = 'center'

        global clear_screen
        clear_screen = True

    """ 
    This function is triggered when a user goes over the time limit, and it triggers an alert popup and sound 
    """

    def timer_alert(self, user):
        timer_alert_widget = TimerAlertWidget()
        timer_alert_widget.timer_alert_widget_popup = Popup(title=f"ALERT: {user} has exceeded the time limit.",
                                                            content=timer_alert_widget, size_hint=(None, None),
                                                            size=(421, 135), auto_dismiss=False)
        timer_alert_widget.timer_alert_widget_popup.open()
        timer_alert_widget.main_screen = self

        # play the sound
        timer_alert_widget.not_acknowledged = True
        # this is set to True, so system knows user hasn't acknowledged the alert yet
        while timer_alert_widget.not_acknowledged:
            playsound(timer_alarm)  # a sound is then played at 800hertz frequency for 10sec
            time.sleep(20)  # it pauses for 20sec and then plays again continuously until user acknowledges
        # the sound can be cut off by other alerts, and potentially by other sounds, and any executions by thread will
        # continue on even after user axed the alert, if those executions occurred before the user axed. Only way to
        # stop this is to close the program
        return True

    """ 
    This function is triggered when the user clicks the Menu 'Exit' button 
    """

    def exit(self, *args):
        exit_widget = ExitWidget()
        exit_widget.exit_widget_popup = Popup(
            title="                             Are you sure you want to quit?\n(unsaved data, "
                  "such as from an open QR Reader, will be lost)", content=exit_widget, size_hint=(None, None),
            size=(417, 155), auto_dismiss=True)
        exit_widget.exit_widget_popup.open()
        return True


""" 
This class represents/is the widget that displays when you click the qr-reader function, asking if you want to restart 
a session or not 
"""


class RestartSessionWidget(BoxLayout):
    restart_popup = None  # necessary so kivy file can call the popup and dismiss it
    main_screen = None  # a reference to main screen so software can print to screen

    """ 
    This function Checks to see if there is any previous sessions and session data, and if there is it will pull 
    that back in
            @param check is to see if we should checkStorage or not
    """

    def set_check_storage(self, check, upload):
        screen_label = self.main_screen.ids.screen_label
        setup_screen_label(screen_label)
        if check:  # if user wants to check for previous session/session data
            global checkStorage
            checkStorage = True
            screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Previous session will be restarted, if " \
                                                    f"one exists.{BaseColors.ENDC}"
        if upload:
            global uploadBackup
            uploadBackup = True
            screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Local records will be uploaded to the " \
                                                    f"online session.{BaseColors.ENDC}"
        self.main_screen.ids.qrreader.disabled = True  # disables QR Reader btn so user can't start multiple streams
        threading.Thread(target=self.main_screen.video, daemon=True).start()  # starts video method on its own thread


""" 
This class represents the information displayed when you want to set the storage location (text and 2 buttons, 
local or online) 
"""


class StorageWidget(BoxLayout):
    text = "Do you want data stored online or locally? \nNote: Files are also saved in the QR-Toolbox " \
           "Archive folder regardless."
    storage_popup = None
    main_screen = None

    """ 
    This function sets the storage based on the users selection (local or online) 
    """

    def set_storage(self, storage):
        global storageChoice
        if storage == 'a':  # Local button was pressed
            global storagePath
            storageChoice = "a"
            storagePath = store(self.main_screen)
        else:  # online btn was pressed
            storageChoice = storage

            login_widget = LoginWidget()  # user must login for online storage
            # login_widget.login_popup = Popup(
            #     title="Enter your username and password", content=login_widget,
            #     size_hint=(None, None), size=(327, 290), auto_dismiss=False)
            login_widget.main_screen = self.main_screen
            # login_widget.login_popup.open()
            login_widget.sign_in()


""" 
This class represents the displayed when you select "Choose Camera Source" from the Setup menu, and is text with 3 
buttons 
"""


class CameraWidget(BoxLayout):
    text = "Which camera do you want to use?"
    camera_popup = None
    main_screen = None

    """
    This function asks the user what camera will be used to read QR Codes
    Only 3 options
        1. A - integrated/built-in webcam (the default)
        2. B - USB or connected webcam
        3. C - PiCamera (from Raspberry Pi) (DISABLED FOR NOW)
    """

    def set_camera(self, camera_choice):
        global cameraSource
        cameraSource = camera_choice  # set camera source based on user choice
        screen_label = self.main_screen.ids.screen_label
        setup_screen_label(screen_label)
        screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Camera source set to '{camera_choice}'." \
                                                f"{BaseColors.ENDC}"


class TimerWidget(BoxLayout):
    timer_popup = None
    main_screen = None

    """ 
    Sets the timer variable to the user defined value 
    """

    def set_timer(self, time_to_set):  # a time of 0min also counts as unsetting the timer
        if time_to_set != "" and time_to_set is not None and int(time_to_set) != 0:
            self.main_screen.timer = int(time_to_set)  # set the timer and print a message
            self.main_screen.ids.screen_label.text = self.main_screen.ids.screen_label.text + f"\n{BaseColors.WARNING}"\
                                                                                              f"Timer set to " \
                                                                                              f"{time_to_set} " \
                                                                                              f"minute(s)." \
                                                                                              f"{BaseColors.ENDC}"
        else:  # unset the timer
            self.main_screen.timer = None
            self.main_screen.ids.screen_label.text = self.main_screen.ids.screen_label.text + f"\n{BaseColors.WARNING}"\
                                                                                              f"Timer unset." \
                                                                                              f"{BaseColors.ENDC}"


""" 
This class represents the Timer Alert box that pops up when a user exceeds the timer, in order to alert the user 
"""


class TimerAlertWidget(BoxLayout):
    timer_alert_widget_popup = None
    main_screen = None
    not_acknowledged = False
    # used to check when main user has acknowledged that a given user has been checked in for too long

    """ 
    This function handles what happens after the user acknowledges that a user/item has exceeded the timer 
    """

    def alert_acknowledged(self):
        self.not_acknowledged = False
        # set this to False so that beeping stops (altho if any have alrdy been triggered this won't stop them)


""" 
This class represents the information displayed when you click the Setup menu 
"""


class SetupWidget(BoxLayout):
    setup_popup = None
    main_screen = None

    """ 
    Redirects program to either the consolidate() method or the upload_backup() method above, based on users choice 
    """

    def upload_consolidate(self):
        if storageChoice == 'a':  # if local mode, call cons() func, otherwise call upload_backup()
            cons(self.main_screen)
        else:
            upload_backup(self.main_screen, True)  # since it comes only from menu, send True

    """ 
    Creates and starts the popup for changing the storage location 
    """

    def change_storage_location(self):
        storage_location = StorageWidget()
        storage_location.storage_popup = Popup(title="Select a storage location", content=storage_location,
                                               size_hint=(None, None),
                                               size=(500, 400), auto_dismiss=True)
        storage_location.main_screen = self.main_screen
        storage_location.storage_popup.open()

    """  
    Creates and starts the popup for changing the camera source 
    """

    def change_camera_source(self):
        camera_location = CameraWidget()
        camera_location.camera_popup = Popup(title="Which camera do you want to use?", content=camera_location,
                                             size_hint=(None, None),
                                             size=(261, 375), auto_dismiss=True)
        camera_location.main_screen = self.main_screen
        camera_location.camera_popup.open()

    """ 
    Creates and starts the popup for setting a timer for how long users can be checked in 
    """

    def set_timer_popup(self):
        timer_widget = TimerWidget()
        timer_widget.timer_popup = Popup(
            title=" Enter the time (in minutes) for the timer.", content=timer_widget,
            size_hint=(None, None), size=(327, 210), auto_dismiss=True)
        timer_widget.main_screen = self.main_screen
        timer_widget.timer_popup.open()


""" 
This class represents the information shown when the qr_single button is pressed, has text, an input box, and 2 buttons 
"""


class QRSingleWidget(BoxLayout):
    qr_single_popup = None
    main_screen = None

    """ 
    Calls the qr_single function with the text the user entered, or warning if no text 
    """

    def setup_qr_single(self, text):
        if text != "" and text is not None:
            qr_single(self.main_screen, text)
        else:
            self.main_screen.ids.screen_label.text = self.main_screen.ids.screen_label.text + f"\n{BaseColors.WARNING}"\
                                                                                              f"QR Code text can't be "\
                                                                                              f"empty.{BaseColors.ENDC}"


""" 
This class represents the information shown when the online button is pressed and a username/password is requested, 
has text, an input box, and 2 buttons 
"""


class LoginWidget(BoxLayout):
    login_popup = None
    main_screen = None

    """ 
    Calls the sign in function with the text the user entered 
    """

    def sign_in(self):
        global user_chose_storage, storageChoice, sql_cursor, sql_address, sql_database, arcgis_url, gis_query
        screen_label = self.main_screen.ids.screen_label
        setup_screen_label(screen_label)
        if storageChoice == "b":
            try:
                self.main_screen.gis = GIS(arcgis_url, client_id='vpeanPqMcHdq7G6z')  # Get ArcGIS access and save it
                search_results = self.main_screen.gis.content.search(query=gis_query, max_items=15)

                # check that query works and there's a layer to get
                # print(search_results)
                data = search_results[0]  # Get the layer we'll be using, so user can see it

                screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Storage location set to online (ArcGIS)." \
                                                        f"{BaseColors.ENDC}"  # if successful
                screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Layer: {data.title}{BaseColors.ENDC}"
                # provides more info on the exact layer chosen
                user_chose_storage = True
            except Exception as e:  # if error in trying to access ArcGIS or run the query
                # e = sys.exc_info()[0]  # used for error checking
                if e.__str__() == "Invalid token.\n(Error Code: 498)":
                    try:
                        self.main_screen.gis._con.token = self.main_screen.gis._con.relogin()
                        search_results = self.main_screen.gis.content.search(query=gis_query,
                                                                             max_items=15)  # query is set in the settings.csv file
                        data = search_results[0]  # Get the layer we'll be using, so user can see it

                        screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Storage location set to online (ArcGIS)." \
                                                                f"{BaseColors.ENDC}"  # if successful
                        screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Layer: {data.title}{BaseColors.ENDC}"
                        # provides more info on the exact layer chosen
                        user_chose_storage = True
                    except Exception as e:
                        screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Error: {e}{BaseColors.ENDC}"
                        user_chose_storage = False
                else:
                    screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Error: {e}{BaseColors.ENDC}"
                    user_chose_storage = False
            except:  # in case the above except clause doesn't catch everything
                screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}An unknown error has occurred.{BaseColors.ENDC}"
                user_chose_storage = False
        elif storageChoice == "c":
            try:
                cxnn = pyodbc.connect(driver='{ODBC Driver 17 for SQL Server}', server=sql_address,
                                      database=sql_database, trusted_connection='yes')
                sql_cursor = cxnn.cursor()

                screen_label.text = screen_label.text + f"\n{BaseColors.OKBLUE}Storage location set to online (SQL)." \
                                                        f"{BaseColors.ENDC}"  # if successful
                user_chose_storage = True
            except Exception as e:  # if error in trying to access ArcGIS or run the query
                # e = sys.exc_info()[0]  # used for error checking
                screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}Error: {e}{BaseColors.ENDC}"
                user_chose_storage = False
            except:  # in case the above except clause doesn't catch everything
                screen_label.text = screen_label.text + f"\n{BaseColors.FAIL}An unknown error has occurred.{BaseColors.ENDC}"
                user_chose_storage = False

    """ 
    This function is called if the user clicks cancel, so user knows no storage is set currently 
    """

    def storage_not_chosen(self):
        global user_chose_storage
        user_chose_storage = False  # no storage has been chosen
        screen_label = self.main_screen.ids.screen_label
        setup_screen_label(screen_label)

        screen_label.text = screen_label.text + f"\n{BaseColors.WARNING}Online storage not set.{BaseColors.ENDC}"


""" 
This class represents the Exit alert box that pops up when you click the 'Exit' button, confirming that you want to exit
"""


class ExitWidget(BoxLayout):
    exit_widget_popup = None

    """ 
    This function closes the program if the user clicked 'Yes' when asked 
    """

    def confirm_exit(self):
        self.get_root_window().close()
        App.get_running_app().stop()


""" 
This class represents the app itself, and everything starts from and runs from this 
"""


class QRToolboxApp(App):
    main_screen = None

    """ 
    Builds the QRToolboxApp instance by instantiating the MainScreenWidget and returning that as the Main Widget 
    for the app 
    """

    def build(self):
        self.main_screen = MainScreenWidget()
        Window.size = (900, 650)  # starting size for the qr tool
        return self.main_screen

    """ 
    This function runs the storage selection popup at the start of the App, and sets some global vars 
    """

    def on_start(self):
        global clear_screen, not_yet, arcgis_url, gis_query, latitude, longitude, localQRBatchFile, settings, \
            sql_address, headers, sql_database, query_in, query_out
        with open(settings, 'r', encoding='utf-8') as set_file:
            reader = csv.reader(set_file)
            reader.__next__()
            values = reader.__next__()
            arcgis_url = values[0]
            gis_query = values[1]
            latitude = values[2]
            longitude = values[3]
            localQRBatchFile = values[4]
            sql_address = values[5]
            sql_database = values[6]
            headers = values[7:]
            query_in = """
            INSERT INTO %s (%s, %s, %s, %s)
            VALUES (?, ?, ?, 'IN');
            """ % (headers[0],headers[1],headers[2],headers[3],headers[4])
            query_out = """
            INSERT INTO %s (%s, %s, %s, %s, %s)
            VALUES (?, ?, ?, 'OUT', ?);
            """ % (headers[0],headers[1],headers[2],headers[3],headers[4],headers[5])

        storage_location = StorageWidget()
        storage_location.storage_popup = Popup(title="Select a storage location", content=storage_location,
                                               size_hint=(None, None),
                                               size=(500, 400), auto_dismiss=False)
        storage_location.main_screen = self.main_screen
        clear_screen = True  # used in/with setup_screen_label()
        not_yet = True
        storage_location.storage_popup.open()


if __name__ == '__main__':
    QRToolboxApp().run()  # runs and starts the whole program
