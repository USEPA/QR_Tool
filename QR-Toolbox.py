# -*- coding: windows-1252 -*-
"""
Name: QR Toolbox v1.3
Description: The QR Toolbox is a suite a tools for creating and reading QR codes. See the About screen for more
information
Author(s): Code integration, minor enhancements, & platform development - Timothy Boe boe.timothy@epa.gov; Muhammad Karimi karimi.muhammad@epa.gov
    qrcode - Lincoln Loop info@lincolnloop.com; pyzbar - Lawrence Hudson quicklizard@googlemail.com;
    OpenCV code - Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/;
Contact: Timothy Boe boe.timothy@epa.gov
Requirements: Python 3.7+, pyzbar, imutils, opencv-python, qrcode[pil], Pillow, Office365-REST-Python-Client, Kivy, kivy-deps.angle,
kivy-deps.glew, kivy-deps.gstreamer, kivy-deps.sdl2, Kivy-Garden

Specific versions:
{"pyzbar": "0.1.8", "imutils": "0.5.3", "qrcode": "6.1", "Pillow": "7.0.0", "opencv-python": "4.2.0.32",
"Office365-REST-Python-Client": "2.2.1", "Kivy": "1.11.1", "kivy-deps.angle": "0.2.0", "kivy-deps.glew": "0.2.0",
"kivy-deps.gstreamer": "0.2.0", "kivy-deps.sdl2": "0.2.0", "Kivy-Garden": "0.1.4"}
"""

# import the necessary packages
import argparse
import csv
import datetime
import os
import os.path
import shutil
import time
import winsound
from datetime import timedelta
from time import strftime
from tkinter import *
from tkinter import filedialog


# colors


class bcolors:
    HEADER = ''
    OKBLUE = '[color=#009999]'
    OKGREEN = '[color=#66cc00]'
    WARNING = '[color=#e3e129]'
    FAIL = '[color=#a72618]'
    ENDC = '[/color]'
    BOLD = ''
    UNDERLINE = ''


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
from office365.sharepoint.files.file import File
from office365.sharepoint.files.file_creation_information import FileCreationInformation
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol

import threading
from kivy.app import App

from Setup.settings import settings

# Sharepoint related variables
listTitle = settings['listTitle']
qrfolder = settings['qrfolder']
bkcsvfolder = settings['bkcsvfolder']
mainDirectory = settings['mainDirectory']
remoteQRBatchFile = "System_Data/names-remote.csv"
localQRBatchFile = settings['localQRBatchFile']
relative_url = settings['relative_url']
qr_storage_file = "System_Data/qr-data.txt"  # file that contains saved session information
backup_file = "System_Data/backup.txt"  # file that contains data that couldn't be uploaded, to later be uploaded
archive_folder = "Archive"

context_auth = AuthenticationContext(url=settings['url'])
context_auth.acquire_token_for_app(client_id=settings['client_id'], client_secret=settings['client_secret'])
ctx = ClientContext(settings['url'], context_auth)

# load variables
# set store folder default, assign system ID, and wait time
storagePath = ""
checkStorage = False  # whether system should check if there is any backed up data or previous session data
user_chose_storage = False
not_done = True
system_id = os.environ['COMPUTERNAME']
t_value = timedelta(seconds=10)
cameraSource = "Integrated"
storageChoice = ""
special_char_bool = True
vs = None  # global video stream variable, to ensure only 1 instance of it exists at a time
clear_screen = False  # if True, clear screen, else don't clear it (true only in 4 cases)
not_yet = False  # prevents the screen from being cleared immediately at the start (only used at the start)

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


def convert(main_screen, data_to_convert, character_list, conversion_dict, is_for_file_name=False, is_for_trouble=False):
    old_data = data_to_convert
    screen_label = main_screen.ids.screen_label
    setup_screen_label(screen_label)

    for char in character_list:
        if char in data_to_convert:
            data_to_convert = data_to_convert.replace(char, conversion_dict[char]) if not is_for_file_name else data_to_convert.replace(char, "-") \
                if not is_for_trouble else data_to_convert.replace(char, " ")
    if old_data != data_to_convert and is_for_file_name and is_for_trouble is not True:
        screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Error saving file with name {old_data}, saved as {data_to_convert} instead.{bcolors.ENDC}"
    return data_to_convert


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


def connect(main_screen, context, connection_type, content=None, file_name=None, location=None, duplicate=False):
    screen_label = main_screen.ids.screen_label
    setup_screen_label(screen_label)
    i = 0
    while i < 3:
        try:
            return_val = True
            if connection_type == 'upload':  # if a file needs to be uploaded
                upload_file(ctx, content, file_name, location)
            elif connection_type == 'execute_query':  # if list item needs to be created and added
                context.execute_query()
            elif connection_type == 'qr_batch':  # if a file from the SharePoint needs to be retrieved (names.csv)
                return_val = File.open_binary(context, relative_url)
            else:
                screen_label.text = screen_label.text + f"\n{bcolors.WARNING}Invalid connection type.{bcolors.ENDC}"
                return_val = False
            if i > 0:
                screen_label.text = screen_label.text + f"\n{bcolors.OKGREEN}Connection successful.{bcolors.ENDC}"
            return return_val
        except:
            # e = sys.exc_info()[0]  # used for error checking
            # print(e)
            if i == 0:
                screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Connection lost. Trying again in 10 seconds.{bcolors.ENDC}"
                time.sleep(10)
            elif i == 1:
                screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Reconnect failed. Trying again in 30 seconds.{bcolors.ENDC}"
                time.sleep(30)
            elif i > 1 and not duplicate and connection_type != 'qr_batch':  # if failed thrice, write to backup.txt
                screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Reconnect failed again.{bcolors.ENDC}{bcolors.OKBLUE} Data will be stored locally and " \
                      f"uploaded at the next upload point, or if triggered from the menu.{bcolors.ENDC}"
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
                screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Reconnect failed again.{bcolors.OKBLUE} Try again when you have " \
                      f"internet connection.{bcolors.ENDC}{bcolors.ENDC}"
                return False
        i += 1


