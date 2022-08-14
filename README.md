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
