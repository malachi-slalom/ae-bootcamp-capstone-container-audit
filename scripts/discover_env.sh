#!/usr/bin/env sh
set -u

os_id=unknown
os_version=unknown
if [ -r /etc/os-release ]; then
	. /etc/os-release
	os_id=${ID:-unknown}
	os_version=${VERSION_ID:-unknown}
fi

container_type=none
if [ -f /.dockerenv ]; then
	container_type=docker
elif [ -f /run/.containerenv ]; then
	container_type=container
elif grep -qaE '(docker|containerd|kubepods|lxc)' /proc/1/cgroup 2>/dev/null; then
	container_type=cgroup
fi

command_name() {
	for candidate in "$@"; do
		if command -v "$candidate" >/dev/null 2>&1; then
			printf '%s' "$candidate"
			return
		fi
	done
	printf 'none'
}

ssh_config=none
if [ -f /etc/ssh/sshd_config ]; then
	ssh_config=/etc/ssh/sshd_config
fi

printf 'OS_ID=%s\n' "$os_id"
printf 'OS_VERSION=%s\n' "$os_version"
printf 'KERNEL=%s\n' "$(uname -sr 2>/dev/null || printf unknown)"
printf 'USER=%s\n' "$(id -un 2>/dev/null || printf unknown)"
printf 'IS_ROOT=%s\n' "$(if [ "$(id -u 2>/dev/null)" = 0 ]; then printf true; else printf false; fi)"
printf 'CONTAINER_TYPE=%s\n' "$container_type"
printf 'LYNIS=%s\n' "$(command_name lynis)"
printf 'SSH_CONFIG=%s\n' "$ssh_config"
printf 'PACKAGE_MANAGER=%s\n' "$(command_name apt-get dnf yum apk)"
printf 'NETWORK_TOOL=%s\n' "$(command_name ss netstat ip)"
