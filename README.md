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
    location  as well.

FUNCTIONS

    check_zip(name, zip_file)
        Check if any zip file members contain a target string in their filename.
    
    copy_matching_files(paths_by_patient_id, copy_dir, show_progress=True)
        Write matching files to new directory.
    
    find_name_in_list(name, name_list, root=None)
        Return all members of a list of strings that contain a target string.
    
    get_matching_paths(patient_ids, search_path, exc_dirs, show_progress=True)
        Get matching files and directories for each MRN.
    
    main()
        Starting point for script
    
    setup_ui(skip_col=False, skip_exc=False)
        UI flow. Returns 1 if manually cancelled, returns -1 if terminated
        with error, returns 0 if completed without errors.
    
    write_to_csv(paths_by_patient_id, output_csv, pause_before_copy=False)
        Write MRNs and matching paths to a csv.
    
FILE

    /Users/clintonwang/Documents/Work/FileCopyUtil.py


