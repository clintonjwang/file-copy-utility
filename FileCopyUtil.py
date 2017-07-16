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
from pandas import DataFrame
import codecs


def find_name_in_list(name, ls):
    matches = []
    for item_name in ls:
        if name in item_name:
            matches.append(item_name)

    return matches


# UI flow
if not easygui.msgbox('This utility allows you to search a directory to retrieve subfolders and filenames that contain MRNs. It produces a .csv with all matches and copies \
the files/folders to a separate directory.'):
    exit(0)

master_ws = easygui.fileopenbox(msg='Choose patient data sheet', filetypes=["*.xlsx", "*.xls"])
if master_ws is None:
    exit(0)

col = easygui.integerbox(msg='Enter the column with patient MRNs (A=0, B=1, etc): ')
if col is None:
    exit(0)

path = easygui.diropenbox(msg='Select a folder to search.')
if path is None:
    exit(0)

try:
    exc_dirs = easygui.enterbox(msg="Enter the name of any subfolders to exclude (case-sensitive). Separate by commas, \
    do not include slashes, and do not specify the path. e.g. animal, rabbit images, Alice's folder").split(', ')
except:
    exit(0)


# Default parameters. Can be converted to UI options if necessary.
show_progress = True
filename = 'FileCopyDirectory.csv'#easygui.enterbox(msg='Name the output file.', default='results.csv')
copy_dir = 'FileCopyResults'#easygui.enterbox(msg='Name the new directory to receive copied files (do not include slashes).', default='results')


# Preprocess user inputs
if len(exc_dirs)==1 and exc_dirs[0]=='':
    exc_dirs=[]

# Get list of MRNs to search
ws = xlrd.open_workbook(master_ws).sheet_by_index(0)
try:
    patient_ids = [int(ws.cell(i,col).value) for i in range(ws.nrows)]
except:
    easygui.msgbox("Parsing error. May be due to wrong column selected or non-numeric entry present. This program will now exit.")
    exit(1)


#creates dictionary
paths_by_patient_id = dict((patient_id, set()) for patient_id in mrn_str.split(','))

#searches for matched patients
for root, subdirs, files in os.walk(path):
    for exc_dir in exc_dirs:
        if exc_dir in subdirs:
            subdirs.remove(exc_dir)

    for patient_id in patient_ids:
        matching_dirs = find_name_in_list(patient_id, subdirs)

        if patient_id in subdirs:
            subdirs.remove(exc_dir)

    for subdir in subdirs:
        counter = 0
        matched_patients = []

        for patient_id in patient_ids:

            if patient_id in subdir:
                paths_by_patient_id[patient_id].add(root + '/' + subdir)
                matched_patients.append(patient_id)

        if show_progress:

            if matched_patients:
                print(counter, " matches found for MNR ", patient_id)
                #raw = '%s: %s' % (root + '/' + subdir, '\t'.join(sorted(matched_patients)))
                #print(raw.encode('utf-8', errors='replace'))

            else:
                raw = '%s: no matches' % (root + '/' + subdir)
                print(raw.encode('utf-8', errors='replace'))


    #creates counter and empty set for matched patients
    for file in files:
        matched_patients = []

        for patient_id in paths_by_patient_id:
            file_path = root + '/' + file

            if patient_id in file_path:
                paths_by_patient_id[patient_id].add(file_path)
                matched_patients.append(patient_id)


    # prints progress of search   
        if show_progress:

            if matched_patients:
                raw = '%s: %s' % (file_path, '\t'.join(sorted(matched_patients)))
                print(raw.encode('utf-8', errors='replace'))

            else:
                raw = '%s: no matches' % (file_path)
                print(raw.encode('utf-8', errors='replace'))


#navigating through dictionary through folders
if filename != None:
    with codecs.open(filename, 'w', 'utf-8') as f:

        for patient_id in paths_by_patient_id:
            raw_write = '%s\t%s\n' % (patient_id, '\t'.join(sorted(paths_by_patient_id[patient_id])))
            f.write(raw_write)


#copy matched patients to new directory
for patient_id in paths_by_patient_id:
    raw = patient_id
    print (raw.encode('utf-8', errors='replace'))
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