# -*- coding: cp1252 -*-
# Name: QR Toolbox v2a
# Description: The QR Toolbox is a suite a tools for creating and reading QR codes. See the About screen for more information
# Author(s): Code integration, minor enhancements, & platform development - Timothy Boe boe.timothy@epa.gov; qrcode - Lincoln Loop info@lincolnloop.com; pyzbar - Lawrence Hudson quicklizard@googlemail.com; OpenCV code - Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/;
# Contact: Timothy Boe boe.timothy@epa.gov
# Requirements: Python 3, pyzbar, imutils, opencv-python, qrcode[pil]

# import the necessary packages
import argparse, datetime, imutils, time, cv2, sys, csv, qrcode, os, os.path, shutil
import io
from imutils.video import VideoStream
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from tkinter import *
from tkinter import filedialog
from datetime import timedelta
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

# load variables
# set share folder default, assign system ID, and wait time
share_folder = "None"
system_id = os.environ['COMPUTERNAME']
t_value = timedelta(seconds=10)
special_characters = ["à", "á", "â", "ã", "ä", "å", "æ", "ç", "è", "é", "ê", "ë", "ì", "í",
                      "î", "ï", "ð", "ñ", "ò", "ó", "ô", "õ", "ö", "ø", "ù", "ú", "û", "ü",
                      "ý", "þ", "ÿ", "À", "Á", "Â", "Ã", "Ä", "Å", "Æ", "Ç", "È", "É", "Ê",
                      "Ë", "Ì", "Í", "Î", "Ï", "Ð", "Ñ", "Ò", "Ó", "Ô", "Õ", "Ö", "Ø", "Ù",
                      "Ú", "Û", "Ü", "Ý", "Þ", "ß"]
code_characters = ["!@!a1!", "!@!a2!", "!@!a3!", "!@!a4!", "!@!a5!", "!@!a6!",
                   "!@!a7!", "!@!c1!", "!@!e1!", "!@!e2!", "!@!e3!", "!@!e4!",
                   "!@!i1!", "!@!i2!", "!@!i3!", "!@!i4!", "!@!o1!", "!@!n1!",
                   "!@!o2!", "!@!o3!", "!@!o4!", "!@!o5!", "!@!o6!", "!@!o7!",
                   "!@!u1!", "!@!u2!", "!@!u3!", "!@!u4!", "!@!y1!", "!@!b1!",
                   "!@!y2!", "!@!A1!", "!@!A2!", "!@!A3!", "!@!A4!", "!@!A5!",
                   "!@!A6!", "!@!A7!", "!@!C1!", "!@!E1!", "!@!E2!", "!@!E3!",
                   "!@!E4!", "!@!I1!", "!@!I2!", "!@!I3!", "!@!I4!", "!@!O1!",
                   "!@!N1!", "!@!O2!", "!@!O3!", "!@!O4!", "!@!O5!", "!@!O6!",
                   "!@!O7!", "!@!U1!", "!@!U2!", "!@!U3!", "!@!U4!", "!@!Y1!",
                   "!@!B1!", "!@!Y2!"]
char_dict_special_to_code = {"é": "!@!e1!"}
char_dict_code_to_special = {"!@!a1!": "à", "!@!a2!": "á", "!@!a3!": "â",
                             "!@!a4!": "ã", "!@!a5!": "ä", "!@!a6!": "å",
                             "!@!a7!": "æ", "!@!c1!": "ç", "!@!e1!": "è",
                             "!@!e2!": "é", "!@!e3!": "ê", "!@!e4!": "ë",
                             "!@!i1!": "ì", "!@!i2!": "í", "!@!i3!": "î",
                             "!@!i4!": "ï", "!@!o1!": "ð", "!@!n1!": "ñ",
                             "!@!o2!": "ò", "!@!o3!": "ó", "!@!o4!": "ô",
                             "!@!o5!": "õ", "!@!o6!": "ö", "!@!o7!": "ø",
                             "!@!u1!": "ù", "!@!u2!": "ú", "!@!u3!": "û",
                             "!@!u4!": "ü", "!@!y1!": "ý", "!@!b1!": "þ",
                             "!@!y2!": "ÿ", "!@!A1!": "À", "!@!A2!": "Á",
                             "!@!A3!": "Â", "!@!A4!": "Ã", "!@!A5!": "Ä",
                             "!@!A6!": "Å", "!@!A7!": "Æ", "!@!C1!": "Ç",
                             "!@!E1!": "È", "!@!E2!": "É", "!@!E3!": "Ê",
                             "!@!E4!": "Ë", "!@!I1!": "Ì", "!@!I2!": "Í",
                             "!@!I3!": "Î", "!@!I4!": "Ï", "!@!O1!": "Ð",
                             "!@!N1!": "Ñ", "!@!O2!": "Ò", "!@!O3!": "Ó",
                             "!@!O4!": "Ô", "!@!O5!": "Õ", "!@!O6!": "Ö",
                             "!@!O7!": "Ø", "!@!U1!": "Ù", "!@!U2!": "Ú",
                             "!@!U3!": "Û", "!@!U4!": "Ü", "!@!Y1!": "Ý",
                             "!@!B1!": "Þ", "!@!Y2!": "ß"}

