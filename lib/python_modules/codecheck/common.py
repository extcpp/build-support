#!/usr/bin/python3
from enum import Enum
from pathlib import Path
from typing import IO

from . import logger as log


class Status(Enum):
    OK = 0
    OK_NEXT_LINE = 1
    OK_NEXT_ACCESS = 2
    OK_SKIP_FILE = 3
    OK_REPLACE = 4
    FAIL = 5
    FAIL_FATAL = 6

    def __int__(self):
        return self.value


def is_good(status: Status):
    return status in (Status.OK, Status.OK_NEXT_LINE, Status.OK_NEXT_ACCESS, Status.OK_SKIP_FILE, Status.OK_REPLACE)


def is_done(status: Status):
    """check if ths status indicates that the work with the file is done"""
    return status in (Status.OK_REPLACE, Status.OK_SKIP_FILE, Status.FAIL_FATAL)


def to_simple_ok(status: Status):
    """convert any good status to a plain Status.OK"""
    if is_good(status):
        return Status.OK
    else:
        return status


class Access(Enum):
    READ = 1
    MODIFY = 2


class OperationState:
    """This is a basic state/context for operationo. Operations can use it to
    store information and to request further acesses by modifying the acesss
    list.
    """

    project_path: Path
    file_path: Path
    file_handle: IO
    line_content: str

    def reset_for_next_pass(self):
        self.project_path = None
        self.file_path = None
        self.replacement_file_handle = None
        self.line_num = None
        self.line_content = None

    def __init__(self, access):
        self.access = list(access)
        self.reset_for_next_pass()


class Operation:
    """An Operation proesses a file. It can consist of serveral read and wirte
    acesses. The most basic operation is a verifaction that uses just one read
    access. More complex operations may use serveral read and write accesses to
    gather information, modify the file, and do a final verifaction.
    """

    def __init__(self, name: str, access: Access):
        log.info("create {} with {}".format(name, access))
        self.name = name
        self.dry_run = True
        self.do_log = False
        self.do_log_detail = False
        # a list that contains the pending accesses
        # access are worked on in list order
        self.access = []

        if access is None:
            pass
        elif access == Access.MODIFY:
            self.access.append(Access.READ)
            self.access.append(Access.MODIFY)
        elif access == Access.READ:
            self.access.append(Access.READ)

    def access_line(self, state: OperationState):
        if self.do_log_detail:
            log.info("{} {}".format(state.line_num, state.line_content))

        if state.replacement_file_handle:
            return self.modify_line(state)
        else:
            return self.read_line(state)

    def access_file(self, state):
        if self.do_log:
            log.info("{}".format(self.name))
            log.info("{}".format(state.project_path))

        if state.replacement_file_handle:
            return self.modify_file(state)
        else:
            return self.read_file(state)

    def new_state(self):
        return self.create_state(self.access)
