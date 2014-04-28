

import sys,re
import requests
import pyperclip
import click

@click.group()
def plick():
    pass

@click.command()
@click.argument('url',help='url of the file to be downloaded',default=pyperclip.getcb().strip())
def download(url):
	url_regex = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
    r'localhost|' # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|' # ...or ipv4
    r'\[?[A-F0-9]*:[A-F0-9:]+\]?)' # ...or ipv6
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)
	if not re.match(url_regex,url):
		print 'Invalid Url! Copy the download url to clipboard and then run `plick download`'
		return
		
	filename = url.split('/')[-1]
	print 'Downloading file %s'%filename

	with open(filename,"wb") as f:
		r = requests.get(url,stream=True)
		length = r.headers.get('content-length')
		if length is None:
			f.write(r.content)
		else:
			dl=0
			for chunk in r.iter_content():
				dl+=int(len(chunk))
				f.write(chunk)
				sys.stdout.write("\r[%d]%%"%((dl*100)/int(length)))
				sys.stdout.flush()	
	
plick.add_command(download)
