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
worded_date_pattern = r'[A-Z][a-z]+, (January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}'
scanned_expire_dates = {}
print("Setup Done!")

for news in soup.find_all('div', {'class': 'contentbox'}): #grab info from one news box
    for title in news.find_all('b'):
        if '%' in title.get_text() or 'Bundle' in title.get_text() or '6 Month' in title.get_text() or 'Free' in title.get_text(): #filtering deals
            if ('/' in news.find('p').get_text()): #finding expiration dates
                deals_text = news.find('p').get_text()
                print(title.get_text())
                dates_found = re.findall(numbered_date_pattern, deals_text)
                scanned_expire_dates = set(dates_found)
            try: #finds if link is available
                print("link found!")
                link = news.find('a').get('href')
                link_storage.append(link)
                specific_html = urllib.request.urlopen(f'https://www.wizard101.com{link}') #opening the url for reading
                htmlParse = BeautifulSoup(specific_html, 'specific_html.parser') #parse specific_html
                if scanned_expire_dates == None or scanned_expire_dates == '':
                    for content_page in htmlParse.find_all('div', {'class': 'emptybox_text boxsizingborderbox'}):
                        for para in content_page.find_all('div'):
                            if para:
                                paragraph_text = para.get_text()
                                dates_found = re.findall(worded_date_pattern, paragraph_text)
                                scanned_expire_dates = set(dates_found)
            except:
                pass
            for date_str in scanned_expire_dates: #process the scanned dates and exclude expired deals
                date_str = datetime.strptime(date_str, "%m/%d")
                if date_str.month == 1 and date_pure.month == 12: #adds current year at the end of expire date, could be catastrophic when new year comes along if this doesn't work
                    date_str = datetime.strftime(date_str, "%m/%d")
                    date_str += f'/{date_pure.year + 1}' 
                else:
                    date_str = datetime.strftime(date_str, "%m/%d")
                    date_str += f'/{date_pure.year}' 
                print(date_str)
                expiration_date = datetime.strptime(date_str, "%m/%d/%Y")
                if (expiration_date) >= datetime.today():
                    print(expiration_date)
                    print("comparing dates")
                    print(datetime.today())
                    expiration_date = datetime.strftime(expiration_date, '%B %d %Y')
                    b_array.append('Date: '+news.find('td', {'class': 'contentbox_headermiddle'}).get_text()+(f' ({expiration_date}) ')+ 'Deal: '+title.get_text()) 

b_array = '\n'.join(b_array) #formatting

if not b_array: #if no sales are found, the window isn't opened
    print("no sales found, exiting")
    exit()

# Initialize the configuration parser
config = configparser.ConfigParser()

# Load the configuration file
if not os.path.exists('Wizard101-Sale-Tracker\config.ini'): #check for if it exists and set default value
    config['Opt-in'] = {'Status': 'False'}
    with open('Wizard101-Sale-Tracker\config.ini', 'w') as configfile:
        config.write(configfile)
else:
    config.read('Wizard101-Sale-Tracker\config.ini')

# Check if the 'Opt-in' section exists in the configuration file (default to false if it doesn't work)
if 'Opt-in' in config:
    opt_in_status = config.getboolean('Opt-in', 'Status', fallback=False)

#gui code copied from internet
sg.theme("DarkBlue")
font = ('Courier New', 11,'underline')
layout = [
    [sg.Text(b_line, enable_events=True, font=font, key=f'-LINK-{index}-')]
    for index, b_line in enumerate(b_array.splitlines(), start=0)
] + [
    [sg.Checkbox('Opt-in for startup launch', opt_in_status, enable_events=True, key='Opt-in-Checkbox', )]
]
driver.close()

# Create the window
window = sg.Window("Sale Tracker", layout)

# Create an event loop
while True:
    event, values = window.read()
    startup_folder = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup') #get the current user's startup folder path
    shortcut_path = os.path.join(startup_folder, "SaleTracker.lnk")
    script_path = r'Wizard101-Sale-Tracker\main.py' #create a shortcut to your Python script in the startup folder / make path dynamic
    if values['Opt-in-Checkbox'] == True :
        window['Opt-in-Checkbox'].update(True)
        opt_in_status = True
        if not os.path.exists(shortcut_path): #create the shortcut if it doesn't exist
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = script_path
            shortcut.WorkingDirectory = os.path.dirname(script_path)
            shortcut.save()
        print("Opted In!")
    elif values['Opt-in-Checkbox'] == False :
        window['Opt-in-Checkbox'].update(False)
        opt_in_status = False
        if os.path.exists(shortcut_path): #remove the shortcut if it exists
            os.remove(shortcut_path)
        print("Opted Out!")
    config.set('Opt-in', 'Status', str(opt_in_status)) #saves to config 
    with open('Wizard101-Sale-Tracker\config.ini', 'w') as configfile: #save the config explicitly to file
        config.write(configfile)
    if event == sg.WIN_CLOSED: #end program if user closes window
        break
    elif event.startswith('-LINK-'):
        index = int(event.split('-')[2])
        webbrowser.open(f'https://www.wizard101.com{link_storage[index]}')
    

window.close()
