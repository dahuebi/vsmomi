![alt text](https://travis-ci.org/dahuebi/vsmomi.svg?branch=master "travis build status")
![alt text](http://vsmomi.readthedocs.org/?badge=latest "readthedocs status")
vsmomi
======

VMWare vSphere CLI.

[vsmomi on travis](https://travis-ci.org/dahuebi/vsmomi?branch=master)
[vsmomi on readthedocs](http://vsmomi.readthedocs.org/)

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
# Linux
source rc.sh
# Windows
call rc.cmd
```

### TODO
* Add Commands: snapshot, customize
* Add Network interfaces to clone/edit
* Add Doc

### Full Help
```
usage: vs [-h] [--vcenter host] [--vc-user user] [--vc-pass password]
          [--auth auth.ini] [--save-auth]
          {clone,customize,destroy,edit,guest-delete,guest-download,guest-execute,guest-upload,ls,m2m,power,help,guest-mktemp}
          ...

positional arguments:
  {clone,customize,destroy,edit,guest-delete,guest-download,guest-execute,guest-upload,ls,m2m,power,help,guest-mktemp}
    clone               Clone VMs
    customize           Customize VMs
    destroy             Destroy VMs
    edit                Edit VM
    guest-delete        Delete from VMs
    guest-download      Download from VMs
    guest-execute       Execute on VMs
    guest-upload        Upload to VMs
    ls                  List VMs
    m2m                 Machine to machine interface
    power               Power VMs
    help                Show help of all command
    guest-mktemp        Delete from VMs

optional arguments:
  -h, --help            show this help message and exit
  --vcenter host        Hostname/IP of the VCenter
  --vc-user user        VCenter username
  --vc-pass password    VCenter password, may be base64 encoded
  --auth auth.ini       Load credentials from auth file
  --save-auth           Save/update auth file

--------------------------------------------------------------------------------
Command 'clone'
usage: vs clone [-h] [--snap <source snapshot>] --target target [target ...]
                [--disk-mode <disk-mode> [<disk-mode> ...]] [--cpus cpus]
                [--memory memory] [--extra-config key=value [key=value ...]]
                [--datastore datastore] [--host host] [--poweron]
                [--cms customization]
                name

positional arguments:
  name                  VM to clone from

optional arguments:
  -h, --help            show this help message and exit
  --snap <source snapshot>
                        Snapshot to clone from, default is latest
  --target target [target ...]
                        List of target VMs to create
  --disk-mode <disk-mode> [<disk-mode> ...]
                        Delta backing for disks, only store deltas, default to *all*
                          all: link all disks
                          none: copy all disks
                          ctrlNr-slotNr: link specific disk
  --cpus cpus           CPUs
  --memory memory       Memory in MB
  --extra-config key=value [key=value ...]
                        Extra config, use key=value
  --datastore datastore
                        Datastore name
  --host host           Host name (which host to place the new VMs on)
  --poweron             Power the cloned VMs on
  --cms customization   Path to customication file

--------------------------------------------------------------------------------
Command 'customize'
usage: vs customize [-h] [--cms customization]
                    [--nic-add <nic-add> [<nic-add> ...]]
                    name

positional arguments:
  name                  VM to clone from

optional arguments:
  -h, --help            show this help message and exit
  --cms customization   Path to customication file
  --nic-add <nic-add> [<nic-add> ...]
                        Customize network interfaces.
                        [mac=,ip=x.x.x.x/mask,gw=]

--------------------------------------------------------------------------------
Command 'destroy'
usage: vs destroy [-h] name [name ...]

positional arguments:
  name        VMs to destroy, name MUST match, no wildcard/regexps.

optional arguments:
  -h, --help  show this help message and exit

--------------------------------------------------------------------------------
Command 'edit'
usage: vs edit [-h] [--cpus cpus] [--memory memory]
               [--extra-config key=value [key=value ...]] [--network network]
               [--iso <[Datastore] path to iso>]
               [--disk-new <disk-new> [<disk-new> ...]]
               [--disk-linked <disk-linked> [<disk-linked> ...]]
               [--disk-destroy <ctrlNr-slotNr> [<ctrlNr-slotNr> ...]]
               name

positional arguments:
  name                  VM to edit

optional arguments:
  -h, --help            show this help message and exit
  --cpus cpus           CPUs
  --memory memory       Memory in MB
  --extra-config key=value [key=value ...]
                        Extra config, use key=value
  --network network     Set network for _ALL_ interfaces
  --iso <[Datastore] path to iso>
                        Load iso into cdrom, format:
                        [Datastore] <path to iso>
  --disk-new <disk-new> [<disk-new> ...]
                        Add a disk
                        [ctrlNr-slotNr,]size=capacity[mb|gb|tg]
  --disk-linked <disk-linked> [<disk-linked> ...]
                        Add a disk with delta backing
                        [<ctrlNr>-<slotNr>,]vm[:snapshot],<ctrlNr>-<slotNr>
  --disk-destroy <ctrlNr-slotNr> [<ctrlNr-slotNr> ...]
                        List of [controllerNumber-slotNumber] to delete, ex: 0-1 2-3

--------------------------------------------------------------------------------
Command 'guest-delete'
usage: vs guest-delete [-h] --guest-user user --guest-pass password --files
                       file [file ...]
                       pattern [pattern ...]

positional arguments:
  pattern               VMs to select

optional arguments:
  -h, --help            show this help message and exit
  --guest-user user     Guest username
  --guest-pass password
                        Guest password
  --files file [file ...]
                        Files to delete

--------------------------------------------------------------------------------
Command 'guest-download'
usage: vs guest-download [-h] --guest-user user --guest-pass password --files
                         file [file ...] [--host-dir host-dir]
                         pattern [pattern ...]

positional arguments:
  pattern               VMs to select

optional arguments:
  -h, --help            show this help message and exit
  --guest-user user     Guest username
  --guest-pass password
                        Guest password
  --files file [file ...]
                        Files to upload
  --host-dir host-dir   Host download directory, will be created.

--------------------------------------------------------------------------------
Command 'guest-execute'
usage: vs guest-execute [-h] --guest-user user --guest-pass password
                        [--cmd ...] [--timeout <timeout>]
                        pattern [pattern ...]

positional arguments:
  pattern               VMs to select

optional arguments:
  -h, --help            show this help message and exit
  --guest-user user     Guest username
  --guest-pass password
                        Guest password
  --cmd ...             Command to execute, will be joined.
  --timeout <timeout>   Command to execute, will be joined.

--------------------------------------------------------------------------------
Command 'guest-upload'
usage: vs guest-upload [-h] --guest-user user --guest-pass password --files
                       file [file ...] --guest-dir guest-dir
                       pattern [pattern ...]

positional arguments:
  pattern               VMs to select

optional arguments:
  -h, --help            show this help message and exit
  --guest-user user     Guest username
  --guest-pass password
                        Guest password
  --files file [file ...]
                        Files to upload
  --guest-dir guest-dir
                        Guest upload directory, will be created.

--------------------------------------------------------------------------------
Command 'ls'
usage: vs ls [-h] [-l | -s] [pattern [pattern ...]]

positional arguments:
  pattern     VM Patterns to list, start with ~ for regexp

optional arguments:
  -h, --help  show this help message and exit
  -l          List extended.
  -s          List only names.

--------------------------------------------------------------------------------
Command 'm2m'
usage: vs m2m [-h]

optional arguments:
  -h, --help  show this help message and exit

--------------------------------------------------------------------------------
Command 'power'
usage: vs power [-h] (--on | --off | --reset | --shutdown | --halt | --reboot)
                pattern [pattern ...]

positional arguments:
  pattern     VMs to select

optional arguments:
  -h, --help  show this help message and exit
  --on
  --off
  --reset
  --shutdown
  --halt
  --reboot

--------------------------------------------------------------------------------
Command 'help'
usage: vs help [-h]

optional arguments:
  -h, --help  show this help message and exit

--------------------------------------------------------------------------------
Command 'guest-mktemp'
usage: vs guest-mktemp [-h] --guest-user user --guest-pass password
                       [--prefix prefix] [--suffix suffix]
                       pattern [pattern ...]

positional arguments:
  pattern               VMs to select

optional arguments:
  -h, --help            show this help message and exit
  --guest-user user     Guest username
  --guest-pass password
                        Guest password
  --prefix prefix       Prefix
  --suffix suffix       Suffix
```
