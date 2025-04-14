# from setuptools import setup, find_packages

# import version


# setup(
#     name='sicredi_etl',
#     version=version.VERSION,

#     description='ETL for Sicredi',
#     long_description=open('README.md').read(),

#     author='Matheus Dos S. Silva',
#     author_email='mattheusxs@gmail.com',

#     packages=find_packages(exclude=['venv', 'dist', 'docs', 'tests']),
#     py_modules=[
#         'main',
#         'version'
#     ],
#     install_requires=[
#         'requests==2.28.2',
#         'polars==0.16.13',
#         'loguru==0.6.0',
#         'google-cloud-bigquery==3.7.0'
#         'xlsx2csv==0.8.1',
#         'Flask',
#         'pytest',
#         'coverage',
#         'pytest-cov',
#         'pytest-html',
#         'mock',
#         'pylint',
#         'autopep8',
#         'unidecode'
#     ],
#     classifiers=[
#         'Development Status :: 5 - Production/Stable',
#         'Environment :: Console',
#         'Intended Audience :: Developers',
#         'Operating System :: POSIX',
#         'Programming Language :: Python :: 3.11.8',
#         'Topic :: Scientific/Engineering :: Information Analysis'
#     ],
#     entry_points='''
#         [console_scripts]
#         spb_etl=main:cli
#     '''
# )
