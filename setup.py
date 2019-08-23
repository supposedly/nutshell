import setuptools
import re

VERSION = None
with open('nutshell/__init__.py') as f:
    VERSION = re.search(r"^__version__\s*=\s*'(\d+\.\d+\.\d+\w*)'", f.read(), re.MULTILINE).group(1)

if VERSION is None:
    raise RuntimeError('Missing or invalid version number')

class PackageLister:
    def __getitem__(self, args):
        if not isinstance(args, tuple):
           args = [args]
        ret = []
        for i in args:
            if isinstance(i, slice):
                ret.append(i.start)
                ret.extend(map(f'{i.start}.'.__add__, i.stop))
            else:
                ret.append(i)
        return ret
f = PackageLister()

# setuptools.find_packages() misses quite a few
# Easier just to maintain this
PACKAGES = f[
  'nutshell': f[
    'tools': f['icons'],
    'common',
    'segment_types': f[
      'colors',
      'icons',
      'nutshell',
      'table': f['lark_assets', 'inline_rulestring']
      ]
    ]
  ]

setuptools.setup(
  name='nutshell',
  author='Wright',
  license='GPL',
  version=VERSION,
  packages=PACKAGES,
  include_package_data=True,
  url='https://github.com/supposedly/nutshell',
  description="Transpiler from a powerful alternative cellular-automaton-specification language to Golly's",
  install_requires=['bidict', 'kizbra>=0.5.1'],  #, 'lark-parser'],
  python_requires='>=3.6',
  entry_points={
    'console_scripts': [
      'nutshell-ca=nutshell.main:main'
    ]
  }
)
