#!/bin/bash

set -e

rm distfiles output *.log *.h5 -rf
mkdir distfiles

wget -O - http://ftp.debian.org/debian/dists/stable/main/source/Sources.gz | gunzip >> distfiles/Sources
#wget -O - http://ftp.debian.org/debian/dists/stable-updates/main/source/Sources.gz | gunzip >> distfiles/Sources
#wget -O - http://security.debian.org/debian-security/dists/stable/updates/main/source/Sources.gz | gunzip >> distfiles/Sources

PACKAGES=$(grep ^Package: distfiles/Sources |sort -u| sed 's/Package: //')
pv distfiles/Sources | python load_sources.py

wget -O - http://ftp.debian.org/debian/dists/stable/main/binary-all/Packages.gz | gunzip >> distfiles/Packages
wget -O - http://ftp.debian.org/debian/dists/stable/main/binary-amd64/Packages.gz | gunzip >> distfiles/Packages
#wget -O - http://ftp.debian.org/debian/dists/stable-updates/main/binary-amd64/Packages.gz | gunzip >> distfiles/Packages
#wget -O - http://security.debian.org/debian-security/dists/stable/updates/main/binary-all/Packages.gz | gunzip >> distfiles/Packages

pv distfiles/Packages | python load_packages.py

wget -O - http://ftp.debian.org/debian/dists/stable/main/i18n/Translation-en.bz2 | bunzip2 >> distfiles/Translation-en
#wget -O - http://ftp.debian.org/debian/dists/stable-updates/main/i18n/Translation-en.bz2 | bunzip2 >> distfiles/Translation-en
#wget -O - http://security.debian.org/debian-security/dists/stable/updates/main/i18n/Translation-en.bz2 | bunzip2 >> distfiles/Translation-en

pv distfiles/Translation-en | python load_descriptions.py

if ! [ -d metadata.ftp-master.debian.org/changelogs ]; then
rm downloadlist* -f
  for PACKAGE in $PACKAGES; do
    LETTER=$(echo $PACKAGE |cut -c1)
    [ 1$(echo $PACKAGE |cut -c-3) = 1'lib' ] && LETTER=$(echo $PACKAGE |cut -c-4)
    echo http://metadata.ftp-master.debian.org/changelogs/main/$LETTER/$PACKAGE/stable_copyright >> downloadlist
    echo http://metadata.ftp-master.debian.org/changelogs/main/$LETTER/$PACKAGE/stable_changelog >> downloadlist
  done

wget  -x --continue -i downloadlist

  for PACKAGE in $PACKAGES; do
    LETTER=$(echo $PACKAGE |cut -c1)
    [ 1$(echo $PACKAGE |cut -c-3) = 1'lib' ] && LETTER=$(echo $PACKAGE |cut -c-4)
    [ -f metadata.ftp-master.debian.org/changelogs/main/$LETTER/$PACKAGE/stable_copyright ] || echo http://metadata.ftp-master.debian.org/changelogs/main/$LETTER/$PACKAGE/stable_$PACKAGE.copyright >> downloadlist404
  done

wget -x --continue -i downloadlist404

fi

python load_copyright.py metadata.ftp-master.debian.org/changelogs/main/*/*/stable_copyright | tee cp_import.log
python load_changelog.py metadata.ftp-master.debian.org/changelogs/main/*/*/stable_changelog | tee cl_import.log

python export.py
python export_json.py

echo empty files: > broken
find output -type f -empty >> broken
find output -type f -empty -delete

echo no license: >> broken
grep "Project license" output/* -c |grep :0|sed 's/:0//' >> broken
grep "Project license" output/* -c |grep :0|sed 's/:0//'|xargs rm


