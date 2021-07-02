import os
import codecs
import argparse
import shutil
import urllib
import zipfile
from io import BytesIO
import requests
import bs4

parser = argparse.ArgumentParser(usage="easy4us", description="decode directories with easytoyou.eu")
parser.add_argument("-u", "--username", required=True, help="easytoyou.eu username")
parser.add_argument("-p", "--password", required=True, help="easytoyou.eu password")
parser.add_argument("-s", "--source", required=True, help="source directory")
parser.add_argument("-o", "--destination", required=True, help="destination directory", default="")
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
        print("copied %s to %s" % (file, cdest))


def clear(session):
    print("clearing page", end='')
    c = 0
    while True:
        c += 1
        res = session.get(base_url + "/decoder/%s/1" % args.decoder, headers=headers)
        s = bs4.BeautifulSoup(res.content, features="lxml")
        inputs = s.find_all(attrs={"name": "file[]"})
        if len(inputs) < 1:
            print()
            break
        final = ""
        for i in inputs:
            final += "%s&" % urllib.parse.urlencode({i["name"]: i["value"]})
        session.post(base_url + "/decoder/%s/1" % args.decoder, data=final,
                     headers=dict(headers, **{"Content-Type": "application/x-www-form-urlencoded"}))
        print("...%d" % c, end='')
        
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
        print(s.text)
        print("error: couldnt find upload form")
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
        bytes = BytesIO(r.content)
        zf = zipfile.ZipFile(bytes)
        for name in zf.namelist():
            data = zf.read(name)
            dest = os.path.join(outpath, os.path.basename(name))
            f = open(dest, 'wb+')
            wrote = f.write(data)
            f.close()
            print("wrote %d bytes to %s" % (wrote, dest))
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
    res = upload(session, dir, phpfiles)
    if res:
        success, failure = res
        print("done. %s successful, %d failed." % (len(success), len(failure)))
        # copy(dir, dest, failure)
        not_decoded.extend([os.path.join(dir, f) for f in failure])
        # download zip
        if len(success) > 0:
            if not download_zip(session, dest):
                # print("download failed. refreshing session...", end='')
                # session = login(args.username, args.password)
                # print("done")
                # if not download_zip(session, dest):
                print("couldn't download. copying originals and continuing")
                # copy(dir, dest, phpfiles)
                not_decoded.extend([os.path.join(dir, f) for f in phpfiles])
            clear(session)

if __name__ == '__main__':
    if args.destination == "":
        args.destination = os.path.basename(args.source) + "_decoded"

    session = login(args.username, args.password)
    if session:
        clear(session)
        for dir, dirnames, filenames in os.walk(args.source):
            print("descended into %s" % dir)
            rel = os.path.relpath(dir, args.source)
            dest = os.path.join(args.destination, rel).strip(".")
            if not os.path.exists(dest):
                os.makedirs(dest)
                # print("created %s" % dest)
            phpfiles = []
            other = []
            for f in filenames:
                csrc = os.path.join(dir, f)
                if f.endswith(".php") and b"ionCube Loader" in open(csrc, "rb").read():
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
                    #else:
                    #    print("%s exists already. skipping." % f)
                phpfiles = needed

            # upload
            if len(phpfiles) > 0:
                for f in batch(phpfiles, 25):
                    process_files(session, dir, dest, f)
        print("finished. ioncube files that failed to decode:")
        for f in not_decoded:
            print(f)
