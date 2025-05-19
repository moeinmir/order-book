import functools
import inspect
import traceback
import sys
import logging
logger = logging.getLogger(__name__)

def log_variables_and_return(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__qualname__
        bound_args = inspect.signature(func).bind(*args, **kwargs)
        bound_args.apply_defaults()
        logger.info(f"[CALL] {func_name}({bound_args.arguments})")
        try:
            result = func(*args, **kwargs)
            current_frame = sys._getframe()
            previous_frame = current_frame.f_back
            local_vars = previous_frame.f_locals
            logger.info(f"[LOCALS after {func_name}] {local_vars}")
            logger.info(f"[RETURN] {func_name} => {result}")
            return result
        except Exception as e:
            logger.error(f"[EXCEPTION] {func_name}: {e}")
            logger.error(traceback.format_exc())
            raise
    return wrapper
