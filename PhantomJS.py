from selenium import webdriver
from selenium.webdriver.common.keys import Keys

driver = webdriver.Chrome()
driver.get("http://www.top.st")
country = driver.find_element_by_tag_name('option', selected="selected")
elem = driver.find_element_by_xpath()
elem.clear()
driver.close()