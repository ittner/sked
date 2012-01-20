# norootforbuild  

# spec file for package Sked
# Copyright 2010 Alexandre Erwin Ittner <alexandre@ittner.com.br>
# Distributed under the GNU GPL version 2 or later.

Name: sked
Summary: A wiki-based personal organizer, calendar, schedule application
Version: 0.6
Release: 1
Url: http://wikisked.sourceforge.net/
License: GPLv2+
Vendor: Alexandre Erwin Ittner <alexandre@ittner.com.br>
Group: Office

Source0: %{name}-%{version}.tar.gz
Autoreqprov: on
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}

BuildArch: noarch
Requires: python-levenshtein, python-dbus
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
python setup.py install --prefix=%{_prefix} --root=$RPM_BUILD_ROOT

%clean
python setup.py clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc README COPYING
%{_prefix}/bin/sked
%{_prefix}/lib/python*/site-packages/libsked/
%{_prefix}/lib/python*/site-packages/sked*.egg-info
%{_prefix}/share/applications/sked.desktop
%{_prefix}/share/man/man1/*
%{_prefix}/share/pixmaps/*

%changelog
* Fri Jan 20 2012 Alexandre Erwin Ittner <alexandre at ittner.com.br> 0.6-1
- Update package to version 0.6.

* Thu Oct 01 2010 Alexandre Erwin Ittner <alexandre at ittner.com.br> 0.5-1
- Update package to version 0.5.

* Thu Sep 30 2010 Alexandre Erwin Ittner <alexandre at ittner.com.br> 0.4-1
- New RPM

