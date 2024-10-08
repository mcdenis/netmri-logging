# NetMRI Logging

This Python module helps integrating the logging infrastructure of Python's
standard library with the Infoblox NetMRI Job system. Its main component is the
`NetMRIJobHandler` class. An instance of the latter forwards log records to the
NetMRI Job's "custom log". For convenience, the module also defines the
`create_logger` function.

## Example
```py
import logging
import netmri_logging
from infoblox_netmri.easy import NetMRIEasy

easy_args = { ... }

with NetMRIEasy(**easy_args) as easy:
    logger = netmri_logging.create_logger(easy, "LoggerName")
    logger.debug("Getting version info.")
    version = easy.send_command("show version")
    logger.info("Here is the version info:\n%s", version)
```