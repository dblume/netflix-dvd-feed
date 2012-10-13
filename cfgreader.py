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

        self.g_name = config.get('global', 'name')
        self.g_url_base = config.get('global', 'url_base')
        self.g_logfile = config.get('global', 'logfile')
        self.g_rss_base = config.get('global', 'rss_base')

        self.smtp_user = config.get('smtp', 'user')
        self.smtp_password = config.get('smtp', 'password')
        self.smtp_from_addr = config.get('smtp', 'from')
        self.smtp_to_addr = config.get('smtp', 'to')

        self.imap_user = config.get('imap', 'user')
        self.imap_password = config.get('imap', 'password')
        self.imap_mailbox = config.get('imap', 'mailbox')

