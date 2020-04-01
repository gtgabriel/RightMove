'''rm.py: a class that connects to rightmove and 
extracts house prices from a set of locations around London'''

__author__      = "Gabriel Grigorescu"
__copyright__   = "Copyright 2020, London"
__version__ = "1.0"
__maintainer__ = "Gabriel Grigorescu"
__email__ = "g.t.grigorescu@gmail.com"
__status__ = "Play with it at your own risk"

import requests
import pandas as pd
import json as js
import datetime
import matplotlib.pyplot as plt
import math
import numpy as np

debug = False

url_template = "https://api.rightmove.co.uk/api/sale/find?"

results_per_page = 25
max_nr_scrapes = 20

global_locations = {'st albans station': 'STATION%5E8573',
             'richmond station' : 'STATION%5E7703',
             'west dulwich station': 'STATION%5E9827',
             'stevenage station': 'STATION%5E8732',
             'welwyn north station':'STATION%5E9770',
             'welwyn garden city station': 'STATION%5E9767',
             'sevenoaks station': 'STATION%5E8081',
             'dunton green station': 'STATION%5E3002',
             'cambridge station' : 'STATION%5E1703',
             'norbiton station' : 'STATION%5E6686',
             'crystal palace station' : 'STATION%5E2507',
             'thames ditton station' : 'STATION%5E9092',
             'harpenden station' : 'STATION%5E4262',
             'surbiton station': 'STATION%5E8912',    
			 'hitchin station': 'STATION%5E4646',
			 'mottingham station': 'STATION%5E6425',
			 'chislehurst station': 'STATION%5E2078',
             'sidcup station': 'STATION%5E8252', 
             'new eltham station': 'STATION%5E6551', 
             'lee station': 'STATION%5E5459', 

            }

# this dict is an example, will be overwritten from outside the module 
general_search_dict = {'index': 0,
               'sortType' : 1,
               'numberOfPropertiesRequested': 50, # max supported for the API, overridden by results_per_page
               'locationIdentifier': global_locations['st albans station'],
               'minBedrooms' : 3,
               'maxBedrooms' : 3,
               'propertyTypes': 'detached', # doesnt seem to work
               'primaryDisplayPropertyType': 'houses',
               'minPrice': 400000,
               'maxPrice': 500000,
               'radius': 2.0,
               'apiApplication': 'IPAD',
                }

# extracting and parsing the output dict a bit, adding a few features
def extract_property(prop_dict):

    prop = {}
    prop['address'] = prop_dict['address']
    prop['bedrooms'] = prop_dict['bedrooms']
    prop['distance'] = prop_dict['distance']
    prop['photoCount'] = prop_dict['photoCount']
    prop['propertyType'] = prop_dict['propertyType']
    prop['price'] = prop_dict['price']
    prop['updateDateStr'] = datetime.datetime.fromtimestamp(int(prop_dict['updateDate'])/1000).strftime('%Y-%m-%d')
    prop['updateDate'] = datetime.datetime.fromtimestamp(int(prop_dict['updateDate'])/1000)
    prop['latitude'] = prop_dict['latitude']
    prop['longitude'] = prop_dict['longitude']
    prop['floorplanCount'] = prop_dict['floorplanCount']
    prop['sortDate'] = datetime.datetime.fromtimestamp(int(prop_dict['sortDate'])/1000)
    prop['sortDateStr'] = datetime.datetime.fromtimestamp(int(prop_dict['sortDate'])/1000).strftime('%Y-%m-%d')
    prop['identifier'] = prop_dict['identifier']
    prop['premiumDisplay'] = prop_dict['premiumDisplay']
    prop['autoEmailReasonType'] = prop_dict['autoEmailReasonType']
    prop['premiumDisplay'] = prop_dict['premiumDisplay']
    prop['priceQualifier'] = prop_dict['priceQualifier']
    prop['scrapeDate'] = datetime.datetime.now()
    prop['days_since_post'] = (prop['scrapeDate'] - prop['sortDate']).days

    return prop


