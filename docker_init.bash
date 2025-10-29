#!/bin/bash

set -e

error_exit() {
  echo -n "!! ERROR: "
  echo $*
  echo "!! Exiting script (ID: $$)"
  exit 1
}

ok_exit() {
  echo $*
  echo "++ Exiting script (ID: $$)"
  exit 0
}

## Environment variables loaded when passing environment variables from user to user
# Ignore list: variables to ignore when loading environment variables from user to user
export ENV_IGNORELIST="HOME PWD USER SHLVL TERM OLDPWD SHELL _ SUDO_COMMAND HOSTNAME LOGNAME MAIL SUDO_GID SUDO_UID SUDO_USER CHECK_NV_CUDNN_VERSION VIRTUAL_ENV VIRTUAL_ENV_PROMPT ENV_IGNORELIST ENV_OBFUSCATE_PART"
# Obfuscate part: part of the key to obfuscate when loading environment variables from user to user, ex: HF_TOKEN, ...
export ENV_OBFUSCATE_PART="TOKEN API KEY"

# Check for ENV_IGNORELIST and ENV_OBFUSCATE_PART
if [ -z "${ENV_IGNORELIST+x}" ]; then error_exit "ENV_IGNORELIST not set"; fi
if [ -z "${ENV_OBFUSCATE_PART+x}" ]; then error_exit "ENV_OBFUSCATE_PART not set"; fi

whoami=`whoami`
script_dir=$(dirname $0)
script_name=$(basename $0)
echo ""; echo ""
echo "======================================"
echo "=================== Starting script (ID: $$)"
echo "== Running ${script_name} in ${script_dir} as ${whoami}"
script_fullname=$0
echo "  - script_fullname: ${script_fullname}"
ignore_value="VALUE_TO_IGNORE"

# everyone can read our files by default
umask 0022

# Write a world-writeable file (preferably inside /tmp -- ie within the container)
write_worldtmpfile() {
  tmpfile=$1
  if [ -z "${tmpfile}" ]; then error_exit "write_worldfile: missing argument"; fi
  if [ -f $tmpfile ]; then rm -f $tmpfile; fi
  echo -n $2 > ${tmpfile}
  chmod 777 ${tmpfile}
}

itdir=/tmp/smartgallery_init
if [ ! -d $itdir ]; then mkdir $itdir; chmod 777 $itdir; fi
if [ ! -d $itdir ]; then error_exit "Failed to create $itdir"; fi

# Set user and group id
# logic: if not set and file exists, use file value, else use default. Create file for persistence when the container is re-run
# reasoning: needed when using docker compose as the file will exist in the stopped container, and changing the value from environment variables or configuration file must be propagated from smartgallerytoo to smartgallerytoo transition (those values are the only ones loaded before the environment variables dump file are loaded)
it=$itdir/smartgallery_user_uid
if [ -z "${WANTED_UID+x}" ]; then
  if [ -f $it ]; then WANTED_UID=$(cat $it); fi
fi
WANTED_UID=${WANTED_UID:-1024}
write_worldtmpfile $it "$WANTED_UID"
echo "-- WANTED_UID: \"${WANTED_UID}\""

it=$itdir/smartgallery_user_gid
if [ -z "${WANTED_GID+x}" ]; then
  if [ -f $it ]; then WANTED_GID=$(cat $it); fi
fi
WANTED_GID=${WANTED_GID:-1024}
write_worldtmpfile $it "$WANTED_GID"
echo "-- WANTED_GID: \"${WANTED_GID}\""

echo "== Most Environment variables set"

# Check user id and group id
new_gid=`id -g`
new_uid=`id -u`
echo "== user ($whoami)"
echo "  uid: $new_uid / WANTED_UID: $WANTED_UID"
echo "  gid: $new_gid / WANTED_GID: $WANTED_GID"

save_env() {
  tosave=$1
  echo "-- Saving environment variables to $tosave"
  env | sort > "$tosave"
}

