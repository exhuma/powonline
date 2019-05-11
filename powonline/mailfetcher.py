import logging
from base64 import b64decode
from hashlib import md5
from os import makedirs
from os.path import dirname, exists, join
from uuid import uuid4

from gouge.colourcli import Simple
from imapclient import FLAGGED, SEEN, IMAPClient
from powonline.config import default

LOG = logging.getLogger(__name__)
IMAGE_TYPES = {
    (b'image', b'jpeg'),
    (b'image', b'png'),
    (b'image', b'gif'),
}


def get_extension(major, minor):
    if major.lower() != 'image':
        raise ValueError('This application only allows storing images '
                         '(got %s)!' % major)
    return minor.lower()


def extract_elements(body, elements):
    if not body.is_multipart:
        elements.append(body)
    else:
        parts, relation = body
        if relation == 'alternative':
            elements.append(parts[0])
        else:
            for part in parts:
                extract_elements(part, elements)


def flatten_parts(body, start_index=0):
    output = []
    index = start_index
    for element in body:
        if element.is_multipart:
            output.extend(flatten_parts(element[0], index))
            index = output[-1][0] + 1
        else:
            output.append((index, element))
            index += 1
    return output


class MailFetcher(object):

    def __init__(self, host, username, password, use_ssl, image_folder,
                 force=False, file_saved_callback=None, fail_fast=False):
        self.host = host
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.image_folder = image_folder
        self.connection = None
        self.force = force
        self.file_saved_callback = file_saved_callback
        self.fail_fast = fail_fast

        # Hardcoded for now (was used in the old app).
        self.use_index = False

    def connect(self):
        LOG.debug('Connecting to mail host...')
        self.connection = IMAPClient(self.host, use_uid=True, ssl=self.use_ssl)
        LOG.debug('Logging in...')
        self.connection.login(self.username, self.password)

    def fetch(self):
        LOG.debug('Fetching mail...')
        if not exists(self.image_folder):
            makedirs(self.image_folder)
            LOG.info('Created image folder at %r' % self.image_folder)

        self.connection.select_folder('INBOX')
        messages = self.connection.search(['NOT', 'DELETED'])
        response = self.connection.fetch(messages, ['FLAGS', 'BODY'])
        for msgid, data in response.items():
            is_read = SEEN in data[b'FLAGS']
            if is_read and not self.force:
                LOG.debug('Skipping already processed message #%r', msgid)
                continue
            else:
                # Add a "forced" note only if the message would not have been
                # processed otherwise.
                LOG.debug('Processing message #%r%s', msgid,
                          ' (forced override)' if is_read else '')
            body = data[b'BODY']
            el = []
            extract_elements(body, el)
            fetch_meta = [(i, data) for i, data in enumerate(el)
                          if (data[0], data[1]) in IMAGE_TYPES]
            if fetch_meta:
                has_error = self.download(msgid, fetch_meta)
                if has_error and self.fail_fast:
                    LOG.error('Failfast activated, bailing out on first error!')
                    return False
        return True

    def in_index(self, md5sum):
        if not self.use_index:
            return False
        indexfile = join(self.image_folder, 'index')
        if not exists(indexfile):
            LOG.debug('%r does not exist. Assuming first run.', indexfile)
            return False
        with open(indexfile) as fptr:
            hashes = [line.strip() for line in fptr]
        return md5sum in hashes

    def add_to_index(self, md5sum):
        if not self.use_index:
            return
        if not md5sum.strip():
            return
        indexfile = join(self.image_folder, 'index')
        with open(indexfile, 'a+') as fptr:
            fptr.write(md5sum + '\n')

    def download(self, msgid, metadata):
        LOG.debug('Downloading images for mail #%r', msgid)
        has_error = False

        fetched = self.connection.fetch([msgid], [b'BODY', b'ENVELOPE'])
        sender = fetched[msgid][b'ENVELOPE'].sender[0]
        raw_from_address = b'%s@%s' % (sender.mailbox, sender.host)
        from_address = raw_from_address.decode('ascii')
        parts = flatten_parts(fetched[msgid][b'BODY'][0])
        images = [part for part in parts if part[1][0] == b'image']
        for image_id, header in images:
            try:
                (major, minor, params, _, _, encoding, size) = header
                if params:
                    # Convert "params" into a more conveniend dictionary
                    params = dict(zip(params[::2], params[1::2]))
                    filename = params[b'name'].decode('ascii', errors='ignore')
                    unique_name = 'image_{}_{}_{}'.format(msgid, image_id,
                        filename)
                else:
                    extension = get_extension(
                        major.decode('ascii'), minor.decode('ascii'))
                    unique_name = 'image_{}_{}_{}.{}'.format(
                        msgid, image_id, uuid4(), extension)
                encoding = encoding.decode('ascii')
                LOG.debug('Processing part #%r in mail #%r', image_id, msgid)
                element_id = ('BODY[%d]' % image_id).encode('ascii')
                response = self.connection.fetch([msgid], [element_id])
                content = response[msgid][element_id]
                if not content:
                    LOG.error('Attachment data was empty for '
                              'message #%r', msgid)
                    has_error = True
                    continue

                if encoding == 'base64':
                    bindata = b64decode(content)
                else:
                    bindata = content.decode(encoding)
                md5sum = md5(bindata).hexdigest()
                if self.in_index(md5sum) and not self.force:
                    LOG.debug('Ignored duplicate file (md5=%s).', md5sum)
                    continue
                elif self.in_index(md5sum) and self.force:
                    LOG.debug('Bypassing index check (force=True)')

                fullname = join(self.image_folder, from_address, unique_name)
                if not exists(fullname) or self.force:
                    suffix = ' (forced overwrite)' if exists(fullname) else ''
                    try:
                        makedirs(dirname(fullname))
                    except FileExistsError:
                        pass
                    with open(fullname, 'wb') as fptr:
                        fptr.write(bindata)
                    LOG.info('File written to %r%s', fullname, suffix)
                    if self.file_saved_callback:
                        self.file_saved_callback(
                            from_address,
                            join(from_address, unique_name))
                    self.add_to_index(md5sum)
                else:
                    has_error = True
                    LOG.warn('%r already exists. Not downloaded!' % fullname)
            except:
                LOG.error('Unable to process mail #%r', msgid, exc_info=True)
                has_error = True

        if has_error:
            self.connection.add_flags([msgid], FLAGGED)
        else:
            self.connection.add_flags([msgid], SEEN)
        return has_error

    def disconnect(self):
        self.connection.shutdown()


