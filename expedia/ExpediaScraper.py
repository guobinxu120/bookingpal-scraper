#!/usr/bin/python
from multiprocessing import Pool
import os, sys, csv, platform, datetime, glob

def _crawl(spider_name_params=None):
    if spider_name_params:
    	print ">>>>> Starting {}th process".format(spider_name_params[4])
    	command = 'scrapy crawl {} -a days={} -a hotel_info={} -a path={}'.format(spider_name_params[0], spider_name_params[1], spider_name_params[2], spider_name_params[3])
    	
        os.system(command)
        print "finished."
    return None

def run_crawler(days, source_file_path):
	if "*" in source_file_path:
		source_file_list = glob.glob(source_file_path.split('*')[0]+"*.csv")
		source_file_list = [f for f in source_file_list if "expedia" in f]
	else:
		source_file_list = [source_file_path]
	for csv_file in source_file_list:
		source_file = open(csv_file)
		csv_base = csv.reader(source_file)
		#print len(list(csv_base))
		spider_name_params = []

		if platform.system().lower() == 'windows':
			root = "rates/"
		else:
			root = "/var/www/html/rates/"

		path = "{}/expedia/".format(datetime.date.today().strftime("%Y%m%d"))

		if not os.path.exists(root+path):
			os.makedirs(root+path)

		for index, record in enumerate(csv_base):		
			if index == 0:
				continue
			param = "\"" + '---'.join(record) + "\""		
			spider_name_params.append(['expedia', days, param, root+path, index])
			
		# for x in range(0,len(spider_name_params), 4):		
		# 	#pool = Pool(processes=len(spider_name_params))		
		# 	pool = Pool(processes=4)
		# 	pool.map(_crawl, spider_name_params[x:x+4])

		pool = Pool(processes=32)
		pool.map(_crawl, spider_name_params)
		#pool.map(_crawl, spider_name_params[:5])
		
	f_done = open('%sdone' % (root+path), 'w')
	f_done.write("done")
	f_done.close()

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print "Usage: python ExpediaScraper.py <Days> <CSV file path>"
	else:
		file_path = sys.argv[2]
		print "Importing {} file...".format(file_path)

		run_crawler(days=sys.argv[1], source_file_path=file_path)

		
	