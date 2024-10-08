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


class NetMRIJobHandler(_deps.logging.Handler):

    def __init__(self,
                 netmri: _deps.NetMRIEasy,
                 level: _deps.typing.Union[int, str] = 0) -> None:
        super().__init__(level)
        self.netmri = netmri


    def emit(self, record: _deps.logging.LogRecord) -> None:
        level = record.levelname.casefold()

        # Validate logging level
        if level not in _JOB_LOGGING_LEVELS:
            raise ValueError(f"Logging level `{record.levelname}` not supported by NetMRI's Job system. Supported values are: {[l.upper() for l in _JOB_LOGGING_LEVELS]}.")
        
        # Forward log record to NetMRI. Don't use `NetMRIEasy.log_message` as it
        # does formatting and we want to use this handler's formatter instead.
        self.netmri.broker("Job").log_custom_message(JobID=self.netmri.batch_id,
                                                     JobDetailID=self.netmri.job_id,
                                                     severity=record.levelname.lower(),
                                                     message=self.format(record))
        

def create_logger(netmri: _deps.NetMRIEasy,
                  name: str,
                  format: str = "[%(asctime)s] [%(levelname)s] %(message)s") -> _deps.logging.Logger:
    """
    Create a logger for a NetMRI Job script or library.

    :param netmri: NetMRI Easy instance bound to the running Job.
    :param name: name of the logger to create. Should not be `root` or the empty
        string cause otherwise, the program may freeze (no idea why.)
    :param format: format of the string representation of the log records. As
        per `logging.Formatter`.
    """
    
    handler = NetMRIJobHandler(netmri)
    handler.setFormatter(_deps.logging.Formatter(format))
    logger = _deps.logging.getLogger(name)
    logger.setLevel(_deps.logging.DEBUG)
    logger.addHandler(handler)
    return logger