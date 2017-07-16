'''
Script that takes a list of patient identifiers, and searches a given path recursively for all paths that contain a patient identifier. Outputs
paths by patient identifier in tab-delimited format to specified file and copies the patient folders into a new folder that is created in the same 
location as where the file is run.

Note: Before running this script, move its location into the drive or directory where you want the copied files to reside. This will likely be on an external
hard drive unless your computer has lots of addition hard drive space. You should also move the excel document with the list of patient MRN's into this location 
as well.
'''

#import the libraries needed to run script
from shutil import copytree, copyfile
import argparse
import xlrd
import os
import easygui
import numpy as np
#from pandas import DataFrame
import codecs

# return all members of name_list that contain name
def find_name_in_list(name, name_list):
    matches = []
    for item_name in name_list:
        if name in item_name:
            matches.append(item_name)

    return matches


# UI flow
def setup_ui():
    if not easygui.msgbox('This utility allows you to search a directory to retrieve subfolders and filenames that contain MRNs. \
It produces a .csv with all matches and copies the files/folders to a separate directory. MRNs must be stored in an .xlsx or .xls format. \
\nWARNING: This assumes MRNs do not begin with 0 and have a fixed number of digits.'):
        exit(0)

    mrn_src = easygui.fileopenbox(msg='Choose patient data sheet.', filetypes=["*.xlsx", "*.xls"])
    if mrn_src is None:
        exit(0)

    col = easygui.integerbox(msg='Enter the column with patient MRNs (A=0, B=1, etc): ')
    if col is None:
        exit(0)

    search_path = easygui.diropenbox(msg='Select a folder to search.')
    if search_path is None:
        exit(0)

    try:
        exc_dirs = easygui.enterbox(msg="Enter the name of any subfolders to exclude (case-sensitive). Leave blank to include all folders. Separate by commas, \
do not include slashes, and do not specify the path. e.g. animal, rabbit images, Alice's folder.").split(', ')

        if len(exc_dirs) == 1 and exc_dirs[0] == '':
            exc_dirs = []

    except:
        exit(0)

    # Get list of MRNs to search
    ws = xlrd.open_workbook(mrn_src).sheet_by_index(0)
    try:
        patient_ids = [str(int(ws.cell(i, col).value)) for i in range(ws.nrows)]
        print(patient_ids)
    except:
        easygui.msgbox("Parsing error. May be due to wrong column selected or non-numeric entry present. This program will now exit.")
        exit(1)

    return patient_ids, search_path, exc_dirs



# Default parameters. Can be converted to UI options if necessary.
show_progress = True
output_csv = 'FileCopyDirectory.csv'#easygui.enterbox(msg='Name the output file.', default='results.csv')
copy_dir = 'FileCopyResults'#easygui.enterbox(msg='Name the new directory to receive copied files (do not include slashes).', default='results')

# Ask user for inputs
patient_ids, search_path, exc_dirs = setup_ui()

# dict to store matching paths
paths_by_patient_id = dict((patient_id, []) for patient_id in patient_ids)

# to track progress
match_counter = 0
dir_counter = 0

#search for matching folders/files
for root, subdirs, files in os.walk(search_path):

    # exclude directories specified by user
    for exc_dir in exc_dirs:
        if exc_dir in subdirs:
            subdirs.remove(exc_dir)

    for patient_id in patient_ids:
        matching_dirs = find_name_in_list(patient_id, subdirs)
        matching_files = find_name_in_list(patient_id, files)

        for matching_dir in matching_dirs:
            paths_by_patient_id[patient_id].append(root + '/' + matching_dir)
            subdirs.remove(matching_dir)
            match_counter += 1

        for matching_file in matching_files:
            paths_by_patient_id[patient_id].append(root + '/' + matching_file)
            match_counter += 1

    if show_progress:
        dir_counter += 1
        print(dir_counter, " directories explored and ", match_counter, " total matches found. (Last directory explored: ", root, ")", sep="")

exit(0)
#navigating through dictionary through folders
with codecs.open(output_csv, 'w', 'utf-8') as f:
    for patient_id in paths_by_patient_id:
        raw_write = '%s\t%s\n' % (patient_id, '\t'.join(sorted(paths_by_patient_id[patient_id])))
        f.write(raw_write)


#copy matched patients to new directory
for patient_id in paths_by_patient_id:
    raw = patient_id
    print(raw.encode('utf-8', errors='replace'))
    my_set = paths_by_patient_id[patient_id]

    for set_contents in my_set:

        if patient_id in os.path.basename(set_contents) and set_contents.count(patient_id) == 1:
            new_path = copy_dir + '/' + os.path.basename(set_contents)
            raw = set_contents
            print(raw.encode('utf-8', errors='replace'))

            if '.' in os.path.basename(set_contents):
                copyfile(set_contents, new_path)
                    
            else:
                copytree(set_contents, new_path)