# -*- mode: python ; coding: utf-8 -*-


block_cipher = None
from kivy_deps import sdl2, glew

b = [
    ('C:\\Users\\jdeagan\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\pyzbar\\*','.\\pyzbar')
    ]

added_paths = [
    ('qrtoolbox.kv','.'),
    ('./Archive','Archive'),
    ('./Library','Library'),
    ('./Setup','Setup'),
    ('./System_Data','System_Data'),
    ('./Temp','Temp')
    ]

a = Analysis(['QR-Toolbox.py'],
             pathex=[],
             binaries=b,
             datas=added_paths,
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
          name='QR-Toolbox-v1.5',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )

