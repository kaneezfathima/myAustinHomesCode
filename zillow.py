from lxml import html, etree
import requests
import unicodecsv as csv
import argparse
import re

# url = "https://www.zillow.com/homes/78727_rb/"
# https://www.zillow.com/homes/for_sale/Austin-TX-78727/house_type/92638_rid/4-_beds/3-_baths/0-400000_price/0-1614_mp/7500-_lot/30.468427,-97.660647,30.389979,-97.77051_rect/12_zm/
# https://www.zillow.com/homes/for_sale/house_type/4-_beds/3-_baths/0-400000_price/0-1614_mp/7500-_lot/30.563296,-97.613697,30.406488,-97.833424_rect/11_zm/0_mmm/
def parse(zipcode,filter=None):

	if filter=="newest":
		#url = "https://www.zillow.com/homes/Cedar-Park,-TX-78613_rb/"
		url = "https://www.zillow.com/homes/for_sale/Cedar-Park-TX-78613/house_type/92551_rid/4-_beds/3-_baths/0-400000_price/0-1594_mp/7500-_lot/30.577188,-97.706395,30.420404,-97.926121_rect/11_zm/"
		print "Line 13...."
	elif filter == "cheapest":
		url = "https://www.zillow.com/homes/for_sale/house_type/4-_beds/3-_baths/0-400000_price/0-1614_mp/7500-_lot/pricea_sort/30.563296,-97.613697,30.406488,-97.833424_rect/11_zm/0_mmm/"
	else:
		url = "https://www.zillow.com/homes/for_sale/house_type/4-_beds/3-_baths/0-400000_price/0-1614_mp/7500-_lot/globalrelevanceex_sort/30.563296,-97.613697,30.406488,-97.833424_rect/11_zm/0_mmm/"
	
	for i in range(5):
		# try:
		headers= {
					'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
					'accept-encoding':'gzip, deflate, sdch, br',
					'accept-language':'en-GB,en;q=0.8,en-US;q=0.6,ml;q=0.4',
					'cache-control':'max-age=0',
					'upgrade-insecure-requests':'1',
					'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
		}
		response = requests.get(url,headers=headers)
		print(response.status_code)
		parser = html.fromstring(response.text)
		#print "response.text...{}".format(response.text.encode('utf-8').strip())
		Html_file= open("response","w")
		Html_file.write(response.text.encode('utf-8').strip())
		Html_file.close()
		search_results = parser.xpath("//div[@id='search-results']//article")
		properties_list = []
		
		for properties in search_results:
			raw_address = properties.xpath(".//span[@itemprop='address']//span[@itemprop='streetAddress']//text()")
			raw_city = properties.xpath(".//span[@itemprop='address']//span[@itemprop='addressLocality']//text()")
			raw_state= properties.xpath(".//span[@itemprop='address']//span[@itemprop='addressRegion']//text()")
			raw_postal_code= properties.xpath(".//span[@itemprop='address']//span[@itemprop='postalCode']//text()")
			raw_price = properties.xpath(".//span[@class='zsg-photo-card-price']//text()")
			raw_info = properties.xpath(".//span[@class='zsg-photo-card-info']//text()")
			raw_broker_name = properties.xpath(".//span[@class='zsg-photo-card-broker-name']//text()")
			url = properties.xpath(".//a[contains(@class,'overlay-link')]/@href")
			raw_title = properties.xpath(".//h4//text()")
			minibubble = properties.xpath(".//div[@class='minibubble template hide' and contains(text(), '')]")
			lotSizesList = []
			yearsBuiltList = []

			for i in minibubble:
				#print "lst ...{}".format(lst)
				v = etree.tostring(i, pretty_print=True)
				lotSize = re.search('"lotSize": [0-9]*.([0-9]*)?,', v)
				lotSizesList.append(lotSize.group())
				year = re.search('"yearBuilt": [0-9]*.,', v)
				yearsBuiltList.append(year.group())
			
			address = ' '.join(' '.join(raw_address).split()) if raw_address else None
			city = ''.join(raw_city).strip() if raw_city else None
			state = ''.join(raw_state).strip() if raw_state else None
			postal_code = ''.join(raw_postal_code).strip() if raw_postal_code else None
			price = ''.join(raw_price).strip() if raw_price else None
			info = ' '.join(' '.join(raw_info).split()).replace(u"\xb7",',')
			broker = ''.join(raw_broker_name).strip() if raw_broker_name else None
			title = ''.join(raw_title) if raw_title else None
			property_url = "https://www.zillow.com"+url[0] if url else None
			lotSize = lotSizesList
			yearBuilt = yearsBuiltList
			
			is_forsale = properties.xpath('.//span[@class="zsg-icon-for-sale"]')
			properties = {
							'address':address,
							'city':city,
							'state':state,
							'postal_code':postal_code,
							'price':price,
							'facts and features':info,
							'real estate provider':broker,
							'url':property_url,
							'title':title,
							'lotSize':lotSize,
							'yearBuilt':yearBuilt
			}
			if is_forsale:
				properties_list.append(properties)
		return properties_list
		# except:
		# 	print ("Failed to process the page",url)

if __name__=="__main__":
	argparser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
	argparser.add_argument('zipcode',help = '')
	sortorder_help = """
    available sort orders are :
    newest : Latest property details,
    cheapest : Properties with cheapest price
    """
	argparser.add_argument('sort',nargs='?',help = sortorder_help,default ='Homes For You')
	args = argparser.parse_args()
	zipcode = args.zipcode
	sort = args.sort
	print ("Fetching data for %s"%(zipcode))
	scraped_data = parse(zipcode,sort)

	#print "scraped_data .... {}".format(scraped_data)
	print ("Writing data to output file")
	try:
		with open("properties-%s.csv"%(zipcode),'wb')as csvfile:
			fieldnames = ['title','address','city','state','postal_code','price','facts and features','real estate provider','url','lotSize','yearBuilt']
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			for row in  scraped_data:
				#print row
				writer.writerow({'title':row['title'], 'address':row['address'],'city':row['city'],'state':row['state'],'postal_code':row['postal_code'],'price':row['price'],'facts and features':row['facts and features'],'real estate provider':row['real estate provider'],'url':row['url'], 'lotSize':row['lotSize'], 'yearBuilt':row['yearBuilt']})
	except :
		print "Error writing to csv"