"""
This function uploads the data that was stored/backed up in the backup.txt file

@param context the URL/HTTP request information for uploading
@param from_menu True if this method was triggered/called from the main menu, False otherwise

@return True if re-upload was successful, False otherwise (or if there was no data to upload)
"""


def upload_backup(context, main_screen_widget, from_menu=False):
    screen_label = main_screen_widget.ids.screen_label
    setup_screen_label(screen_label)
    if os.path.exists(backup_file):  # check if file exists, if not then return
        with open(backup_file, "r") as backup:
            screen_label.text = screen_label.text + "\nUploading backed up data..."
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
                        successful = create_list_item(main_screen_widget, context, content, True)
                    else:  # means it was a file to be uploaded
                        successful = connect(main_screen_widget, context, 'upload', content, file_name, location, True)
                    if not successful:
                        screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Upload of backed up data failed.{bcolors.ENDC}{bcolors.OKBLUE} Program will " \
                                                        f"try again at next upload, or you can trigger upload manually from the menu.{bcolors.ENDC}"
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
            screen_label.text = screen_label.text + f"\n{bcolors.OKGREEN}Upload complete!{bcolors.ENDC}"
        os.remove(backup_file)  # file removed if upload is successful
    elif from_menu:
        screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}No backed-up data to upload.{bcolors.ENDC}"


"""
This function Creates a list item, used with the SharePoint site and the Office365-REST-Python-Client
@param context the context of the site that is being communicated with/uploaded to
@param content the content to add as a list item
"""


def create_list_item(main_screen, context, content, duplicate=False):
    screen_label = main_screen.ids.screen_label
    setup_screen_label(screen_label)

    screen_label.text = screen_label.text + "\nCreating list item example..."
    list_object = context.web.lists.get_by_title(listTitle)
    values = content.split(",")
    sid = values[0]
    tstr = values[1]
    barstr = values[2]
    status = values[3]

    item_properties = {'__metadata': {'type': 'SP.Data.QR_x0020_TimestampsListItem'}, 'Title': barstr,
                       'QR_x0020_Terminal': sid, 'Time_x0020_Stamp': tstr, 'Info': status}
    item = list_object.add_item(item_properties)
    succeed = connect(main_screen, context, 'execute_query', content, duplicate=duplicate)
    if succeed:
        screen_label.text = screen_label.text + "\nList item '{0}' has been created.".format(item.properties["Title"])
    else:
        screen_label.text = screen_label.text + f"\n{bcolors.WARNING}List item '{item.properties['Title']}' has NOT been created.{bcolors.ENDC}"
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
    library = context.web.lists.get_by_title(mainDirectory)

    file_context = library.context
    info = FileCreationInformation()
    info.content = file_content
    info.url = filename
    info.overwrite = True

    # upload file to sub folder as defined by 'sub_folder', this value is generally either variable qrfolder or bkcsvfolder as defined above
    target_file = library.rootFolder.folders.get_by_url(sub_folder).files.add(info)
    file_context.execute_query()

    return target_file


"""
This function creates QR codes in batches from a CSV file (defined in the global variables)
    -The function always checks and performs the QR code creation in its root folder first, and the generated codes
    are then stored in the Archive folder.
    -If the local choice was chosen, the codes are also stored in the location entered by the user
    -If the online/SharePoint choice was chosen, the function then also reads a CSV file (defined in global variables) 
    on the SharePoint site and generates QR Codes from that, which are stored in the same location as that CSV file
"""


