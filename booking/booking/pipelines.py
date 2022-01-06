# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import requests
import time
from scrapy.utils.project import get_project_settings
import sys, os, datetime
import json
from scrapy import signals
from scrapy.exporters import JsonLinesItemExporter

SETTINGS = get_project_settings()

class BookingPipeline(object):
	def __init__(self):
		#Instantiate API Connection
		self.files = {}
		print ">>>>>> Initialize pipeline."
		
	@classmethod
	def from_crawler(cls, crawler):
		pipeline = cls()
		crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
		crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
		return pipeline


	def spider_opened(self, spider):
		#open a static/dynamic file to read and write to
		path = spider.path

		file = open(path+'%s.json' % spider.hotel_info[4], 'w+b')
		self.files[spider] = file
		#file.write('{"HotelName":"{}","Rates":['.format("My hotel"))
		# header = '{"HotelName":"%s",\
		# 			"HotelInfo":{ \
		# 				"cityOrininId":"%s" \
		# 				"cityOriginName":"%s" \
		# 				"propertyId":"%s"\
		# 			},\
		# 		"Rates":[' % 
		# 		(spider.hotel_info[0], spider.hotel_info[1], spider.hotel_info[4], spider.hotel_info[9])

		header = '{"HotelName":"%s","HotelInfo":{"cityOriginId":"%s","cityOriginName":"%s","propertyId":"%s"},"Rates":[ \n' % \
			 (spider.hotel_info[9], spider.hotel_info[0], spider.hotel_info[1], spider.hotel_info[4])

		file.write(header)
		
		log_path = '/'.join(path.split('/')[:-2]) + "/log.csv"
		print "Log Path:", log_path
		if not os.path.exists(log_path):
			log_file = open(log_path, "a")
			header = "cityOriginId,cityOriginName,propertyOriginName,hotel_desc,propertyAddress,Phone,PostalCode,propertyLatitude,propertyLongitude,vendorName1,propertyId1,propertyURL1,queryDate1,allProperties1,destinationType1,propertyClass1,reviewScore1,page1,position1,numberOfReviews1,vendorName2,propertyId2,propertyURL2,queryDate2,allProperties2,destinationType2,propertyClass2,reviewScore2,page2,position2,numberOfReviews2\n"
			log_file.writelines([header])
			log_file.close()


		self.exporter = JsonLinesItemExporter(file)
		self.exporter.start_exporting()

	def spider_closed(self, spider):
		self.exporter.finish_exporting()
		file = self.files.pop(spider)
		file.seek(-1, 1)
		file.write("]}")
		file.close()

		param = spider.hotel_info#spider.hotel_info.strip('"').split('---')
        
		prop_log = param[0] + ",\"" + param[1] + "\","
		prop_log = prop_log + '"' + param[9] + '","' + param[13] + '","' + param[14] + '",,' +param[14].split(',')[-1].split(' ')[-1]+',' + param[11] + ',' + param[12] + ','
		#prop_log = prop_log + ',,,,,,,,,,,'
		prop_log = prop_log + "expedia" + "," + param[4] + ',"' + param[10] + '",' + datetime.date.today().strftime("%Y/%m/%d") + ',' + param[2] + ',' + param[3] + ',' + ','.join(param[5:9]) + ',' + param[15]
		prop_log = prop_log + "\n"

		log_path = '/'.join(spider.path.split('/')[:-2]) + "/log.csv"
		if os.path.exists(log_path):
			log_file = open(log_path, "a")
			log_file.writelines([prop_log])
			log_file.close()

	def process_item(self, item, spider):		
		self.exporter.export_item(dict(item))
		file = self.files[spider]
		file.write(",")
		return item