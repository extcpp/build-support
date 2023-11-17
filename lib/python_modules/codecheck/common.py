#!/usr/bin/python3
from enum import Enum
from pathlib import Path
from typing import IO

from . import logger as log


class Status(Enum):
    OK = 0
    OK_REPLACE = 1  # file was repaced
    OK_SKIP_FILE = 2  # file can be skipped
    OK_SKIP_LINEWISE_ACCESS = 3
    FAIL = 4  # failure
    FAIL_FATAL = 5  # failure forcing exit

    def __int__(self):
        return self.value

    @classmethod
    def is_good(cls, status):
        cls.check(status)
        return status in (Status.OK, Status.OK_REPLACE, Status.OK_SKIP_FILE, Status.OK_SKIP_LINEWISE_ACCESS)

    @classmethod
    def is_done(cls, status, linewise=False):
        """check if ths status indicates that the work with the file is done"""
        cls.check(status)
        if linewise:
            return status == Status.OK_SKIP_LINEWISE_ACCESS
            #  return status in (Status.OK, Status.OK_SKIP_LINEWISE_ACCESS)
        else:
            return status in (Status.OK_REPLACE, Status.OK_SKIP_FILE, Status.FAIL_FATAL, Status.FAIL_FATAL)

    @classmethod
    def to_simple_ok(cls, status):
        """convert any good status to a plain Status.OK"""
        cls.check(status)
        if cls.is_good(status):
            return Status.OK
        else:
            return status

    @classmethod
    def check(cls, status):
        assert status.name
        if status is None:
            raise ValueError("status can not be None")


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
