#!/usr/bin/env python

from distutils.core import setup
import libsked

setup(name="sked",
    version=libsked.VERSION,
    description="The wikish scheduler",
    author="Alexandre Erwin Ittner",
    author_email="alexandre@ittner.com.br",
    url="http://wikisked.sourceforge.net/",
    license="GNU GPL version 2 or later",
    long_description="""
Sked is a personal organizer, calendar, schedule and braindump application
with a wiki-like syntax for text formatting and organization. It is easier
think of it as the result of the merge of a calendar with a desktop wiki.

Sked is designed to optimize your workflow and everything is tailored to speed
up editing operations: links and styles are unobtrusively inferred from the
syntax, entries are automatically saved after a few seconds, almost all
commands have keyboard shortcuts, and the last entries are kept in a history.
Also, the wiki code is *not* hidden from the editing interface -- this makes
editing easier, avoids the create/view/change cycle, and allows you to copy
and paste text among other applications without loss of information. An
user-defined delay is given before the text reformatting, so its appearance
will not change while you are typing.

All entries are stored in a compressed and encrypted database in your $HOME
directory. The encryption aims protect the information even from a skilled
adversary.
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