def qr_batch(main_screen_widget):
    screen_label = main_screen_widget.ids.screen_label
    setup_screen_label(screen_label)
    screen_label.text = screen_label.text + "\n\nThe batch QR code function is used to quickly create multiple QR codes by referencing a .csv file." \
          "\n-If QR Toolbox is in local mode, the CSV file must be stored in the root folder of the program (where it was installed), and named 'names.csv'." \
          "\n    The Tool will then automatically create QR codes for each line in the csv, and save each QR Code image to the Tools root folder" \
          "\n    (this folder is usually called 'QR-Toolbox', and should be found in C:/Users/<user>/AppData/Local/Programs). Where <user> refers" \
          "\n    to your user name on your computer. However, if you changed the install location, it may not be at that file path." \
          "\n-If QR Toolbox is in online mode, the csv file must be stored on the SharePoint site where QR codes are" \
          "\n    located, and must also be named 'names.csv'. The Tool will then do the same as above, but will also store each" \
          "\n    QR code image to the SharePoint site." \
          "\n-'names.csv' may consist of two columns 'first' & 'second'. The 'first' and 'second' columns could be " \
          "\n    populated with participant's first and last names, or other information, and will be joined together with a space in between.\n"

    # this code creates a batch of QR codes from a csv file stored in the local directory
    # QR code image size and input filename can be modified below

    success = True
    # This one creates the batch of QR codes in the chosen folder as well as the Archive folder
    if storageChoice == 'a':
        with open(localQRBatchFile) as csvfile:
            reader = csv.reader(csvfile)

            for row in reader:
                labeldata = row[0] if len(row) == 1 else row[0] + " " + row[1] if row[1] != '' else row[0]

                # convert special char to code character
                codeLabelData = convert(main_screen_widget, labeldata, special_characters, char_dict_special_to_code)

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4)

                qr.add_data(codeLabelData)
                qr.make(fit=True)
                screen_label.text = screen_label.text + "\nCreating QR code: " + labeldata

                # draw QR image

                img = qr.make_image()
                qrFile = labeldata + ".jpg"
                qrFile = convert(main_screen_widget, qrFile, bad_file_name_list, None, True)  # remove special chars that can't be in filename
                img.save(archive_folder + "/" + qrFile)

                # open QR image and add qr data as name
                img = Image.open(archive_folder + "/" + qrFile)
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype("arial", 24)
                color = 0
                draw.text((37, 10), labeldata, font=font, fill=color)
                img.save(archive_folder + "/" + qrFile)
                if storageChoice == 'a':
                    try:
                        img.save(storagePath + "/" + qrFile)
                    except:
                        success = False
    elif storageChoice == 'b':  # For storing the new QR Codes online, if that was selected
        resp = connect(main_screen_widget, ctx, 'qr_batch')  # runs the retrieval of the csv file from SharePoint through connect()

        if type(resp) == bool:  # if a boolean value is returned, then the retrieval failed
            return False
        elif resp.status_code == 404:
            screen_label.text = screen_label.text + f"\n\n{bcolors.FAIL}The batch file '" + relative_url + "' doesn't exist. " \
                f"Please create a CSV file with the appropriate name and add it to the SharePoint site with the correct file path.{bcolors.ENDC}"
            return False

        with open(remoteQRBatchFile, 'wb') as output_file:
            output_file.write(resp.content)

        with open(remoteQRBatchFile) as csvfile:
            reader = csv.reader(csvfile)

            for row in reader:  # get each row from the CSV file
                labeldata = row[0] if len(row) == 1 else row[0] + " " + row[1] if row[1] != '' else row[0]
                # above: gets data from 1 row or 2 rows depending on what is in each

                # Check for special char
                if special_char_bool is False:
                    skip_label = False
                    for special_char in special_characters:
                        if special_char in labeldata:
                            skip_label = True
                    if skip_label:
                        screen_label.text = screen_label.text + "\nQR Code was skipped due to special character."
                        return

                # convert special char to code character
                codeLabelData = convert(main_screen_widget, labeldata, special_characters, char_dict_special_to_code)

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4)

                qr.add_data(codeLabelData)
                qr.make(fit=True)
                screen_label.text = screen_label.text + "\nCreating QR code: " + labeldata

                # draw QR image

                img = qr.make_image()
                qrfile = labeldata + ".jpg"
                qrfile = convert(main_screen_widget, qrfile, bad_file_name_list, None, True)  # convert chars that can't be in filename
                img.save(archive_folder + "/" + qrfile)

                # open QR image and add qr data as name

                img = Image.open(archive_folder + "/" + qrfile)
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype("arial", 18)
                color = 0
                draw.text((37, 10), labeldata, font=font, fill=color)
                img.save(archive_folder + "/" + qrfile)

                with open(archive_folder + "/" + qrfile, 'rb') as content_file:  # upload file
                    file_content = content_file.read()
                success = connect(main_screen_widget, ctx, 'upload', file_content, qrfile, qrfolder)

        os.remove(remoteQRBatchFile)

    if success:
        screen_label.text = screen_label.text + f"\n\n{bcolors.OKGREEN}Success!{bcolors.ENDC}\n"
        if storageChoice == 'b':  # if the other upload was successful, also try to upload the backed-up data
            upload_backup(ctx, main_screen_widget)
    else:
        screen_label.text = screen_label.text + f"\n{bcolors.FAIL}Some or no files were saved in {storagePath}, only in Archive folder.{bcolors.ENDC}" if \
            storageChoice == 'a' else screen_label.text + f"\n{bcolors.WARNING}Some or no files were saved in {storagePath}, only in Archive folder.{bcolors.ENDC}"



"""
This function creates a single QR code based on the text inserted by the user, which is then stored in the Archive folder.
    - If user chose the local option, the QR code is also stored in the location entered by the user
    - If user chose the online SharePoint option, the QR code is stored on the SharePoint site
"""


def qr_single(main_screen_widget, text):
    screen_label = main_screen_widget.ids.screen_label
    setup_screen_label(screen_label)

    if storageChoice == 'b' and special_char_bool is False:
        skip_label = False
        for special_char in special_characters:
            if special_char in text:
                skip_label = True
        if skip_label:
            screen_label.text = screen_label.text + "\nQR Code was skipped due to special character."
            return

    text_copy = text
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
    fileName = text + ".jpg"
    fileName = convert(main_screen_widget, fileName, bad_file_name_list, None, True)  # convert chars that can't be in a file name
    img.save(archive_folder + "/" + fileName)

    # Open QR image and add QR data as name
    img = Image.open(archive_folder + "/" + fileName)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial", 24)
    color = 0
    draw.text((37, 10), text, font=font, fill=color)
    img.save(archive_folder + "/" + fileName)

    succeed = True
    # Store QR code locally, if that was chosen
    if storageChoice == 'a':
        try:
            img.save(storagePath + "/" + fileName)
        except:
            succeed = False
    elif storageChoice == 'b':  # Store QR code online, if chosen
        # upload file
        with open(archive_folder + "/" + fileName, 'rb') as content_file:
            file_content = content_file.read()
        succeed = connect(main_screen_widget, ctx, 'upload', file_content, fileName, qrfolder)

    if succeed:
        screen_label.text = screen_label.text + f"\n{bcolors.OKGREEN}Success!{bcolors.ENDC}"
        if storageChoice == 'b':
            upload_backup(ctx, main_screen_widget)  # if the other upload was successful, also try to upload the backed-up data
    else:
        screen_label.text = screen_label.text + f"\n{bcolors.FAIL}File not saved in {storagePath}, only in Archive folder.{bcolors.ENDC}" if \
            storageChoice == 'a' else screen_label.text + f"\n{bcolors.WARNING}Successful locally, not online.{bcolors.ENDC}"


