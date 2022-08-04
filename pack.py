import os
import sys
import time

from tarfile import TarFile

from less import compile_less


def tar_dir(archive_path: str, dir_path: str):
    try:
        # 删除旧文件
        if os.path.exists(archive_path):
            os.remove(archive_path)
        # 创建 tar 保存文件夹
        if not os.path.exists(os.path.dirname(archive_path)):
            os.makedirs(os.path.dirname(archive_path))

        # 创建 tar 文件
        archive = TarFile.open(archive_path, 'w:gz')
        # 压缩文件
        # +1: / 符号
        prefix_len = len(dir_path) + 1
        for (current, dirs, files) in os.walk(dir_path):
            if current.endswith('__pycache__'):
                continue
            for file in files:
                absfile = os.path.join(current, file)
                relfile = absfile[prefix_len:]
                archive.add(absfile, arcname=relfile)
        archive.close()

        # 返回
        if os.path.exists(archive_path):
            return True, ''
        return False, '打包文件夹失败'
    except Exception as e:
        return False, e.__str__()


def package_sample():
    print('Packaging sample')
    root = os.path.dirname(__file__)
    sample_dir = os.path.abspath(os.path.join(root, 'src/restfx/internal_assets/sample'))
    tar_name = os.path.abspath(os.path.join(root, 'src/restfx/internal_assets/sample.tar.gz'))

    # 将依赖写到示例的 requirements.txt 上
    source_file = os.path.join(root, 'requirements/production.txt')
    target_file = os.path.join(sample_dir, 'requirements.txt')

    with open(source_file, mode='rb') as source:
        with open(target_file, mode='wb') as target:
            target.write(source.read())

    try:
        tar_dir(tar_name, sample_dir)
        print('Package complete!\n')
        time.sleep(1)
    except Exception as e:
        print('Failure:' + str(e))
        sys.exit(1)
    finally:
        # 删除
        os.unlink(target_file)


def renew_version():
    # 用法
    # build 版本号
    # 未传版本号参数时表示不更新版本号
    import sys
    new_version = None if len(sys.argv) == 1 else sys.argv[1]
    if new_version is None:
        return

    print('Renewing version onto %r...' % new_version)

    root = os.path.dirname(__file__)
    meta_file = os.path.abspath(os.path.join(root, 'src/restfx/__meta__.py'))

    try:
        with open(meta_file, mode='r', encoding='utf8') as fp:
            lines = fp.readlines()
        # 版本在第二行，可以写死
        version_line = lines[1].strip()
        version = version_line.split('=')[1].strip(' \'')
        print('The old version is %s' % version)
        [major, minor, build] = version.split('.')
        if new_version == 'auto':
            build = int(build) + 1
            new_version = '%s.%s.%s' % (major, minor, build)

        print('The new version is %r' % new_version)

        lines[1] = 'version = \'%s\'\n' % new_version
        lines[2] = 'version_info = (%s, %s, %s)\n' % (major, minor, build)

        with open(meta_file, mode='w', encoding='utf8') as fp:
            fp.writelines(lines)
        print('Renew version complete!\n')
        time.sleep(1)
    except Exception as e:
        print('Failure:' + str(e))
        import sys
        sys.exit(1)


if __name__ == '__main__':
    compile_less()
    package_sample()
    renew_version()
