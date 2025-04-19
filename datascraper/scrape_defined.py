#import required packages
from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import time
import csv
import re  # Add this import explicitly
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Define WebDriver options globally
options = webdriver.ChromeOptions()
options.add_argument("--disable-notifications")
options.add_argument("--disable-infobars")

# options.add_argument("--headless=new")  # Uncomment for headless mode

# Extract reviews with 3 stars or less
def extractReviews():
    global options
    search = input('Enter business name and location: ')
    search_query = search.replace(' ', '+')

    # Use the global options variable
    browser = webdriver.Chrome(options=options)
    browser.get(f"https://www.google.com/maps/search/{search_query}")
    time.sleep(3)

    all_reviews = []
    
    # Accept cookies
    try:
        accept_button = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//button[.//span[contains(text(),"Alle akzeptieren")]]'))
        )
        accept_button.click()
        print("Accepted cookies on business page.")
    except (TimeoutException, NoSuchElementException):
        print("No cookie prompt or already accepted")

    # First extract business overview information
    try:
        print("Extracting business overview information...")
        
        # Extract business name
        business_name = "N/A"
        try:
            business_name = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.DUwDvf"))
            ).text
            print(f"Business name: {business_name}")
        except:
            print("Could not find business name")
        
        # Extract average rating
        avg_rating = "N/A"
        try:
            rating_element = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.F7nice span.ceNzKf"))
            )
            avg_rating = rating_element.text
            print(f"Average rating: {avg_rating}")
        except:
            print("Could not find average rating")
        
        # Extract total number of reviews
        total_reviews = "N/A"
        try:
            reviews_element = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.F7nice span.RDApEe"))
            )
            total_reviews = reviews_element.text
            print(f"Total reviews: {total_reviews}")
        except:
            print("Could not find total reviews")
        
        # Extract price level (€, €€, €€€, etc.)
        price_level = "N/A"
        try:
            price_elements = browser.find_elements(By.XPATH, "//span[contains(@aria-label, '€')]")
            if price_elements:
                price_level = price_elements[0].get_attribute('aria-label')
            print(f"Price level: {price_level}")
        except:
            print("Could not find price level")
            
        # Extract price range if available (like "10-20 € pro Person")
        price_range = "N/A"
        try:
            price_range_elements = browser.find_elements(By.XPATH, 
                "//span[contains(text(), '€ pro Person') or contains(text(), '€ per person')]")
            if price_range_elements:
                price_range = price_range_elements[0].text
            print(f"Price range: {price_range}")
        except:
            print("Could not find price range")
        
        # Store business overview data
        business_data = {
            "Business Name": business_name,
            "Average Rating": avg_rating,
            "Total Reviews": total_reviews,
            "Price Level": price_level,
            "Price Range": price_range
        }
        
    except Exception as e:
        print(f"Error extracting business overview: {e}")
        business_data = {}

    # Click "Rezensionen"
    try:
        reviews_button = WebDriverWait(browser, 6).until(
            EC.element_to_be_clickable((By.XPATH, '//div[contains(@class, "Gpq6kf") and contains(@class, "NlVald") and text()="Rezensionen"]'))
        )
        reviews_button.click()
        print("Clicked on Rezensionen.")
    except (TimeoutException, NoSuchElementException):
        print("Trying alternative method to click on reviews")
        try:
            reviews_button = WebDriverWait(browser, 6).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label, "Rezensionen")]'))
            )
            reviews_button.click()
            print("Clicked on Rezensionen (alternative method).")
        except:
            print("Could not find reviews button")

    # Scroll through ALL reviews
    try:
        reviewArea = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "DxyBCb")]'))
        )
        
        # Continuous scrolling until no new reviews appear
        previous_reviews_count = 0
        max_attempts = 50  # Limit to prevent infinite scrolling
        no_new_reviews_count = 0
        
        print("Starting to scroll through all reviews...")
        
        for attempt in range(max_attempts):
            # Get current number of reviews
            reviewDivs = browser.find_elements(By.XPATH, "//div[contains(@class, 'jftiEf')]")
            current_reviews_count = len(reviewDivs)
            
            # If no new reviews loaded after 3 attempts, break the loop
            if current_reviews_count == previous_reviews_count:
                no_new_reviews_count += 1
                if no_new_reviews_count >= 3:
                    print(f"No new reviews found after 3 attempts. Breaking scroll loop at {current_reviews_count} reviews.")
                    break
            else:
                no_new_reviews_count = 0  # Reset counter when new reviews are found
            
            print(f"Scroll attempt {attempt+1}: {current_reviews_count} reviews found so far")
            previous_reviews_count = current_reviews_count
            
            # Scroll down
            browser.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", reviewArea)
            time.sleep(2)  # Wait slightly longer for content to load
            
    except Exception as e:
        print(f"Error while scrolling: {e}")

    # Extract reviews
    reviewDivs = browser.find_elements(By.XPATH, "//div[contains(@class, 'jftiEf')]")
    
    for review in reviewDivs:
        try:
            # Get rating text (like "4 stars" or "Bewertet mit 3 von 5 Sternen")
            rating_element = review.find_element(By.CLASS_NAME, 'kvMYJc') if review.find_elements(By.CLASS_NAME, 'kvMYJc') else None
            if rating_element:
                rating_text = rating_element.get_attribute('aria-label')
                
                # Extract the numeric rating
                rating_match = re.search(r'(\d+)', rating_text)
                if rating_match:
                    rating_value = int(rating_match.group(1))
                    
                    # Only include reviews with 1, 2, or 3 stars
                    if rating_value <= 3:
                        # Find the share button for this review
                        try:
                            # Find the "More actions" button first
                            more_button = review.find_element(By.XPATH, './/button[@aria-label="Mehr Aktionen" or @aria-label="More actions" or @data-tooltip="More actions"]')
                            browser.execute_script("arguments[0].click();", more_button)
                            time.sleep(1)
                            
                            # Then find and click the Share button in the menu
                            share_button = WebDriverWait(browser, 3).until(
                                EC.element_to_be_clickable((By.XPATH, '//div[contains(text(), "Share") or contains(text(), "Teilen")]'))
                            )
                            browser.execute_script("arguments[0].click();", share_button)
                            time.sleep(1)
                            
                            # Get the URL from the share dialog
                            share_url_input = WebDriverWait(browser, 3).until(
                                EC.presence_of_element_located((By.XPATH, '//input[contains(@aria-label, "Link") or contains(@aria-label, "URL")]'))
                            )
                            review_link = share_url_input.get_attribute('value')
                            
                            # Close the share dialog
                            close_button = browser.find_element(By.XPATH, '//button[@aria-label="Close" or @aria-label="Schließen"]')
                            browser.execute_script("arguments[0].click();", close_button)
                            time.sleep(0.5)
                        except Exception as e:
                            print(f"Could not get direct share link: {e}")
                            # Fallback - try to extract from the review element directly
                            review_link = "No direct link available"
                            
                            # Check if we can find a data-review-id attribute
                            try:
                                review_id = review.get_attribute('data-review-id')
                                if review_id:
                                    # Construct a URL using the review ID
                                    current_url = browser.current_url
                                    base_url = current_url.split('?')[0]
                                    review_link = f"{base_url}?entry=ttu#lrd={review_id}"
                            except:
                                pass
                        
                        # Add the review to our collection with the direct link
                        all_reviews.append({
                            "Reviewer": review.find_element(By.CLASS_NAME, 'd4r55').text if review.find_elements(By.CLASS_NAME, 'd4r55') else "N/A",
                            "About": review.find_element(By.CLASS_NAME, 'RfnDt').text if review.find_elements(By.CLASS_NAME, 'RfnDt') else "N/A",
                            "Rating": rating_text,
                            "Reviewed On": review.find_element(By.CLASS_NAME, 'rsqaWe').text if review.find_elements(By.CLASS_NAME, 'rsqaWe') else "N/A",
                            "Review Text": review.find_element(By.CLASS_NAME, 'MyEned').text if review.find_elements(By.CLASS_NAME, 'MyEned') else "N/A",
                            "Review Link": review_link
                        })
        except Exception as e:
            print(f"Error processing a review: {e}")

    # After scraping reviews, go to About section ("Über uns" or similar)
    try:
        print("Navigating to About section...")
        
        # Go back to main business page first
        browser.back()
        time.sleep(2)
        
        # Look for About/Info tabs (try different German variations)
        about_tab_found = False
        for about_text in ["Über", "Info", "Informationen", "About"]:
            try:
                about_tab = WebDriverWait(browser, 3).until(
                    EC.element_to_be_clickable((By.XPATH, 
                        f'//div[contains(@class, "Gpq6kf") and contains(text(), "{about_text}")]'))
                )
                about_tab.click()
                about_tab_found = True
                print(f"Clicked on {about_text} tab")
                time.sleep(2)
                break
            except:
                continue
        
        if not about_tab_found:
            print("Could not find About section tab")
        
        # Extract all available information
        about_data = {}
        
        # Function to extract information categories
        def extract_category(category_name):
            try:
                # Find the section with this category
                sections = browser.find_elements(By.XPATH, 
                    f'//div[contains(@class, "HeZRrf")]//*[contains(text(), "{category_name}")]//ancestor::div[contains(@class, "HeZRrf")]')
                
                if sections:
                    section = sections[0]
                    # Get all option items in this section
                    items = section.find_elements(By.CSS_SELECTOR, "div.LTs0Rc")
                    if items:
                        return [item.text for item in items if item.text.strip()]
                return []
            except:
                return []
        
        # Extract common categories
        categories = {
            "Serviceleistungen": "Service Options",
            "Parkmöglichkeiten": "Parking Options",
            "Angebote": "Offerings",
            "Speisemöglichkeiten": "Dining Options", 
            "Zahlungsarten": "Payment Options",
            "Atmosphäre": "Atmosphere",
            "Einrichtungen": "Amenities",
            "Barrierefreiheit": "Accessibility",
            "Planung": "Planning",
            "Beliebt für": "Popular For"
        }
        
        # Extract each category
        for german_name, english_name in categories.items():
            options = extract_category(german_name)
            if options:
                about_data[english_name] = ", ".join(options)
                print(f"Found {english_name}: {about_data[english_name]}")
        
    except Exception as e:
        print(f"Error extracting about section data: {e}")
        about_data = {}

    # Now combine all data for the final output
    # For each review, add the business data and about data
    for review in all_reviews:
        review.update(business_data)
        review.update(about_data)

    browser.quit()
    print(f"Extracted {len(all_reviews)} reviews with 3 stars or less.")

    return all_reviews

if __name__ == "__main__":
    data = extractReviews()

    # Save reviews to JSON
    # with open("googleReviews.json", "w", encoding="utf-8") as f:
    #     json.dump(data, f, indent=4, ensure_ascii=False)
        
        
    # Save reviews to CSV
    if data:
        # Get all possible fields
        all_fields = set()
        for review in data:
            all_fields.update(review.keys())
        
        # Filter out empty fields
        non_empty_fields = []
        for field in all_fields:
            for review in data:
                if field in review and review[field] not in ["N/A", ""]:
                    non_empty_fields.append(field)
                    break
        
        # Save the CSV with only non-empty fields
        with open("googleReviews.csv", "w", encoding="utf-8", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=non_empty_fields)
            writer.writeheader()
            writer.writerows(data)
        print(f"Reviews with business data saved to googleReviews.csv")
    else:
        print("No reviews to save")
    print("Done.")



