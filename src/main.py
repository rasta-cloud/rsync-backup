import os
import datetime
import sys
import json
import shutil
import pathlib

if len(sys.argv) != 2:
    print("Program usage: " + sys.argv[0] + "[config file]")
    exit(1)

# Load config file
config = json.load(open(sys.argv[1]))

# Check if necessary information is filled in
if "destination_directory" not in config:
    print("Error - You have to specify destination_directory (Destination for backup data)!")
    exit(1)
if "source_locations" not in config:
    print("Error - You have to specify source_locations (Paths to data, which you want to backup)!")
    exit(1)
if "storage_duration" not in config or type(config['storage_duration']) != int:
    print("Error - You have to specify storage_duration (Number of days to store data)!")
    exit(1)

if "port" not in config:
    config['port'] = 22
else:
    if type(config['port']) != int:
        print("Error - Port must be an integer!")
        exit(1)

# Prepare some necessary variables
date_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
if 'server_name' not in config:
    backup_dir = config['destination_directory'] + "/localhost"
else:
    backup_dir = config['destination_directory'] + "/" + config['server_name']
backup_path = backup_dir + "/" + date_time
latest_link = backup_dir + "/latest"
rsync_base = "/usr/bin/rsync -aA "
if config['port'] != 22:
    rsync_base += "-e 'ssh -o StrictHostKeyChecking=no -p " + str(config['port']) + "' "
else:
    rsync_base += "-e 'ssh -o StrictHostKeyChecking=no' "

# Run prebackup script
if "prebackup_script" in config and config['prebackup_script']:
    if 'server_name' not in config:
        remote_command = config['prebackup_script']
    else:
        remote_command = "ssh -o StrictHostKeyChecking=no "
        if config['port'] != 22:
            remote_command += "-p " + str(config['port']) + " "
        remote_command += "'" + config['ssh_user'] + "@" + config['server_name'] + "' '" + \
                          config['prebackup_script'] + "'"
    result_code = os.system(remote_command)
    if result_code > 0:
        print(result_code)

# Add directives to rsync related to every entry of the list of source dirs
for source_location in config['source_locations']:
    rsync = rsync_base
    src_loc = ""
    if 'dir' in source_location and 'file' in source_location:
        print(f'Error - As source you have to define either file or dir ({source_location})!')
        exit(1)
    if 'dir' in source_location:
        src_loc = source_location['dir']
        if src_loc[-1] != "/":
            src_loc += "/"
        if "exclude" in source_location:
            for exclude_path in source_location['exclude']:
                rsync += "--exclude='" + exclude_path + "' "
    elif 'file' in source_location:
        src_loc = source_location['file']
    if 'server_name' not in config:
        rsync += src_loc + " "
    else:
        rsync += "'" + config['ssh_user'] + "@" + config['server_name'] + ":" + src_loc + "' "
    rsync += "--link-dest '" + latest_link + src_loc + "' "
    rsync += "'" + backup_path + src_loc + "' "
    # Needed to create directory manually, because Synology's ash can't recognize parameter --mkpath in rsync command
    pathlib.Path(backup_path + src_loc).mkdir(parents=True, exist_ok=True)
    # Finally run rsync. Yup
    os.system(rsync)

# Edit symlink to an added folder
if os.path.exists(backup_path):
    if os.path.islink(latest_link):
        os.unlink(latest_link)
    os.symlink(backup_path, latest_link)

# Run postbackup script
if "postbackup_script" in config and config['postbackup_script']:
    if 'server_name' not in config:
        remote_command = config['postbackup_script']
    else:
        remote_command = "ssh "
        if config['port'] != 22:
            remote_command += "-p " + str(config['port']) + " "
        remote_command += "'" + config['ssh_user'] + "@" + config['server_name'] + "' '" + \
                          config['postbackup_script'] + "'"
    result_code = os.system(remote_command)
    if result_code > 0:
        print(result_code)

# Delete folders older than the time defined at config['storage_duration']
def edit_rw(action, name, exc):
    if os.path.islink(name):
        os.unlink(name)
    elif not os.access(name, os.W_OK):
        os.chmod(name, 0o700)
        shutil.rmtree(name, onerror=edit_rw)

dir_list = next(os.walk(backup_dir))[1]
dir_list.remove("latest")
storage_duration = datetime.timedelta(days=config['storage_duration'])
date_time_to_remove = datetime.datetime.now() - storage_duration
for data_dir in dir_list:
    creation_date_time = datetime.datetime.strptime(data_dir, "%Y-%m-%d-%H-%M-%S")
    if creation_date_time < date_time_to_remove:
        shutil.rmtree(backup_dir + "/" + data_dir, onerror=edit_rw)