load_env() {
  tocheck=$1
  overwrite_if_different=$2
  ignore_list="${ENV_IGNORELIST}"
  obfuscate_part="${ENV_OBFUSCATE_PART}"
  if [ -f "$tocheck" ]; then
    echo "-- Loading environment variables from $tocheck (overwrite existing: $overwrite_if_different) (ignorelist: $ignore_list) (obfuscate: $obfuscate_part)"
    while IFS='=' read -r key value; do
      doit=false
      # checking if the key is in the ignorelist
      for i in $ignore_list; do
        if [[ "A$key" ==  "A$i" ]]; then doit=ignore; break; fi
      done
      if [[ "A$doit" == "Aignore" ]]; then continue; fi
      rvalue=$value
      # checking if part of the key is in the obfuscate list
      doobs=false
      for i in $obfuscate_part; do
        if [[ "A$key" == *"$i"* ]]; then doobs=obfuscate; break; fi
      done
      if [[ "A$doobs" == "Aobfuscate" ]]; then rvalue="**OBFUSCATED**"; fi

      if [ -z "${!key}" ]; then
        echo "  ++ Setting environment variable $key [$rvalue]"
        doit=true
      elif [ "A$overwrite_if_different" == "Atrue" ]; then
        cvalue="${!key}"
        if [[ "A${doobs}" == "Aobfuscate" ]]; then cvalue="**OBFUSCATED**"; fi
        if [[ "A${!key}" != "A${value}" ]]; then
          echo "  @@ Overwriting environment variable $key [$cvalue] -> [$rvalue]"
          doit=true
        else
          echo "  == Environment variable $key [$rvalue] already set and value is unchanged"
        fi
      fi
      if [[ "A$doit" == "Atrue" ]]; then
        export "$key=$value"
      fi
    done < "$tocheck"
  fi
}

# smartgallerytoo is a specfiic user not existing by default on ubuntu, we can check its whomai
if [ "A${whoami}" == "Asmartgallerytoo" ]; then 
  echo "-- Running as smartgallerytoo, will switch smartgallery to the desired UID/GID"
  # The script is started as smartgallerytoo -- UID/GID 1025/1025

  # We are altering the UID/GID of the smartgallery user to the desired ones and restarting as that user
  # using usermod for the already create smartgallery user, knowing it is not already in use
  # per usermod manual: "You must make certain that the named user is not executing any processes when this command is being executed"
  sudo groupmod -o -g ${WANTED_GID} smartgallery || error_exit "Failed to set GID of smartgallery user"
  sudo usermod -o -u ${WANTED_UID} smartgallery || error_exit "Failed to set UID of smartgallery user"
  sudo chown -R ${WANTED_UID}:${WANTED_GID} /home/smartgallery || error_exit "Failed to set owner of /home/smartgallery"
  save_env /tmp/smartgallerytoo_env.txt  
  # restart the script as smartgallery set with the correct UID/GID this time
  echo "-- Restarting as smartgallery user with UID ${WANTED_UID} GID ${WANTED_GID}"
  sudo su smartgallery $script_fullname || error_exit "subscript failed"
  ok_exit "Clean exit"
fi

# If we are here, the script is started as another user than smartgallerytoo
# because the whoami value for the smartgallery user can be any existing user, we can not check against it
# instead we check if the UID/GID are the expected ones
if [ "$WANTED_GID" != "$new_gid" ]; then error_exit "smartgallery MUST be running as UID ${WANTED_UID} GID ${WANTED_GID}, current UID ${new_uid} GID ${new_gid}"; fi
if [ "$WANTED_UID" != "$new_uid" ]; then error_exit "smartgallery MUST be running as UID ${WANTED_UID} GID ${WANTED_GID}, current UID ${new_uid} GID ${new_gid}"; fi

########## 'smartgallery' specific section below

# We are therefore running as smartgallery
echo ""; echo "== Running as smartgallery"

# Load environment variables one by one if they do not exist from /tmp/smartgallerytoo_env.txt
it=/tmp/smartgallerytoo_env.txt
if [ -f $it ]; then
  echo "-- Loading not already set environment variables from $it"
  load_env $it true
fi

######## Environment variables (consume AFTER the load_env)


echo ""; echo "==================="
echo "== Running SmartGallery"
cd /app; python smartgallery.py || error_exit "SmartGallery failed or exited with an error"

ok_exit "Clean exit"