class rm:

    def __init__(self, new_search_dict):
        self.df = pd.DataFrame()
        self.search_details = general_search_dict
        if new_search_dict is not None:
            self.set_search_details(new_search_dict)

    def run_test_search(self):

        # first reset to page 1
        if self.search_details:
            self.search_details['index'] = 0

        r = requests.get(url_template, params = self.search_details)
        answer_dict = js.loads(r.text)
        r.close()
        totalAvailableResults = 0
        if answer_dict['result'] == 'SUCCESS':
            if debug: print('total available results: ', str(answer_dict['totalAvailableResults']))
            totalAvailableResults = int(answer_dict['totalAvailableResults'])
        return totalAvailableResults

    def how_many_searches(self):
        try:
            nr_searches = math.ceil(self.run_test_search()/results_per_page)
            if debug: print('results per page :', results_per_page)
            if debug: print('Needed scrapes: ', nr_searches)
            return nr_searches
        except:
            return None

    def get_search_details(self):
        return self.search_details

    def set_search_details(self, new_dict):
        try:
            for key in new_dict:
                if key in self.search_details.keys():
                    if key == 'locationIdentifier':
                        self.search_details[key] = global_locations[new_dict[key]]
                    else:
                        self.search_details[key] = new_dict[key]
                else:
                    print('I didnt load this parameter, not understood: ', key)
            return
        except:
            print('Something went wrong when updating search details, check your dictionary')

    def clear_df(self):
        self.df = pd.DataFrame()

    def run_search(self):
        # run first search, check returned results
        nr_searches = self.how_many_searches()
        if (nr_searches is None) or nr_searches == 0: return

        for this_search in range(min(nr_searches, max_nr_scrapes)):

            if debug:
                print('-------------------')
                print('Scraping Round : ', this_search + 1)
                print('-------------------')

            self.search_details['index'] = results_per_page * this_search
            r = requests.get(url_template, params = self.search_details)
            # print('URL : ', r.url)
            answer_dict = js.loads(r.text)
            r.close()

            try:
                if answer_dict['result'] == 'SUCCESS':

                    if debug:
                        print('Scraped: ', answer_dict['result'])
                        print('total results: ', answer_dict['totalAvailableResults'])

                    if int(answer_dict['totalAvailableResults']) > 0:
                        out_dict = js.loads(r.content)
                        props_list = []

                        if len(out_dict['properties']) > 0:
                            for i in range(len(out_dict['properties'])):
                                p = extract_property(out_dict['properties'][i])
                                # let's add the searched location as well
                                p['searched_location'] = answer_dict['searchableLocation']['name']
                                props_list.append(p)

                        if len(props_list) > 0:
                            df = pd.DataFrame(props_list)
                            self.df = self.df.append(df)

            except:
                if debug:
                    print('Parsing the SUCCESSed Scrape went bad!!!')
                    print(self.search_details)

        # done with scraping, setting back the index
        self.search_details['index'] = 0
        # remove duplicates
        self.df = self.df.drop_duplicates().reset_index(drop=True)
        if debug: print('Added ', len(self.df), ' houses')
        return

    def price_hist(self, title_bit = None):
        bins = np.arange(min(self.df.price), max(self.df.price), 25_000)
        plt.hist(self.df.price, bins)
        plt.grid(True)
        plt.xticks(rotation=45)
        title = 'Houses by price '
        if title_bit: title+= title_bit
        plt.title(title)
        plt.show()

    def days_posted_hist(self):
        plt.hist(self.df.days_since_post, bins = np.arange(0,max(self.df.days_since_post),10))
        plt.show()


def price_hist(df, title_bit=None):
    bins = np.arange(min(df.price), max(df.price), 25_000)
    plt.hist(df.price, bins)
    plt.grid(True)
    plt.xticks(rotation=45)
    title = 'Houses by price '
    if title_bit: title += title_bit
    plt.title(title)
    plt.show()

def main():
    # do nothing for now
    pass

if __name__ == "__main__":
    main()
    
