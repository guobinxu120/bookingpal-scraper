# -*- coding: utf-8 -*-
from urlparse import urljoin
from scrapy import Request,Spider, FormRequest, Selector


from collections import OrderedDict
from scrapy.utils.response import open_in_browser
import re, json, time, random
from datetime import timedelta, date


#?selected_currency=USD;checkin=2017-04-06;checkout=2017-04-09;group_adults=2
class BookingSpider(Spider):
	name = "booking"
	#start_urls = [	"http://www.booking.com/",]
	
	# def __init__(self, hotel_info, days, path, *args, **kwargs):


	########## test ######################
	def __init__(self, *args, **kwargs):
		hotel_info = "sdgfvadsfgasdf"
	######################################3
		super(BookingSpider, self).__init__(*args, **kwargs)

		print " ########## Initializing in Scrapy __init__"
		if not hotel_info:
			print "No parameter received."
			raise CloseSpider('Received no hotel information!')
		else:
			self.hotel_info = hotel_info.split('---')
			# self.start_urls = [self.hotel_info[10]]
			# self.days = days
			# self.path = path


			########   test  ###############
			self.start_urls = ["http://www.booking.com/hotel/us/melia-orlando-suite-hotel-at-celebration.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmaMIBiAEBmAExuAEGyAEM2AED6AEB-AECqAID;sid=0e088a816401f8e026640121bd2341bb;ucfs=1;room1=A,A;dest_type=city;dest_id=20023488;srfid=7effefe1fba3998f04f4d47e4342235e8168159bX145;highlight_room="]
			self.days = 3
			self.path = "../../test_result.json"
			#############################################

	def start_requests(self):
		for url in self.start_urls:
			#yield Request(url, self.parse, meta={'proxy':'https://108.59.14.203:13010'})
			link = url.split('?')[0].replace("http","https")
			yield Request(link, self.parse)


	def parse(self, response):
		lastDate = int(self.days)
		nMaxStayDays = [1,2,3,7]
		nMaxAdults = 2
		
		for s in (date.today()+timedelta(n+1) for n in range(lastDate)): # From today to last Days ()
			start = s.strftime("%Y-%m-%d")
			for nStayDay in nMaxStayDays:
				end = (s + timedelta(nStayDay)).strftime("%Y-%m-%d")

				for nAdults in range(nMaxAdults, 0, -1):
					url = response.url + "?selected_currency=USD;checkin={};checkout={};group_adults={}".format(start, end, nAdults)
					#print url
					checkInDate = '/'.join([start.split('-')[1],start.split('-')[2],start.split('-')[0]])
					param = {'checkIn':checkInDate, 'days':nStayDay, 'adults':nAdults, 'childs':0}
					yield Request(url, self.parse_offer, meta={'param':param, 'try':0})
					

	

	def parse_offer(self, response):

		item = OrderedDict()
		item['CheckIn'] = response.meta['param']['checkIn']
		item['LengthOfStay'] = response.meta['param']['days']
		item['Adults'] = response.meta['param']['adults']
		item['Childs'] = response.meta['param']['childs']
		item['RoomTypes'] = []

		freeParking = response.xpath('//*[@data-name-en="Free Parking"]')
		freeInternet = response.xpath('//*[@data-name-en="Free WiFi Internet Access Included"]')
		currency = response.xpath('//*[@data-id="currency_selector"]/input/@value').extract_first()
		
		if not currency:
			currency = "USD"

		roomTypes = response.xpath('//tr[contains(@class, "maintr")]')

		#open_in_browser(response)
		for rmcnt, roomType in enumerate(roomTypes):

			roomInfo = OrderedDict()

			roomTypeName = ''.join(roomType.xpath('./td[contains(@class, "roomType")]//a[contains(@class, "room-name")]/text()').extract()).replace('\n','')
			roomInfo['name'] = roomTypeName
			roomInfo['RoomTypeCode'] = roomType.xpath('.//*[@class="rt-room-info"]/@id').extract_first()
			roomInfo['rooms'] = []

			classNameForRoom = "room_loop_counter" + str(rmcnt+1)

			rooms = roomType.xpath('./following-sibling::tr[contains(@class, "{}")][@id]'.format(classNameForRoom))
			if rooms:
				for room in rooms:
					price = room.xpath('.//strong//text()').re('[\d.,]+')[0]
					maxPersons = room.xpath('./@data-occupancy').extract_first()
					freeCancellation = room.xpath('.//*[contains(text(), "FREE cancellation")]')
					freeBreakfast = room.xpath('.//*[contains(text(), "Breakfast included")]')
					freeBreakfast1 = room.xpath('.//*[@class="bicon-coffee mp-icon meal-plan-icon"]')

					room = OrderedDict()

					room['RoomName'] = roomTypeName
					room['Price'] = float(price.replace(',',''))
					room['Currency'] = currency
					room['MaxPersons'] = maxPersons
					room['PriceOptions'] = {}
					room['PriceOptions']['breakfast'] = True if freeBreakfast or freeBreakfast1 else False
					room['PriceOptions']['lunch'] = False
					room['PriceOptions']['dinner'] = False
					room['PriceOptions']['freeCancellation'] = True if freeCancellation else False
					room['PriceOptions']['freeInternet'] = True if freeInternet else False
					room['PriceOptions']['freeParking'] = True if freeParking else False
					room['PriceOptions']['freeShuttle'] = False # temper

					roomInfo['rooms'].append(room)
					#print "   ", maxPersons, price, "FreeCancellation:",True if freeCancellation else False,"FreeParking:",True if freeParking else False,"FreeInternet:",True if freeInternet else False,,"FreeBreakfast:",True if freeBreakfast else False

				item['RoomTypes'].append(roomInfo)
		item['url'] = response.url

		yield item