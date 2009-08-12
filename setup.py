#!/usr/bin/env python

from distutils.core import setup

setup(name="Sked",
    version="0.1",
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
    package_data={"libsked": [ "sked.glade", "sked.dtd"] },
    scripts=["sked"]
)
