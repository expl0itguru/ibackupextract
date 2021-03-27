import sys
import os
import argparse
import plistlib
import shutil
import hashlib
import sqlite3

# Globals
conn = None
curs = None
args = None

# Message types
def info(msg):
    print(f"\033[32m[INFO]\033[0m {msg}")

def warn(msg):
    print(f"\033[33m[WARN]\033[0m {msg}")

def error(msg):
    print(f"\033[31m[ERRO]\033[0m {msg}", file=sys.stderr)

def verbose(msg, minVerbosity=1):
    if args.verbose >= minVerbosity:
        print(f"\033[36m[VERB]\033[0m {msg}")

# TODO: Revise if unneeded in future iterations
class Query():
    FETCH_ONE = 0
    FETCH_MANY = 1
    FETCH_ALL = 2

    def __init__(self, query):
        verbose(f"Loading query: {query}")
        self.query = query

    # Method potentially vulnerable without removal of colons which could allow manipulation of queries
    def bind(self, token, val):
        if token[0] != ":" and token[-1] != ":":
            warn(f"Dangerous token usage for query ({self.query}): {token}")

        self.query = self.query.replace(token, Query.escape(val))

    def execute(self, fetType=FETCH_ALL):
        try:
            curs.execute(self.query)

            # Execute the correct fetch type based on input
            if fetType == Query.FETCH_ONE:
                return curs.fetchone()
            elif fetType == Query.FETCH_MANY:
                return curs.fetchmany()
            elif fetType == Query.FETCH_ALL:
                return curs.fetchall()
            else:
                warn(f"Incorrectly defined fetch type ({fetType}) for query: {self.query}")
                return curs.fetchall()
            
        except Exception as e:
            warn(f"'{self.query}' query failed with reason: {e}")
        
        # Return an empty result upon failure
        return []

    @staticmethod
    def escape(val):
        return val.replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\\", "\\\\").replace("\x1a", "\\\\Z").replace("\0", "\\\\0")

