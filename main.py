#CURRENT TASK: FIX OPT IN SYSTEM
#WISHLIST: HAVE IT SO THAT IT ACTIVATES EVERY DAY AND PINGS WHEN IT FINDS A SALE
import os
import win32com.client
import configparser
from bs4 import BeautifulSoup #scraping imports
from selenium import webdriver
import webbrowser
import urllib.request 
from datetime import datetime #time import
import PySimpleGUI as sg #gui import
import re #regex import

date_pure = datetime.now()
date = date_pure.strftime("%B").lower()+'-'+str(date_pure.year)
print('Current tracking date: ', date) #date format check
driver = webdriver.Chrome()
driver.get(f'https://www.wizard101.com/game/news/{date}')

base_html = driver.page_source
soup = BeautifulSoup(base_html, features='lxml')

#find all information on the page
b_array = []
link_storage = []
numbered_date_pattern = r'\b\d{1,2}/\d{1,2}\b' #expiration date check setup
worded_date_pattern = r'[A-Z][a-z]+, (July \d{1,2}(st|nd|rd|th))'
unique_dates = {}
print("Setup Done!")
for news in soup.find_all('div', {'class': 'contentbox'}): #grab info from one news box
    for title in news.find_all('b'):
        if '%' in title.get_text() or 'Bundle' in title.get_text() or '6 Month' in title.get_text(): #filtering deals
            if ('/' in news.find('p').get_text()): #finding expiration dates
                deals_text = news.find('p').get_text()
                print(deals_text)
                dates_found = re.findall(numbered_date_pattern, deals_text)
                unique_dates = set(dates_found)
            try: #finds if link is available
                link = news.find('a').get('href')
                link_storage.append(link)
                specific_html = urllib.request.urlopen(f'https://www.wizard101.com{link}') #opening the url for reading
                htmlParse = BeautifulSoup(specific_html, 'specific_html.parser') #parse specific_html
                if unique_dates == None or unique_dates == '':
                    for content_page in htmlParse.find_all('div', {'class': 'emptybox_text boxsizingborderbox'}):
                        for para in content_page.find_all('div'):
                            if para:
                                paragraph_text = para.get_text()
                                dates_found = re.findall(worded_date_pattern, paragraph_text)
                                unique_dates = set(dates_found)
                                print(unique_dates)
            except:
                link_storage.append("")
            '''if unique_dates < date: fix this shit
                unique_dates = "Expired"'''
            b_array.append('Date: '+news.find('td', {'class': 'contentbox_headermiddle'}).get_text()+(f' ({unique_dates}) ')+ 'Deal: '+title.get_text()) 
b_array = '\n'.join(b_array) #formatting

if not b_array: #if no sales are found, the window isn't opened
    exit()


# Initialize the configuration parser
config = configparser.ConfigParser()

# Load the configuration file if it exists
config_file_path = 'config.ini'
if os.path.exists(config_file_path):
    config.read(config_file_path)

# Check if the 'Opt-in' section exists in the configuration file
if 'Opt-in' in config:
    opt_in_status = config.getboolean('Opt-in', 'Status')
else:
    # If the section doesn't exist, set a default value
    opt_in_status = False

#gui code copied from internet
sg.theme("DarkBlue")
font = ('Courier New', 11,'underline')
layout = [
    [sg.Text(b_line, enable_events=True, font=font, key=f'-LINK-{index}-')]
    for index, b_line in enumerate(b_array.splitlines(), start=0)
] + [
    [sg.Checkbox('Opt-in', key='Opt-in')]
]
driver.close()

# Create the window
window = sg.Window("Sale Tracker", layout)

# Create an event loop
while True:
    event, values = window.read()
    startup_folder = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup') #get the current user's startup folder path
    shortcut_path = os.path.join(startup_folder, "SaleTracker.lnk")
    if event == sg.WIN_CLOSED: #end program if user closes window
        break
    elif event.startswith('-LINK-'):
        index = int(event.split('-')[2])
        webbrowser.open(f'https://www.wizard101.com{link_storage[index]}')
    if values['Opt-in']:
        script_path = r'C:\Users\13178\Documents\GitHub\personal projects\wizard101 webscraper\main.py' #create a shortcut to your Python script in the startup folder
        config['Opt-in'] = {'Status': 'True'} #saves to config
        # Create the shortcut if it doesn't exist
        if not os.path.exists(shortcut_path):
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = script_path
            shortcut.WorkingDirectory = os.path.dirname(script_path)
            shortcut.save()
        print("Opted In!")
    else:
        # Remove the shortcut if it exists
        config['Opt-in'] = {'Status': 'False'} #saves to config
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
        print("Opted Out!")

window.close()
