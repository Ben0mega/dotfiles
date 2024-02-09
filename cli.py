#!/bin/python
import sys
import argparse
import json
import shutil
import os.path
import platform
import subprocess
from typing import Union
import datetime
import hashlib


def main(args):
    parser = argparse.ArgumentParser(
        description="command line interface for managing dotfiles",
    )
    subparsers = parser.add_subparsers(help="command", required=True, dest="command")
    install_cmd = subparsers.add_parser("install", help="install files from repo")
    install_cmd.add_argument(
        "files",
        nargs="*",
        help="Files you want to install from the repo - defaults to all if not specified",
    )

    sync_installed_into_repo_cmd = subparsers.add_parser(
        "sync_installed_into_repo", help="pull updates from external files"
    )
    sync_installed_into_repo_cmd.add_argument(
        "files",
        nargs="*",
        help="Files you want to sync to the repo - defaults to all installed files if not specified",
    )
    sync_installed_into_repo_cmd.add_argument("--force-push", action="store_true")

    sync_repo_to_installed_files_cmd = subparsers.add_parser(
        "sync_repo_to_installed_files", help="push updates to external files"
    )
    sync_repo_to_installed_files_cmd.add_argument(
        "files",
        nargs="*",
        help="Files you want to sync to the repo - defaults to all installed files if not specified",
    )
    sync_repo_to_installed_files_cmd.add_argument("--overwrite", action="store_true")

    add_files_into_repo_cmd = subparsers.add_parser(
        "add_files_into_repo", help="add external files to repo"
    )
    add_files_into_repo_cmd.add_argument(
        "files", nargs="+", help="Files you want to add to the repo - required argument"
    )
    add_files_into_repo_cmd.add_argument("--host-specific", action="store_true")

    parsed_args = parser.parse_args(args[1:])
    if parsed_args.command == "install":
        install_files_from_repo(parsed_args.files or None)
    elif parsed_args.command == "sync_installed_into_repo":
        sync_installed_into_repo(parsed_args.files or None, parsed_args.force_push)
    elif parsed_args.command == "sync_repo_to_installed_files":
        sync_repo_to_installed_files(parsed_args.files or None, parsed_args.overwrite)
    elif parsed_args.command == "add_files_into_repo":
        add_installed_into_repo(
            parsed_args.files if not parsed_args.host_specific else [],
            parsed_args.files if parsed_args.host_specific else [],
        )


def install_files_from_repo(
    maybe_repo_files=None,
):  # not specifying files -> do all files
    """
    installs files from repo.  errors if they already exists
    """
    print(repr(maybe_repo_files))
    return
    copies_to_do = []
    for relative_to_repo_filename, relative_to_home_filename in iterate_over_files(
        maybe_repo_files, False
    ):
        if os.path.exists(os.path.join(get_home_dir(), relative_to_home_filename)):
            error("File already exists:", f)
        copies_to_do.append((relative_to_repo_filename, relative_to_home_filename))
    exit_on_error()
    installed_files = get_installed_files()
    for relative_to_repo_filename, relative_to_home_filename in copies_to_do:
        installed_files[relative_to_home_filename] = get_hash(
            os.path.join(get_repo_location(), relative_to_repo_filename)
        )
        shutil.copy(
            os.path.join(get_repo_location(), relative_to_repo_filename),
            os.path.join(get_home_dir(), relative_to_home_filename),
        )
    save_installed_files(installed_files)


def sync_repo_to_installed_files(
    maybe_repo_files=None, overwrite=False
):  # not specifying files -> do all files
    """
    pushes updates from the repo to external files. errors if the files were modified
    """
    copies_to_do = []
    installed_files = get_installed_files()
    for relative_to_repo_filename, relative_to_home_filename in iterate_over_files(
        maybe_repo_files, True
    ):
        abs_home_path = os.path.join(get_home_dir(), relative_to_home_filename)
        if (
            os.path.exists(abs_home_path)
            and not overwrite
            and get_hash(abs_home_path) != installed_files[relative_to_home_filename]
        ):
            error("File was modified from repo state - syncing would overwrite!:", f)
        copies_to_do.append((relative_to_repo_filename, relative_to_home_filename))
    exit_on_error()
    for relative_to_repo_filename, relative_to_home_filename in copies_to_do:
        installed_files[relative_to_home_filename] = get_hash(
            os.path.join(get_repo_location(), relative_to_repo_filename)
        )
        shutil.copy(
            os.path.join(get_repo_location(), relative_to_repo_filename),
            os.path.join(get_home_dir(), relative_to_home_filename),
        )
    save_installed_files(installed_files)


def sync_installed_into_repo(
    maybe_repo_files=None, force_push=False
):  # not specifying files -> do all files
    """
    pulls updates from external files.  Errors if the files were modified in the repo before this update
    """
    copies_to_do = []
    installed_files = get_installed_files()
    for relative_to_repo_filename, relative_to_home_filename in iterate_over_files(
        maybe_repo_files, True
    ):
        abs_repo_path = os.path.join(get_repo_location(), relative_to_repo_filename)
        if (
            not force_push
            and get_hash(abs_repo_path) != installed_files[relative_to_home_filename]
        ):
            error("File was modified remotely - updating would overwrite!:", f)
        copies_to_do.append((relative_to_home_filename, relative_to_repo_filename))
    exit_on_error()
    for relative_to_home_filename, relative_to_repo_filename in copies_to_do:
        shutil.copy(
            os.path.join(get_home_dir(), relative_to_home_filename),
            os.path.join(get_repo_location(), relative_to_repo_filename),
        )
        installed_files[relative_to_home_filename] = get_hash(
            os.path.join(get_repo_location(), relative_to_repo_filename)
        )
    save_installed_files(installed_files)
    commit_and_push()