# display landing screen

print("     _/_/      _/_/_/        _/_/_/_/_/                    _/  _/                   ")
print("  _/    _/    _/    _/          _/      _/_/      _/_/    _/  _/_/_/      _/_/    _/    _/")
print(" _/  _/_/    _/_/_/            _/    _/    _/  _/    _/  _/  _/    _/  _/    _/    _/_/  ")
print("_/    _/    _/    _/          _/    _/    _/  _/    _/  _/  _/    _/  _/    _/  _/    _/  ")
print(" _/_/  _/  _/    _/          _/      _/_/      _/_/    _/  _/_/_/      _/_/    _/    _/ \n")
print("QR Toolbox v2a \n")
print("The QR Toolbox is a suite a tools for creating and reading QR codes.\n")
print("USEPA Homeland Security Research Program \n")
print("System ID: " + system_id + "\n")


def video():
    # construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
                    help="path to output CSV file containing barcodes")
    #    ap.add_argument("-o1", "--output2", type=str, default=files_name,
    #            help="path to output CSV file containing barcodes")
    args = vars(ap.parse_args())
    # initialize time and date and make filename friendly
    time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))

    # initialize the video stream and allow the camera sensor to warm up
    print("[ALERT] starting video stream...")
    print("Press 'Q' to exit")
    vs = VideoStream(src=0).start()
    # this is for a mobile solution
    # vs = VideoStream(usePiCamera=True).start()
    time.sleep(5.0)

    # open the output CSV file for writing and initialize the set of
    # barcodes found thus far
    csv = open(args["output"], "w", encoding="utf-8")
    # csv = io.open(args["output"], "w", encoding="utf-8") # use this for Python 2

    if os.path.exists(share_folder):
        csv2 = open(os.path.join(share_folder, "QRT" + "-" + system_id + "_" + time_header + ".csv"), "w",
                    encoding="utf-8")
    else:
        print("Alert: Share folder not established or is unavailable. Files will be saved to the working directory")
        print("")

    # time track variables. These are used to keep track of QR codes as they enter the screen
    found = []
    found_time = []
    found_status = []

    # loop over the frames from the video stream
    while True:
        # grab the frame from the threaded video stream and resize it to
        # have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        # find the barcodes in the frame and decode each of the barcodes
        barcodes = pyzbar.decode(frame, symbols=[ZBarSymbol.QRCODE])

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
            if ("!@!" in barcodeData):
                for code_char in code_characters:
                    barcodeData = barcodeData.replace(code_char, char_dict_code_to_special[code_char])

            # draw the barcode data and barcode type on the image
            text = "{} ({})".format(barcodeData, barcodeType)
            cv2.putText(frame, text, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # if the barcode text is currently not in our CSV file, write
            # the timestamp + barcode to disk and update the set
            # if barcode data has never been seen, check the user in and record id, date, and time information
            if barcodeData not in found:
                csv.write("{},{},{},{}\n".format(system_id, datetime.datetime.now(),
                                                 barcodeData, "IN"))
                csv.flush()

                # csv2 writes to share folder location
                if os.path.exists(share_folder):
                    csv2.write("{},{},{},{}\n".format(system_id, datetime.datetime.now(),
                                                      barcodeData, "IN"))
                    csv2.flush()
                else:
                    pass

                found.append(barcodeData)
                found_time.append(datetime.datetime.now())
                found_status.append("IN")
                sys.stdout.write('\a')
                sys.stdout.flush()
                print(barcodeData + " checking IN at " + str(datetime.datetime.now()) + " at location: " + system_id)

            # if barcode information is found...

            elif barcodeData in found:

                time_check = datetime.datetime.now() - found_time[found.index(barcodeData)]
                status_check = found_status[found.index(barcodeData)]

                # if time exceeds wait period and user is checked in then check them out

                if time_check > t_value and status_check == "IN":
                    index_loc = found.index(barcodeData)
                    found_status[index_loc] = "OUT"
                    found_time[index_loc] = datetime.datetime.now()
                    csv.write("{},{},{},{},{}\n".format(system_id, datetime.datetime.now(),
                                                        barcodeData, "OUT", time_check))
                    csv.flush()
                    # csv2 writes to share folder location
                    # check and make sure share folder exists
                    if os.path.exists(share_folder):
                        csv2.write("{},{},{},{},{}\n".format(system_id, datetime.datetime.now(),
                                                             barcodeData, "OUT", time_check))
                        csv2.flush()
                    else:
                        pass
                    sys.stdout.write('\a')
                    sys.stdout.flush()
                    print(barcodeData + " checking OUT at " + str(
                        datetime.datetime.now()) + " at location: " + system_id + " for duration of " + str(time_check))
                    # if found and check-in time is less than the specified wait time then wait
                elif time_check < t_value and status_check == "OUT":
                    pass
                # if found and time check exceeds specified wait time and user is checked out, delete ID and affiliated data from the list. This resets everything for said user and allows the user to check back in at a later time.
                elif time_check > t_value and status_check == "OUT":
                    del found_status[index_loc]
                    del found_time[index_loc]
                    del found[index_loc]
            else:
                print("Something happened... error")

        # show the output frame
        cv2.imshow("QR Toolbox", frame)
        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break

    # close the output CSV file do a bit of cleanup
    print("[ALERT] cleaning up... \n")
    csv.close()
    csv2.close()
    vs.close()
    vs.stream.close()
    vs.stop()
    vs.stream.stop()
    vs.release()
    vs.stream.release()
    vs.camera.stop()
    vs.camera.close()
    vs.camera.release()
    cv2.destroyAllWindows()


def qr_batch():
    print("")
    print(
        "The batch QR code tool is used to automatically create multiple QR codes by referencing a .csv file. The csv file must be stored in the tools origin folder, named 'names.csv', and consist of two columns 'first' & 'last'. The 'first' and 'last' columns should be populated with participant's first and last names. The tool will automatically create QR codes for each participant's full name and save each QR image to the tools origin folder. \n")
    input("Press Enter to Continue \n")
    # this code creates a batch of QR codes from a csv file stored in the local directory
    # QR code image size and input filename can be modified below
    with open('names.csv') as csvfile:
        fieldnames = ["first", "last"]
        reader = csv.reader(csvfile)

        for row in reader:
            labeldata = row[0] + " " + row[1]

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4)

            qr.add_data(labeldata)
            qr.make(fit=True)
            print("Creating QR code: " + labeldata)
            img = qr.make_image()
            img.save(labeldata + ".jpg")
            img = Image.open(labeldata + ".jpg")
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("arial", 24)
            color = 0
            draw.text((37, 10), labeldata, font=font, fill=color)
            img.save(labeldata + ".jpg")
        #            img = qr.make_image()
        #            img.save(labeldata+".jpg") #assigns data as label name

        print("Success! \n")


