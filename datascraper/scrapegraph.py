#import required packages
from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

#define a function to get the review URLs
options = webdriver.ChromeOptions()
# options.add_argument("--headless=new")  

def getUrls():
    search = input('Enter business name and location: ')
    forUrl = search.replace(' ', '+')
    browser = webdriver.Chrome(options=options)
    browser.get(f"https://www.google.com/maps/search/{forUrl}")
    
    time.sleep(3)  # Allow page to load

 
    # Try to find and click "Alle akzeptieren" (Accept All)
    accept_button = WebDriverWait(browser, 5).until(
        EC.element_to_be_clickable((By.XPATH, '//button[.//span[contains(text(),"Alle akzeptieren")]]'))
    )
    accept_button.click()
    print("Accepted cookies.")



    results = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@role='feed']"))
    )
    
    # Extract business links
    anchorTags = results.find_elements(By.XPATH, "//a[contains(@href, '/maps/place/')]")

    urls = [tag.get_attribute('href') for tag in anchorTags]

    browser.quit()
    return urls

#define a function that extracts reviews from the collected URLs
def extractReviews(urls):
    all_reviews = []
    
    for url in urls[:2]:
        try:
            
            browser = webdriver.Chrome(options=options)
            browser.get(url)
            time.sleep(3)
            accept_button = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//button[.//span[contains(text(),"Alle akzeptieren")]]')))
            accept_button.click()
            print("Accepted cookies for the 2nd.")

            # Click the Reviews tab
            WebDriverWait(browser, 6).until(
                EC.element_to_be_clickable((By.XPATH, '//div[contains(@class, "Gpq6kf") and contains(@class, "NlVald") and text()="Rezensionen"]'))
            ).click()

            # Scroll through reviews
            reviewArea = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "DxyBCb")]'))
            )
            
            for _ in range(10):
                browser.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", reviewArea)
                time.sleep(1)

            # Extract reviews
            reviewDivs = browser.find_elements(By.XPATH, "//div[contains(@class, 'jftiEf')]")

            for review in reviewDivs:
                all_reviews.append(
                    {
                        "Reviewer": review.find_element(By.CLASS_NAME, 'd4r55').text if review.find_elements(By.CLASS_NAME, 'd4r55') else "N/A",
                        "About": review.find_element(By.CLASS_NAME, 'RfnDt').text if review.find_elements(By.CLASS_NAME, 'RfnDt') else "N/A",
                        "Rating": review.find_element(By.CLASS_NAME, 'kvMYJc').get_attribute('aria-label') if review.find_elements(By.CLASS_NAME, 'kvMYJc') else "N/A",
                        "Reviewed On": review.find_element(By.CLASS_NAME, 'rsqaWe').text if review.find_elements(By.CLASS_NAME, 'rsqaWe') else "N/A",
                        "Review Text": review.find_element(By.CLASS_NAME, 'MyEned').text if review.find_elements(By.CLASS_NAME, 'MyEned') else "N/A",
                    }
                )

            browser.quit()
            print(len(all_reviews))

        except Exception as e:
            print(f"Error: {e}")
            continue

    return all_reviews

#integrated the defined functions
if __name__ == "__main__":
    # call getUrls() to get the URLs from Google Maps
    urls = getUrls()

    # call extractReviews() to extract reviews from the collected URLs
    data = extractReviews(urls)

    # write the extracted reviews to a file
    with open("googleReviews.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
