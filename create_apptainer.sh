apptainer build --sandbox ubuntu_sandbox docker://ubuntu:22.04
apptainer shell --fakeroot --writable ubuntu_sandbox

(enter apptainer) 

apt-get update
apt-get install -y wget ca-certificates gcc make perl openssl

wget https://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/chainCleaner -O /usr/local/bin/chainCleaner
wget https://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/chainNet -O /usr/local/bin/chainNet
wget https://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/chainSort -O /usr/local/bin/chainSort
wget -L https://github.com/ucscGenomeBrowser/kent/blob/master/src/hg/mouseStuff/chainCleaner/NetFilterNonNested.perl -O /usr/local/bin/NetFilterNonNested.perl

chmod -R +x /usr/local/bin/

(exit out of the apptainer)

apptainer build chaincleaner.sif ubuntu_sandbox
