import logging

# Todo: see if running a second logger is a good way to pass export run status eg INFO level

def get_logger(log_name: str = None,
               stream_logging_level: str = "DEBUG",
               file_handler: bool = False,
               file_logging_level: str = "WARNING"):
	# Todo: archive log files regularly
	if not log_name:
		log_name = __name__

	logger = logging.getLogger(log_name)
	logger.setLevel("DEBUG")

	# Main console logging handler
	# Todo: allow console logging selection in app config
	ch = logging.StreamHandler()
	ch.setLevel(stream_logging_level)
	ch_formatter = logging.Formatter("{levelname}:{name}:{funcName}:{message}",
	                                 style="{")
	ch.setFormatter(ch_formatter)
	logger.addHandler(ch)

	# Optional debug-only console logging handler
	def show_only_debug(record):
		return record.levelname == "DEBUG"

	dch = logging.StreamHandler()
	dch.setLevel("DEBUG")
	dch_formatter = logging.Formatter("{levelname}:{name}:{funcName}:{message}",
	                                    style="{")
	dch.setFormatter(dch_formatter)
	dch.addFilter(show_only_debug)
	logger.addHandler(dch)

	# Main file logging handler
	# Todo: look into (timed) rotating log files
	if file_handler:
		fh = logging.FileHandler("logging/app.log",
		                         mode="a",
		                         encoding="utf-8")
		fh.setLevel(file_logging_level)
		fh_formatter = logging.Formatter("{asctime}{levelname}:{name}:{message}",
		                                 style="{",
		                                 datefmt="%Y-%m-%d %H:%M:%S")
		fh.setFormatter(fh_formatter)
		logger.addHandler(fh)

	return logger



# Todo: decide whether to add custom level for export run status
# https://earthly.dev/blog/logging-in-python/

# Define the custom log level
VERBOSE = 15
logging.VERBOSE = VERBOSE
logging.addLevelName(logging.VERBOSE, 'VERBOSE')

# Set up basic logging configuration for the root logger
logging.basicConfig(level=logging.DEBUG)

# Define a custom logging method for the new level
def verbose(self, message, *args, **kwargs):
    if self.isEnabledFor(logging.VERBOSE):
        self._log(logging.VERBOSE, message, args, **kwargs)

# Add the custom logging method to the logger class
logging.Logger.verbose = verbose

# Create a logger instance
logger = logging.getLogger()

# Log a message using the custom level and method
logger.verbose("This is a verbose message")