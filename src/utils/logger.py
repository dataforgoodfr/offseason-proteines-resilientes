from logging import INFO, FileHandler, Formatter, Logger, StreamHandler, getLogger


def set_up_root_logger(log_file=None, level=INFO) -> Logger:
    """
    Sets up the root logger.
    """

    root_logger = getLogger("")
    root_logger.setLevel(level)
    formatter = Formatter("%(name)-12s: %(levelname)-8s %(message)s")

    console = StreamHandler()
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    if log_file is not None:
        file = FileHandler(log_file, mode="w")
        file.setFormatter(formatter)
        root_logger.addHandler(file)

    return root_logger