"""
This function consolidates QR csv results into a single file. This function looks for files with QRT in the first part 
of their name. If true, all csvs within the shared folder directory that also fit this condition. A number of error
checks are built in to prevent bad things from happening
"""


def cons(main_screen_widget):
    screen_label = main_screen_widget.ids.screen_label
    setup_screen_label(screen_label)

    time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    cons_filename = os.path.join(storagePath, 'Consolidated_Record_' + time_header + '.csv')
    if os.path.exists(storagePath):
        QRT_files = [fn for fn in os.listdir(storagePath) if fn.startswith('QRT-R-') and fn.endswith('.csv') and fn.__contains__("_")]

        if not QRT_files:
            screen_label.text = screen_label.text + "\nNo entries to combine. Check the storage directory and try again"
        else:
            try:
                with open(cons_filename, 'wb') as outfile:
                    for i, fname in enumerate(QRT_files):
                        fname = os.path.join(storagePath, fname)
                        with open(fname, 'rb') as infile:
                            shutil.copyfileobj(infile, outfile)
                            screen_label.text = screen_label.text + f"\n{fname} has been imported."
                screen_label.text = screen_label.text + f"\n{bcolors.OKGREEN}\nConsolidated file created in the specified shared drive under " \
                                                        f"the filename " + cons_filename + f"{bcolors.ENDC}\n"
            except:
                screen_label.text = screen_label.text + f"\n{bcolors.WARNING}[WARNING] Either the system was unable to write the consolidated file " \
                                                        f"to the specified shared directory or the file " + cons_filename + " is currently in use " \
                                                        f"or unavailable. The consolidated record may be incomplete.{bcolors.ENDC}\n"
    else:
        screen_label.text = screen_label.text + f"\n{bcolors.WARNING}A storage location has not been established. Specify a storage folder using the " \
              f"'Choose Storage Location' option before continuing\n{bcolors.ENDC}"
        pass


# GUI PART OF PROGRAM STARTS HERE
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window


"""
This function allows the user to select a shared folder. If user escapes, a share folder is not created
    - Note: the Tkinter code can be finicky when displayed in IDE i.e., the file window will not show when operated in
    IDE while the root.withdraw command is turned on. Commenting out the root.withdraw command will fix, but root
    window remains; destroy() can be used to remove this. May need to search for a better solution in the future
"""


def store(main_screen):
    screen_label = main_screen.ids.screen_label
    setup_screen_label(screen_label)

    root = Tk()
    root.title('Storage Directory')
    root.withdraw()
    store_path = filedialog.askdirectory(title='Select a Network Storage Directory')
    if os.path.exists(store_path):
        screen_label.text = screen_label.text + f"\n{bcolors.OKGREEN}Storage directory established: {store_path}{bcolors.ENDC}"
    else:
        screen_label.text = screen_label.text + f"\n{bcolors.WARNING}Storage directory NOT established{bcolors.ENDC}"
    return store_path


"""
This method allows the home screen and one command along with it, but when any other command is pressed it formats the screen
 - Formatted to the left and removing whatever was already there
 @param screen_label the reference to the scrollable label on the screen that text is put on
"""


def setup_screen_label(screen_label):
    global clear_screen, not_yet

    if clear_screen and not not_yet:
        screen_label.text = ""
        clear_screen = False

    if not not_yet:
        screen_label.halign = 'left'
    not_yet = False


"""
This class is the main class for the GUI, it is the main screen within which all other screens/widgets/buttons are located in
"""


