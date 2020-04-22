#!C:\Users\klock\PycharmProjects\sample-market-maker\venv\Scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'bitmex-market-maker==1.5','console_scripts','marketmaker'
__requires__ = 'bitmex-market-maker==1.5'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('bitmex-market-maker==1.5', 'console_scripts', 'marketmaker')()
    )
