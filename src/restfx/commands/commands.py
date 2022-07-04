import os
import sys
import uuid

from .. import __meta__
from ..util import helper

_COMMANDS = {}


def register(command_name: str, handler, description: str = '', args: str = ''):
    """

    :param command_name: 命令名称
    :param handler: 命令的处理函数
    :param description: 命令的描述
    :param args: 命令参数描述，如： -i interface -m mask
    :return:
    """
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
        return False
    try:
        command['handler'](working_dir, *args)
        return True
    except Exception as e:
        raise e


def get_command(command_name: str):
    if command_name not in _COMMANDS:
        print('Command %r not found' % command_name)
        return None
    return _COMMANDS[command_name]


def get_commands():
    return [
        '%s %s\t%s' % (
            command['name'],
            command['arguments'],
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
    https://gitee.com/wangankeji/restfx
    https://github.com/wangankeji/restfx
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

    command_genid(project_path)

    print("""Created !

It is time to have fun with restfx.
""".format(project_name=project_name))


# noinspection PyUnusedLocal
def command_genid(working_dir: str, *argv):
    print('working-dir:' + working_dir)
    project_path = os.path.abspath(working_dir)
    # 生成 uuid
    setting_file = os.path.abspath(os.path.join(project_path, 'settings.py'))

    if not os.path.isfile(setting_file):
        raise IOError('File settings.py not found at path:' + working_dir)

    print('Generating APP ID')

    with open(setting_file, mode='r', encoding='utf8') as fp:
        lines = fp.readlines()

    found = False
    idx = -1
    for line in lines:
        idx += 1
        if not line.startswith('APP_ID = '):
            continue
        found = True
        break

    app_id = uuid.uuid4().hex
    app_line = "APP_ID = '%s'\n" % app_id

    if found:
        lines[idx] = app_line
    else:
        lines.append(app_line)
        lines.append('\n')

    with open(setting_file, mode='w', encoding='utf8') as fp:
        fp.writelines(lines)

    print('App ID generated: ' + app_id)
