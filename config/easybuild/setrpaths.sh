#!/bin/bash
#
# This file was adopted from ComputeCanada:
#  https://github.com/ComputeCanada/easybuild-computecanada-config/blob/main/setrpaths.sh
#
# Modified for use at CCR with latest Gentoo prefix.
#

function print_usage {
	echo "Usage: $0 --path <path to search> [--add_origin] [--add_path=<path>]"
}

function patch_rpath {
	local filename=${1?No filename given}
	local rpath=''
	local filetype=$(file -b $filename)
	local REX_DYNAMIC="^ELF 64-bit LSB.*dynamically linked.*"
	local REX_SO="^ELF 64-bit LSB shared object.*x86-64.*"
	local REX_OS_INTERPRETER=".*interpreter /lib64/ld-linux-x86-64.so.2.*"
	local REX_LINUX_INTERPRETER=".*interpreter.*ld-linux-x86-64.so.2"
	local REX_LSB_INTERPRETER=".*interpreter.*ld-lsb-x86-64.so.3"

	if [[ -n "$EPREFIX" ]]; then
		PREFIX=$EPREFIX
		FORCE_RPATH="--force-rpath"
	else
		echo "gentoo module not loaded. Aborting"
		exit 1
	fi

	if [[ $filetype =~ $REX_DYNAMIC ]]; then
		if [[ $filetype =~ $REX_OS_INTERPRETER ]]; then
			patchelf --set-interpreter "$PREFIX/lib64/ld-linux-x86-64.so.2" "$filename"
			rpath='set'
		elif [[ $ARG_ANY_INTERPRETER -eq 1 && ( $filetype =~ $REX_LINUX_INTERPRETER || $filetype =~ $REX_LSB_INTERPRETER ) ]]; then
			patchelf --set-interpreter "$PREFIX/lib64/ld-linux-x86-64.so.2" "$filename"
			rpath='set'
		fi
	fi

	if [[ $filetype =~ $REX_SO ]]; then
		if ! ldd $filename | grep 'statically linked' > /dev/null; then
		    rpath='set'
		fi
	fi

	if [[ -n "$rpath" && ("$ARG_ADD_ORIGIN" == "1" || -n "$ARG_ADD_PATH") ]] ; then
		rpath=$(patchelf --print-rpath "$filename")
		rpath_old=$rpath

		if [[ "$ARG_ADD_ORIGIN" == "1" && "${rpath##\$ORIGIN}" == "$rpath" ]]; then
			if [ -n "$rpath" ] ; then
				rpath='$ORIGIN:'$rpath
			else
				rpath='$ORIGIN'
			fi
		fi

		if [[ -n "$ARG_ADD_PATH" ]]; then
			if [ -n "$rpath" ] ; then
				rpath="$ARG_ADD_PATH:"$rpath
			else
				rpath="$ARG_ADD_PATH"
			fi
		fi

		if [ "$rpath" != "$rpath_old" ] ; then
			patchelf $FORCE_RPATH --set-rpath "$rpath" "$filename"
		fi
	fi
}

function patch_zip {
	local filename=${1?Missing filename}
	local tmp=$(mktemp --directory)
	local fullname=$(readlink -f $filename)

	cd $tmp

	# Extract all and patch every binary file, and update the archive
	unzip -q $fullname
	for fname in $(find . -type f); do
	        oldperm=$(stat --format %a $fname)
	        chmod u+w $fname
		patch_rpath $fname;
		chmod $oldperm $fname
	done
	zip -rq $fullname .

	cd -
	rm -rf $tmp
}

TEMP=$(getopt -o p: --longoptions path:,add_origin,add_path:,any_interpreter -n $0 -- "$@")
eval set -- "$TEMP"
ARG_ADD_ORIGIN=0
ARG_ADD_PATH=
ARG_ANY_INTERPRETER=0

while true; do
	case "$1" in
		-p|--path)
			case "$2" in
				"") ARG_PATH=""; shift 2 ;;
				*) ARG_PATH=$2; shift 2 ;;
			esac ;;
		--add_origin)
			ARG_ADD_ORIGIN=1; shift ;;
		--any_interpreter)
			ARG_ANY_INTERPRETER=1; shift ;;
		--add_path)
			case "$2" in
				"") ARG_ADD_PATH=""; shift 2 ;;
				*) ARG_ADD_PATH=$2; shift 2 ;;
			esac ;;
		--) shift; break ;;
		*) echo "Unknown parameter $1"; print_usage; exit 1 ;;
	esac
done

if [[ -z "$ARG_PATH" ]]; then
	print_usage; exit 1
fi

# Avoid failing to set rpaths when a symlink is provided
if [[ -L "$ARG_PATH" ]]; then
	echo "error: $ARG_PATH is a symlink. Please provide a path not a symlink."
	exit 1
fi

SAVEIFS=$IFS
IFS=$(echo -en "\n\b")
for filename in $(find $ARG_PATH -type f); do
	if [[ -z "$filename" ]]; then
		continue
	fi
	if [[ $filename == *.jar ]]; then
		patch_zip $filename
	elif [[ $filename == *.whl ]]; then
		patch_zip $filename
	else
		patch_rpath $filename
	fi
done
IFS=$SAVEIFS
exit 0
