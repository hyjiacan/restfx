import os
import sys
import uuid

from restfx import __meta__
from restfx.util import helper

_COMMANDS = {}


def register(command_name: str, handler, description: str = None, args: str = None):
    _COMMANDS[command_name] = {
        'name': command_name,
        'handler': handler,
        'arguments': args,
        'description': '' if description is None else description
    }


def run_command(working_dir: str, command_name: str, *args):
    helper.print_meta(command_name)

    command = get_command(command_name)
    if command is None:
        return
    try:
        command['handler'](working_dir, *args)
    except Exception as e:
        raise e


def get_command(command_name: str):
    if command_name not in _COMMANDS:
        print('Command %s not found' % command_name)
        return None
    return _COMMANDS[command_name]


def get_commands():
    return [
        '%s%s\t%s' % (
            command['name'],
            (' <%s>' % command['arguments']) if command['arguments'] else '',
            command['description']
        )
        for command in _COMMANDS.values()
    ]


# noinspection PyUnusedLocal
def command_help(*argv):
    commands = get_commands()
    print("""Usage: {name} <command> [arguments]

Commands:
\t{commands}

Documentation links:
    https://gitee.com/hyjiacan/restfx
    https://github.com/hyjiacan/restfx
""".format(name=__meta__.name,
           commands='\n\t'.join(commands)))


# noinspection PyUnusedLocal
def command_version(*argv):
    print('Version: ' + __meta__.version)


# noinspection PyUnusedLocal
def command_create(working_dir: str, project_name, *argv):
    print('working-dir:' + working_dir)
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    project_path = os.path.abspath(os.path.join(working_dir, project_name))

    print('Creating restfx project "%s"' % project_name)

    if os.path.exists(project_path):
        print('[ERROR] Project path "%s" exists.' % project_path)
        sys.exit(1)

    # 示例文件
    sample_file = os.path.abspath(os.path.join(pkg_root, 'internal_assets', 'sample.tar.gz'))
    print('Creating project structure')
    import tarfile
    tarfile = tarfile.open(sample_file)
    tarfile.extractall(project_path)
    tarfile.close()

    print('Generating APP ID')
    # 生成 uuid
    setting_file = os.path.abspath(os.path.join(project_path, 'settings.py'))
    with open(setting_file, mode='r', encoding='utf8') as fp:
        lines = fp.readlines()
        app_id = uuid.uuid4()
        print(app_id)
        # 在第5行
        lines[5] = "APP_ID = '%s'%s" % (app_id, os.linesep)

    with open(setting_file, mode='w', encoding='utf8') as fp:
        fp.writelines(lines)

    print("""Created !

Now you can enjoy restfx.
""".format(project_name=project_name))