def qr_single():
    print("")
    print(
        "Enter text to generate a single QR code and press Enter. The resulting QR image will be saved in the tool's origin folder. \n")
    custom_labeldata = input("QR Text: ")
    copy_labeldata = custom_labeldata
    print("Creating QR code...")

    for special_char in special_characters:
        if (special_char in copy_labeldata):
            for char in copy_labeldata:
                if (char == special_char):
                    copy_labeldata = copy_labeldata.replace(char, char_dict_special_to_code[special_char])

    # this code creates a single QR code based on information entered into the command line. The resulting QR code is stored in the local directory
    # QR code image size and input filename can be modified below
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4)

    # qr.add_data(custom_labeldata)
    qr.add_data(copy_labeldata)
    qr.make(fit=True)

    # draw label

    img = qr.make_image()
    img.save(custom_labeldata + ".jpg")
    img = Image.open(custom_labeldata + ".jpg")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial", 24)
    color = 0
    draw.text((37, 10), custom_labeldata, font=font, fill=color)
    img.save(custom_labeldata + ".jpg")

    print("Success! \n")


def about():
    # displays the about screen
    print("\n")
    print("QR Toolbox v2a \n")
    print(
        "About: The QR Toolbox is a suite a tools for creating and reading QR codes. The toolbox is platform agnostic, lightweight, open source, and written in pure Python. This toolbox may be used to track resources, serve as a check-in capability for personnel, or customized to meet other operational needs. \n")
    print("Version: 2.0a \n")
    print(
        "Credits: The QR Toolbox consists of a number of python packages, namely: \n qrcode - Lincoln Loop info@lincolnloop.com; \n pyzbar - Lawrence Hudson quicklizard@googlemail.com; \n OpenCV code - Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/; \n Code integration, minor enhancements, & platform development - Timothy Boe boe.timothy@epa.gov \n")
    print(
        "Contact: Timothy Boe: boe.timothy@epa.gov; or Paul Lemieux: lemieux.paul@epa.gov; USEPA Homeland Security Research Program \n")


