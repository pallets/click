from .core import Option
import logging


def simplelog(*args, **kwargs):

    """ Decorator to add a very simple logging facility to scripts

    For parameters see SimpleLog.__init__
    """

    def make_simplelog(f):

        return SimpleLog(f, **kwargs)

    return make_simplelog


class SimpleLog(object):

    __name__ = "SimpleLog"

    def __init__(self, callback, verbose_help=None, debug_help=None,
                 quiet_help=None, remove_args=False, verbose_args=None,
                 debug_args=None, quiet_args=None, verbose_arg_name=None,
                 debug_arg_name=None, quiet_arg_name=None,
                 default_level=None, quiet_level=None, verbose_level=None,
                 debug_level=None, logger_name=None, flavor=None):

        """ Handler class for SimpleLog

        :param verbose_help: Override the text displayed for the verbose
                     parameter [Enable verbose logging]
        :param debug_help: Override the text displayed for the debug parameter
                           [Enable debugging]
        :param quiet_help: Override the text displayed for the quiet parameter
                           [Enable quiet mode]
        :param remove_args: Remove the logging arguments, so they are not
                            submitted to the main command [Disabled]
        :param verbose_args: List of arguments for the "verbose"-setting
                             [--verbose and -v]
        :param debug_args: List of arguments for the "debug"-setting
                           [--debug and -d]
        :param quiet_args: List of arguments for the "quiet"-setting
                           [--quiet and -q]
        :param verbose_arg_name: Name of the "verbose" argument [verbose]
        :param debug_arg_name: Name of the "debug" argument [debug]
        :param quiet_arg_name: Name of the "quiet" argument [quiet]
        :param default_level: Default level [logging.ERROR]
        :param verbose_level: Level for "verbose"-setting [logging.INFO]
        :param debug_level: Level for "debug"-setting [logging.DEBUG]
        :param quiet_level: Level for "quiet"-setting [logging.CRITICAL]
        :param logger_name: Logger to configure [root-logger]
        :param flavor: Parameter-flavor to use:
                       * qvd: Usage of --quiet, --verbose and --debug parameters
                       * vvv: Usage mulitple -v parameters (Uses
                         "Increase verbosity" for verbose_help-parameter and the
                         verbose_args and verbose_arg_name)
        """

        self.callback = callback

        self.verbose_help = verbose_help or None
        self.debug_help = debug_help or "Enable debugging"
        self.quiet_help = quiet_help or "Enable quiet mode"
        self.remove_args = remove_args or False
        self.verbose_args = verbose_args or ["--verbose", "-v"]
        self.debug_args = debug_args or ["--debug", "-d"]
        self.quiet_args = quiet_args or ["--quiet", "-q"]
        self.verbose_arg_name = verbose_arg_name or "verbose"
        self.debug_arg_name = debug_arg_name or "debug"
        self.quiet_arg_name = quiet_arg_name or "quiet"
        self.default_level = default_level or logging.ERROR
        self.verbose_level = verbose_level or logging.INFO
        self.debug_level = debug_level or logging.DEBUG
        self.quiet_level = quiet_level or logging.CRITICAL
        self.logger_name = logger_name or None
        self.flavor = flavor or "qvd"

        if self.flavor == "qvd":

            self.verbose_help = "Enable verbose logging"

            self.__click_params__ = [
                Option(
                    [self.verbose_arg_name] + self.verbose_args,
                    is_flag=True,
                    help=self.verbose_help
                ),
                Option(
                    [self.debug_arg_name] + self.debug_args,
                    is_flag=True,
                    help=self.debug_help
                ),
                Option(
                    [self.quiet_arg_name] + self.quiet_args,
                    is_flag=True,
                    help=self.quiet_help
                )
            ]

        elif self.flavor == "vvv":

            self.verbose_help = "Increase verbosity"

            self.__click_params__ = [
                Option(
                    [self.verbose_arg_name] + self.verbose_args,
                    count=True,
                    help=self.verbose_help
                )

            ]

        else:

            raise Exception("Unknown Flavor value %s" % self.flavor)

        if hasattr(callback, "__click_params__"):

            # Add parameters of the original command as well

            self.__click_params__ = self.__click_params__ + \
                callback.__click_params__

    def __call__(self, *args, **kwargs):

        """ Call the main program, but set up logging first
        """

        verbose = False
        debug = False
        quiet = False

        if self.flavor == "qvd":

            verbose = kwargs[self.verbose_arg_name]
            debug = kwargs[self.debug_arg_name]
            quiet = kwargs[self.quiet_arg_name]

        elif self.flavor == "vvv":

            verbosity = kwargs[self.verbose_arg_name]

            if verbosity == 0:

                quiet = True

            elif verbosity == 1:

                # Meaning the default, which is already set above

                pass

            elif verbosity == 2:

                verbose = True

            elif verbosity > 2:

                debug = True

            else:

                raise Exception("Verbosity had an unknown value %s" % verbosity)

        else:

            raise Exception("Unknown Flavor value %s" % self.flavor)

        if self.remove_args:

            for key in (self.verbose_arg_name, self.debug_arg_name,
                        self.quiet_arg_name):

                if key in kwargs:

                    kwargs.pop(key, None)

        if not self.logger_name:

            # As a precaution, set up the root logger beforehand

            logging.basicConfig()

        logger = logging.getLogger(self.logger_name)

        logger.setLevel(self.default_level)

        if quiet:
            logger.setLevel(self.quiet_level)

        if verbose:
            logger.setLevel(self.verbose_level)

        if debug:
            logger.setLevel(self.debug_level)

        self.callback(*args, **kwargs)
