# norootforbuild  

# spec file for package Sked
# Copyright 2010 Alexandre Erwin Ittner <alexandre@ittner.com.br>
# Distributed under the GNU GPL version 2 or later.

Summary: The wikish scheduler
Name: sked
Version: 0.4
Release: 1
Source0: %{name}-%{version}.tar.gz
License: GPLv2+
Group: Productivity/Office/Organizers
Autoreqprov: on
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Alexandre Erwin Ittner <alexandre@ittner.com.br>
Url: http://wikisked.sourceforge.net/
Requires: python-levenshtein
BuildRequires: python

%description
Sked is a personal organizer, calendar, schedule and braindump application
with a wiki-like syntax for text formatting and organization. It is easier
think of it as the result of the merge of a calendar with a desktop wiki.

%prep
%setup -n %{name}-%{version}

%build
python setup.py build

%install
python setup.py install --no-compile --prefix=/usr/ --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
