#!/usr/bin/env python3

""" Script that takes a list of patient identifiers, and searches a given path
recursively for all paths that contain a patient identifier. Outputs paths by
patient identifier in tab-delimited format to specified file and copies the
patient folders into a new folder that is created in the same  location as where
the file is run.

Note: Before running this script, move its location into the drive or directory
where you want the copied files to reside. This will likely be on an external
hard drive unless your computer has lots of additional hard drive space. You
should also move the excel document with the list of patient MRN's into this
location  as well. """

# TODO(clintonjwang): Account for MRNs starting with 0

from csv import writer as _writer
import easygui
import os
import re
from shutil import copytree, copyfile
import time
from xlrd import open_workbook
from zipfile import ZipFile

logname = "FileCopyLogs.log"

def find_number_in_filename(mrn, name_list, root=None):
    """Return all members of a list of strings that contain a target MRN.

    name_list: list of filenames and dir names to compare mrn against
    mrn: mrn to search for, integer expected

    If mrn = 550, matching names will include 't2scans550_01' and '00550.txt'
    but exclude 'mri1550' and '5500.txt'.
    .zip files in name_list will also be included if one of its members
    is considered a match."""
    mrn = str(mrn)

    matches = []
    for filename in name_list:
        if _mrn_in_name(mrn, filename):
            matches.append(filename)
        elif filename.endswith('.zip') and _check_zip(mrn, root+'/'+filename):
            matches.append(filename)

    return matches

def _write_to_log(msg, print_to_screen=True):
    """Append message to a file."""
    with open(logname, 'a') as f:
        f.write(msg + "\n")

    if print_to_screen:
        print(msg)

def _mrn_in_name(mrn, filename):
    """Determines if an MRN (string, no leading zeros) is contained within a filename."""
    if mrn not in filename:
        return False
    else:
        return re.search("^(.*[^0-9])?0*" + str(mrn) + "([^0-9].*)?$", filename) is not None

def _check_zip(mrn, zip_file):
    """Check if any zip file members contain a target string in their filename."""
    zip_members = ZipFile(zip_file).namelist()
    for filename in zip_members:
        if _mrn_in_name(mrn, filename):
            return True

    return False

def setup_ui(skip_col=False, skip_exc=False):
    """UI flow. Returns None if cancelled or terminated with error, else returns
    patient_ids, search_path and directories to exclude."""
    if not easygui.msgbox(('This utility searches a directory to retrieve subfolders and filenames that contain MRNs. '
                        'It will copy these files/folders to separate folders for each MRN. MRNs must be stored in an .xlsx or .xls format.\n'
                        'NOTE: This program will search inside .zip files as well. If there is a match, it will copy the entire .zip file.\n'
                        'WARNING: This assumes MRNs do not begin with 0 and have a fixed number of digits.')):
        return None

    mrn_src = easygui.fileopenbox(msg='Choose patient data sheet.', filetypes=["*.xlsx", "*.xls"])
    if mrn_src is None:
        return None

    if skip_col:
        col = 0
    else:
        col = easygui.integerbox(msg='Enter the column with patient MRNs (A=0, B=1, etc): ')
        if col is None:
            return None

    search_path = easygui.diropenbox(msg='Select a folder to search.')
    if search_path is None:
        return None

    if skip_exc:
        exc_dirs = []
    else:
        try:
            exc_dirs = easygui.enterbox(msg=("Enter the name of any subfolders to exclude (case-sensitive). Leave blank to include all folders. Separate by commas,"
                                            "do not include slashes, and do not specify the path. e.g. animal, rabbit images, Alice's folder.")).split(', ')
            if len(exc_dirs) == 1 and exc_dirs[0] == '':
                exc_dirs = []
        except:
            return None

    # Get list of MRNs to search
    ws = open_workbook(mrn_src).sheet_by_index(0)
    try:
        patient_ids = [int(ws.cell(i, col).value) for i in range(ws.nrows)]
    except:
        easygui.msgbox("Parsing error. May be due to wrong column selected or non-numeric entry present. This program will now exit.")
        return None

    _write_to_log("Searching for the following patients: " + str(patient_ids))

    return [patient_ids, search_path, exc_dirs]

