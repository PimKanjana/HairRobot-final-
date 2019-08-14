# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
         ( '*.ui', '.' ),
		 ( '*.png', '.' )
         ]

# Pyinstallers dependency analysis will not detect that pylons TL DLLs are
# required (since they are searched and loaded from machine code at runtime).
# Consequently it would not include them in the archive. This is amended by
# simply adding all DLLs from the pypylon directory to the list of binaries.

import pypylon
import pathlib
pypylon_dir = pathlib.Path(pypylon.__file__).parent
pylon_dlls = [(str(dll), '.') for dll in pypylon_dir.glob('*.dll')]

icon_file = ['\\Users\\Admin\\OneDrive\\Documents\\SeniorProject\\GUI(submitted)\\human_icon.ico']

a = Analysis(['FullAppUpdate_v4.py'],
             pathex=['C:\\Users\\Admin\\OneDrive\\Documents\\SeniorProject\\GUI(submitted)'],
             binaries=pylon_dlls,
             datas=added_files,
             hiddenimports=['win32api'],
             hookspath=[],
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
          [],
          exclude_binaries=True,
          name='PFue-II',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
		  icon=icon_file )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='PFue-II')
