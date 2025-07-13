from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    return webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )

def scrape_links(skip: int = 0):
    driver = create_driver()
    try:
        url = f"https://learn.microsoft.com/en-us/azure/architecture/browse?skip={skip}"
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "card-content-title"))
        )

        link_elements = driver.find_elements(By.CLASS_NAME, "card-content-title")
        links = [link.get_attribute("href") for link in link_elements if link.get_attribute("href")]

        return links

    except Exception as e:
        print(f"⚠️  Skip={skip} failed with: {e}")
        return []
    
    finally:
        driver.quit()


def scrape_architecture_page(url: str):
    driver = create_driver()
    try:
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "is-1"))
        )

        title_elements = driver.find_elements(By.CLASS_NAME, "is-1")
        title = title_elements[0].text if title_elements else None

        tag_elements = driver.find_elements(By.CLASS_NAME, "tag-filled")
        tags = [tag.text for tag in tag_elements]

        content_elements = driver.find_elements(By.CLASS_NAME, "content")
        content = content_elements[2].text if len(content_elements) >= 3 else None

        return {
            "url": url,
            "title": title,
            "tags": tags,
            "content": content
        }

    except Exception as e:
        print(f"⚠️ Error scraping {url}: {e}")
        return {}

    finally:
        driver.quit()
