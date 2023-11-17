#!/usr/bin/python3
import re

from . import logger as log
from .common import Operation, OperationState, Status, Access

g_nofix_re = re.compile(r"//.*HDR_NOFIX")
g_copy_re = re.compile(r"//.*Copyright.*Jan Christoph Uhde")
g_copy_exact_re = re.compile(r"// Copyright - ((20\d{2}|xxxx)(-20\d{2})?) - Jan Christoph Uhde <Jan@UhdeJC.com>")
g_copy_format = (
    "// Copyright - {} - Jan Christoph Uhde <Jan@UhdeJC.com>\n"
    + "// Please see LICENSE.md for license or visit https://github.com/extcpp/basics\n"
)


class CopyrightState(OperationState):
    def __init__(self, access: Access):
        super(CopyrightState, self).__init__(access)


class Copyright(Operation):
    def __init__(self, op):
        super(Copyright, self).__init__("Copyright", op)
        self.dry_run = False
        self.file_types = (".h", ".hpp", ".c", ".cpp", ".cc")  # must be tuple
        self.do_log = False
        self.mark_start = True

    @classmethod
    def create_state(cls, *args, **kwags):
        return CopyrightState(*args, **kwags)

    def read_file(self, state: OperationState) -> Status:
        state.line_for_copyright = 0
        state.insert_new = True  # fix old if set to False
        return Status.OK

    def read_line(self, state: OperationState):
        if g_nofix_re.search(state.line_content):
            state.access = []
            return Status.OK_SKIP_FILE
        if g_copy_re.search(state.line_content):
            state.line_for_copyright = state.line_num
            state.insert_new = False

            if g_copy_exact_re.match(state.line_content):
                state.access = []
                return Status.OK_SKIP_FILE
            else:
                return Status.OK_SKIP_LINEWISE_ACCESS

        return Status.OK

    def modify_file(self, state: OperationState):
        out = state.replacement_file_handle
        if state.insert_new:
            log.info("insert {}".format(str(state.insert_new)))
            out.write(g_copy_format.format("2023"))

            with open(state.file_path, "r") as infile:
                out.write(infile.read())

            return Status.OK_REPLACE

        return Status.OK

    def modify_line(self, state: CopyrightState):
        assert not state.insert_new
        out = state.replacement_file_handle

        # need to fix
        if state.line_num == state.line_for_copyright:
            out.write(g_copy_format.format("xxxx-2020"))
            return Status.OK
        elif state.line_num == "EOF":
            return Status.OK_REPLACE

        # just copy rest of file
        out.write(state.line_content)
        return Status.OK
