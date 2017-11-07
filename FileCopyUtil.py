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
location as well. """

from csv import writer as _writer
import easygui
import io
import itertools
import os
import re
from shutil import copytree, copyfile
import sys
import time
from xlrd import open_workbook
from zipfile import ZipFile

logname = None

def _write_to_log(msg, print_to_screen=True):
    """Append message to a file and print to screen."""
    if logname is not None:
        with open(logname, 'a') as f:
            f.write(msg + "\n")

    if print_to_screen:
        print(msg)

def _name_has_mrn(filename):
    """Returns whether a filename contains some MRN (has exactly 7 digits in a row).
    False negatives are ok, but false positives are not, so the criteria for a match should be tight."""
    return re.search(r"^(.*\D)?\d{7}(\D.*)?$", filename) is not None

def _mrn_in_name(mrn, filename):
    """Determines if a specific MRN (string, but no leading zeros) is contained within a filename."""
    if mrn not in filename:
        return False
    else:
        return re.search("^(.*[^0-9])?0*" + mrn + "([^0-9].*)?$", filename) is not None

def _check_zip(mrn, zip_file):
    """Check if any zip file members contain a target string in their filename."""
    try:
        zip_members = ZipFile(zip_file).namelist()
    except Exception as e:
        _write_to_log("Error opening zip file %s: %s, %s" % (zip_file, str(sys.exc_info()[0]), str(e)), print_to_screen=False)
        return False

    for filename in zip_members:
        if _mrn_in_name(mrn, filename):
            return True

    return False

def _has_different_mrn(subdir, patient_ids):
    """Returns True if subdir's name has an MRN that does not match one of the MRNs in patient_ids.
    patient_ids should be a list of ints."""
    try: 
        i = subdir
        return i not in patient_ids
    except ValueError:
        return _name_has_mrn(subdir)

def _make_dir(new_dir):
    try:
        os.mkdir(new_dir)
    except FileExistsError:
        pass
    except:
        print("Unexpected error in mkdir for %s: %s" % (new_dir, str(sys.exc_info()[0])))

def find_number_in_filename(mrn, name_list, root=None):
    """Return all members of a list of strings that contain a target MRN.

    name_list: list of filenames and dir names to compare mrn against
    mrn: mrn to search for, integer expected

    If mrn = 550, matching names will include 't2scans550_01' and '00550.txt'
    but exclude 'mri1550' and '5500.txt'.
    .zip files in name_list will also be included if one of its members
    is considered a match."""
    matches = []
    for filename in name_list:
        if _mrn_in_name(mrn, filename):
            matches.append(filename)
        elif filename.endswith('.zip') and _check_zip(mrn, root+'/'+filename):
            matches.append(filename)

    return matches

def setup_ui(skip_col=False, skip_exc=True):
    """UI flow. Returns None if cancelled or terminated with error, else returns
    patient_ids, search_path and directories to exclude."""
    if not easygui.msgbox(('This utility searches a directory to retrieve subfolders and filenames that contain MRNs or accession numbers. '
                        'It will copy these files/folders to separate folders for each number. MRNs can be entered manually, or uploaded in .xlsx or .xls format.\n'
                        'NOTE: This program will search inside .zip files as well. If there is a match, it will copy the entire .zip file. Other compressed formats not supported.')):
        return None

    patient_ids = easygui.enterbox(msg=('Enter accession numbers or MRNs to search for, separated by commas '
                                    '(e.g. 12345678, E123456789, E234567890). Leave blank to upload an excel file instead.'))
    if patient_ids is None:
        return None
    else:
        patient_ids = patient_ids.strip().split(',')

    if patient_ids == [""]:
        mrn_src = easygui.fileopenbox(msg='Choose excel sheet containing MRNs/accession numbers in a single column.', filetypes=["*.xlsx", "*.xls"])
        if mrn_src is None:
            return None

        if skip_col:
            col = 0
        else:
            col = easygui.integerbox(msg='Enter the column number containing MRNs (0 for column A, 1 for column B, etc). Headers are allowed.')
            if col is None:
                return None

        # Get list of MRNs to search
        ws = open_workbook(mrn_src).sheet_by_index(0)

        header_offset = 0
        try:
            int(ws.cell(0, col).value)
        except ValueError:
            header_offset = 1

        try:
            patient_ids = [ws.cell(i, col).value for i in range(header_offset, ws.nrows)]
        except ValueError:
            easygui.msgbox("Parsing error. May be due to wrong column selected or non-numeric entry present. This program will now exit.")
            return None

    search_path = easygui.diropenbox(msg='Select a folder to search.')
    if search_path is None:
        return None

    if skip_exc:
        exc_dirs = ["#recycle"]#, "animal"]
    else:
        exc_dirs = easygui.enterbox(msg=("Enter the name of any subfolders to exclude (case-sensitive). Leave blank to include all folders. Separate by commas, "
                                        "do not include slashes, and do not specify the path. e.g. animal, rabbit images, Alice's folder.")).split(', ')
        try:
            if len(exc_dirs) == 1 and exc_dirs[0] == '':
                exc_dirs = []
        except TypeError:
            return None


    _write_to_log("Searching for the following patients: " + str(patient_ids))

    return [patient_ids, search_path, exc_dirs]

def get_matching_paths(patient_ids, search_path, exc_dirs, log_freq=50):
    """Get matching files and directories for each MRN."""
    t1 = time.time()
    # dict to store matching paths
    paths_by_patient_id = dict((patient_id, []) for patient_id in patient_ids)

    # to track progress
    match_dir_cnt = 0
    match_file_cnt = 0
    dir_cnt = 0
    searched_dirs = []
    skipped_dirs = []

    #search for matching folders/files
    for root, subdirs, files in os.walk(search_path):
        searched_dirs.append(root)

        # exclude directories specified by user
        for exc_dir, subdir in itertools.product(exc_dirs, subdirs):
            if exc_dir in subdir:
                exc_dirs.append(root + '/' + exc_dir)
                subdirs.remove(subdir)
                break

        # exclude directories with an MRN that is not one of the target MRNs
        temp_exdirs = []
        for subdir in subdirs:
            if _has_different_mrn(subdir, patient_ids):
                skipped_dirs.append(root + '/' + subdir)
                temp_exdirs.append(subdir)
                _write_to_log("Excluding folder %s because it's suspected to contain an irrelevant MRN" % subdir, print_to_screen=False)

        subdirs[:] = [d for d in subdirs if d not in temp_exdirs]

        temp_exdirs = []
        for patient_id in patient_ids:
            matching_dirs = find_number_in_filename(patient_id, subdirs)
            matching_files = find_number_in_filename(patient_id, files, root)

            for matching_dir in matching_dirs:
                paths_by_patient_id[patient_id].append(root + '/' + matching_dir)
                temp_exdirs.append(matching_dir)
                match_dir_cnt += 1

            for matching_file in matching_files:
                paths_by_patient_id[patient_id].append(root + '/' + matching_file)
                match_file_cnt += 1

        subdirs[:] = [d for d in subdirs if d not in temp_exdirs]
        
        dir_cnt += 1
        if dir_cnt % log_freq == 1:
            _write_to_log(("%d directories explored, %d matching files found, and %d matching folders found. "
                        "(Last directory explored: %s at %s)") % (dir_cnt, match_file_cnt, match_dir_cnt, root, time.strftime("%X")))

    _write_to_log(("Search complete. %d directories explored, %d matching files found, and %d matching folders found. "
            "Time it took to run: %.4f s.\n") % (dir_cnt, match_file_cnt, match_dir_cnt, time.time() - t1))

    try:
        with io.open('SearchHist.log', 'w', encoding='utf8') as f:
            f.write('The following directories were searched for the run at %s:\n' % time.strftime("%x, %X"))
            f.write('\n'.join(searched_dirs))
            f.write('\n\nThe following directories were excluded:\n')
            f.write('\n'.join(skipped_dirs))
            f.write('\n\nDirectories not listed here are matches, or subfolders of a matching directory.')
    except:
        print("Unexpected error while writing search history: " % str(sys.exc_info()[0]))

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

def copy_matching_files(paths_by_patient_id, copy_dir):
    """Write matching files to new directory."""
    t1 = time.time()
    potential_duplicates = []

    _make_dir(os.getcwd() + '/' + copy_dir)

    for patient_id in paths_by_patient_id:
        if len(paths_by_patient_id[patient_id]) == 0:
            continue

        base_dir = os.getcwd() + '/' + copy_dir + '/' + str(patient_id)
        _make_dir(base_dir)

        for match in paths_by_patient_id[patient_id]:
            new_name = base_dir + '/' + os.path.basename(match)

            while os.path.exists(new_name):
                potential_duplicates.append(os.path.basename(new_name))
                new_name += '+'
                
            #for zip files, just copy once to the main directory, and assume that any zips with the same name are duplicates
            if match.endswith('.zip') or match.endswith('.zipx'):
                new_name = os.getcwd() + '/' + copy_dir + '/' + os.path.basename(match)
                if os.path.exists(new_name):
                    continue
                
            if '.' in os.path.basename(match):
                try:
                    copyfile(match, new_name) # no exception thrown when overwriting
                except:
                    print("Unexpected error in copying file %s: %s" % (match, str(sys.exc_info()[0])))
            else:
                try:
                    copytree(match, new_name)
                except:
                    _write_to_log("Unexpected error in copying directory %s: %s" % (match, str(sys.exc_info()[0])))

    _write_to_log("Copy complete. Time it took to run: %.4f s.\n"  % (time.time() - t1))

    if len(potential_duplicates) > 0:
        easygui.msgbox('Copy complete. Potential duplicates detected. Duplicates will have "+" added to the end of their name. See duplicates.log file.')
        try:
            with io.open(copy_dir + '/duplicates.log', 'w', encoding='utf8') as f:
                f.write('\n'.join(potential_duplicates))
        except:
            print("Unexpected error while writing duplicate log: " % str(sys.exc_info()[0]))
    else:        
        easygui.msgbox('Copy complete.')

def main():
    """Starting point for script"""
    # Default parameters. Can be converted to UI options if necessary.
    output_csv = None#'MRN_Matches.csv'
    copy_dir = 'FileCopies'
    logname = None#"FileCopyLogs_" + time.strftime("%m%d%H%M") + ".log"

    # Ask user for inputs
    ret = setup_ui()
    if ret is None:
        return
    else:
        [patient_ids, search_path, exc_dirs] = ret

    # Get matching files and directories for each MRN
    paths_by_patient_id = get_matching_paths(patient_ids, search_path, exc_dirs)

    # Write matches to csv
    if output_csv is not None:
        write_to_csv(paths_by_patient_id, output_csv)

    # Write matching files to new directory
    copy_matching_files(paths_by_patient_id, copy_dir)

if __name__ == "__main__":
    main()
