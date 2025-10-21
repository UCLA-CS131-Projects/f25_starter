DEBUG_MODE = True  # Toggle for debugging
INFO_MODE = True  # Toggle for general information
indent_amount = 0  # Tracks current indentation level for functions

# Color for print statements
BLUE = "\033[94m"
RESET = "\033[0m"


def debug(msg):
    global indent_amount
    if DEBUG_MODE:
        print(" " * indent_amount + f"DEBUG: {msg}")


def info(msg):
    global indent_amount
    if INFO_MODE:
        print(" " * indent_amount + f"INFO: {msg}")


def debug_logger(func):
    def wrapper(*args, **kwargs):
        global indent_amount
        if DEBUG_MODE:
            print(" " * indent_amount + f"{BLUE}Entering: {func.__name__}{RESET}")
            indent_amount += 2  # Increase indentation for nested calls
        result = func(*args, **kwargs)
        if DEBUG_MODE:
            indent_amount -= 2  # Decrease indentation after exiting
            print(" " * indent_amount + f"{BLUE}Exiting: {func.__name__}{RESET}")
        return result

    return wrapper


def debug_logger_with_return_val(func):
    def wrapper(*args, **kwargs):
        global indent_amount
        if DEBUG_MODE:
            print(" " * indent_amount + f"{BLUE}Entering: {func.__name__}{RESET}")
            indent_amount += 2  # Increase indentation for nested calls
        result = func(*args, **kwargs)
        if DEBUG_MODE:
            indent_amount -= 2  # Decrease indentation after exiting
            print(
                " " * indent_amount
                + f"{BLUE}Exiting: {func.__name__} with return value: {result}{RESET}"
            )
        return result

    return wrapper
