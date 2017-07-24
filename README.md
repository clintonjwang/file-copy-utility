Help on module FileCopyUtil:

NAME

    FileCopyUtil

DESCRIPTION

    Script that takes a list of patient identifiers, and searches a given path
    recursively for all paths that contain a patient identifier. Outputs paths by
    patient identifier in tab-delimited format to specified file and copies the
    patient folders into a new folder that is created in the same  location as where
    the file is run.
    
    Note: Before running this script, move its location into the drive or directory
    where you want the copied files to reside. This will likely be on an external
    hard drive unless your computer has lots of additional hard drive space. You
    should also move the excel document with the list of patient MRN's into this
    location as well.

FUNCTIONS

    copy_matching_files(paths_by_patient_id, copy_dir)
        Write matching files to new directory.
    
    find_number_in_filename(mrn, name_list, root=None)
        Return all members of a list of strings that contain a target MRN.
        
        name_list: list of filenames and dir names to compare mrn against
        mrn: mrn to search for, integer expected
        
        If mrn = 550, matching names will include 't2scans550_01' and '00550.txt'
        but exclude 'mri1550' and '5500.txt'.
        .zip files in name_list will also be included if one of its members
        is considered a match.
    
    get_matching_paths(patient_ids, search_path, exc_dirs, log_freq=50)
        Get matching files and directories for each MRN.
    
    main()
        Starting point for script
    
    setup_ui(skip_col=False, skip_exc=True)
        UI flow. Returns None if cancelled or terminated with error, else returns
        patient_ids, search_path and directories to exclude.
    
    write_to_csv(paths_by_patient_id, output_csv, pause_before_copy=False)
        Write MRNs and matching paths to a csv.


FILE

    /Users/clintonwang/Documents/Work/Script/FileCopyUtil.py


