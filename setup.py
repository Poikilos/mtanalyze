import setuptools
import sys
import os

versionedModule = {}
versionedModule['urllib'] = 'urllib'
if sys.version_info.major < 3:
    versionedModule['urllib'] = 'urllib2'


install_requires = []

if os.path.isfile("requirements.txt"):
    with open("requirements.txt", "r") as ins:
        for rawL in ins:
            line = rawL.strip()
            if len(line) < 1:
                continue
            install_requires.append(line)

description = (
    "Automate the installation of any source with zero"
    " configuration. The source can be a zip or gz binary"
    " package, appimage, directory, or executable file."
)
long_description = description
if os.path.isfile("readme.md"):
    with open("readme.md", "r") as fh:
        long_description = fh.read()

setuptools.setup(
    name='mtanalyze',
    version='0.3.0',
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        ('License :: OSI Approved ::'
         ' GNU General Public License v3 or later (GPLv3+)'),
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Installation/Setup',
    ],
    keywords='python install installer deb debian AppImage shortcut',
    url="https://github.com/poikilos/mtanalyze",
    author="Jake Gustafson",
    author_email='7557867+poikilos@users.noreply.github.com',
    license='GPLv3+',
    # packages=setuptools.find_packages(),
    packages=['mtanalyze'],
    include_package_data=True,  # look for MANIFEST.in
    # scripts=['example'],
    # ^ Don't use scripts anymore (according to
    #   <https://packaging.python.org/en/latest/guides
    #   /distributing-packages-using-setuptools
    #   /?highlight=scripts#scripts>).
    entry_points={
        'console_scripts': [
            'minebest=mtanalyze.minebest:main'
        ],
    },
    install_requires=install_requires,
    # versionedModule['urllib'],
    # ^ "ERROR: Could not find a version that satisfies the requirement
    #   urllib (see nopackage) (from versions: none)
    # ERROR: No matching distribution found for urllib"
    # (urllib imports fine in Python3 on Fedora 35 though
    # pip uninstall urllib and pip uninstall urllib2 do nothing)
    test_suite='nose.collector',
    tests_require=['nose'],
    zip_safe=True,
)
