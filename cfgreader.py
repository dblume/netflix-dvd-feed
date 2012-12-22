import ConfigParser

class CfgReader(object):
    """
    A simple utility class that encapsulates read-only access
    to parameters stored in a ConfigParser style config file.

    For example, if the .cfg file has the following:

        [section]
        foo = bar

    Then this object will have the member, section.foo,
    with the value, "bar".
    """

    class Tuple(object):
        def __setattr__(self, name, value):
            raise Exception("This object is read only")

    def __init__(self, cfg_filename):
        config = ConfigParser.SafeConfigParser()
        with open(cfg_filename, "r") as f:
            config.readfp(f)

        for section in config.sections():
            s = CfgReader.Tuple()
            for option in config.options(section):
                s.__dict__[option] = config.get(section, option)
#                setattr(s.__class__, option,
#                        config.get(section, option))
            setattr(self, section, s)

