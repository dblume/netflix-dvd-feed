#!/usr/bin/env python
import sys
import os
import cStringIO
import time
import codecs
import smtplib
import traceback
from argparse import ArgumentParser
import imaplib
import email
from email.header import decode_header
import quopri
import re
import cgi
import cfgreader

# Read in custom configurations
g_cfg = cfgreader.CfgReader(__file__.replace('.py', '.cfg'))

# These two strings will form the header and individual
# items of the RSS feed.
feed_header = """<?xml version="1.0" encoding="iso-8859-1"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>DVDs shipped for %s</title>
<link>http://dvd.netflix.com/Queue</link>
<atom:link href="http://%s/%s.xml" rel="self" type="application/rss+xml" />
<pubDate>%%s</pubDate>
<description>Feed automatically generated by %s</description>
<language>en-us</language>
""" % (g_cfg.main.name, g_cfg.main.url_base,
       g_cfg.main.rss_base, g_cfg.main.url_base)

feed_item = """<item>
<title>%s</title>
<pubDate>%s</pubDate>
<link>%s</link>
<guid isPermaLink="false">%s</guid>
<description>The disc &lt;a href="%s"&gt;%s&lt;/a&gt; was shipped on %s.</description>
</item>
"""


def set_v_print(verbose):
    """
    Defines the function v_print.
    It prints if verbose is true, otherwise, it does nothing.
    See: http://stackoverflow.com/questions/5980042
    :param verbose: A bool to determine if v_print will print its args.
    """
    global v_print
    if verbose:
        def v_print(*s):
            print ' '.join([i.encode('utf8') for i in s])
    else:
        v_print = lambda *s: None


def send_email(subject, msg, toaddrs,
               fromaddr='"%s" <%s>' % (os.path.basename(__file__),
                                       g_cfg.smtp.from_addr)):
    """ Sends Email
    This function is only used in an emergency.
    """
    smtp = smtplib.SMTP('localhost', port=g_cfg.smtp.port)
    smtp.login(g_cfg.smtp.user, g_cfg.smtp.password)
    smtp.sendmail(fromaddr, toaddrs,
                  "Content-Type: text/plain; charset=\"us-ascii\"\r\n"
                  "From: %s\r\nTo: %s\r\nSubject: %s\r\n%s" %
                  (fromaddr, ", ".join(toaddrs), subject, msg))
    smtp.quit()


def write_feed(script_dir, feed_items):
    """ Given a list of feed_items, write an FSS feed. """
    now = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
    index = 0
    do_move = False
    temp_fname = os.path.join(script_dir, g_cfg.main.rss_base + '.temp.xml')
    dest_fname = os.path.join(script_dir, g_cfg.main.rss_base + '.xml')
    with open(temp_fname, 'wb') as f:
        f.write(feed_header % (now,))
        for title, url, ship_date in reversed(feed_items):
            title = cgi.escape(title)
            guid = "%s+%s+%d" % (url, now, index)
            f.write(feed_item % (title,
                                 ship_date,
                                 url,
                                 guid,
                                 url, title, ship_date[:-15]))
            index += 1
        f.write('</channel></rss>')
        do_move = True
    if do_move:
        os.rename(temp_fname, dest_fname)
        return "OK (Wrote %d new item%s.)" % \
               (len(feed_items), len(feed_items) > 1 and "s" or "")
    return "Could not update the feed file."


def is_line_after_dvd_list(line):
    """ Returns whether this line is known to come after the
    list of titles being shipped. """
    lines = ["WE RECEIVED",
             "*****",
             "KEEP SHIPMENTS COMING",
             "WHY DID WE SEND MORE DISCS"]
    return any(line.startswith(words) for words in lines)


def titles_from_text_part(part):
    """ Given a text part of the message, try to get all the titles.
    They'll be the lines after "WE SHIPPED:" and before "WE RECEIVED" or
    "***" """
    titles = list()
    titles_begin = False
    txt = str(part)
    for line in txt.splitlines():
        if line.startswith("WE SHIPPED"):
            titles_begin = True
        elif line.startswith("* Est. arrival") or len(line) < 2:
            continue
        elif is_line_after_dvd_list(line):
            break
        elif titles_begin == True:
            titles.append(line.strip())
            v_print("Found title", line.strip())
    return titles


def get_titles_from_html_part(part, debug):
    """ Gets the titles *and* URLs with the same regex. """
    titlepat = re.compile('<h2 style="box-sizing(?:[^<>]+?)><a class="medium" href="([^"]+?)" (?:[^<>]+?)>(.+?)</a></h2>', re.MULTILINE)
    raw_txt = quopri.decodestring(part.get_payload())

    # text will have some lines that start with a space as part of a soft break. Eg.,
    # 'Stuff ... <a href="h'
    # ' ttp://www.google.co'
    # When joined, a space would be inserted in the word "http".
    # So, when the last line wasn't empty and the new line starts with a space, concat them.
    txt_io = cStringIO.StringIO()
    last_line_empty = True
    for line in raw_txt.splitlines():
        if len(line) > 0:
            if last_line_empty or line[0] != ' ':
                txt_io.write(line)
            else:
                txt_io.write(line[1:])
            last_line_empty = False
        else:
            txt_io.write('\n')
            last_line_empty = True
    txt = txt_io.getvalue()
    txt_io.close()

    if debug:
        n = 0
        for l in txt.splitlines():
           print "%03d: \"%s\"" % (n, l)
           n += 1

    titles = []
    urls = []
    matches = titlepat.search(txt)
    if matches is None:
        v_print("Found no titles in html part of message.")
        return "NO", ["The HTML body no longer has the title bordered by the same markup."], []
    while matches is not None:
        urls.append(matches.groups()[0])
        titles.append(matches.groups()[1])
        txt = txt[matches.end():]
        matches = titlepat.search(txt)
    v_print("Found %d titles: %s" % (len(titles), str(titles)))
    return "OK", titles, urls


