import ConfigParser

class CfgReader(object):
    """
    A simple utility class that encapsulates easy access
    to parameters set in a ConfigParser style config file.
    """

    def __init__(self, cfg_filename):
        config = ConfigParser.SafeConfigParser()
        with open( cfg_filename, "r") as f:
            config.readfp(f)

        for section in config.sections():
            for option in config.options(section):
                setattr(self, "%s_%s" % (section, option),
                        config.get(section, option))
