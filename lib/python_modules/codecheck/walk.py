#!/usr/bin/python3
import sys
import os
from pathlib import Path
from typing import IO

from . import logger as log
from codecheck.common import Status, Access, Operation, OperationState, to_simple_ok, is_done, is_good
from codecheck.configuration import Configuration


def execute_operation(
    full_path: Path, project_path: Path, replacement_file_handle: IO, operation: Operation, state: OperationState
) -> Status:
    state.project_path = project_path
    state.file_path = full_path
    state.replacement_file_handle = replacement_file_handle

    status = operation.access_file(state)
    if is_done(status) or not is_good(status):
        return status

    with open(full_path) as source_file_handle:
        for state.line_num, state.line_content in enumerate(source_file_handle):
            status = operation.access_line(state)
            if is_done(status):
                return status

        if not is_done(status):
            state.line_num = "EOF"
            state.line_content = ""
            status = operation.access_line(state)

    return status


def handle_file(conf: Configuration, full_path: Path, operation: Operation):
    project_path = full_path.relative_to(conf.project_root)

    log.debug("---> " + str(full_path))

    # assert that we have path objects
    assert project_path.parts
    assert full_path.parts

    state = operation.new_state()
    status = None

    while state.access:
        access = state.access.pop(0)

        # creates a file handle to which the operation result will be written
        if access == Access.MODIFY:
            if operation.dry_run:
                log.info("dryrun on target {}".format(full_path))
                status = execute_operation(full_path, project_path, sys.stdout, operation, state)
                assert status.name
            else:
                target_file = full_path.parent.joinpath(full_path.name + ".replacement")
                with open(target_file, "w") as replacement_file_handle:
                    status = execute_operation(full_path, project_path, replacement_file_handle, operation, state)

                if status == Status.OK_REPLACE:
                    log.info("replace {}".format(project_path))
                    os.rename(target_file, full_path)
                    break
                else:
                    os.unlink(target_file)

        elif access == Access.READ:
            status = execute_operation(full_path, project_path, None, operation, state)

        if status is Status.OK_NEXT_ACCESS:
            continue

        if is_done(status) or not is_good(status):
            break

    log.debug("<--- handle file " + status.name)
    return status


def check_modify_source(config: Configuration):
    def to_full_path(root, path):
        return Path(root).joinpath(path)

    def to_full_path_string(root, path):
        return str(to_full_path(root, path))

    def should_include_path(root, path, include):
        full_path = to_full_path_string(root, path)

        if full_path.startswith(tuple(include)):
            return True

        for i in include:
            if i.startswith(full_path):
                return True

        return False

    log.info("project_root {}".format(config.project_root))

    # NOTE:
    # project_root and root are NOT the same

    include = [str(config.project_root.joinpath(d)) for d in config.dirs]
    exclude = [str(config.project_root.joinpath(d)) for d in config.dirs_to_exclude]  # or files
    log.debug("to include: {} ".format(include))
    log.debug("to exclude: {} ".format(exclude))

    for operation in config.operations:
        if not operation.access:
            continue

        log.info(operation.name)

        for root, dirs, files in os.walk(config.project_root):
            log.debug("dirs in: {} ".format(dirs))
            dirs[:] = [d for d in dirs if should_include_path(root, d, include)]
            log.debug("dirs out: {} ".format(dirs))

            if root in exclude:
                continue

            for filename in files:
                filename = Path(filename)
                full_path = to_full_path(root, filename)
                assert full_path.parts

                if str(full_path) in exclude:
                    continue

                if filename.suffix in operation.file_types:
                    status = handle_file(config, full_path, operation)
                    if not is_good(status):
                        return status

    return Status.OK
