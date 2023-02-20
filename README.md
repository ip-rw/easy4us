NOTICE
======
~~Until somebody can get in touch with the authors of easytoyou.eu and we can get some idea of whether they dislike this sort of automation then I think it's fair to say you run this at your own risk. Please read this issue and ideally add a little concrete information if you're so inclined...
https://github.com/ip-rw/easy4us/issues/6~~

```
Hi,

unfortunately we had to put an end to this situation, to stop spam ours services.
now decoding is possible only through the website upload form.

I know how hard it was to create your script, and as a recompense I'll give you 90 days of membership free for your account "step"

please delete https://github.com/ip-rw/easy4us this crypt has been hell for our service every day lag delay for our clients.
```

I offered a new server but they seem happy with what they have. I had a quick look and now they only allow 1 file upload at a time. It would appear if you have larger jobs then your best bet is to contact them directly. Which is a shame because this was so handy...

This wont work anymore. You could easily modify things to send one file at a time but you'd just get blocked for flooding. Contact them directly for larger jobs. I'm going to archive this.

easy4us
=======

easytoyou.eu are a brilliant service that allows unlimited ionCube decoding for a very reasonable monthly fee. it has no
way to upload a directory, so to decode a large webapp is a slow, manual process.

this script should take care of this process for you. the usage should be clear enough.

this is held together with sticky tape and hope, don't be surprised if it fails on big jobs. you should be able to rerun 
and pick up where you left off. if you'd prefer to copy the original ioncubed files in place of failures so the webapp should still run then I think the changes are in there and commented/pretty easy to do.

Setup:
Git clone repo to local folder.

Change into that folder and install the pip requirements
```
git clone https://github.com/ip-rw/easy4us
cd easy4us
pip install -r requirements.txt
```
Then follow as outlined below to use the command line.

```
usage: easy4us
decode directories with easytoyou.eu

  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        easytoyou.eu username
  -p PASSWORD, --password PASSWORD
                        easytoyou.eu password
  -s SOURCE, --source SOURCE
                        source directory
  -o DESTINATION, --destination DESTINATION
                        destination directory
  -d DECODER, --decoder DECODER
                        decoder (default: ic11php72)
  -w, --overwrite       overwrite

```

For example:
```
python main.py -u USERNAME -p PASSWORD -s SOURCEDIR -o DESTDIR -w 
```
Check the site make sure you're using the correct decoder - I don't know how often they update these so any issues with the default check it first.
