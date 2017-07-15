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
import csv
import codecs

easygui.msgbox('This utility allows you to search a directory to retrieve subfolders and filenames that contain MRNs. It produces a .csv with all matches and copies \
    the files/folders to a separate directory.')

#get the excel sheet
#print('Choose patient data sheet')
master_ws = easygui.fileopenbox(msg='Choose patient data sheet', filetypes=["*.xlsx", "*.xls"])
workbook = xlrd.open_workbook(master_ws)
ws = workbook.sheet_by_index(0)
#num_rows = ws.nrows

#get correct MRN column
col = easygui.integerbox(msg='Enter the column with patient MRNs (A=0, B=1, etc): ')
#col = int(input ('Enter the column with patient MRNs (A=0, B=1, etc): '))

#file browser for choosing which directory to index
#print ('Choose directory for indexing')
path = easygui.diropenbox(msg='Choose directory to search')
filename = easygui.enterbox(msg='Name the output file:', default='results.csv')
copy_dir = easygui.enterbox(msg='Name the new directory to receive copied files:', default='results')
show_progress = True

exc_dirs = easygui.enterbox(msg="Enter the name of any subfolders to exclude (case-sensitive). Separate by commas, \
    do not include slashes, and do not specify the path. e.g. animal, rabbit images, Aaron's stuff").split(', ')
if len(exc_dirs)==1 and exc_dirs[0]=='':
    exc_dirs=[]

#choose output csv
#print ('Name the output file (.csv)')
#filename = easygui.filesavebox(msg='Name the output file (e.g. results.csv)')
#copy_dir = input('Name the new directory to receive copied files:')
#show_progress = input('Choose whether to display the progress of the file search as Y or N:')
#show_progress = easygui.ynbox(msg='Display the progress of the file search?')

#sorts directory titles into array of strings
#folders = [f for f in sorted(os.listdir(path))]
#folders = np.asarray(folders, dtype=str)

#gets worksheet row values and puts into an array of strings
try:
    arr = [int(ws.cell(i,col).value) for i in range(ws.nrows)]
except:
    easygui.msgbox("Parsing error. May be due to wrong column selected or non-numeric entry present. This program will now exit.")
    exit()

print(arr)
#for i in range(1,num_rows+1):
#     row = np.asarray(ws.row_values(i))
#     arr = np.append(arr, [row], axis = 0)

"""arr2 = arr[:,1]
mrn_str = str(int(float(str(arr2[1]))))
for x in range (2, len(arr2)):
     mrn_str = mrn_str + "," + str(int(float(str(arr2[x]))))
"""

'''
#The subsequent section of code should only be activated if the script is being run on a Mac

argument_parser = argparse.ArgumentParser()
argument_parser.add_argument('-d', '--directory', type=str, required=True, help='The directory to search recursively.')
argument_parser.add_argument('-p', '--patient_ids', type=str, required=True, help='Patient IDs to look for comma-separated without whitepsace (e.g. 123,852,489)')
argument_parser.add_argument('-o', '--output_file', type=str, help='The name of the output file where results should be saved (tab-delimited format).')
argument_parser.add_argument('-v', '--verbose', type=str, help='Print out progress information about directory structure.')
argument_parser.add_argument('-c', '--copy_files', type=str, help='Copy files to this new directory')

arguments = argument_parser.parse_args()

path = arguments.directory
mrn_str = arguments.patient_ids
copy_dir = arguments.copy_files
show_progress = arguments.verbose
filename = arguments.output_file

'''

counter = 0
#creates dictionary
paths_by_patient_id = dict((patient_id, set()) for patient_id in mrn_str.split(','))

#searches for matched patients
for root, subdirs, files in os.walk(path):
    for exc_dir in exc_dirs:
        if exc_dir in subdirs:
            subdirs.remove(exc_dir)

    for subdir in subdirs:
        matched_patients = []

        for patient_id in paths_by_patient_id:

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

          

                

        


