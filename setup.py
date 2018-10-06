from cx_Freeze import setup, Executable

base = None    

executables = [Executable("disc.py", base=base)]

packages = ["idna","asyncio", "discord", "msvcrt"]
options = {
    'build_exe': {    
        'packages':packages,
    },    
}

setup(
    name = "TCNOMessage",
    options = options,
    version = "0.1",
    description = 'aylmao',
    executables = executables
)