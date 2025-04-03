###########################################################################
## Export of Script Module: netmri_logging
## Language: Python
## Category: Internal
## Description: Integrates the Python logging infrastructure with NetMRI.
###########################################################################
class _deps:
    import logging
    import typing

    from infoblox_netmri.easy import NetMRIEasy


_JOB_LOGGING_LEVELS = "debug", "error", "warning", "info"
"""
Logging levels of a NetMRI Job.

From
https://<netmri-host>/netmri/help/netmri_help/netmri_help.tdf#NetMRI_Help/perl_methods.htm#chapter_16_job_scripting_1301933438_1098987

Values are case-folded.
"""


_closed_name = f"_{__name__}__closed"
"""
Name of the attribute indicating that the NetMRIEasy instance has been closed.
Follows Python's name mangling convention since this attribute is for private
use of this module only.
"""


class _NetMRIClose(_deps.typing.Protocol):
    """
    Type of the `NetMRI.close_sessions` method.
    """
    
    def __call__(_, self: _deps.NetMRIEasy) -> str: # type: ignore
        ...


def _netmri_close_patch(
            close: _NetMRIClose
        ) -> _NetMRIClose:
    """
    Decorator for the `NetMRIEasy.close_session` method that sets a boolean attribute on
    the instance indicating that the method has been called. The name of the
    attribute is defined in `_closed_name` attribute of this module.
    """
    
    def decorator(
            self: _deps.NetMRIEasy) -> str:
        setattr(self, _closed_name, True)
        return close(self)
    return decorator


def _patch_netmri(netmri: _deps.NetMRIEasy) -> None:
    netmri_type = type(netmri)
    if not hasattr(netmri_type, _closed_name):
        netmri_type.close_session = _netmri_close_patch(
            netmri_type.close_session)
        # Set closed attribute now. We can then check whether the class has
        # already been patched by checking the existence of the attribute.
        setattr(netmri_type, _closed_name, False)


_sending_count = 0
"""
How many records are being sent at the moment by any instance of the
`NetMRIJobHandler` class.
"""


class NetMRIJobHandler(_deps.logging.Handler):

    def __init__(self,
                 netmri: _deps.NetMRIEasy,
                 level: _deps.typing.Union[int, str] = 0) -> None:
        super().__init__(level)
        _patch_netmri(netmri)
        self.netmri = netmri


    def emit(self, record: _deps.logging.LogRecord) -> None:
        global _sending_count
        
        # Disregard a log record if it is the result of sending a previous log
        # record (avoid infinite recursion) or if the NetMRI instance has been
        # exited. Not thread safe, but works with a single thread.
        if _sending_count > 0 or getattr(self.netmri, _closed_name, False):
            return

        _sending_count+=1
        
        level = record.levelname.casefold()

        # Validate logging level
        if _deps.logging.raiseExceptions and level not in _JOB_LOGGING_LEVELS:
            raise ValueError(f"Logging level `{record.levelname}` not supported by NetMRI's Job system. Supported values are: {[l.upper() for l in _JOB_LOGGING_LEVELS]}.")
        
        # Forward log record to NetMRI. Don't use `NetMRIEasy.log_message` as it
        # does formatting and we want to use this handler's formatter instead.
        self.netmri.broker("Job").log_custom_message(JobID=self.netmri.batch_id,
                                                     JobDetailID=self.netmri.job_id,
                                                     severity=record.levelname.lower(),
                                                     message=self.format(record))
        _sending_count-=1
        

def create_logger(netmri: _deps.NetMRIEasy,
                  name: str,
                  formatter: _deps.typing.Optional[_deps.logging.Formatter] = None) -> _deps.logging.Logger:
    """
    Create a logger for a NetMRI Job script or library.

    :param netmri: NetMRI Easy instance bound to the running Job.
    :param name: name of the logger to create. Should not be `root` or the empty
        string cause otherwise, the program may freeze (no idea why.)
    :param format: format of the string representation of the log records. As
        per `logging.Formatter`.
    """

    DEFAULT_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"
    
    handler = NetMRIJobHandler(netmri)
    handler.setFormatter(formatter or _deps.logging.Formatter(DEFAULT_FORMAT))
    logger = _deps.logging.getLogger(name)
    logger.setLevel(_deps.logging.DEBUG)
    logger.addHandler(handler)
    return logger