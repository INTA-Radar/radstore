import pymongo
import xmltodict
import pymongo
#import gridfs
import base64
import zlib
import re
import simplejson
import dateutil.parser
import datetime
import os
import requests
import glob

client = pymongo.MongoClient()
db = client['radar']
api_url='http://127.0.0.1:3003/api/v1'

def process_blob(blob):
	return zlib.decompress(blob[4:])

def process_metadata(val):
	if isinstance(val,dict):
		return dict((k.replace('@',''),process_metadata(v)) for k,v in val.iteritems())

	elif isinstance(val,list):
		return map(process_metadata, val)

	elif isinstance(val,tuple):
		return tuple(map(process_metadata, val))

	elif isinstance(val,basestring):
		val = val.strip()
		if len(val) == 0: return val

		l = val.lower()
		if l == 'on': return True
		elif l == 'off': return False
		elif l == 'none': return None

		try: return float(val)
		except: pass
		try: return int(val)
		except: pass
		try: 
			if 'T' in val: return dateutil.parser.parse(val)
		except: pass

		try: return map(float, val.split())
		except: pass
		try: return map(int, val.split())
		except: pass

	return val


def upload(fname):
	print fname
	with open(fname) as f:
		t = ''
		for line in f:
			if line == '<!-- END XML -->\n': break
			t += line
		data = xmltodict.parse(t)
		data = process_metadata(data)

		doc = {
			'name': os.path.split(fname)[-1],
			'type': 'vol',
			'datetime': data['volume']['datetime'].isoformat(),
			'variable': data['volume']['scan']['slice'][0]['slicedata']['rawdata']['type'],
			#'metadata': data['volume']
		}
		# print simplejson.dumps(data, indent=3, default=lambda x:str(x))
		# asdffdsa

		#result = db['product'].insert_one(doc)
		resp = requests.post(api_url+'/products', 
			headers={'Content-Type':'application/json'}, data=simplejson.dumps(doc, default=str))

		data = simplejson.loads(resp.text)

		id = data['data']['product']['_id']
		requests.post(api_url+'/products/%s/content' % id, data=open(fname).read())

		# blob = None
		# blobdata = None
		# for line in f:
		# 	if blobdata is None:
		# 		if line.startswith('<BLOB'):
		# 			blobdata = ''
		# 			blob = xmltodict.parse(line+'</BLOB>')
		# 	else:
		# 		if line == '</BLOB>\n':
		# 			d = {
		# 				'datetime': data['volume']['@datetime'],
		# 				'type': data['volume']['scan']['slice'][0]['slicedata']['rawdata']['@type'],
		# 				'blobid': blob['BLOB']['@blobid']
		# 			}
		# 			blobfile = fs.new_file(**d)
		# 			blobfile.write(process_blob(blobdata))
		# 			blobfile.close()
		# 			blobdata = None
		# 		else:
		# 			blobdata += line
		
import sys
def main():
	

	# clean all 
	#client.drop_database('radar')
	#os.system('rm fs/*')
	#db['product'].create_index([('id',pymongo.ASCENDING)],unique=True)

	cmd = sys.argv[1]
	if cmd == "import_file":
		param = sys.argv[2].split('=')
		fname = param[1]
		upload(fname)
	elif cmd == "import_dir":
		params = dict(x.split('=') for x in sys.argv[2:])
		pattern = os.path.join(params['dir'],params.get('pattern',''))
		for fname in glob.glob(pattern):
			try:
				upload(fname)
			except Exception,e:
				print "ERROR: %s" % e
	else:
		print "ERROR: Invalid command: %s" % cmd

if __name__ == '__main__':
	main()