class Helpers():
    @staticmethod
    def getDomainGroup(field):
        if "-" in field:
            return field.split("-")[0], field.split("-")[1]            
        else:
            return field, ""            
    
    @staticmethod
    def getGeneration(type):
        devices = { tuple(["iPad1,1"]):                                    "iPad",
                    tuple(["iPad2,2"]):                                    "iPad 2",
                    tuple(["iPad3,1", "iPad3,2", "iPad3,3"]):              "iPad (3rd Generation)",
                    tuple(["iPad3,4", "iPad3,5", "iPad3,6"]):              "iPad (4th Generation)",
                    tuple(["iPad6,11", "iPad6,12"]):                       "iPad (5th Generation)",
                    tuple(["iPad7,5", "iPad,7,6"]):                        "iPad (6th Generation)",
                    tuple(["iPad7,11", "iPad7,12"]):                       "iPad (7th Generation)",
                    tuple(["iPad11,6", "iPad11,7"]):                       "iPad (8th Generation)",
                    tuple(["iPad4,1", "iPad4,2", "iPad4,3"]):              "iPad Air",
                    tuple(["iPad5,3", "iPad5,4"]):                         "iPad Air 2",
                    tuple(["iPad11,3", "iPad11,4"]):                       "iPad Air (3rd Generation)",
                    tuple(["iPad13,1", "iPad13,2"]):                       "iPad Air (4th Generation)",
                    tuple(["iPad6,7", "iPad6,8"]):                         "iPad Pro (12.9-inch)",
                    tuple(["iPad6,3", "iPad6,4"]):                         "iPad Pro (9-7-inch)",
                    tuple(["iPad7,1", "iPad7,2"]):                         "iPad Pro (12.9-inch 2nd Generation)",
                    tuple(["iPad7,3", "iPad7,4"]):                         "iPad Pro (10.5-inch)",
                    tuple(["iPad8,1", "iPad8,2", "iPad8,3", "iPad8,4"]):   "iPad Pro (11-inch)",
                    tuple(["iPad8,5", "iPad8,6", "iPad8,7", "iPad8,8"]):   "iPad Pro (12.9-inch 3rd Generation)",
                    tuple(["iPad8,9," "iPad8,10"]):                        "iPad Pro (11-inch 2nd Generation)",
                    tuple(["iPad8,11", "iPad8,12"]):                       "iPad Pro (12.9-inch 4th Generation)",
                    tuple(["iPad2,5", "iPad2,6", "iPad2,7"]):              "iPad mini",
                    tuple(["iPad4,4", "iPad4,5", "iPad4,6"]):              "iPad mini 2",
                    tuple(["iPad4,7", "iPad4,8", "iPad4,9"]):              "iPad mini 3",
                    tuple(["iPad5,1", "iPad5,2"]):                         "iPad mini 4",
                    tuple(["iPad11,1", "iPad11,2"]):                       "iPad mini (5th Generation)",
                    tuple(["iPhone1,1"]):                                  "iPhone 2G",
                    tuple(["iPhone1,2"]):                                  "iPhone 3G",
                    tuple(["iPhone2,1"]):                                  "iPhone 3GS",
                    tuple(["iPhone3,1", "iPhone3,2", "iPhone3,3"]):        "iPhone 4",
                    tuple(["iPhone4,1"]):                                  "iPhone 4S",
                    tuple(["iPhone5,1", "iPhone5,2"]):                     "iPhone 5",
                    tuple(["iPhone5,3", "iPhone5,4"]):                     "iPhone 5c",
                    tuple(["iPhone6,1", "iPhone6,2"]):                     "iPhone 5s",
                    tuple(["iPhone7,2"]):                                  "iPhone 6",
                    tuple(["iPhone7,1"]):                                  "iPhone 6 Plus",
                    tuple(["iPhone8,1"]):                                  "iPhone 6s",
                    tuple(["iPhone8,2"]):                                  "iPhone 6s Plus",
                    tuple(["iPhone8,4"]):                                  "iPhone SE (1st Generation)",
                    tuple(["iPhone9,1", "iPhone9,3"]):                     "iPhone 7",
                    tuple(["iPhone9,2", "iPhone9,4"]):                     "iPhone 7 Plus",
                    tuple(["iPhone10,1", "iPhone10,4"]):                   "iPhone 8",
                    tuple(["iPhone10,2", "iPhone10,5"]):                   "iPhone 8 Plus",
                    tuple(["iPhone10,3", "iPhone10,6"]):                   "iPhone X",
                    tuple(["iPhone11,8"]):                                 "iPhone XR",
                    tuple(["iPhone11,2"]):                                 "iPhone XS",
                    tuple(["iPhone11,6", "iPhone11,4"]):                   "iPhone XS Max",
                    tuple(["iPhone12,1"]):                                 "iPhone 11",
                    tuple(["iPhone12,3"]):                                 "iPhone 11 Pro",
                    tuple(["iPhone12,5"]):                                 "iPhone 11 Pro Max",
                    tuple(["iPhone12,8"]):                                 "iPhone SE (2nd Generation)",
                    tuple(["iPhone13,1"]):                                 "iPhone 12 mini",
                    tuple(["iPhone13,2"]):                                 "iPhone 12",
                    tuple(["iPhone13,3"]):                                 "iPhone 12 Pro",
                    tuple(["iPhone13,4"]):                                 "iPhone 12 Pro Max"}

        for key in devices:
            if type in key:
                return devices[key]

        return "Unknown Device"
        
