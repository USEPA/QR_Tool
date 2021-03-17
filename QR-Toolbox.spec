# -*- mode: python ; coding: utf-8 -*-
from kivy_deps import sdl2, glew
from kivy.app import App
import pkg_resources, csv, tkinter, cv2, imutils, qrcode, office365
from tkinter import filedialog
from imutils.video import VideoStream
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
from office365.sharepoint.files.file_creation_information import FileCreationInformation
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol

from pathlib import Path
from pylibdmtx import pylibdmtx
from arcgis.gis import GIS

block_cipher = None


a = Analysis(['QR-Toolbox.spec'],
             pathex=['C:\\Users\\mkarimi\\PycharmProjects\\QR_Tool'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

# dylibs not detected because they are loaded by ctypes
a.binaries += TOC([
    (Path(dep._name).name, dep._name, 'BINARY')
    for dep in pylibdmtx.EXTERNAL_DEPENDENCIES + pyzbar.EXTERNAL_DEPENDENCIES
])

# a dependency of libzbar.dylib that pyinstaller does not detect
MISSING_DYLIBS = (
    Path('/usr/local/lib/libjpeg.8.dylib'),
)
a.binaries += TOC([
    (lib.name, str(lib.resolve()), 'BINARY') for lib in MISSING_DYLIBS
])

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='QR-Toolbox',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe, Tree('C:/Users/mkarimi/PycharmProjects/QR_Tool'),
               a.binaries,
               a.zipfiles,
               a.datas,
               *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
               strip=False,
               upx=True,
               upx_exclude=[],
               name='QR-Toolbox')
