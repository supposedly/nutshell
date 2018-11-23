import setuptools
import re

VERSION = None
with open('nutshell/__init__.py') as f:
    VERSION = re.search(r"^__version__\s*=\s*'(\d+\.\d+\.\d+\w*)'", f.read(), re.MULTILINE).group(1)

if VERSION is None:
    raise RuntimeError('Missing or invalid version number')

PACKAGES = [
  'nutshell',
  'nutshell.tools',
  'nutshell.tools.icons',
  'nutshell.common',
  'nutshell.segment_types',
  'nutshell.segment_types.colors',
  'nutshell.segment_types.icons',
  'nutshell.segment_types.nutshell',
  'nutshell.segment_types.table',
  'nutshell.segment_types.table.lark_assets',
  ]

setuptools.setup(
  name='nutshell',
  author='Wright',
  license='GPL',
  version=VERSION,
  packages=PACKAGES,
  include_package_data=True,
  url='https://github.com/eltrhn/nutshell',
  description="Transpiler from a powerful alternative cellular-automaton-specification language to Golly's",
  install_requires=['bidict', 'ergo>=0.4.7'],  #, 'lark-parser'],
  python_requires='>=3.6',
  entry_points={
    'console_scripts': [
      'nutshell-ca=nutshell.main:main'
    ]
  }
)
