import requests
import os
import json
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


with open('merged_claims.json', 'r') as json_file:
    dataset = json.load(json_file)


def create_session():
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504, 403]
    )
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session


wrong_pages_num = 0

def save_html(item, folder_path, delay=1):
    global wrong_pages_num
    url = item["url"]
    if url:
        session = create_session()  
        while True:
            try:
                response = session.get(url, timeout=10)  
                response.raise_for_status()  

                title = item["claim_id"]
                filename = f"{title}.html"
                file_path = os.path.join(folder_path, filename)

                response.encoding = 'utf-8'  

                
                with open(file_path, "w", encoding='utf-8') as file:
                    file.write(response.text)

                time.sleep(delay)  
                break  

            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:  
                    delay *= 2
                    if delay >= 30:
                        print(f"Max delay reached for {url}. Skipping...")
                        break
                    print(f"429 Too Many Requests: increasing delay to {delay}s and retrying...")
                    time.sleep(delay)
                else:
                    print(f"Failed to retrieve {url}: {e}")
                    wrong_pages_num += 1
                    break  

            except requests.exceptions.RequestException as e:
                print(f"Request failed for {url}: {e}")
                wrong_pages_num += 1
                break  

            except Exception as e:
                print(f"Unexpected error while retrieving {url}: {e}")
                wrong_pages_num += 1
                break


def save_html_from_dataset(dataset, folder_path, batch_size=100, max_workers=5):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for i in range(0, len(dataset), batch_size):
        batch = dataset[i:i + batch_size]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(save_html, item, folder_path) for item in batch]

            for future in tqdm(as_completed(futures), total=len(futures), desc=f"Batch {i // batch_size + 1}"):
                try:
                    future.result(timeout=15)
                except TimeoutError:
                    print("A task took too long and was skipped.")

    print("Processing complete.")
    print(f"Number of failed pages: {wrong_pages_num}")


save_html_from_dataset(dataset, "saved_pages")






from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import os
import time

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--enable-unsafe-swiftshader')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--allow-insecure-localhost')  
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.116 Safari/537.36")

driver_path = r"YOUR PATH TO chromedriver.exe"
driver = webdriver.Chrome(executable_path=driver_path, options=options)
wait = WebDriverWait(driver, 10)

folder_path = "saved_pages"
file_names = os.listdir(folder_path)
claim_ids = {int(file.split(".")[0]) for file in file_names}
original_ids = set(range(1, 4158))
null_pages_claim_ids = sorted(list(original_ids - claim_ids))

with open('merged_claims.json', 'r') as json_file:
    dataset = json.load(json_file)

success_pages = []
failed_pages = []

for idx in null_pages_claim_ids:
    attempts = 0
    url = dataset[idx - 1]["url"]
    title = dataset[idx - 1]["claim_id"]
    filename = f"{title}.html"
    file_path = os.path.join(folder_path, filename)
    
    print(f"Attempting to fetch: {url}")
    
    while attempts < 5:
        try:
            driver.get(url)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            html = driver.page_source
            if "You don't have permission to access" in html:
                print("Permission denied for:", filename)
                failed_pages.append(filename)
                break
            
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(html)
            print("Page saved:", filename)
            success_pages.append(filename)
            break
        
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            attempts += 1
            time.sleep(2) 

    else:
        print(f"Failed to fetch {url} after {attempts} attempts")
        failed_pages.append(filename)

driver.quit()

print("Success pages:", success_pages)
print("Failed pages:", failed_pages)
print("Total successful:", len(success_pages))
print("Total failed:", len(failed_pages))
