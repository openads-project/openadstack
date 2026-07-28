#!/usr/bin/env bash

set -o pipefail

source "/opt/ros/${ROS_DISTRO}/setup.bash"

state_file="/tmp/last-ros-clock"
now="$(timeout 5 ros2 topic echo /clock --once --field clock.sec 2>/dev/null | head -n 1)" || exit 1
previous="$(cat "${state_file}" 2>/dev/null || echo "${now}")"
echo "${now}" > "${state_file}"

if (( now < previous )); then
  rm -f "${state_file}"
  kill -TERM 1
  exit 1
fi
