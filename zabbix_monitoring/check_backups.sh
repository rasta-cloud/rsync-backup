#!/bin/bash

config_path="/var/client_backups/config"
logs_path="/var/log/backups"
result=""
a_date=$(date "+%s")
for conf_file in "${config_path}"/*
do
	[[ -e "${conf_file}" ]] || break
	dest_dir=$(jq '.destination_directory' < "${conf_file}" | tr -d '"')
	srv_name=$(jq '.server_name' < "${conf_file}" | tr -d '"')
	latest_dir=$(realpath "${dest_dir}/${srv_name}/latest")
	latest_dir_name=$(echo "${latest_dir}" | rev | cut -d "/" -f 1 | rev)
	creation_date_time=$(date -d "$(echo "${latest_dir_name}" | sed "s|\(....\)-\(..\)-\(..\)-\(..\)-\(..\)-\(..\)|\1/\2/\3 \4:\5:\6|")" "+%s")
	if [[ ${creation_date_time} -lt $(( a_date - 90000 )) ]]
	then
		result+="Missing backup for server ${srv_name}. Last backup is from ${latest_dir_name}"$'\n'
	else
		for i in $(jq '.source_directories[].dir' < "${conf_file}" | tr -d '"')
		do
			if [[ ! -d "${latest_dir}${i}" ]]
			then
				result="${result}Missing backup for directory ${i} from server ${srv_name}."$'\n'
			fi
		done
	fi

done

today=$(date "+%Y-%m-%d")
for log_file in "${logs_path}"/*
do
	if [[ $(date -r "${log_file}" "+%Y-%m-%d") == "${today}" && -s "${log_file}" ]]
	then
		result="${result} Log file ${log_file}:"$'\n'$(cat "${log_file}")$'\n'
	fi
done

if [[ -z "${result}" ]]
then
	echo "OK"
else
	echo "${result::-1}"
fi