def share():
    # allows the user to select a shared folder. If user escapes, a share folder is note created
    # note: the Tkinter code can be finicky when displayed in IDE i.e., the file window will not show when operated in IDE while the root.withdraw command is turned on. Commenting out the root.withdraw command will fix, but root window remains; destroy() can be used to remove this. May need to search for a better solution in the future
    print("")
    root = Tk()
    root.title('Share Directory')
    root.withdraw()
    share_folder = filedialog.askdirectory(title='Select a Network Share Directory')
    if os.path.exists(share_folder):
        print("Share directory established: " + share_folder)
    else:
        print("Share directory NOT established")
    print("")
    return share_folder


def cons():
    # consolidate QR csv results into a single file. This function looks for files with QRT in the first part of their name. If true, all csvs within the shared folder directory that also fit this condition. A number of error checks are built in to prevent bad things from happening
    time_header = str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
    cons_filename = os.path.join(share_folder, 'Consolidated_Record_' + time_header + '.csv')
    if os.path.exists(share_folder):
        QRT_files = [fn for fn in os.listdir(share_folder) if fn.startswith('QRT')]

        if not QRT_files:
            print("No entries to combine. Check the shared directory and try again")
        else:
            try:
                with open(cons_filename, 'wb') as outfile:
                    for i, fname in enumerate(QRT_files):
                        fname = os.path.join(share_folder, fname)
                        with open(fname, 'rb') as infile:
                            shutil.copyfileobj(infile, outfile)
                            print(fname + " has been imported.")
                print(
                    "\nConsolidated file created in the specified shared drive under the filename " + cons_filename + "\n")
            except:
                print(
                    "\nWARNING: Either the system was unable to write the consolidated file to the specified shared directory or the file " + cons_filename + " is currently in use or unavailable. The consolidated record may be incomplete. \n")
    else:
        print(
            "\nA shared folder has not been established. Specify a shared folder using the Establish Share Folder option before continuing \n")
        pass


# main menu

while True:
    print("==============|  MENU  |===============")
    print("A. QR Reader")
    print("B. QR Creator - Batch")
    print("C. QR Creator - Single")
    print("D. Establish Share Folder")
    print("E. Consolidate Records")
    print("F. About/Credits")
    print("G. Exit \n")
    choice = input("Enter your selection: ")
    if choice.lower() == 'a':
        video()
    elif choice.lower() == 'b':
        qr_batch()
    elif choice.lower() == 'c':
        qr_single()
    elif choice.lower() == 'd':
        share_folder = share()
    elif choice.lower() == 'e':
        cons()
    elif choice.lower() == 'f':
        about()
    elif choice.lower() == 'g':
        break
    else:
        print("Invalid choice \n")
