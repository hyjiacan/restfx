from restfx import __meta__


def print_meta(append=None):
    info = '{name} {version}'.format(name=__meta__.name, version=__meta__.version)
    if append is not None:
        info += '  <%s>' % append

    project_url = __meta__.website

    info_len = len(info)
    url_len = len(project_url)

    if info_len > url_len:
        max_len = info_len
        project_url = project_url.center(info_len, ' ')
    else:
        max_len = url_len
        info = info.center(url_len, ' ')

    line_width = '-' * (max_len + 8)
    print("#{line}#\n|    {info}    |\n|    {url}    |\n#{line}#\n".format(
        line=line_width, info=info, url=project_url))
