import logging


class Logger:

    def __init__(self, filename):
        logging.basicConfig(
            filename=f"logger\loggs\{filename}", level=logging.INFO)

    def log_debug(self, message):
        logging.debug(message)

    def log_info(self, message):
        logging.info(message)

    def log_warning(self, message):
        logging.warning(message)

    def log_error(self, message):
        logging.error(message)
