from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import tkinter.font as tkFont
from tkinter import messagebox
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import chromedriver_autoinstaller
import random, time, os, sys, csv
from datetime import datetime, timedelta
import requests
from functools import partial
import shutil
from cryptography.fernet import Fernet
from threading import Thread
from bs4 import BeautifulSoup
import subprocess


def bypass_clould_flare(driver, url):
	driver.get(url)
	time.sleep(10) # wait until page has loaded
	driver.execute_script("window.open('');") # open page in new tab
	driver.switch_to.window(driver.window_handles[-1])
	driver.get(url)
	time.sleep(10) # wait until page has loaded
	
	current_window = driver.current_window_handle

	# Get all window handles
	all_windows = driver.window_handles

	# Close all windows except the current one
	for window in all_windows:
		if window != current_window:
			driver.switch_to.window(window)
			driver.close()

	# Switch back to the current window
	driver.switch_to.window(current_window)

	time.sleep(1)
	driver.get("https://google.com")
	time.sleep(1)
	driver.get(url) # this should pass cloudflare captchas now
	time.sleep(7)


if __name__ == "__main__":
	chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]  #크롬드라이버 버전 확인

	subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrometemp"')

	options = webdriver.ChromeOptions()
	options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
	options.add_argument('--disable-popup-blocking')


	try:
		driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe', options = options)   
	except:
		try:
			chromedriver_autoinstaller.install(True)
			driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe', options = options)
		except:
			service = Service(executable_path=ChromeDriverManager(version="114.0.5735.90").install())
			driver = webdriver.Chrome(service=service, options=options)

	
	bypass_clould_flare(driver, "https://www.busandal90.net/")