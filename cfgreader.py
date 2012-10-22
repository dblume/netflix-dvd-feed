import ConfigParser

class CfgReader(object):
    """
    A simple utility class that encapsulates read-only access
    to parameters stored in a ConfigParser style config file.

    For example, if the .cfg file has the following:

        [section]
        foo = bar

    Then this object will have the member, section_foo,
    with the value, "bar".
    """

    def __init__(self, cfg_filename):
        config = ConfigParser.SafeConfigParser()
        with open(cfg_filename, "r") as f:
            config.readfp(f)

        for section in config.sections():
            for option in config.options(section):
                setattr(self, "%s_%s" % (section, option),
                        config.get(section, option))
