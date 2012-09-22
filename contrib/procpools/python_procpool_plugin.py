"""
This is a plugin for the Evennia services.

To add, simply add the path to this module
("contrib.procpools.python_procpool_plugin") to the
settings.SERVER_SERVICES_PLUGIN_MODULES list and reboot the server.

If you want to adjust the defaults, copy this file to
game/gamesrc/conf/, re-point settings.SERVER_SERVICES_PLUGINS_MODULES
and edit the file there. This is to avoid eventual upstream
modifications to this file.

It is not recommended to use this with an SQLite3 database, at least
if you plan to do many out-of-process database write - SQLite3 does
not work very well with a high frequency of off-process writes due to
file locking clashes.

"""
import os
from django.conf import settings


# Process Pool setup

# convenient flag to turn off process pool without changing settings
PROCPOOL_ENABLED = True
# relay process stdout to log (debug mode, very spammy)
PROCPOOL_DEBUG = True
# max/min size of the process pool. Will expand up to max limit on demand.
PROCPOOL_MIN_NPROC = 5
PROCPOOL_MAX_NPROC = 20
# after sending a command, this is the maximum time in seconds the process
# may run without returning. After this time the process will be killed
PROCPOOL_TIMEOUT = 15
# maximum time (seconds) a process may idle before being pruned from pool (if pool bigger than minsize)
PROCPOOL_IDLETIME = 20
# only change if the port clashes with something else on the system
PROCPOOL_HOST = 'localhost'
PROCPOOL_PORT = 5001
# 0.0.0.0 means listening to all interfaces
PROCPOOL_INTERFACE = '0.0.0.0'
# user-id and group-id to run the processes as (for OS:es supporting this).
# If you plan to run unsafe code one could experiment with setting this
# to an unprivileged user.
PROCPOOL_UID = None
PROCPOOL_GID = None
# real path to a directory where all processes will be run. If
# not given, processes will be executed in game/.
PROCPOOL_DIRECTORY = None


# don't need to change normally
SERVICE_NAME = "PythonProcPool"

# plugin hook

def start_plugin_services(server):
    """
    This will be called by the Evennia Server when starting up.

    server - the main Evennia server application
    """
    if not PROCPOOL_ENABLED:
        return

    # terminal output
    print '  amp (Process Pool): %s' % PROCPOOL_PORT

    from contrib.procpools.ampoule import main as ampoule_main
    from contrib.procpools.ampoule import service as ampoule_service
    from contrib.procpools.ampoule import pool as ampoule_pool
    from contrib.procpools.ampoule.main import BOOTSTRAP as _BOOTSTRAP
    from contrib.procpools.python_procpool import PythonProcPoolChild

    # for some reason absolute paths don't work here, only relative ones.
    apackages = ("twisted",
                 os.path.join(os.pardir, "contrib", "procpools", "ampoule"),
                 os.path.join(os.pardir, "ev"),
                 os.path.join(os.pardir))
    aenv = {"DJANGO_SETTINGS_MODULE":"settings",
            "DATABASE_NAME":settings.DATABASES.get("default", {}).get("NAME") or settings.DATABASE_NAME}
    if PROCPOOL_DEBUG:
        _BOOTSTRAP = _BOOTSTRAP % "log.startLogging(sys.stderr)"
    else:
        _BOOTSTRAP = _BOOTSTRAP % ""

    procpool_starter = ampoule_main.ProcessStarter(packages=apackages,
                                                   env=aenv,
                                                   path=PROCPOOL_DIRECTORY,
                                                   uid=PROCPOOL_UID,
                                                   gid=PROCPOOL_GID,
                                                   bootstrap=_BOOTSTRAP,
                                                   childReactor=os.name == 'nt' and "select" or "epoll")
    procpool = ampoule_pool.ProcessPool(name=SERVICE_NAME,
                                        min=PROCPOOL_MIN_NPROC,
                                        max=PROCPOOL_MAX_NPROC,
                                        recycleAfter=500,
                                        timeout=PROCPOOL_TIMEOUT,
                                        ampChild=PythonProcPoolChild,
                                        starter=procpool_starter)
    procpool_service = ampoule_service.AMPouleService(procpool,
                                                      PythonProcPoolChild,
                                                      PROCPOOL_PORT,
                                                      PROCPOOL_INTERFACE)
    procpool_service.setName(SERVICE_NAME)
    # add the new services to the server
    server.services.addService(procpool_service)


