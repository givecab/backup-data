from cx_Freeze import setup, Executable
import sys

# Determinar base para Windows GUI
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

setup(
    name='backup-data',
    version='1.0',
    description='Backup Data App',
    options={'build_exe': {
        'packages': ['os', 'shutil', 'tkinter', 'ctypes', 'threading', 'datetime'],
        'include_files': []
    }},
    executables=[Executable(
        script='src/backup_data.py',
        target_name='backup_data.exe',
        base=base
    )]
)