#!/usr/bin/env python

from distutils.core import setup

setup(name="sked",
    version="0.2",
    description="The wikish scheduler",
    author="Alexandre Erwin Ittner",
    author_email="alexandre@ittner.com.br",
    url="http://wikisked.sourceforge.net/",
    license="GNU GPL version 2",
    long_description="""
Sked is a personal organizer, calendar, schedule and braindump application
with a wiki-like syntax for text formatting and organization. It's easier
think of it as the result of the merge of a calendar with a desktop wiki.
""",
    packages=["libsked"],
    package_data={"libsked": [ "*.ui", "sked.dtd", "help.xml", "sked.png" ] },
    scripts=["sked"],
    data_files=[
        ('share/doc/sked', ["README", "COPYING"]),
        ('share/applications', ["sked.desktop"]),
        ('share/pixmaps', ["libsked/sked.png"])
    ]
)
