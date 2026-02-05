import logging
import os

APP_NAME = "agents"
LOG_DIR_BASE = f"./artifacts/{APP_NAME}"

def get_user_session_logger(user_id: str, session_id: str, specified_name: str="") -> logging.logger:
    """
    Gets or creates a logger for a specific session.
    A new FileHandler is added only if one doesn't already exist.
    """

    # Use the session_id as the logger name
    logger = logging.getLogger(f"{specified_name}{'_' if specified_name else ''}{session_id}")
    logging.debug(f"new logger {logger.handlers=}")

    if not logger.handlers:

        logger.setLevel(logging.DEBUG)

        log_dir = f"{LOG_DIR_BASE}/{user_id}/{session_id}"
        os.makedirs(log_dir, exist_ok=True)
        logger.debug(f"Start logging into file for user {user_id} session {session_id}. Dir: {log_dir}")

        log_file_path = os.path.join(log_dir, f"{session_id}.log")
        file_handler = logging.FileHandler(log_file_path)

        formatter = logging.Formatter(
            '%(asctime)s - **%(name)s** - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        logger.propagate = False

    return logger