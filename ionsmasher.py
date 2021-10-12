#!/usr/bin/python3
import sys
import time
import os
import re
import urllib.request
import logging
import codecs
import argparse
import shutil
import urllib
import zipfile
from io import BytesIO
import requests
import bs4

try:
    import configparser  # py3
except ImportError:
    import ConfigParser as configparser  # py2

####### Begin Config ########
current_script_path = os.path.abspath(os.path.dirname(sys.argv[0]))

logname = 'ionsmasher.log'
output_log_path = os.path.join(current_script_path, logname)

logging.basicConfig(filename=output_log_path,
                    filemode='a',
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%M-%d:%H:%M:%S',
                    level=logging.DEBUG)

logging.info("Running IonSmasher!")

logger = logging.getLogger('ionsmasher')
print("Logfile path: ", output_log_path)


####### End Config ########

def read_configs(config_paths, config_dict):
    """Read a config file from filesystem
    :param config_paths: A list of config file paths.
    :type config_paths: list
    :param config_dict: A Config dictionary profile.
    :type config_dict: dict
    :return: Config profile dictionary
    :rtype: dict
    """

    # We return all these values
    config = config_dict
    profile = config['profile']

    # grab values from config files
    cp = configparser.ConfigParser()
    try:
        cp.read(config_paths)
    except Exception as e:
        raise Exception("%s: configuration file error" % profile)

    if len(cp.sections()) > 0:
        # we have a configuration file - lets use it
        try:
            # grab the section - as we will use it for all values
            section = cp[profile]
        except Exception as e:
            # however section name is missing - this is an error
            raise Exception("%s: configuration section missing" % profile)

        for option in list(config.keys()):
            if option not in config or config[option] is None:
                try:
                    config[option] = re.sub(r"\s+", '', section.get(option))
                    if config[option] == '':
                        config.pop(option)
                except (configparser.NoOptionError, configparser.NoSectionError):
                    pass
                except Exception as e:
                    pass

    # remove blank entries
    for x in sorted(config.keys()):
        if config[x] is None or config[x] == '':
            try:
                config.pop(x)
            except:
                pass

    return config


easytoyou_config_paths = ['.ionsmasher.cfg',
                          os.path.expanduser('~/.ionsmasher.cfg'),
                          os.path.expanduser('~/.ionsmasher/ionsmasher.cfg')]

easytoyou_config_dict = {'username': os.getenv('EASYTOYOU_USERNAME'),
                         'password': os.getenv('EASYTOYOU_PASSWORD'),
                         'profile': 'EASYTOYOU'}

"""
To setup config securely:
nano ~/.ionsmasher.cfg
"""
# Then enter the desired below with your details
"""
[EASYTOYOU]
username = cooluser
password = SomePasswordWouldBeHere
"""

# Read config file if it exists and override the above
easytoyou_profile = read_configs(easytoyou_config_paths, easytoyou_config_dict)

username = None
password = None

if 'username' in easytoyou_profile:
    username = easytoyou_profile['username']
if 'password' in easytoyou_profile:
    password = easytoyou_profile['password']


###############################
# Functions for printing colored text out: Source: https://stackoverflow.com/a/34443116/1621381
def black(text):
    print('\033[30m', text, '\033[0m', sep='')


def red(text):
    print('\033[31m', text, '\033[0m', sep='')


def green(text):
    print('\033[32m', text, '\033[0m', sep='')


def yellow(text):
    print('\033[33m', text, '\033[0m', sep='')


def blue(text):
    print('\033[34m', text, '\033[0m', sep='')


def magenta(text):
    print('\033[35m', text, '\033[0m', sep='')


def cyan(text):
    print('\033[36m', text, '\033[0m', sep='')


def gray(text):
    print('\033[90m', text, '\033[0m', sep='')


# string to remove from all downloaded files
remove_text = """
/*
 * @ https://EasyToYou.eu - IonCube v10 Decoder Online
 * @ PHP 7.2
 * @ Decoder version: 1.0.4
 * @ Release: 01/09/2021
 */
"""


