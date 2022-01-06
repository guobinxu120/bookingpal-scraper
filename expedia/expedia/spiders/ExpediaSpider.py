# -*- coding: utf-8 -*-
from urlparse import urljoin
from scrapy import Request,Spider, FormRequest, Selector


from collections import OrderedDict
from scrapy.utils.response import open_in_browser
import re, json, time, random
from datetime import timedelta, date

from time import mktime


class ExpediaSpider(Spider):
	name = "expedia"
	# use_selenium = True
	priority = 1
	def __init__(self, hotel_info, days, path, *args, **kwargs):
		super(ExpediaSpider, self).__init__(*args, **kwargs)

		print " ########## Initializing in Scrapy __init__"
		if not hotel_info:
			print "No parameter received."
			raise CloseSpider('Received no hotel information!')
		else:
			self.hotel_info = hotel_info.split('---')
			self.start_urls = [self.hotel_info[10]]
			# self.start_urls = ['https://www.expedia.com/Holiday-Inn-Resort-Orlando-Lake-Buena-Vista.h19535.Hotel-Information']
			self.days = days
			self.path = path

	# def __init__(self, *args, **kwargs):
	# 	super(ExpediaSpider, self).__init__(*args, **kwargs)
    #
	# 	# self.hotel_info = hotel_info.split('---')
	# 	self.start_urls = ['https://www.expedia.com/Surf-Side-Hotel.h10922493.Hotel-Information']
	# 	self.days = "2"
	# 	self.path = ""

	def start_requests(self):
		for url in self.start_urls:
			# yield Request(url, self.parse, meta={'proxy':'138.68.16.252:80'})
			request = Request(url, self.parse, dont_filter=True)
			# request.meta['proxy'] = "http://138.68.16.252:80"
			yield request

	def parse(self, response):
		print "########"
		try:
			# self.hotel_info[9] = response.xpath('//h1[@id = "hotel-name"]/text()')[0]
			token = re.findall('infosite.token\s=\s\'(.*)\';', response.body)[0]
			print token
			hotelid = re.findall('infosite.hotelId\s=\s\'(.*)\';', response.body)[0]
			room_type_raw_data = re.findall('roomsAndRatePlans\s=\s(\{.*\});', response.body)
			room_types_info = json.loads(room_type_raw_data[0])
		except:
			print "Error"
		else:

			room_types = []
			for room in room_types_info['rooms'].values():
				item = {}
				item['roomTypeCode'] = room['roomTypeCode']
				item['name'] = room['name']
				item['breakfast'] = True if "2001" in room['amenities'] else False
				item['internet'] = True if "2390" in room['amenities'] or "2403" in room['amenities'] else False
				item['parking'] = True if "3861" in room['amenities'] else False

				item['maxGuests'] = room['maxGuests']
				item['maxChildren'] = room['maxChildren']
				room_types.append(item)

			lastDate = int(self.days)
			# lastDate = 10
			nMaxStayDays = [1,2,3,7]
			nMaxAdults = 2
			for s in (date.today()+timedelta(n+1) for n in range(lastDate)): # From today to last Days ()
				start = s.strftime("%m/%d/%Y")
				for nStayDay in nMaxStayDays:
					end = (s + timedelta(nStayDay)).strftime("%m/%d/%Y")
					url = "https://www.expedia.com/api/infosite/{}/getOffers".format(hotelid)
					queries = "?clientid=KLOUD-HIS"
					queries += "&token={}".format(token)
					queries += "&brandId=0"
					queries += "&countryId=0"
					queries += "&isVip=false"
					queries += "&chid="
					queries += "&chkin={}".format(start)
					queries += "&chkout={}".format(end)
					queries += "&daysInFuture="
					queries += "&stayLength="
					for nAdults in range(nMaxAdults, 0, -1):
						queries += "&adults={}".format(nAdults)
						queries += "&children={}".format(0)
						queries += "&ts={}".format(str(int(float(time.time()*1000))))
						queries += "&tla=VPS"
						self.priority -= 1
						# headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
						# yield Request(url+queries, self.parse_offer, meta={'checkIn':start, 'adults':nAdults, 'days':nStayDay, 'childs':0, 'roomTypes':room_types,'proxy':'http://138.68.16.252:80'})
						request = Request(url+queries, self.parse_offer, meta={'checkIn':start, 'adults':nAdults, 'days':nStayDay, 'childs':0, 'roomTypes':room_types, 'try':0}, priority=self.priority, dont_filter=True)
						# request.meta['proxy'] = "http://138.68.16.252:80"
						yield request
						
	def parse_offer(self, response):
		
		item = OrderedDict()
		item['CheckIn'] = response.meta['checkIn']
		item['LengthOfStay'] = response.meta['days']
		item['Adults'] = response.meta['adults']
		item['Childs'] = response.meta['childs']
		item['RoomTypes'] = []

		bSuccessed = True
		try:
			data = json.loads(response.body)		
			offers = data['offers']

			print ">>>>>>>>",len(offers)
			for index, offer in enumerate(offers):
				duplicated_room = False
				# if offer['drrpresent'] == False:
				# 	print "[",index,"]", "Sold Out!!!"
				# 	continue
				# if offer['offerType'] != "1" and offer['offerType'] != "5":
				# 	continue
				roomInfo = OrderedDict()

				roomInfo['name'] = ""
				for roomtype in response.meta['roomTypes']:
					if roomtype['roomTypeCode'] == offer['roomTypeCode']:
						roomInfo['name'] = roomtype['name']
				roomInfo['RoomTypeCode'] = offer['roomTypeCode']
				roomInfo['rooms'] = []

				try:
					try:
						price = offer["price"]["displayPrice"]
						currency = offer['price']['priceObject']['currencyCode']
					except:
						continue
						price = offer["nightlyRates"][0][0]["displayPrice"]
						currency = offer["nightlyRates"][0][0]["priceObject"]["currencyCode"]

					room = OrderedDict()
					room['RoomName'] = offer['roomName']
					room['Price'] = float(re.findall('[\d.]+',price.replace(',',''))[0])
					#room['BarPrice'] = ""
					room['Currency'] = currency					
					
					room['MaxPersons'] = ""
					#room['Meal'] = "none"
					free_internet = False
					free_parking = False

					print "[",index,"]", price, roomInfo['name'],offer['offerType']
					for roomtype in response.meta['roomTypes']:
						if roomtype['roomTypeCode'] == offer['roomTypeCode']:
							room['MaxPersons'] = roomtype['maxGuests']
							free_internet = roomtype['internet']
							free_parking = roomtype['parking']

					meal = "breakfast" if "2205" in offer['amenities'] or "2103" in offer['amenities'] or "2194" in offer['amenities'] else "none"
					#if "2109" in offer['amenities']:
					room['PriceOptions'] = {}
					room['PriceOptions']['breakfast'] = True if meal is not "none" else False
					room['PriceOptions']['lunch'] = False
					room['PriceOptions']['dinner'] = False
					cancellation_date_str = "2017" + str(offer['cancellationWindowDate'])#"Tue, Mar 28"
					cancellation_date = time.strptime(cancellation_date_str, "%Y%a, %b %d")
					cancellable_date = date.fromtimestamp(mktime(cancellation_date))
					t = date.today()
					room['PriceOptions']['freeCancellation'] = True if cancellable_date > t else False
					room['PriceOptions']['freeInternet'] = free_internet
					room['PriceOptions']['freeParking'] = free_parking
					room['PriceOptions']['freeShuttle'] = False # temper
					#room['Policies'] = []
					if item['RoomTypes']:
						for r in item['RoomTypes']:
							if r['RoomTypeCode'] == offer['roomTypeCode']:
								r['rooms'].append(room)
								duplicated_room = True

					if not duplicated_room:
						roomInfo['rooms'].append(room)

				except Exception as e:
					print "Exception occured while catching..."
					print e
					print "[[["
					#print json.dumps(offer)
					print "]]]"
					continue
				if not duplicated_room:
					item['RoomTypes'].append(roomInfo)
		except:
			print "No rate info"
			bSuccessed = False
			if response.meta['try'] < 2:				
				#meta['proxy'] = 'https://108.59.14.203:13010'
				yield Request(response.url, self.parse_offer, meta={'checkIn':response.meta['checkIn'], 'adults':response.meta['adults'],\
															'days':response.meta['days'], 'childs':response.meta['childs'],\
															'roomTypes':response.meta['roomTypes'], \
															'try':response.meta['try']+1},\
															#'proxy':'https://108.59.14.203:13010',\
															 dont_filter=True)
		if bSuccessed:
			yield item

