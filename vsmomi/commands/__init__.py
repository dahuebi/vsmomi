

from .clone import Clone
from .customize import Customize
from .destroy import Destroy
from .edit import Edit
from .guest_delete import GuestDelete
from .guest_download import GuestDownload
from .guest_execute import GuestExecute
from .guest_upload import GuestUpload
from .guest_mktemp import GuestMkTemp
from .ls import Ls
from .m2m import M2M
from .power import Power
from .snapshot import Snapshot
from .help import Help

commands = [
    Clone,
    Customize, 
    Destroy,
    Edit,
    GuestDelete,
    GuestDownload,
    GuestExecute,
    GuestUpload,
    Ls,
    M2M,
    Power,
    Snapshot,
    Help,
    GuestMkTemp,
]
