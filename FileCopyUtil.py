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

from shutil import copytree, copyfile
import xlrd
import os
from csv import writer
import easygui
from zipfile import ZipFile
import time

def find_number_in_filename(name, name_list, root=None):
    """Return all members of a list of strings that contain a target string."""
    matches = []
    for item_name in name_list:
        if name in item_name:
            matches.append(item_name)
        elif item_name.endswith('.zip') and check_zip(name, root+'/'+item_name):
            matches.append(item_name)

    return matches

def check_zip(name, zip_file):
    """Check if any zip file members contain a target string in their filename."""
    zip_members = ZipFile(zip_file).namelist()
    for item_name in zip_members:
        if name in item_name:
            return True

    return False

def setup_ui(skip_col=False, skip_exc=False):
    """UI flow. Returns 1 if manually cancelled, returns -1 if terminated
    with error, returns 0 if completed without errors."""
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
    ws = xlrd.open_workbook(mrn_src).sheet_by_index(0)
    try:
        patient_ids = [str(int(ws.cell(i, col).value)) for i in range(ws.nrows)]
        print(patient_ids)
    except:
        easygui.msgbox("Parsing error. May be due to wrong column selected or non-numeric entry present. This program will now exit.")
        return None

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
        if show_progress and dir_cnt % 10 == 1:
            print(dir_cnt, " directories explored, ", match_file_cnt, " matching files found, and ", match_dir_cnt,
                " matching folders found. (Last directory explored: ", root, ")", sep="")

    print("Search complete. ", dir_cnt, " directories explored, ", match_file_cnt,
        " matching files found, and ", match_dir_cnt, " matching folders found. Time it took to run: " + str(time.time() - t1) + " s.\n", sep="")

    return paths_by_patient_id

def write_to_csv(paths_by_patient_id, output_csv, pause_before_copy=False):
    """Write MRNs and matching paths to a csv."""
    with open(output_csv, 'w') as f:
        csv_writer = writer(f)
        for patient_id in paths_by_patient_id:
            csv_writer.writerow([patient_id] + paths_by_patient_id[patient_id])

    if pause_before_copy:
        if not easygui.ynbox("Matches written to " + output_csv + ". Copy matching files to a new directory?"):
            exit(0)
    else:
        print("Matches written to ", output_csv, ". Starting to copy matching files.", sep="")

def copy_matching_files(paths_by_patient_id, copy_dir, show_progress=True):
    """Write matching files to new directory."""
    t1 = time.time()
    potential_duplicates = []

    for patient_id in paths_by_patient_id:
        base_dir = os.getcwd() + '/' + copy_dir + '/' + patient_id
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

    print("Copy complete. Time it took to run: " + str(time.time() - t1) + " s.\n", sep="")

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