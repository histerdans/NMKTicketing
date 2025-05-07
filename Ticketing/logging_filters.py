import logging

class DeleteActionFilter(logging.Filter):
    def filter(self, record):
        # Customize to check for 'delete' keyword; adjust this as needed
        return 'delete' in record.getMessage().lower()