from cx_Freeze import setup, Executable

setup(
    name="backup-data",
    version="0.1",
    description="App para backup de archivos por extensión",
    options={
        "build_exe": {
            "packages": ["psutil"],
            "include_files": []
        }
    },
    executables=[Executable("src/backup_data.py", base="Win32GUI", target_name="backup_data.exe")]
)