class MainScreenWidget(BoxLayout):
    sys_id = os.environ["COMPUTERNAME"]

    def __init__(self, **kwargs):
        super(MainScreenWidget, self).__init__(**kwargs)
        Window.bind(on_request_close=self.exit)

    """
    This function starts a VideoStream, and captures any QR Codes it sees (in a certain distance)
    Those codes are decoded, and written to a local CSV file along with the Computer Name, date, time, and IN/OUT
        -If local was chosen, the CSV file is also saved at the location entered by the user
        -If online was chosen, the CSV file is also saved on the SharePoint site
    """

    def video(self):
        global not_done, user_chose_storage, vs

        while not_done:
            pass

        screen_label = self.ids.screen_label
        setup_screen_label(screen_label)

        screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}[ALERT] Starting video stream...{bcolors.ENDC}\n"
        screen_label.text = screen_label.text + f"{bcolors.OKBLUE}To exit, click on the webcam window and press 'Q'{bcolors.ENDC}"

        if user_chose_storage:
            # construct the argument parser and parse the arguments
            ap = argparse.ArgumentParser()
            ap.add_argument("-o", "--output", type=str, default="System_Data/barcodes.txt",
                            help="path to output CSV file containing barcodes")
            args = vars(ap.parse_args())
            # initialize time and date and make filename friendly
            time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
            file_name = "QRT-R-" + system_id + "_" + time_header + ".csv"

            # initialize the video stream and allow the camera sensor to warm up

            if cameraSource == 'Integrated':  # start correct camera based on user choice at beginning
                vs = VideoStream(src=0).start()  # for integrated/built in webcam
            elif cameraSource == 'Separate':
                vs = VideoStream(src=1).start()  # for separate webcam (usually USB connected)
            elif cameraSource == 'PiCamera':
                vs = VideoStream(usePiCamera=True).start()  # for mobile solution like Raspberry Pi Camera
            else:
                screen_label.text = screen_label.text + f"\n{bcolors.FAIL}An error has occurred.{bcolors.ENDC}"
                return

            time.sleep(5.0)  # give camera time

            # open the output txt file for writing and initialize the set of barcodes found thus far
            global checkStorage
            contentStrings = ""  # used to contain data recorded from qr codes, to save in files
            if os.path.isfile(args["output"]) and checkStorage:  # check if user wanted to restart prev session
                if storageChoice.lower() == 'b':  # do this only if QR Toolbox is in online-mode
                    # Write previous records back to contentStrings
                    with open(args["output"], "r") as txt:
                        screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}Restoring records...{bcolors.ENDC}"
                        for line in txt:  # get each record from the file by line
                            if line == '\n': continue  # if line is newline only then skip it
                            line_array = line.split(",")
                            last_system_id = line_array[0]
                            file_date = datetime.datetime.strptime(line_array[1], "%m/%d/%Y").date()  # get date from file
                            file_time = datetime.datetime.strptime(line_array[2], "%H:%M:%S.%f").time()  # get time from file
                            print(file_date, file_time)

                            barcodeDataSpecial = line_array[3]  # get the QR Code from the file
                            status = line_array[4]  # get the status from the file
                            if "OUT" in status:  # if the status is OUT, also get the QRCodes' duration from the file
                                duration = line_array[5][:len(line_array[5]) - 1:]  # also remove newline char
                            else:
                                status = status[:len(status) - 1]  # else just remove the newline char from the status

                            # Convert barcodeDataSpecial's special chars to regular chars
                            barcodeDataReg = convert(self, barcodeDataSpecial, special_characters, char_dict_special_to_reg)

                            if status == "IN":  # if status is IN, use 5 params
                                contentstr = "{},{},{},{},{}\n".format(last_system_id, file_date, file_time,
                                                                    barcodeDataReg, status)  # for online CSV file
                                contentstr2 = '{},{},{},{},{}\n'.format(last_system_id, file_date, file_time,
                                                                     barcodeDataSpecial, status)  # for list item
                            else:  # if status is OUT, use 6 params
                                contentstr = "{},{},{},{},{},{}\n".format(last_system_id, file_date, file_time, barcodeDataReg,
                                                                       status, duration)  # for online CSV file
                                contentstr2 = '{},{},{},{},{},{}\n'.format(last_system_id, file_date, file_time,
                                                                        barcodeDataSpecial, status, duration)  # for list item
                            create_list_item(self, ctx, contentstr2)
                            contentStrings = contentStrings + contentstr

                txt = open(args["output"], "a", encoding="utf-8")  # reopen txt file for appending (to continue records)
                screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}Previous records restored.{bcolors.ENDC}"
            else:
                txt = open(args["output"], "w", encoding="utf-8")  # else open new file/overwrite previous
                if checkStorage:
                    screen_label.text = screen_label.text + f"\n{bcolors.WARNING}No previous records found. CSV file will not include " \
                                                            f"past records.{bcolors.ENDC}"

            # time track variables. These are used to keep track of QR codes as they enter the screen
            found = []
            found_time = []
            found_status = []

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
                        screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}Previous session restarted.{bcolors.ENDC}"
                else:
                    screen_label.text = screen_label.text + f"\n{bcolors.WARNING}No previous session found [qr-data.txt not found].{bcolors.ENDC}"

            # loop over the frames from the video stream
            while True:
                # grab the frame from the threaded video stream and resize it to have a maximum width of 400 pixels
                frame = vs.read()
                frame = imutils.resize(frame, width=400)

                # find the barcodes in the frame and decode each of the barcodes
                barcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.QRCODE])
                datestr = strftime("%m/%d/%Y")
                timestr = datetime.datetime.now().strftime("%H:%M:%S.%f")

                # loop over the detected barcodes
                for barcode in barcodes:
                    # extract the bounding box location of the barcode and draw the bounding box surrounding the barcode on the image
                    (x, y, w, h) = barcode.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                    # the barcode data is a bytes object so if we want to draw it on our output image we need to convert it to a string first
                    barcodeData = barcode.data.decode("utf-8")
                    barcodeType = barcode.type

                    # Convert barcodeData code chars back to special chars
                    barcodeData = convert(self, barcodeData, code_characters, char_dict_code_to_special)

                    # Draw the barcode data and barcode type on the image
                    img = Image.new('RGB', (400, 15), color='white')
                    img.putalpha(0)
                    d = ImageDraw.Draw(img)
                    textToPrint = convert(self, barcodeData, trouble_characters, None, True, True)  # replace \t,\n,\r with ' '
                    try:
                        d.text((0, 0), textToPrint + ' (' + barcodeType + ')', fill='blue')
                    except UnicodeEncodeError:
                        screen_label.text = screen_label.text + f"\n{bcolors.FAIL}[ERROR] Can't use QR Codes not generated by the system.{bcolors.ENDC}"
                        continue

                    pil_image = Image.fromarray(frame)
                    pil_image.paste(img, box=(x, y - 15), mask=img)
                    frame = np.array(pil_image)

                    # if the barcode text is currently not in our CSV file, write the timestamp + barcode to disk and update the set
                    # of barcode data has never been seen, check the user in and record id, date, and time information
                    if barcodeData not in found:
                        datetime_scanned = datetime.datetime.now()  # this one appended to found_time arr
                        date_scanned = datetime.datetime.now().strftime("%m/%d/%Y")  # this one prints to csv
                        time_scanned = datetime.datetime.now().strftime("%H:%M:%S.%f")  # this one prints to csv
                        txt.write("{},{},{},{},{}\n".format(system_id, date_scanned, time_scanned,
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
                            barcodeDataNew = convert(self, barcodeData, special_characters, char_dict_special_to_reg)

                            contentstr = "{},{},{},{},{}\n".format(system_id, datestr, timestr, barcodeDataNew, "IN")  # for online CSV file
                            contentstr2 = '{},{},{},{},{}\n'.format(system_id, datestr, timestr, barcodeData, "IN")  # for list item
                            checked_in = create_list_item(self, ctx, contentstr2)
                            contentStrings = contentStrings + contentstr

                        winsound.Beep(500, 400)  # makes a beeping sound on scan in
                        if checked_in:
                            screen_label.text = screen_label.text + f"\n{barcodeData} checking IN at {str(datetime_scanned)} at location: {system_id}"

                    # if barcode information is found...
                    elif barcodeData in found:
                        # get current time and also total time passed since user checked in
                        datetime_scanned = datetime.datetime.now()  # this one appended to found_time arr
                        date_scanned = datetime.datetime.now().strftime("%m/%d/%Y")  # this one prints to csv
                        time_scanned = datetime.datetime.now().strftime("%H:%M:%S.%f")  # this one prints to csv
                        time_check = datetime_scanned - found_time[found.index(barcodeData)]
                        status_check = found_status[found.index(barcodeData)]

                        # if time exceeds wait period and user is checked in then check them out
                        if time_check > t_value and status_check == "IN":
                            index_loc = found.index(barcodeData)
                            found_status[index_loc] = "OUT"
                            found_time[index_loc] = datetime_scanned
                            txt.write("{},{},{},{},{},{}\n".format(system_id, date_scanned, time_scanned,
                                                                barcodeData, "OUT", time_check))  # write to local CSV file
                            txt.flush()

                            checked_out = True
                            if storageChoice.lower() == 'b':  # if user chose online/Sharepoint version
                                barcodeDataNew = convert(self, barcodeData, special_characters, char_dict_special_to_reg)
                                # (above) convert qr code text special chars to reg chars
                                contentstr = "{},{},{},{},{},{}\n".format(system_id, datestr, timestr, barcodeDataNew, "OUT", time_check)
                                contentstr2 = "{},{},{},{},{},{}\n".format(system_id, datestr, timestr, barcodeData, "OUT",
                                                                        time_check)

                                checked_out = create_list_item(self, ctx, contentstr2)
                                contentStrings = contentStrings + contentstr

                            winsound.Beep(500, 400)  # makes a beeping sound on scan in
                            if checked_out:
                                screen_label.text = screen_label.text + f"\n{barcodeData} checking OUT at {str(datetime_scanned)} at location: " \
                                                                        f"{system_id} for duration of {str(time_check)}"
                        # if found and check-in time is less than the specified wait time then wait
                        elif time_check < t_value and status_check == "OUT":
                            pass
                        # if found and time check exceeds specified wait time and user is checked out, delete ID and affiliated
                        # data from the list. This resets everything for said user and allows the user to check back in at a later time.
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
                        screen_label.text = screen_label.text + f"\n{bcolors.FAIL}[Error] Barcode data issue in video() function.{bcolors.ENDC}"

                # show the output frame
                cv2.imshow("QR Toolbox", frame)
                key = cv2.waitKey(1) & 0xFF

                # if the `q` key was pressed, break from the loop
                if key == ord("q") or key == ord("Q"):
                    break

            # close the output CSV file and do a bit of cleanup
            screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}[ALERT] Cleaning up... \n{bcolors.ENDC}"
            txt.close()

            if os.path.exists(qr_storage_file) and os.stat(qr_storage_file).st_size == 0:
                os.remove(qr_storage_file)  # if the file is empty, delete it
            checkStorage = False  # Reset the global variable that tells code to check the qr_storage_file

            # This part is necessary to show special characters properly on any of the local CSVs
            if os.path.exists(args["output"]):
                barcodesTxt = open(args["output"], 'r', encoding="utf-8")
                newCSV = open(archive_folder + "/" + file_name, 'w', encoding="ANSI")

                data = barcodesTxt.read()
                newCSV.write(data)

                barcodesTxt.close()
                newCSV.close()
            else:
                data = f"\n{bcolors.FAIL}[ERROR] barcodes.txt not found as expected.{bcolors.ENDC}"
                screen_label.text = screen_label.text + data

            if storageChoice == 'a':  # if local was chosen, also store barcodes file at the location given
                if os.path.exists(storagePath):  # check if file path exists
                    with open(os.path.join(storagePath, file_name), "w", encoding="ANSI") as csv2:
                        csv2.write(data)
                else:
                    screen_label.text = screen_label.text + f"\n{bcolors.WARNING}[ALERT]: Storage folder not established or is unavailable. " \
                          f"Files will only be saved to the working directory\n{bcolors.ENDC}"
            elif storageChoice.lower() == 'b':  # if online was chosen, upload data to SharePoint as well
                success = connect(self, ctx, 'upload', contentStrings, file_name, bkcsvfolder)
                if success:
                    upload_backup(ctx, self)

            if os.path.exists(args["output"]) and os.stat(args["output"]).st_size == 0:  # delete barcodes.txt if empty
                os.remove(args["output"])  # not removed until the end in case something goes wrong above and it's needed
            vs.stop()
            vs.stream.release()
            vs = None
            cv2.destroyAllWindows()

            not_done = True  # set these so qr reader waits on user choice before starting video
            user_chose_storage = False

    """
    This function prepares the program and then runs the video() function to read QR Codes
        - The preparation involves setting up and starting the popup, and checking if a video stream already exists
        - It also runs the video stream on a different thread, so that the user can do 2 things at once with the program
    """

    def qr_reader(self):
        restart_session_popup = RestartSessionWidget()
        restart_session_popup.restart_popup = Popup(title="Do you want to start a new session or restart the previous one?",
                      content=restart_session_popup, size_hint=(None, None), size=(725, 170), auto_dismiss=True)

        global vs
        if vs is not None:
            screen_label = self.ids.screen_label
            screen_label.text = screen_label.text + f"\n{bcolors.WARNING}[ALERT] A video stream already exists.{bcolors.ENDC}"
            return

        restart_session_popup.restart_popup.open()
        restart_session_popup.main_screen = self
        threading.Thread(target=self.video, daemon=True).start()

    """ This function calls the qr_batch function and runs the qr_batch generator """

    def qr_batch(self):
        qr_batch(self)

    """ This function creates a popup widget to prompt the user for text for the QR code, can be multi-line """

    def qr_single(self):
        qr_single_widget = QRSingleWidget()
        qr_single_widget.qr_single_popup = Popup(
            title="Enter text to generate a single QR Code and click OK. The resulting image will be saved in the "
                  "tool's origin folder, and selected storage location.", content=qr_single_widget,
            size_hint=(None, None), size=(327, 290), auto_dismiss=True)
        qr_single_widget.main_screen = self
        qr_single_widget.qr_single_popup.open()

    """ This function shows the setup menu as a popup widget w/4 buttons """

    def setup(self):
        setup_popup = SetupWidget()
        setup_popup.setup_popup = Popup(title="Choose an option", content=setup_popup, size_hint=(None, None), size=(251, 475),
                                        auto_dismiss=True)
        setup_popup.main_screen = self
        setup_popup.setup_popup.open()

    """ This function provides more information on the purpose and development of this software """

    def about(self):
        # displays the about screen
        text = "[u]QR Toolbox v1.3[/u]\n"
        text = text + "About: The QR Toolbox is a suite a tools for creating and reading QR codes. The toolbox is platform " \
              "agnostic, lightweight, open source, and written in pure Python. This toolbox may be used to track resources," \
              " serve as a check-in capability for personnel, or customized to meet other operational needs. \n"
        text = text + "Version: 1.3 \n\n"
        text = text + "Credits: The QR Toolbox consists of a number of python packages, namely: \n qrcode - " \
              "Lincoln Loop info@lincolnloop.com; \n pyzbar - Lawrence Hudson quicklizard@googlemail.com; \n OpenCV code - " \
              "Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/; \n Code integration, minor enhancements, & " \
              "platform development - Timothy Boe boe.timothy@epa.gov and Muhammad Karimi karimi.muhammad@epa.gov \n"
        text = text + "Contact: Timothy Boe: boe.timothy@epa.gov; or Paul Lemieux: lemieux.paul@epa.gov; USEPA Homeland Security " \
              "Research Program \n"
        screen_label = self.ids.screen_label
        screen_label.text = text
        screen_label.font_size = 18
        screen_label.valign = 'middle'
        screen_label.halign = 'center'

        global clear_screen
        clear_screen = True

    """ This function is triggered when the user clicks the Menu 'Exit' button """

    def exit(self, *args):
        exit_widget = ExitWidget()
        exit_widget.exit_widget_popup = Popup(title="                             Are you sure you want to quit?\n(unsaved data, "
                "such as from an open QR Reader, will be lost)", content=exit_widget, size_hint=(None, None), size=(417, 155), auto_dismiss=True)
        exit_widget.exit_widget_popup.open()
        return True


""" This class represents/is the widget that displays when you click the qr-reader function, asking if you want to restart a session or not """


class RestartSessionWidget(BoxLayout):
    restart_popup = None
    main_screen = None

    """ 
    This function Checks to see if there is any previous sessions and session data, and if there is it will pull that back in
            @param check is to see if we should checkStorage or not
    """

    def set_check_storage(self, check):
        global not_done, user_chose_storage
        screen_label = self.main_screen.ids.screen_label
        setup_screen_label(screen_label)
        if check:
            global checkStorage
            checkStorage = True
            screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}Previous session will be restarted, if one exists.{bcolors.ENDC}"
        user_chose_storage = True
        not_done = False