def replace(string, substitutions):
    substrings = sorted(substitutions, key=len, reverse=True)
    regex = re.compile('|'.join(map(re.escape, substrings)))
    return regex.sub(lambda match: substitutions[match.group(0)], string)


#################################
parser = argparse.ArgumentParser(usage="easy4us", description="decode directories with easytoyou.eu")
parser.add_argument("-u", "--username", required=False, help="easytoyou.eu username", default=username)
parser.add_argument("-p", "--password", required=False, help="easytoyou.eu password", default=password)
parser.add_argument("-s", "--source", required=True, help="source directory")
parser.add_argument("-o", "--destination", required=False, help="destination directory", default="")
parser.add_argument("-d", "--decoder", help="decoder (default: ic10php72)", default="ic10php72")
parser.add_argument("-w", "--overwrite", help="overwrite", action='store_true', default=False)
base_url = "https://easytoyou.eu"
args = parser.parse_args()

headers = {"Connection": "close",
           "Cache-Control": "max-age=0",
           "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.30 Safari/537.36",
           "Origin": "https://easytoyou.eu"}

not_decoded = []


def login(username, password):
    session = requests.session()
    login = base_url + "/login"
    login_data = {"loginname": username, "password": password}
    resp = session.post(login, headers=dict(headers, **{"Content-Type": "application/x-www-form-urlencoded"}),
                        data=login_data, allow_redirects=True)
    if "/account" in resp.url:
        return session
    return False


def copy(src, dest, files):
    for file in files:
        csrc = os.path.join(src, file)
        cdest = os.path.join(dest, file)
        shutil.copyfile(csrc, cdest)
        message = "copied %s to %s" % (file, cdest)
        green(message)
        logging.info(message)


def clear(session):
    print('')
    print("clearing page", end='')
    logging.info("clearing page")
    c = 0
    while True:
        c += 1
        res = session.get(base_url + "/decoder/%s/1" % args.decoder, headers=headers)
        s = bs4.BeautifulSoup(res.content, features="lxml")
        inputs = s.find_all(attrs={"name": "file[]"})
        if len(inputs) < 1:
            print('')
            break
        final = ""
        for i in inputs:
            final += "%s&" % urllib.parse.urlencode({i["name"]: i["value"]})
        session.post(base_url + "/decoder/%s/1" % args.decoder, data=final,
                     headers=dict(headers, **{"Content-Type": "application/x-www-form-urlencoded"}))
        print("...%d" % c, end='')
        logging.info("...%d" % c)

        # print("deleted %s files" % len(inputs))


def parse_upload_result(r):
    s = bs4.BeautifulSoup(r.content, features="lxml")
    success = []
    failure = []
    for el in s.find_all("div", {"class": "alert-success"}):
        res = [s.strip() for s in el.text.split()]
        success.append(res[1])

    for el in s.find_all("div", {"class": "alert-danger"}):
        # print(el.text)
        res = [s.strip() for s in el.text.split()]
        failure.append(res[3])
    return success, failure


def upload(session, dir, files):
    r = session.get(base_url + "/decoder/%s" % args.decoder, headers=headers, timeout=300)
    s = bs4.BeautifulSoup(r.content, features="lxml")
    el = s.find(id="uploadfileblue")
    if not el:
        red(s.text)
        red("error: couldn't find upload form")
        logging.info(s.text, "error: couldn't find upload form")
        return
    n = el.attrs["name"]
    upload = []
    for file in files:
        if file.endswith(".php"):
            full = codecs.open(os.path.join(dir, file), 'rb')
            upload.append((n, (file, full, "application/x-php")))
    upload.append(("submit", (None, "Decode")))
    if len(upload) > 0:
        r = session.post(base_url + "/decoder/%s" % args.decoder,
                         headers=headers,
                         files=upload)
        return parse_upload_result(r)


