import requests
import json
from tqdm import tqdm

API_KEY = 'INSERT-YOUR-API-KEY'
API_URL = 'https://factchecktools.googleapis.com/v1alpha1/claims:search'

fact_sites = [
    'africacheck.org',
    'politifact.com',
    'leadstories.com',
    'fullfact.org',
    'factcheck.afp.com',
    'factcheck.org',
    'checkyourfact.com',
    'misbar.com',
    'washingtonpost.com',
    'boomlive.in',
    'dubawa.org',
    'polygraph.info',
    'usatoday.com',
    'altnews.in',
    'indiatoday.in',
    'newsmeter.in',
    'newsmobile.in',
    'factly.in',
    'vishvasnews.com',
    'aap.com.au',
    'thelogicalindian.com',
    'verafiles.org',
    'nytimes.com',
    'healthfeedback.org',
    'thequint.com',
    'newsweek.com',
    'icirnigeria.org',
    'bbc.co.uk',
    'factcheck.thedispatch.com',
    'ghanafact.com',
    'factcheckni.org',
    'theferret.scot',
    'rappler.com',
    'covid19facts.ca',
    'newsmobile.in:80',
    'thegazette.com',
    'abc.net.au',
    'ha-asia.com',
    'sciencefeedback.co',
    'cbsnews.com',
    'fit.thequint.com',
    'namibiafactcheck.org.na',
    'thejournal.ie',
    'poynter.org',
    'zimfact.org',
    'climatefeedback.org',
    'factchecker.in',
    'pesacheck.org',
    'ghana.dubawa.org',
    'scroll.in'
]


all_params = [{
    'key': API_KEY,
    'reviewPublisherSiteFilter': site,
    'languageCode': 'en',
    'maxAgeDays': 365*5,
    'pageSize': 100,
}
for site in fact_sites]


claims = []
for params in tqdm(all_params):
    print(len(claims))
    while True:
        try:
            response = requests.get(API_URL, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
           
                claims.extend(data.get('claims', []))
       
                next_page_token = data.get('nextPageToken')
                if next_page_token:
                    params['pageToken'] = next_page_token 
                    continue
                else:
                    break  
            else:
                print(f"Error: {response.status_code}, {response.text}")
                break
        except requests.exceptions.Timeout:
            print("Time out，requesting...")
            continue
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            break
        
print(len(claims))    

with open('raw_claims.json', 'w') as json_file:
    json.dump(claims, json_file, indent=4)