""" This class represents the information displayed when you want to set the storage location (text and 2 buttons, local or online) """


class StorageWidget(BoxLayout):
    text = "Do you want data stored on Sharepoint (online) or locally? \nNote: Files are also saved in the QR-Toolbox Archive folder regardless."
    storage_popup = None
    main_screen = None

    """ This function sets the storage based on the users selection (local or online) """
    
    def set_storage(self, storage):
        global storageChoice
        if storage:  # Local button was pressed
            global storagePath
            storageChoice = "a"
            storagePath = store(self.main_screen)
        elif not storage:
            storageChoice = "b"
            screen_label = self.main_screen.ids.screen_label
            setup_screen_label(screen_label)
            screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}Storage location set to online (SharePoint).{bcolors.ENDC}"


""" This class represents the displayed when you select "Choose Camera Source" from the Setup menu, and is text with 3 buttons """


class CameraWidget(BoxLayout):
    text = "Which camera do you want to use?"
    camera_popup = None
    main_screen = None

    """
    This function asks the user what camera will be used to read QR Codes
    Only 3 options
        1. A - integrated/built-in webcam (the default)
        2. B - USB or connected webcam
        3. C - PiCamera (from Raspberry Pi)
    """

    def set_camera(self, camera_choice):
        global cameraSource
        cameraSource = camera_choice
        screen_label = self.main_screen.ids.screen_label
        setup_screen_label(screen_label)
        screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}Camera source set to '{camera_choice}'.{bcolors.ENDC}"


