# from datetime import datetime
# from selenium import webdriver
# from selenium.common.exceptions import TimeoutException
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# SEARCH_URL = "https://www.uta.edu/directory"
# IFRAME_URL = "iframe[src='https://findpeople.uta.edu/']"
# INPUT_BOX = "input[ng-model='$ctrl.ngModel']"
# RESULT_TABLE = "table.ias-table"

# def process_table_data(table):
#     # Creating a list to store data (if any) 
#     table_data = []

#     # Get the column names from the thead element
#     thead = table.find_element(By.CSS_SELECTOR, "thead")
#     columns = [th.text for th in thead.find_elements(By.CSS_SELECTOR, "th")]

#     # Get the rows from the tbody element
#     tbody = table.find_element(By.CSS_SELECTOR, "tbody")
#     rows = tbody.find_elements(By.CSS_SELECTOR, "tr")

#     # Extract the data from each row
#     for row in rows:
#         cells = row.find_elements(By.CSS_SELECTOR, "td")
#         # print('CELLS', cells)

#         if len(cells) > 0:
#             data = {}
#             for i, cell in enumerate(cells[:6]):
#                 data[columns[i]] = cell.text
#             table_data.append(data)

#     return table_data

# def search_employee(query, headless=True):
#     # Initialize the web driver

#     options = webdriver.FirefoxOptions()

#     options.binary_location = r"/usr/lib/firefox/firefox"

#     if headless:
#         options.add_argument('--headless')

#     driver = webdriver.Firefox(options=options)

#     # navigate to the website
#     driver.get(SEARCH_URL)

#     # wait for the iframe to load
#     wait = WebDriverWait(driver, 30)
#     iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, IFRAME_URL)))

#     # switch to iframe
#     driver.switch_to.frame(iframe)

#     # find the search input field and enter a keyword
#     search_input = driver.find_element(By.CSS_SELECTOR, INPUT_BOX)
#     search_input.send_keys(query)

#     # wait for the results to load
#     driver.implicitly_wait(10)

#     # Wait for the table to be visible
#     try:
#         search_result_wait = WebDriverWait(driver, 10)
#         table = search_result_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, RESULT_TABLE)))
#     except TimeoutException:
#         driver.quit()
#         return []

#     table_data = process_table_data(table)

#     # close the browser
#     driver.quit()

#     return table_data

# query = 'dillhoff'
# headless = True
# # headless = False

# now = datetime.now()

# records = search_employee(query, headless)

# print(datetime.now() - now)

# if records:
#     print(f"Found {len(records)} records")
#     for data in records:
#         print(data)
# else:
#     print("No records found")

# #     raise exception_class(message, screen, stacktrace)
# # selenium.common.exceptions.WebDriverException: Message: Process unexpectedly closed with status 255