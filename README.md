![alt text](https://travis-ci.org/dahuebi/vsmomi.svg?branch=master "travis build status")

vsmomi
======

VMWare vSphere CLI.

[pyvmomi](https://github.com/vmware/pyvmomi) (VMware vSphere API Python Bindings).

### Example Usage

##### List Virtual Machines
```
vs ls
vs ls -l # long
vs ls -s # short
```

### Install
```
git clone https://github.com/dahuebi/vsmomi.git
cd vsmomi
virtualenv .
source bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PWD
```

### TODO
* Add Commands: snapshot, customize
* Add Doc
