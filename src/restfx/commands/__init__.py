import os
import sys

from .commands import (
    run_command,
    register,
    command_help,
    command_create,
    command_version
)

register('help', command_help, 'Show this help message')
register('version', command_version, 'Show the version information')
register('create', command_create, 'Create restfx project structure', 'project-name')


def execute(argv=None):
    args = (argv or sys.argv)[1:]

    working_dir = os.path.abspath(os.path.curdir)

    if len(args) == 0:
        run_command(working_dir, 'help')
        return

    command_name = args.pop(0)
    run_command(working_dir, command_name, *args)