def download_zip(session, outpath):
    try:
        if not os.path.exists(outpath):
            os.makedirs(outpath)
        r = session.get(base_url + "/download.php?id=all", headers=headers)
        zip_bytes = BytesIO(r.content)
        zf = zipfile.ZipFile(zip_bytes)
        for name in zf.namelist():
            data = zf.read(name)
            # Let's replace EasyToYou.eu comment from file content
            substitutions = {remove_text: "\n"}
            # Convert to string so we can replace
            data = replace(data.decode('utf-8'), substitutions)
            # Convert back to bytes so we can write
            data = bytes(data, 'utf-8')
            dest = os.path.join(outpath, os.path.basename(name))
            with open(dest, 'wb+') as f:
                wrote = f.write(data)
            green("wrote %d bytes to %s" % (wrote, dest))
            logging.info("wrote %d bytes to %s" % (wrote, dest))
        zf.close()
        return True
    except Exception as e:
        print(e)
        return False


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def process_files(session, dir, dest, phpfiles):
    print("uploading %d files..." % len(phpfiles), end='', flush=True)
    logging.info("uploading %d files..." % len(phpfiles))
    res = upload(session, dir, phpfiles)
    if res:
        success, failure = res
        print('')
        green("done. %s successful, %d failed." % (len(success), len(failure)))
        logging.info("done. %s successful, %d failed." % (len(success), len(failure)))
        # copy(dir, dest, failure)
        not_decoded.extend([os.path.join(dir, f) for f in failure])
        # download zip
        if len(success) > 0:
            if not download_zip(session, dest):
                # print("download failed. refreshing session...", end='')
                # session = login(args.username, args.password)
                # print("done")
                # if not download_zip(session, dest):
                yellow("couldn't download. copying originals and continuing")
                logging.info("couldn't download. copying originals and continuing")
                # copy(dir, dest, phpfiles)
                not_decoded.extend([os.path.join(dir, f) for f in phpfiles])
            clear(session)


if __name__ == '__main__':
    if args.destination == "":
        args.destination = os.path.basename(args.source) + "_decoded"
        args.destination = os.path.join(current_script_path, args.destination)

    # Let's expand paths from ~
    args.source = os.path.expanduser(args.source)
    args.destination = os.path.expanduser(args.destination)

    if args.username == "":
        args.username = username if username else None

    if args.password == "":
        args.password = password if password else None

    if args.username is None:
        message = 'Please set username in profile config or pass it as an argument via --username'
        red(message)
        logging.info(message)
        sys.exit()
    if args.password is None:
        message = 'Please set password in profile config or pass it as an argument via --password'
        red(message)
        logging.info(message)
        sys.exit()

    session = login(args.username, args.password)
    if session:
        clear(session)
        for dir, dirnames, filenames in os.walk(args.source):
            print('')
            message = "descended into %s" % dir
            print(message)
            logging.info(message)
            rel = os.path.relpath(dir, args.source)
            dest = os.path.join(args.destination, rel).strip(".")
            if not os.path.exists(dest):
                os.makedirs(dest)
                # print("created %s" % dest)
            phpfiles = []
            other = []
            for f in filenames:
                csrc = os.path.join(dir, f)
                if f.endswith(".php") and b"if(!extension_loaded('ionCube Loader'))" in open(csrc, "rb").read():
                    phpfiles.append(f)
                else:
                    other.append(f)

            copy(dir, dest, other)

            # check overwrite
            if not args.overwrite:
                needed = []
                for f in phpfiles:
                    csrc = os.path.join(dest, f)
                    if not os.path.exists(csrc):
                        needed.append(f)
                    # else:
                    #    print("%s exists already. skipping." % f)
                phpfiles = needed

            # upload
            if len(phpfiles) > 0:
                for f in batch(phpfiles, 25):
                    process_files(session, dir, dest, f)
        green('finished.')
        print(f'Source folder: {args.source}')
        print(f'Destination folder: {args.destination}')
        print("Logfile path: ", output_log_path)
        if not_decoded:
            message = "ioncube files that failed to decode:"
            red(message)
            logging.info(message)
            for f in not_decoded:
                red(f)
                log_entry = f'failed to decode: {f}'
                logging.info(log_entry)
