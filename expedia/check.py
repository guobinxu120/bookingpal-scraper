import os, sys, csv, platform, datetime, glob, json

if __name__ == '__main__':
	print sys.argv
	if len(sys.argv) != 2:
		print "Usage: Wrong"
	else:
		path = sys.argv[1]

		print "Path : ", path

		json_file_list = glob.glob(path+"*.json")
		for i, file in enumerate(json_file_list):
			try:
				with open(file) as json_data:

					data = json.load(json_data)
			except:
				print i,file