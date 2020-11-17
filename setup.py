import re

import setuptools

with open("src/restfx/__init__.py", encoding="utf8") as f:
    version = re.search(r'__version__ = ([\'"])(.*?)\1', f.read()).group(2)

setuptools.setup(
    name='restfx',
    version=version,
    install_requires=[
        'Werkzeug>=1.0.0'
    ]
)
