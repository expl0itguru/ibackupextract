# ibackupextract
Cross-platform utility to extract iOS backups

# Usage
$ python3 ibackupextract.py -h
usage: ibackupextract.py [-h] -s SRC [-d DST] [-v] [-i]

optional arguments:
  -h, --help         show this help message and exit
  -d DST, --dst DST  folder to store extracted files (default: _unback_)
  -v, --verbose      increase output verbosity (max: -vv)
  -i, --info         just print info about the backup

required arguments:
  -s SRC, --src SRC  folder containing Manifest.db

# Dependencies
* pip install argparse

# Quick Start
\# Create a backup of a connected iOS device
$ idevicebackup2 backup --full ./backup

\# Invoke the script to extract the files
$ python3 ibackupextract.py -s backup -d extract
