import os


def compile_less():
    root = os.path.dirname(__file__)
    dir_name = os.path.abspath(os.path.join(root, 'src/restfx/internal_assets/styles'))

    import lesscpy

    for file in os.listdir(dir_name):
        file_path = os.path.join(dir_name, file)
        if not os.path.isfile(file_path) or not file.lower().endswith('.less'):
            continue

        print('Compiling file %s' % file)
        with open(file_path, encoding='utf8') as fp:
            output_content = lesscpy.compile(fp, minify=True)

        output_file = os.path.splitext(file_path)[0] + '.css'
        with open(output_file, mode='w', encoding='utf8') as fp:
            fp.write(output_content)

    print('Compiled!')


if __name__ == '__main__':
    compile_less()
