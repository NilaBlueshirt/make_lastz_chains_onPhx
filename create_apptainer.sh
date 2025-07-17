apptainer build --sandbox ubuntu_sandbox docker://ubuntu:22.04
apptainer shell --fakeroot --writable ubuntu_sandbox

# Enter apptainer
apt-get update
apt-get install -y wget ca-certificates gcc make perl openssl

# Here we only install the necessary binaries
# Note that the links point to the newest release, the ones we used were v482 from June 2025
wget https://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/chainCleaner -O /usr/local/bin/chainCleaner
wget https://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/chainNet -O /usr/local/bin/chainNet
wget https://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/chainSort -O /usr/local/bin/chainSort

# If the whole kent distribution is need:
# apt-get install -y rsync
# rsync -azvP rsync://hgdownload.soe.ucsc.edu/genome/admin/exe/linux.x86_64/ /usr/local/bin/

# This perl file (Commit fbdd299) supports chainCleaner, and the verion we have here is the same one Michael has in the make_lastz_chains repo
wget -L https://github.com/ucscGenomeBrowser/kent/blob/master/src/hg/mouseStuff/chainCleaner/NetFilterNonNested.perl -O /usr/local/bin/NetFilterNonNested.perl

chmod -R +x /usr/local/bin/

# Exit out of the apptainer
exit

apptainer build example.sif ubuntu_sandbox