def add_installed_into_repo(non_host_specific_files, host_specific_files):
    """
    adds external files to repo.  errors if the files are already in the repo
    """
    pull()
    config = load_config()
    installed_files = get_installed_files()
    all_files = [(os.path.abspath(f), False) for f in non_host_specific_files] + [
        (os.path.abspath(f), True) for f in host_specific_files
    ]

    hostname = get_hostname()
    for f, is_host_specific in all_files:
        f = make_relative_to_home(f)
        if is_host_specific and type(config[f]) == dict and hostname in config[f]:
            error("File already added for hostname:", f)
        elif not host_specific_files and type(config[f]) == str:
            error("File already added:", f)
        elif (
            not host_specific_files
            and type(config[f]) == dict
            and "__default__" in config[f]
        ):
            error("File already added:", f)
    exit_on_error()

    installed_files = get_installed_files()
    for f, is_host_specific in all_files:
        f = make_relative_to_home(f)
        folder_in_repo = get_repo_location()
        if is_host_specific:
            folder_in_repo = os.path.join(get_repo_location(), hostname)
        repo_name = find_good_repo_name(folder_in_repo, f)

        if is_host_specific:
            if f not in config:
                config[f] = {}
            if type(config[f]) == str:
                config[f] = {"__default__": config[f]}
            config[f][hostname] = repo_name
        else:
            if f in config and type(config[f]) == dict:
                config[f]["__default__"] = repo_name
            else:
                config[f] = repo_name
        shutil.copy(
            os.path.join(get_home_dir(), f), os.path.join(folder_in_repo, repo_name)
        )
        installed_files[f] = get_hash(os.path.join(get_home_dir(), f))
    save_installed_files(installed_files)
    save_config(config)


def get_home_dir():
    home_dir = os.path.abspath(os.path.expanduser("~"))
    return home_dir


def make_relative_to_home(f):
    return os.path.relpath(os.path.abspath(f), get_home_dir())


def find_good_repo_name(base_folder, relative_to_home_filename):
    base_parts = []
    remainder = relative_to_home_filename
    remainder, base_part = os.path.split(remainder)
    if base_part.startswith("."):
        base_part = "_" + base_part
    base_parts = [base_part] + base_parts

    possible_name = os.path.join(base_folder, "__".join(base_parts))
    while os.path.exists(possible_name):
        remainder, base_part = os.path.split(remainder)
        if base_part.startswith("."):
            base_part = "_" + base_part
        base_parts = [base_part] + base_parts
        possible_name = os.path.join(base_folder, "__".join(base_parts))
    return possible_name


error_exists = False


def error(*args):
    print("ERROR:", *args)
    global error_exists
    error_exists = True


def exit_on_error():
    if error_exists:
        sys.exit(1)


def get_repo_location() -> str:
    return os.path.dirname(__file__)


def get_config_path() -> str:
    return os.path.join(get_repo_location(), "config.json")


def save_config(config) -> None:
    with open(get_config_path(), "w") as json_file:
        json.dump(config, json_file, indent=4, sort_keys=True)
    commit_and_push()


def load_config() -> dict[str, Union[dict[str, str], str]]:
    with open(get_config_path(), "r") as json_file:
        return json.load(json_file)


def get_installed_files_path() -> str:
    return os.path.join(get_repo_location(), "installed_files.json")


def get_installed_files() -> dict[str, str]:
    if not os.path.exists(get_installed_files_path()):
        return {}
    with open(get_installed_files_path(), "r") as json_file:
        return json.load(json_file)


def save_installed_files(installed_files) -> None:
    with open(get_installed_files_path(), "w") as json_file:
        json.dump(installed_files, json_file, indent=4, sort_keys=True)


def iterate_over_files(maybe_repo_files, only_installed_files=False):
    pull()
    config = load_config()
    installed_files = get_installed_files()
    hostname = get_hostname()
    if maybe_repo_files is not None:
        maybe_repo_files_set = set()
        for f in maybe_repo_files:
            maybe_repo_files_set.add(f)
            maybe_repo_files_set.add(os.path.abspath(f))
        maybe_repo_files = maybe_repo_files_set

    for relative_to_home_filename in config:
        if type(config[relative_to_home_filename]) == str:
            relative_to_repo_filename = config[relative_to_home_filename]
        elif hostname in config[relative_to_home_filename]:
            relative_to_repo_filename = config[relative_to_home_filename][hostname]
        else:
            relative_to_repo_filename = config[relative_to_home_filename]["__default__"]
        installed_filename = os.path.join(get_home_dir(), relative_to_home_filename)

        if maybe_repo_files is not None:
            if (
                installed_filename not in maybe_repo_files
                and relative_to_home_filename not in maybe_repo_files
                and relative_to_repo_filename not in maybe_repo_files
            ):
                continue
        if only_installed_files and relative_to_home_filename not in installed_files:
            continue
        yield relative_to_repo_filename, relative_to_home_filename


def get_hash(fname) -> str:
    with open(fname, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def get_hostname() -> str:
    return platform.node()


def pull():
    subprocess.check_call(["git", "pull"], cwd=get_repo_location())


def commit_and_push():
    subprocess.check_call(["git", "add", "-A"])
    subprocess.check_call(
        [
            "git",
            "commit",
            "-a",
            "-m",
            "Update from " + get_hostname() + "@" + str(datetime.datetime.now()),
        ]
    )
    subprocess.check_call(["git", "push"])


if __name__ == "__main__":
    main(sys.argv)
