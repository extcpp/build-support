#!/usr/bin/python3
import re

from obi.util.path import remove_from_front, change_ext
from .. import logger as log
from ..common import Operation, OperationState, Status

g_guard_re = re.compile(r"#ifndef\s+_?(?P<guard>EXT_.*(HEADER|HPP|H))")


class IncludeGuardState(OperationState):
    def __init__(self, access):
        super(IncludeGuardState, self).__init__(access)  # creates a copy of access


class IncludeGuard(Operation):
    def __init__(self, op):
        super(IncludeGuard, self).__init__("IncludeGuard", op)
        self.dry_run = False
        self.file_types = (".h", ".hpp")  # must be tuple
        self.do_log = False
        self.mark_start = True

    @classmethod
    def create_state(cls, *args, **kwags):
        return IncludeGuardState(*args, **kwags)

    def read_file(self, state: OperationState) -> Status:
        state.line_for_infdef = 0
        state.starting = True
        state.insert_new = True  # else fix old

        # hpp h to header
        path = state.project_path
        if path.parts[1] == "ext":
            path = remove_from_front(state.project_path, "include")
        path = change_ext(path, "_HEADER")
        state.guard = "_".join(path.parts).upper()
        return Status.OK

    def read_line(self, state: OperationState):
        if state.starting and (state.line_content.startswith("//") or state.line_content == "\n"):
            state.line_for_infdef = state.line_num
        else:
            state.starting = False

        if state.line_content.startswith("#"):
            if state.line_content.startswith("#pragma once") and state.insert_new:
                state.line_for_infdef = state.line_num

            match = g_guard_re.search(state.line_content)

            if match:
                state.line_for_infdef = state.line_num
                if match["guard"] == state.guard:
                    state.access = []
                    return Status.OK_SKIP_FILE
                else:
                    state.insert_new = False
                    return Status.OK_NEXT_ACCESS

        return Status.OK_NEXT_LINE

    def modify_file(self, OperationState):
        return Status.OK

    def modify_line(self, state: IncludeGuardState):
        out = state.replacement_file_handle

        # insert new
        if state.insert_new:
            if state.line_for_infdef == state.line_num:
                log.info("insert new gurad in")
                out.write(state.line_content)
                out.write("#ifndef {}\n".format(state.guard))
                out.write("#define {}\n".format(state.guard))
                return Status.OK
            elif state.line_num == "EOF":
                out.write("#endif // {}".format(state.guard))
                return Status.OK_REPLACE

        # fix old
        if not state.insert_new:
            if state.line_for_infdef == state.line_num:
                out.write("#ifndef {}\n".format(state.guard))
                out.write("#define {}\n".format(state.guard))
                return Status.OK
            elif state.line_for_infdef + 1 == state.line_num:
                return Status.OK
            elif state.line_num == "EOF":
                return Status.OK_REPLACE

        # just copy rest of file
        out.write(state.line_content)
        return Status.OK_NEXT_LINE
