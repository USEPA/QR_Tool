# About
### Name: EPA QR Tool
### Version: 1.7.2

### Description
A python-based tool for tracking assets (e.g., people, equipment) through the use of QR codes. The system uses USB-interface or built-in webcams along with the open-source python-based software for scanning and generating QR codes. The system was designed to read QR codes attached to assets. QR stations (consisting of a laptop and webcam) can be staged at various locations for the purpose of tracking an entity for logistical and health and safety purposes.

# Use Instructions
Run the QR-Toolbox-v1.7.exe file (downloaded from the most recent release). The executable does not require any form of installation or admin rights to run.

If using the tool in online mode or creating a batch of QR codes from a file, find your installation location and fill out the variables in the settings.csv file, which is found in the Setup folder.
The 1st, 3rd, and 5th lines are headers to identify what information goes where.
If creating a batch of QR codes, place the csv file with the values to be converted in the same directory as the executable and replace the file name in the 2nd line with your csv file name.
If operating in Online mode, the 4th line has the ArcGIS variables and the 6th line has the SQL variables. The necessary information for each is listed below.

For ArcGIS:
1. ArcGIS target url (ex. `https://example.maps.arcgis.com/home/`)
2. Application Token (ex `8g0PVcPTvH8RV450`)
3. Query information regarding target Layer name and owner (ex `owner:johndoe_EPA AND title:"Example Layer"`)
4. Device Latitude and Longitude if such information is relevant, otherwise it defaults to 0,0.

For SQL:
1. SQL Server Address (ex. `THIS-LAPTOP`)
2. SQL Database Name (ex. `QR_Tool`)
3. SQL Table Name (ex. `Table_1`)
4. SQL Table Column Names for "Scan Source", "Scan Date/Time", "Scanned Text", "Scanned Status", and "Elapsed Time"

If you do not have an application token that links to your ArcGIS, you will need to create a new application. To do this:
1. In ArcGIS Online, create a New Item
2. When asked what the New Item is, select Application
3. For the type of application, select Other application
4. Name it as you want and finish creating the new application item.
5. Once the Applicaiton has been created, open it and go to Settings. Under the Credentials heading you will see Client ID and a string of numbers and letters. This is the Application token that you will use for connecting the QR Tool

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
    - Navigate to wherever you installed the program files and find 'names.csv' or create a new csv file and place it in the same directory (If making a new file, make sure to update the settings file appropriately)
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
Note: To use this tool in online mode, users require an ArcGIS Online (see the settings.csv in Setup folder). 
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