import logging


class SafeUsernameFormatter(logging.Formatter):
    def format(self, record):
        # If username is not present, set a default value
        if not hasattr(record, 'username'):
            record.username = 'N/A'
        return super().format(record)
