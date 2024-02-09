#!/bin/bash

alias steam-wine='WINEPREFIX=~/.steam_wine WINEDEBUG=-all wine ~/.steam_wine/drive_c/Program\ Files\ \(x86\)/Steam/Steam.exe >/dev/null 2>&1 '
alias ls='ls --color=auto'
alias startx='ssh-agent startx'
alias cd="z"
alias vim="nvim"

export EDITOR=nvim
export TERMINAL="urxvt"

function start_gui {
    export TERMINAL="urxvt"
    exec ssh-agent startx
}

function update {
    pacman -Qmq | grep -Ee '-(cvs|svn|git|hg|bzr|darcs)$' > /tmp/packages_to_update
    echo 'visual-studio-code-insiders-bin' >> /tmp/packages_to_update
    yay -Syu --needed $(tr '\n' ' ' < /tmp/packages_to_update)
}

function minecraft {
	pushd .
	/usr/bin/minecraft $@
	cd ~/.minecraft/logs
	#/home/bmehne/Code/c10t/build/c10t -d -M 4000 -w  ~/.minecraft/saves/first -o ~/.minecraft/saves/first/`date +%Y-%m-%d`.png
	/home/bmehne/Code/c10t/build/c10t -M 4000 -w  ~/.minecraft/saves/first -o ~/.minecraft/saves/first/`date +%Y-%m-%d`.png
	rm swap.bin c10t.log
	popd
}

function yaourt {
	echo "Use yay or aurman"
}

function activate_virtualenv {
	to_activate="$(find -wholename '*/bin/activate')"
	if [ "$to_activate" = "" ]
	then
		echo "Could not find a virtualenv!"
	else
		for tactivate in $to_activate
		do
			source "$tactivate"
		done
	fi
}


function code_env {
	ssh-add ~/.ssh/id_rsa
	code-insiders
}

function les {
	if [ "$#" != "1" ]
	then
		ls "$@"
	elif [ -f "$1" ]
	then
		less "$1"
	else
		ls "$@"
	fi
}

function virtual_video_and_mic {
	echo "Must do:"
	echo " modprobe snd_aloop"
	echo " modprobe v4l2loopback exclusive_caps=1"
	echo "Redirect to the new alsa audio"
	 ffmpeg -f x11grab -framerate 20 -video_size 1920x1080 -i :0.0+1920 -vcodec rawvideo -pix_fmt yuv420p -threads 0 -f v4l2 /dev/video2
}

function ffconcat {
	FILE="$(mktemp)"
	all_args=( "$@" )
	len="${#all_args[@]}"
	last_arg="${all_args[$len-1]}"
	non_last_args="${all_args[@]:0:$len-1}"
	for ((i=0; i <= "${#non_last_args[@]}"; i++))
	do
		f="${all_args[$i]}"
		FULL_F="$(realpath "$f")"
		echo file "'"${FULL_F}"'" >> "$FILE"
	done
	#cat $FILE
	ffmpeg -f concat -safe 0 -i "$FILE" -c copy "$last_arg"
	rm "$FILE"
}

function help {
    cheat "$@"
    if [ "$?" == "0" ]
    then
        return
    fi
    tldr "$@"
    if [ "$?" == "0" ]
    then
        return
    fi
    cht.sh "$@"
    if [ "$?" == "0" ]
    then
        return
    fi
    howdoi "$@"
}

function compress {
	BASENAME="$(basename "$1")"
	DIRNAME="$(dirname "$1")"
	NAME="$1"
	7z a -mx=9 /tmp/"$BASENAME".7z "$NAME"
	if [ "$?" == "0" ]
	then
		mv "$NAME" /tmp/"$BASENAME"
		if [ "$?" == "0" ]
		then
			mv "/tmp/$BASENAME".7z "$DIRNAME"/"$BASENAME".7z
			if [ "$?" == "0" ]
			then
				rm -R "/tmp/$BASENAME"
			else
				echo "Failed to copy compressed file"
			fi
		else
			echo "Failed to copy original away!"
		fi
	else
		echo "Compression failed"
	fi

}

function screensaver_disable {
	if [ "$1" == "" ]
	then
		ENDTIME=""
	else
		ENDTIME="$(date -d "+$1" +%s)"
		echo "Disabling screensaver until: $(date -d "+$1")"
		if [ "$?" != "0" ]
		then
			echo "Failed to parse date"
			return
		fi
	fi
	while [ 1 ] 
	do
		xdotool mousemove_relative -- -1 -1
		xdotool mousemove_relative -- 1 1
		sleep 100
		if [ "$ENDTIME" != "" ]
		then
			if [ "$ENDTIME" -lt "$(date +%s)" ]
			then
				echo "Endtime reached: $(date)"
				break
			fi
		fi
	done
}

function pgrep_ {
	ps aux | head -n 1
	ps aux | grep "$@" | grep -v "$(echo grep "$@")"
}


function pgrep_pid {
	ps aux | grep "$@" | grep -v "$(echo grep "$@")" | awk '{ print $2 }'
}

function screensaver_kill {
	pgrep_pid "xautolock" | xargs kill
}

function ntfy.sh_warning {
default_title="Message from $(hostname)"
curl \
  -H "Title: ${2:-$default_title}" \
  -H "Tags: warning" \
  -d "$1" \
  https://ntfy.sh/b_585761a8590bc5cab4b562b2ba4b8106
}


function tm() {
 	RAW_DIR="${1:-$PWD}"
	DIR="$(realpath $RAW_DIR | sed 's#/#_#g')"
	if [ "$(tmux ls | grep "$DIR"":")" != "" ]
	then
		tmux a -t "$DIR"
	else
		tmux new -s "$DIR"
	fi
}

function tma() {
	if [ "$1" == "" ]
	then
		tmux a
		return
	fi
 	RAW_DIR="${1:-$PWD}"
	DIR="$(realpath $RAW_DIR | sed 's#/#_#g')"
	if [ "$(tmux ls | grep "$DIR"":")" != "" ]
	then
		tmux a -t "$DIR"
	else
		tmux a
	fi
}

function waitpid() {
	tail --pid="$1" -f /dev/null
}

function unixtime() {
	date -d "@$1"
}
