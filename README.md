# About
### Name: EPA QR Tool
### Version: 1.6

### Description
A python-based tool for tracking assets (e.g., people, equipment) through the use of QR codes. The system uses USB-interface or built-in webcams along with the open-source python-based software for scanning and generating QR codes. The system was designed to read QR codes attached to assets. QR stations (consisting of a laptop and webcam) can be staged at various locations for the purpose of tracking an entity for logistical and health and safety purposes.

# Use Instructions
Run the QR-Toolbox-v1.6.exe file (downloaded from the most recent release). The executable does not require any form of installation or admin rights to run.

If using the tool in online mode find your installation location and fill out the variables in the settings.py file, which is found in the Setup folder.
Refer to and follow the User Guide in the Documentation folder for more information.

# Quick Start Guide
This Guide contains info on how to quickly get started using the application.

### Running the Program
1. To Launch the Tool
   - Double-click on the software shortcut on your desktop or in your start menu
2. To Create a Single QR Code
    - Click 'QR Creator - Single'
3. To Create Multiple QR Codes
    - Click 'QR Creator - Batch'
4. To Modify QR Codes Created Through 'QR Creator - Batch' 
    - Navigate to "C:/Users/<yourusername>/AppData/Local/Programs/QR-Toolbox" or wherever you installed the program files
and find 'names.csv'
        - Once there, open that file and change the text as you wish
5. To Scan QR Codes
    - Click 'QR Reader'
6. To Restart a Scanning Session
    - Click "QR Reader" and then click "Restart previous session"
7. To Upload Backed-Up Data
    - Click the 'Setup' button and then 'Upload/Consolidate' when in Online Storage Mode
8. To Consolidate CSV Files
    - Click the 'Setup' button and then 'Upload/Consolidate' when in Local Storage Mode (will consolidate CSV files in the chosen location)
9. To Change the Camera
    - Click the 'Setup' button and then 'Change Camera Source', then choose the camera source you want
10. To Change Storage Location
    - Click the 'Setup' button and then 'Change Storage (Local/Online)', then choose the storage location you want
11. To Choose Special Character Conversion
    - Click the 'Setup' button and then 'Special Character Conversion', then choose your preference
12. To Find the Saved Files
    - Navigate to either "C:/Users/<yourusername>/AppData/Local/Programs/QR-Toolbox", or to wherever you installed the program files and then navigate
to 'Archive' within those program files, to see the QR Codes and CSV files
13. To Exit
    - Click either the "Exit" button or the 'X' button in the top right corner of the window

_See the User Guide in the Documentation folder for more detailed information._

# Important Notes
Note: To use this tool in online mode, users require an ArcGIS Online (see the settings.py in Setup folder). 
This information is specific to your organization or account.

This tool requires Microsoft Visual C++ Redistributable Package 2013

# Credits
### Authors 
Code integration, enhancements, & platform development - Timothy Boe boe.timothy@epa.gov, Muhammad Karimi 
karimi.muhammad@epa.gov, and Jordan Deagan deagan.jordan@epa.gov
Office 365 integration - Xiaowen Huang
qrcode - Lincoln Loop info@lincolnloop.com
pyzbar - Lawrence Hudson quicklizard@googlemail.com
OpenCV code - Adrian Rosebrock https://www.pyimagesearch.com/author/adrian/

### Contact 
Timothy Boe boe.timothy@epa.gov   
Jonathan Pettit pettit.Jonathan@epa.gov