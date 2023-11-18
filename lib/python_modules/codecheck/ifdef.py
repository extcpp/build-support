#!/usr/bin/python3
import re

from .common import Operation, OperationState, Status

g_ifdef_re = re.compile(r"^#[ \t]*(if(n?def)?)[ \t]+(?P<if_value>.*)$")
g_endif_re = re.compile(r"^#[ \t]*endif(?P<endif_space>([ \t])*)(?P<endif_value>.*)$")


class IfDefState(OperationState):
    def __init__(self, access):
        super(IfDefState, self).__init__(access)  # creates a copy of access


class IfDef(Operation):
    def __init__(self, op):
        super(IfDef, self).__init__("IfDef", op)
        self.dry_run = False
        self.file_types = (".h", ".hpp", ".c", ".cpp", ".cc")  # must be tuple
        self.do_log = False
        self.mark_start = True

    @classmethod
    def create_state(cls, *args, **kwags):
        return IfDefState(*args, **kwags)

    def read_file(self, state: OperationState) -> Status:
        state.replacements = []
        state.stack = []  # used for matchinga
        return Status.OK

    def read_line(self, state: OperationState):
        match = g_ifdef_re.match(state.line_content)
        if match:
            state.stack.append((state.line_num, match["if_value"]))
            return Status.OK_NEXT_LINE

        match = g_endif_re.match(state.line_content)
        if match:
            if_value_pair = state.stack.pop()
            space = match["endif_space"]
            if not space:
                space = " "
            target_endif_value = r"#endif{}// {}{}".format(space, if_value_pair[1], "\n")
            if target_endif_value is not state.line_content:
                state.replacements.append((state.line_num, target_endif_value))

        return Status.OK_NEXT_LINE

    def modify_file(self, state: OperationState):
        if not state.replacements:
            return Status.OK_SKIP_FILE
        else:
            state.replacements.reverse()
            return Status.OK

    def modify_line(self, state: IfDefState):
        out = state.replacement_file_handle
        if state.line_num == "EOF":
            return Status.OK_REPLACE
        else:
            if state.replacements:
                pair = state.replacements[-1]
                if pair[0] == state.line_num:
                    out.write(pair[1])
                    state.replacements.pop()
                    return Status.OK_NEXT_LINE

        out.write(state.line_content)
        return Status.OK_NEXT_LINE