def run_cli():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Fetch photos from IMAP.')
    parser.add_argument('--verbose', '-v', dest='verbose',
                        default=0, action='count',
                        help='Prints actions on stdout.')
    parser.add_argument('--host', dest='host',
                        required=True,
                        help='IMAP Hostname')
    parser.add_argument('--login', '-l', dest='login',
                        required=True,
                        help='IMAP Username')
    parser.add_argument('--password', '-p', dest='password',
                        help='IMAP password.')
    parser.add_argument('--destination', '-d', dest='destination',
                        required=True,
                        help='The folder where files will be stored')
    parser.add_argument('--force', dest='force',
                        action='store_true', default=False,
                        help='Force fecthing mails. Even if they are read or '
                        'in the index')
    parser.add_argument('--fail-fast', dest='failfast',
                        action='store_true', default=False,
                        help='Exit on first error')

    args = parser.parse_args()

    if args.verbose >= 2:
        Simple.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    elif args.verbose >= 1:
        Simple.basicConfig(level=logging.INFO, stream=sys.stdout)
    else:
        Simple.basicConfig(level=logging.WARNING)

    if not args.password:
        from getpass import getpass
        password = getpass('Password: ')
    else:
        password = args.password

    fetcher = MailFetcher(
        args.host,
        args.login,
        password,
        True,
        args.destination,
        args.force,
        fail_fast=args.failfast)
    try:
        fetcher.connect()
    except Exception as exc:
        LOG.critical('Unable to connect: %s', exc)
        sys.exit(1)

    try:
        is_success = fetcher.fetch()
    except Exception as exc:
        LOG.critical('Unable to fetch: %s', exc)
        sys.exit(1)

    exit_code = 0 if is_success else 1
    sys.exit(exit_code)


if __name__ == '__main__':
    Simple.basicConfig(level=logging.DEBUG)
    logging.getLogger('imapclient').setLevel(logging.INFO)
    config = default()
    host = config.get('email', 'host')
    login = config.get('email', 'login')
    password = config.get('email', 'password')
    port = config.getint('email', 'port', fallback=143)
    ssl_raw = config.get('email', 'ssl', fallback='true')
    ssl = ssl_raw.lower()[0] in ('1', 'y', 't')
    fetcher = MailFetcher(
        host,
        login,
        password,
        ssl,
        'lost_images',
        force=True)
    fetcher.connect()
    fetcher.fetch()
    fetcher.disconnect()