# Handle usage and setting of argument variables for us by other functions
def main():
    global args

    parser = argparse.ArgumentParser()
    requiredNamed = parser.add_argument_group('required arguments')    
    requiredNamed.add_argument("-s", "--src", required=True, help="folder containing Manifest.db")    
    parser.add_argument("-d", "--dst", default="_unback_", help="folder to store extracted files (default: _unback_)")
    parser.add_argument("-v", "--verbose", default=0, action="count", help="increase output verbosity (max: -vv)")
    parser.add_argument("-i", "--info", action="store_true", help="just print info about the backup")
        
    args = parser.parse_args()

    # Opens the Info.plist file stored within the backup and pulls data from it
    if args.info:
        with open(os.path.join(args.src, "Info.plist"), "rb") as fHandle:
            data = plistlib.load(fHandle)

        print("Applications:")
        for app in data["Installed Applications"]:
            if app in data["Applications"]:
                print(f"+ {app} (App Store)")
            else:
                print(f"+ {app}")
        
        # TODO: Revisit to adjust for other platforms where tabs don't format the same
        print("-" * 30)
        print(f"Build Version:\t\t{data['Build Version']}")
        print(f"Device Name:\t\t{data['Device Name']}")
        print(f"Display Name:\t\t{data['Display Name']}")
        print(f"GUID:\t\t\t{data['GUID']}")
        print(f"ICCID:\t\t\t{data['ICCID']}")
        print(f"IMEI:\t\t\t{data['IMEI']}")
        print(f"Last Backup Date:\t{data['Last Backup Date']}")
        print(f"MEID:\t\t\t{data['MEID']}")
        print(f"Phone Number:\t\t{data['Phone Number']}")
        print(f"Product Type:\t\t{data['Product Type']} ({Helpers.getGeneration(data['Product Type'])})")
        print(f"Product Version:\t{data['Product Version']}")
        print(f"Serial Number:\t\t{data['Serial Number']}")
        print(f"Target Identifier:\t{data['Target Identifier']}")
        print(f"Target Type:\t\t{data['Target Type']}")
        print(f"Unique Identifier:\t{data['Unique Identifier']}") 
        
        exit()

# Initiate connection to SQLite DB (Manifest.db)
def init():
    global conn, curs

    if os.getuid == 0 or os.geteuid == 0:
        warn("It is not advisable to run this script as root.")

    dbPath = os.path.join(args.src, "Manifest.db")

    try:
        conn = sqlite3.connect(dbPath)
        curs = conn.cursor()

        verbose(f"Connected to SQLite DB: {dbPath}")
            
    except sqlite3.Error as error:
        error(f"Unable to read {path}: {error}")

# Use info from Manifest.db to rearrange backed up data
def extract():
    if not os.path.exists(args.dst):
        verbose(f"Creating destination directory: {args.dst}")

        try:
            os.makedirs(args.dst)

        except Exception as e:
            error(f"Unable to create destination folder {args.dst}: {e}")
    
    info("Extracting backup...")
    data = Query("SELECT * FROM files;").execute()

    try:
        for row in data:
            idx =           row[0][0:2]
            fileId =        row[0]
            domain, group = Helpers.getDomainGroup(row[1])        
            relPath =       row[2]
            flags =         row[3]
            details =       row[4]                          # Unused binary plist of file metadata
            
            src = os.path.join(args.src, idx, fileId)
            dst = os.path.join(args.dst, domain, group, relPath)

            if not os.path.exists(os.path.dirname(dst)):
                    os.makedirs(os.path.dirname(dst))

            # File
            if flags == 1:
                verbose(f"{src} -> {dst}", 2)
                shutil.copy(src, dst)
            
            # Folder
            elif flags == 2:
                verbose(f"Created folder: {dst}", 2)
            
            # Other, protected
            elif flags == 4:
                verbose(f"Creating blank item in place of protected item: {dst}", 2)

                with open(dst, "w+"):
                    pass

            else:
                warn(f"Malformed flags for entity with ID: {fileId}")                               

    except Exception as e:
        error(f"Failed to copy {src} -> {dst}: {e}")
            
    info("Finished extracting backup.")

if __name__ == "__main__":
    main()
    init()
    extract()

    # Attempt to close database connection
    if curs:
        verbose("Closing cursor.")
        curs.close()

    if conn:
        verbose("Closing connection.")
        conn.close()

else:
    error("This script is not intended to be imported.")