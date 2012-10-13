# netflix-dvd-feed
netflix-dvd-feed is a script that scans email from NetFlix and creates an RSS feed for DVDs.  It should be run as a cronjob.  It's a replacement for their AtHomeRSS feed.

## Getting Started

1. Forward all your email from Netflix to a new mailbox, say, netflix@yourdomain.com
2. Rename netflix-dvd-feed.cfg.sample to netflix-dvd-feed.cfg
3. Customize the variables in netflix-dvd-feed.cfg (More on this below.)
4. Set up a cronjob that runs the script every day.
5. Bob's your uncle.

## What It Does

In addition to scanning and parsing email from NetFlix and making a feed out of it, it logs its progress to a logfile, and if it runs into trouble (say, because NetFlix changes the format of their email), it'll email you. 

The logfile it writes looks something like this:

    2012-10-11, 11:14   0s OK
    2012-10-10, 11:14   1s OK (Wrote 1 new item.)
    2012-10-09, 11:14   0s OK
    2012-10-08, 11:14   1s OK (Wrote 1 new item.)

The RSS feed it writes validates at [the feed validation service](http://validator.w3.org/appc/).

## Customizing netflix-dvd-feed.cfg

netflix-dvd-feed.cfg looks like this:

    [global]
    domain = yourdomain.com
    name = John Doe
    url_base = netflixdvds.%(domain)s
    logfile = logfile.txt
    rss_base = dvds_at_home_feed
    [smtp]
    from = dvds_at_home_script@yourdomain.com
    to = johnd@yourdomain.com
    user = smtp_username
    password = mooltipass
    [imap]
    mailbox = mail.yourdomain.com
    user = username@yourdomain.com
    password = mooltipass

### The Global Section

This section refers to stuff like the name and location of the new RSS file.

**domain**: This is the domain that the script resides at and will write the RSS feed to. 
**name**: The name of the person to whom the NetFlix feed belongs.
**url_base**: The base of the URL that the RSS feed is at.
**logfile**: The name of the logfile.
**rss_base**: The base filename of the RSS file.

### The SMTP Section

This section is for when the script needs to email you that it ran into a problem

**from**: The address from which email will be sent.
**to**: The address to which email should be sent if there's a problem.
**user**: The SMTP username used to access email
**password**: The SMTP password needed to send email.

### The IMAP Section

This section refers to the mailbox to which you're forwarding your email from NetFlix.

**mailbox**: The internet address of the email mailbox.
**user**: The IMAP username used to read the NetFlix email
**password**: The IMAP password.

## Debugging

Run the command with the ``--debug`` flag for it to print output directly to stdout.

## Licence

This software uses the [MIT License](http://opensource.org/licenses/mit-license.php).

Thanks!

--David Blume
