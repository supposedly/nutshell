import setuptools

packages = [
  'nutshell',
  'nutshell.common',
  'nutshell.segment_types',
  'nutshell.segment_types.colors',
  'nutshell.segment_types.icons',
  'nutshell.segment_types.nutshell',
  'nutshell.segment_types.table',
  ]

setuptools.setup(
  name='nutshell',
  license='GPL',
  version='0.1.0',
  author='wright',
  packages=packages,
  include_package_data=True,
  url='https://github.com/eltrhn/nutshell',
  description="Transpiler from an alternative CA-rule-spec language to Golly's",
  install_requires=['bidict', 'ergo>=0.4.4',],  # & lark later on
  python_requires='>=3.6',
  entry_points={
      'console_scripts': [
          'nutshell-ca=nutshell.main:main'
      ]
  }
)
