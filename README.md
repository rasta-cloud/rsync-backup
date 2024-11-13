Rsync backup
==
Backup your files from machines (remote or localhost) using Rsync.

Usage:
---
Run:
```
# python3 ./src/main.py [config file]
```
Example:
```
# python3 ./src/main.py "/var/backup/config/example_config"
```
Description of JSON config file:
---
- `server_name` - IP address or FQDN of the server, which you want to back up. If empty, script will back up data from local host
- `ssh_user` (required) - Name of a user on the backed-up machine
- `port` (optional) - SSH port on the backed-up machine. If not specified, the script will use the default port 22
- `destination_directory` (required) - Directory on the local machine, where the script will save backed-up files
- `source_locations` (required) - List of directories or files to back up. Must contain either dir or file, but not both
  - `file` - Path to a file
  - `dir` - Path to a directory
    - `exclude` (optional) - List of excluded directories in the specified directory
- `storage_duration` (required) - Count of backups to store
- `prebackup_script` (optional) - Script which will run before the backup starts
- `postbackup_script` (optional) - Script which will run after the backup ends


Tips
---
- Run this script with root privileges to set the same owners on backed-up files as it was on the source machine
- For logging into the backed-up machine is recommended to use an SSHkey instead of a password

Prerequisites
---
- rsync
- python3

Zabbix monitoring
---
In folder zabbix_monitoring you can find files to set up monitoring in Zabbix to check backups made by this  script

- file `zbx_export_templates.json` - monitoring template exported from Zabbix. Import it to Zabbix and use it by monitored host
- file `check_backups.sh` - bash script to check backups.

Set up custom backup check in Zabbix Agent:
```
UserParameter=check.backups, /path/to/check_backups.sh
```