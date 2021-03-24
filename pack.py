import os

from tarfile import TarFile


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


if __name__ == '__main__':
    print('Packaging sample')
    root = os.path.dirname(__file__)
    sampledir = os.path.abspath(os.path.join(root, 'src/restfx/internal_assets/sample'))
    tarname = os.path.abspath(os.path.join(root, 'src/restfx/internal_assets/sample.tar.gz'))

    try:
        tar_dir(tarname, sampledir)
        print('Complete!\n')
    except Exception as e:
        print('Failure:' + str(e))
        exit(1)