def subject_is_recognized(subject):
    """ Returns whether this subject line is known to be associated
    with email that contains a title of a DVD to be shipped.
    """
    recognized_subjects = ["We sent you ", "We shipped you "]
    if any(subject.startswith(words) for words in recognized_subjects):
        return True
    return subject.startswith("For ") and subject.find(':') != -1


def main(script_dir, debug):
    """ Fetch all the mail, and try to find messages that
    match a pattern like, "For Wed: Some Movie".

    It'll add those movies to the RSS feed, and if that's
    completed successfully, then it'll delete the processed email.
    """
    server = imaplib.IMAP4(g_cfg.imap.mailbox)
    server.login(g_cfg.imap.user, g_cfg.imap.password)
    server.select()
    status, data = server.search(None, 'ALL')
    if status != 'OK':
        raise Exception('Getting the list of messages resulted in %s' % status)

    messages_to_delete = []
    feed_items = []
    for num in data[0].split():  # For each email message...
        status, data = server.fetch(num, '(RFC822)')
        if status != 'OK':
            raise Exception('Fetching message %s resulted in %s' % (num, status))
        msg = email.message_from_string(data[0][1])
        subject = msg['Subject']
        if subject.startswith('=?UTF-'):
            subject = decode_header(subject)[0][0]

        if subject.startswith('Fwd: '):
            subject = subject[5:]

        if subject.startswith("We received") or \
           subject.startswith("Shipping today!"):
            # We will bypass, but delete this message as recognized
            v_print("Bypassing message", num, subject)
            messages_to_delete.append(num)
            continue

        if not subject_is_recognized(subject):
            print 'Subject "%s" was unexpected, but the script is continuing. ' \
                  'Please take a look at the mailbox.' % subject
            continue

        # From the plain text part of the message, get all the titles...
        titles = None
        html_part = None
        for part in msg.walk():
            # multipart/* are just containers
            if part.get_content_maintype() == 'multipart':
                v_print("Skipping multipart part looking for text/plain.")
                continue
            content_type = part.get_content_type()
            if content_type == "text/plain":
                v_print("Processing %s part of the message." % content_type)
                titles = titles_from_text_part(part)
                break
            else:
                if content_type == "text/html":
                    html_part = part
                v_print("Skipping %s part looking for text/plain." % content_type)

        if not titles and html_part is not None:
            v_print("No titles yet, so searching for them in text/html part.")
            status, titles, urls = get_titles_from_html_part(html_part, debug)
            if status != 'OK':
                raise Exception(titles[0])

        messages_to_delete.append(num)
        # Append the movie names and URLs to a list of items
        for i in range(len(titles)):
            feed_items.append((titles[i], urls[i], msg['Date']))

    # Ensure the new feed is written
    update_status = "OK"
    if len(feed_items) > 0:
        update_status = write_feed(script_dir, feed_items)

    if update_status.startswith("OK") and debug == False:
        # Now delete only the messages marked for deletion
        for num in messages_to_delete:
            server.store(num, '+FLAGS', '\\Deleted')
#        server.expunge()  # DCB TODO DEBUG Temporarily commented out to keep message in Trash

    server.close()
    server.logout()
    print update_status
    return update_status


if __name__ == '__main__':
    # Everything here and below is boiler-plate for cron jobs.
    script_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    parser = ArgumentParser(description="cronjob to create Netflix DVD feed.")
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    set_v_print(args.verbose)

    start_time = time.time()
    if args.debug:
        message = main(script_dir, args.debug)
    else:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = sys.stderr = cStringIO.StringIO()
        try:
            main(script_dir, args.debug)
        except Exception, e:
            exceptional_text = "Exception: " + str(e.__class__) + " " + str(e)
            print exceptional_text
            traceback.print_exc(file=sys.stdout)
            try:
                send_email('Exception thrown in %s' % (os.path.basename(__file__),),
                           exceptional_text + "\n" + traceback.format_exc(),
                           (g_cfg.smtp.to,))
            except Exception, e:
                traceback.print_exc(file=sys.stdout)
                print "Could not send email to notify you of the exception. :("

        message = sys.stdout.getvalue()
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    # Finally, let's save this to a statistics page
    if os.path.exists(os.path.join(script_dir, g_cfg.main.logfile)):
        with codecs.open(os.path.join(script_dir, g_cfg.main.logfile), 'r', 'utf-8') as f:
            lines = f.readlines()
    else:
        lines = []
    lines = lines[:168]  # Just keep some recent lines
    status = u'\n                       '.join(message.decode('utf-8').splitlines())
    lines.insert(0, u"%s %3.0fs %s\n" % (time.strftime('%Y-%m-%d, %H:%M', time.localtime()),
                                         time.time() - start_time,
                                         status))
    with codecs.open(os.path.join(script_dir, g_cfg.main.logfile), 'w', 'utf-8') as f:
        f.writelines(lines)