def get_matching_paths(patient_ids, search_path, exc_dirs, show_progress=True):
    """Get matching files and directories for each MRN."""
    t1 = time.time()
    # dict to store matching paths
    paths_by_patient_id = dict((patient_id, []) for patient_id in patient_ids)

    # to track progress
    match_dir_cnt = 0
    match_file_cnt = 0
    dir_cnt = 0

    #search for matching folders/files
    for root, subdirs, files in os.walk(search_path):

        # exclude directories specified by user
        for exc_dir in exc_dirs:
            if exc_dir in subdirs:
                subdirs.remove(exc_dir)

        for patient_id in patient_ids:
            matching_dirs = find_number_in_filename(patient_id, subdirs)
            matching_files = find_number_in_filename(patient_id, files, root)

            for matching_dir in matching_dirs:
                paths_by_patient_id[patient_id].append(root + '/' + matching_dir)
                subdirs.remove(matching_dir)
                match_dir_cnt += 1

            for matching_file in matching_files:
                paths_by_patient_id[patient_id].append(root + '/' + matching_file)
                match_file_cnt += 1

        dir_cnt += 1
        if show_progress and dir_cnt % 50 == 1:
            _write_to_log(("%d directories explored, %d matching files found, and %d matching folders found. "
                            "(Last directory explored: %s)") % (dir_cnt, match_file_cnt, match_dir_cnt, root))

    _write_to_log(("Search complete. %d directories explored, %d matching files found, and %d matching folders found. "
            "Time it took to run: %.4f s.\n") % (dir_cnt, match_file_cnt, match_dir_cnt, time.time() - t1))

    return paths_by_patient_id

def write_to_csv(paths_by_patient_id, output_csv, pause_before_copy=False):
    """Write MRNs and matching paths to a csv."""
    with open(output_csv, 'w') as f:
        csv_writer = _writer(f)
        for patient_id in paths_by_patient_id:
            csv_writer.writerow([patient_id] + paths_by_patient_id[patient_id])

    if pause_before_copy:
        if not easygui.ynbox("Matches written to " + output_csv + ". Copy matching files to a new directory?"):
            exit(0)
    else:
        _write_to_log("Matches written to " + output_csv + ". Starting to copy matching files.")

def copy_matching_files(paths_by_patient_id, copy_dir, show_progress=True):
    """Write matching files to new directory."""
    t1 = time.time()
    potential_duplicates = []

    for patient_id in paths_by_patient_id:
        base_dir = os.getcwd() + '/' + copy_dir + '/' + str(patient_id)
        try:
            os.mkdir(base_dir)
        except:
            pass

        for match in paths_by_patient_id[patient_id]:
            new_path = base_dir + '/' + os.path.basename(match)

            if '.' in os.path.basename(match):
                try:
                    copyfile(match, new_path)
                except:
                    potential_duplicates.append(os.path.basename(match))
            else:
                try:
                    copytree(match, new_path)
                except:
                    potential_duplicates.append(os.path.basename(match) + '/')

    _write_to_log("Copy complete. Time it took to run: %.4f s.\n"  % (time.time() - t1))

    if len(potential_duplicates) > 0:
        easygui.msgbox('Copy complete. Potential file duplicates detected. Only the first one found was copied. See duplicates.log file.')
        with open('duplicates.log', 'w') as f:
            f.write('\n'.join(potential_duplicates))
    else:
        easygui.msgbox('Copy complete.')

def main():
    """Starting point for script"""
    # Default parameters. Can be converted to UI options if necessary.
    output_csv = 'FileCopyDirectory.csv'
    copy_dir = 'FileCopyResults'
    logname = "FileCopyLogs_" + time.strftime("%m%d%H%M") + ".log"

    # Ask user for inputs
    ret = setup_ui()
    if ret is None:
        return
    else:
        [patient_ids, search_path, exc_dirs] = ret

    # Get matching files and directories for each MRN
    paths_by_patient_id = get_matching_paths(patient_ids, search_path, exc_dirs)

    # Write matches to csv
    write_to_csv(paths_by_patient_id, output_csv)

    # Write matching files to new directory
    copy_matching_files(paths_by_patient_id, copy_dir)

if __name__ == "__main__":
    main()