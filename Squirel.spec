# -*- mode: python ; coding: utf-8 -*-
from kivy_deps import sdl2, glew
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.textinput import TextInput

import qrcode, random

from PIL import Image, ImageDraw, ImageFont
from tkinter import Tk
import tkinter.filedialog as filedialog
from fpdf import FPDF
from datetime import datetime

from pathlib import Path
from pylibdmtx import pylibdmtx

block_cipher = None


a = Analysis(['SQUIREL.py'],
             pathex=['C:\\Users\\MKARIMI\\PycharmProjects\\QR_Tool'],
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
    for dep in pylibdmtx.EXTERNAL_DEPENDENCIES
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
          name='SQUIREL',
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
               name='SQUIREL')