""" This class represents the information displayed when you click the Setup menu """


class SetupWidget(BoxLayout):
    setup_popup = None
    main_screen = None

    """ Redirects program to either the consolidate() method or the upload_backup() method above, based on users choice """
    
    def upload_consolidate(self):
        if storageChoice == 'a':
            cons(self.main_screen)
        else:
            upload_backup(ctx, self.main_screen, True)  # since it comes only from menu, send True

    """ Creates and starts the popup for changing the storage location """

    def change_storage_location(self):
        storage_location = StorageWidget()
        storage_location.storage_popup = Popup(title="Select a storage location", content=storage_location, size_hint=(None, None),
                                               size=(500, 400), auto_dismiss=True)
        storage_location.main_screen = self.main_screen
        storage_location.storage_popup.open()

    """  Creates and starts the popup for changing the camera source """

    def change_camera_source(self):
        camera_location = CameraWidget()
        camera_location.camera_popup = Popup(title="Which camera do you want to use?", content=camera_location, size_hint=(None, None),
                                               size=(261, 375), auto_dismiss=True)
        camera_location.main_screen = self.main_screen
        camera_location.camera_popup.open()

    """ Creates and starts the popup that allows the user to choose whether or not special characters will be converted (if not, they're skipped) """

    def set_special_character_conversion(self):
        special_char_widget = AskSpecialCharConversionWidget()
        special_char_widget.special_char_popup = Popup(title="Do you want to allow conversion of QR Codes with special characters? (Only affects QR "
        "Creator functions when using Sharepoint storage.)", content=special_char_widget, size_hint=(None, None), size=(375, 300), auto_dismiss=True)
        special_char_widget.main_screen = self.main_screen
        special_char_widget.special_char_popup.open()


