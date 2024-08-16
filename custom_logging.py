import logging
import sqlite3
import datetime
import termcolor
import logging.handlers

# Define the color mapping
COLORS = {
    "WARNING": "yellow",
    "INFO": "white",
    "DEBUG": "blue",
    "CRITICAL": "red",
    "ERROR": "red",
}

# Custom formatter with color support
class ColoredFormatter(logging.Formatter):
    def __init__(self, fmt, use_color=True):
        logging.Formatter.__init__(self, fmt)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            def colored(text, color):
                return termcolor.colored(text, color=color, attrs=["bold"])

            record.levelname2 = colored("{:<7}".format(record.levelname), COLORS[levelname])
            record.message2 = colored(record.msg, COLORS[levelname])

            asctime2 = datetime.datetime.fromtimestamp(record.created)
            record.asctime2 = termcolor.colored(asctime2, color="green")

            record.module2 = termcolor.colored(record.module, color="cyan")
            record.funcName2 = termcolor.colored(record.funcName, color="cyan")
            record.lineno2 = termcolor.colored(record.lineno, color="cyan")
        else:
            record.levelname2 = record.levelname
            record.message2 = record.msg
            record.asctime2 = record.asctime
            record.module2 = record.module
            record.funcName2 = record.funcName
            record.lineno2 = record.lineno

        return logging.Formatter.format(self, record)

# Database connection class
class ConnectDB:
    def __init__(self):
        self.connection = sqlite3.connect('database/logging.db')
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS LOGS (
                FILE_NAME TEXT,
                FUNCTION_NAME TEXT,
                FILE_NO TEXT,
                MESSAGE TEXT,
                LOAD_TIME DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')


    def execute_query(self, sql, params=None):
        if params:
            self.cursor.execute(sql, params)
        else:
            self.cursor.execute(sql)

    def close_connection(self):
        self.connection.commit()
        self.connection.close()

# Custom handler for logging to the database
class CustomHandler(logging.StreamHandler):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def emit(self, record):
        datenow = datetime.datetime.now()
        query = """
        INSERT INTO LOGS (FILE_NAME, FUNCTION_NAME, FILE_NO, MESSAGE, LOAD_TIME)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (record.filename, record.funcName, record.lineno, record.msg, datenow)
        self.db.execute_query(query, params)

if __name__ == '__main__':
    db = ConnectDB()

    # Logger setup
    logger = logging.getLogger('logging')
    logger.setLevel(logging.DEBUG)

    # Custom handler for logging to the database
    custom_handler = CustomHandler(db)

    # Stream handler with colored formatting
    stream_handler = logging.StreamHandler()
    handler_format = ColoredFormatter(
        "%(asctime2)s [%(levelname2)s] %(module2)s:%(funcName2)s:%(lineno2)s - %(message2)s"
    )
    stream_handler.setFormatter(handler_format)
    
    # Rotating file handler
    rotating_handler = logging.handlers.RotatingFileHandler(
        'app.log', maxBytes=1048576, backupCount=5
    )
    rotating_handler.setFormatter(handler_format)

    # Adding handlers to the logger
    logger.addHandler(custom_handler)
    logger.addHandler(stream_handler)
    logger.addHandler(rotating_handler)

    try:
        logger.debug('This is debug')
        logger.info('This is info')
        logger.warning('This is warning')
        logger.error('This is error')
        1/0
    except ZeroDivisionError as e:
        logger.critical(f'This is critical: {e}')
    finally:
        db.close_connection()
