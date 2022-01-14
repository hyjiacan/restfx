import os
import sys

from .commands import (
    run_command,
    register,
    command_help,
    command_create,
    command_version, command_genid
)

register('help', command_help, 'Show this help message')
register('version', command_version, 'Show the version information')
register('create', command_create, 'Create restfx project structure', 'project-name')
register('genid', command_genid, 'Generate a new id for app')


def execute(working_dir: str, argv=None):
    args = (argv or sys.argv)[1:]

    working_dir = working_dir or os.path.abspath(os.path.curdir)

    if len(args) == 0:
        return run_command(working_dir, 'help')

    command_name = args.pop(0)
    return run_command(working_dir, command_name, *args)