""" This class represents the information shown when the qr_single button is pressed, has text, an input box, and 2 buttons """


class QRSingleWidget(BoxLayout):
    qr_single_popup = None
    main_screen = None

    """ Calls the qr_single function with the text the user entered """

    def setup_qr_single(self, text):
        qr_single(self.main_screen, text)


""" This class represents the information when the special char conversion button is clicked (text with 2 buttons) """


class AskSpecialCharConversionWidget(BoxLayout):
    special_char_popup = None
    main_screen = None

    """ This function Sets the boolean variable based on users choice, and prints the according message (when special chars come up, acts accor) """

    def set_special_char_bool(self, ask_bool):
        global special_char_bool
        special_char_bool = ask_bool  # True if user says yes, False if user says no
        screen_label = self.main_screen.ids.screen_label
        setup_screen_label(screen_label)
        if ask_bool:
            screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}QR Codes with special characters will be converted to regular characters. " \
                                                    f"(Online Mode only){bcolors.ENDC}"
        else:
            screen_label.text = screen_label.text + f"\n{bcolors.OKBLUE}QR Codes with special characters will be skipped. (Online Mode only){bcolors.ENDC}"


""" This class represents the Exit alert box that pops up when you click the 'Exit' button, confirming that you want to exit """


class ExitWidget(BoxLayout):
    exit_widget_popup = None

    """ This function closes the program if the user clicked 'Yes' when asked """

    def confirm_exit(self):
        self.get_root_window().close()
        App.get_running_app().stop()


""" This class exists to instantiate a scrollview (which is used on the main screen to allow user to scroll the text displayed) """


class ScreenWidget(ScrollView):
    pass


""" This class represents the app itself, and everything starts from and runs from this """


class QRToolboxApp(App):
    main_screen = None

    """ Builds the QRToolboxApp instance by instantiating the MainScreenWidget and returning that as the Main Widget for the app """

    def build(self):
        self.main_screen = MainScreenWidget()
        return self.main_screen

    """ This function runs the storage selection popup at the start of the App, and sets some global vars """

    def on_start(self):
        global clear_screen, not_yet
        storage_location = StorageWidget()
        storage_location.storage_popup = Popup(title="Select a storage location", content=storage_location, size_hint=(None, None),
                                               size=(500, 400), auto_dismiss=False)
        storage_location.main_screen = self.main_screen
        clear_screen = True
        not_yet = True
        storage_location.storage_popup.open()
        pass


if __name__ == '__main__':
    QRToolboxApp().run()
