import re

import setuptools

with open("src/restfx/__meta__.py", encoding="utf8") as f:
    version = re.search(r'version = ([\'"])(.*?)\1', f.read()).group(2)

setuptools.setup(
    name='restfx',
    version=version,
    install_requires=[
        'Werkzeug>=2.0.3',
        'MarkupSafe>=2.0.1',
    ]
)
