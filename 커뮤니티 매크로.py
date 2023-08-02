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
import pyautogui
import pyperclip

APP_VERSION = '0.34'
is_running = False
session = requests.session()
ori_session = ''
limit_site = 1
community_site_dict = {}
community_site_list = []
work_account_list = []
work_type_list=["상단업", "글쓰기"]

temp_subject = ''
temp_content = ''


class SimpleEnDecrypt:
	def __init__(self, key=b'eUmt0mpWllw3313m6TufYm2hLrqyszx1ejpGOShSRCg='):
		if key is None: # 키가 없다면
			key = Fernet.generate_key() # 키를 생성한다
		self.key = key
		self.f   = Fernet(self.key)
	
	def encrypt(self, data, is_out_string=True):
		if isinstance(data, bytes):
			ou = self.f.encrypt(data) # 바이트형태이면 바로 암호화
		else:
			ou = self.f.encrypt(data.encode('utf-8')) # 인코딩 후 암호화
		if is_out_string is True:
			return ou.decode('utf-8') # 출력이 문자열이면 디코딩 후 반환
		else:
			return ou
			
	def decrypt(self, data, is_out_string=True):
		if isinstance(data, bytes):
			ou = self.f.decrypt(data) # 바이트형태이면 바로 복호화
		else:
			ou = self.f.decrypt(data.encode('utf-8')) # 인코딩 후 복호화
		if is_out_string is True:
			return ou.decode('utf-8') # 출력이 문자열이면 디코딩 후 반환
		else:
			return ou


				
def getCommunitySite():
	global community_site_dict
	url = "http://marco.newsoft.kr/site.php"
	res = session.get(url)
	res.raise_for_status() # 문제시 프로그램 종료

	for x in res.json():
		community_site_dict[x["site_name"]] = x["site_url"]

	community_site_combobox["values"] = [*community_site_dict]



def setDefault():
	ItemUtil(community_account_list,"커뮤니티 계정").loadItemList()
	ItemUtil(work_list,"작업 리스트").loadItemList()
	getCommunitySite()


def checkSession():
	global session
	global ori_session

	while True:
		url = "http://marco.newsoft.kr/index.php"
		res = session.get(url)
		res.raise_for_status() # 문제시 프로그램 종료
		res = res.json()
		

		if res["version"] != APP_VERSION:
			messagebox.showerror("경고","프로그램을 업데이트 해주세요.")
			break
	
		if ori_session != res["session"]:
			break
		time.sleep(5)
	exitBot()
	
	

def macroLogin():
	global session
	global ori_session
	global limit_site



	id = macro_id_textbox.get()
	pw = macro_pw_textbox.get()
	data = {
		"id" : id,
		"pw" : pw,
	}
	if not id:
		messagebox.showerror("경고","프로그램 아이디를 입력해주세요.")
		return
	if not pw:
		messagebox.showerror("경고","프로그램 비밀번호를 입력해주세요.")
		return

	url = "http://marco.newsoft.kr/index.php"
	res = session.post(url, data=data)
	res.raise_for_status() # 문제시 프로그램 종료
	res = res.json()
	if res["error"] == '0':
		expires_at = res["expires_at"]
		ori_session = res["session"]
		limit_site = res["limit_site"]
		expires_at_label.config(text=f"만료날짜 : {expires_at}")

		if res["version"] != APP_VERSION:
			messagebox.showerror("경고","프로그램을 업데이트 해주세요.")
			sys.exit(0)

		t = Thread(target=checkSession, daemon=True)
		t.start()
		

		add_work_list_btn['state'] = "normal"
		add_community_account_btn['state'] = "normal"
		start_btn['state'] = "normal"

		login_btn['state'] = "disabled"
		join_btn['state'] = "disabled"

		setDefault()
	else:
		messagebox.showerror("경고",res["error"])
		return


def macroJoin():
	messagebox.showinfo("알림","관리자에게 문의해주세요.")


def addCommunityAccount():
	global limit_site
	community_site = community_site_combobox.get()
	community_id = community_id_textbox.get()
	community_pw = community_pw_textbox.get()
	if not community_site:
		messagebox.showerror("경고","사이트를 선택해주세요.")
	elif not community_id:
		messagebox.showerror("경고","아이디를 입력해주세요.")
	elif not community_pw:
		messagebox.showerror("경고","비밀번호를 입력해주세요.")
	else:
		count = 0
		for row_id in community_account_list.get_children():
			row = community_account_list.item(row_id)['values']
			if row[1] == community_site:
				count += 1

		if count >= int(limit_site):
			messagebox.showerror("경고",f"같은 사이트에 다른계정추가는 {limit_site}개 이하만 가능합니다.")
		else:
			community_pw = SimpleEnDecrypt().encrypt(community_pw)
						
			community_account_list.insert('', 'end', values=(len(community_account_list.get_children())+1,community_site, community_id, community_pw))
			ItemUtil(community_account_list,"커뮤니티 계정").saveItemList()


class AddWork:
	def __init__(self, reserves_at = None):
		self.work_type = work_type_combobox.get().strip()
		self.reserves_at = reserves_at
		try:
			work_account = community_account_list.get_children()[int(work_account_combobox.get())-1]
		except:
			work_account = None

		if is_timer.get():
			work_reserve_time = str(timer_hour.get()) + ":" + str(timer_minute.get()) + ":" + str(timer_second.get())
			self.reserves_at = datetime.strptime(work_reserve_time, '%H:%M:%S').time()
		else:
			self.reserves_at = 0
		
		if self.work_type is None or self.work_type=='':
			messagebox.showerror("경고","타입을 선택해주세요.")
		elif work_account is None:
			messagebox.showerror("경고","계정을 선택해주세요.")
		else:
			self.work_site = community_account_list.item(work_account)['values'][1]
			self.work_id = community_account_list.item(work_account)['values'][2]
			self.work_pw = community_account_list.item(work_account)['values'][3]
			
			if self.work_type == '상단업':
				work_list.insert('', 0, values=(len(work_list.get_children())+1, self.work_type, self.work_site, self.work_id, self.work_pw, self.reserves_at))
			elif self.work_type == '글쓰기':
				self.openWritePopup()
			ItemUtil(work_list,"작업 리스트").treeviewSortColumn()
	

	def openWritePopup(self):
		global temp_subject
		global temp_content
		self.write_content = temp_content

		write_popup = Toplevel(root)
		self.write_popup = write_popup
		write_popup.geometry("500x150")
		write_popup.resizable(False, False)
		write_popup.title('글쓰기')

		write_popup.attributes('-topmost', 'true')

		write_subject_label = Label(write_popup, text="제목")
		write_subject_label.place(x=10,y=20)
		self.write_subject = StringVar(write_popup, value=temp_subject)
		write_subject_textbox = ttk.Entry(write_popup, width=50, textvariable=self.write_subject, font=customFont)
		write_subject_textbox.place(x=105, y=20)

		write_content_label = Label(write_popup, text="이미지")
		write_content_label.place(x=10,y=50)
		
		open_img = Button(write_popup, text='불러오기', width=50,height=1, command=self.loadImg)
		open_img.place(x=103, y=50)

		self.img_name_label = Label(write_popup, text=f"선택된 이미지 : {temp_content}")
		self.img_name_label.place(x=103,y=80)

		add_work_write_btn = Button(write_popup, text='등록', width=50,height=1, command=self.write)
		add_work_write_btn.place(x=103,y=110)

		write_popup.wait_window()
	

	def loadImg(self):
		self.write_content = filedialog.askopenfilename(initialdir='./',title='파일선택', filetypes=[('image files', ('.png', '.jpg', 'jepg', 'gif'))])
		self.img_name_label.config(text = f"선택된 이미지 : {self.write_content}")


	def write(self):
		current_time = time.time()
		
		if self.write_content != '':
			img_type = self.write_content.split('.')[-1]
			createDirectory("./AutoDoc")
			shutil.copyfile(self.write_content, f"./AutoDoc/{current_time}.{img_type}")

			global temp_subject
			global temp_content

			temp_subject = self.write_subject.get()
			temp_content = self.write_content

			work_list.insert('', 0, values=(len(work_list.get_children())+1, self.work_type, self.work_site, self.work_id, self.work_pw, self.reserves_at, self.write_subject.get(), f"./AutoDoc/{current_time}.{img_type}"))


			self.write_popup.destroy()
		else:
			messagebox.showerror("경고","이미지를 불러주세요.")
		


def createDirectory(directory):
	try:
		if not os.path.exists(directory):
			os.makedirs(directory)
	except OSError:
		print("Error: Failed to create the directory.")


class ItemUtil:
	def __init__(self, item_name, file_name=None):
		self.item_name = item_name
		self.file_name = file_name

	def treeviewSortColumn(self):
		rows = [(self.item_name.set(item, "#6"), item) for item in self.item_name.get_children('')]
		rows.sort(reverse=True)

		# rearrange items in sorted positions
		for index, (values, item) in enumerate(rows):
			self.item_name.move(item, '', index)
		self.idxReset()

	def saveItemList(self):
		with open(f"{self.file_name}.csv", "w", newline='', encoding='utf-8') as f:
			w = csv.writer(f, delimiter=',')
			for row_id in self.item_name.get_children():
				row = self.item_name.item(row_id)['values']
				try:
					w.writerow(row)
				except:
					saveLog(self.file_name, '데이터 저장에 실패하였습니다.')
				
		self.loadItemList()

	def loadItemList(self):
		if os.path.isfile(f"{self.file_name}.csv"):
			with open(f"{self.file_name}.csv", encoding='utf-8') as f:
				w = csv.reader(f, delimiter=',')
				self.item_name.delete(*self.item_name.get_children())
				try:
					for row in w:
						self.item_name.insert("", 'end', values=row)
				except:
					saveLog(self.file_name, '데이터 불러오기에 실패하였습니다.')

				
		if self.file_name == "커뮤니티 계정":
			work_account_list = []
			for row_id in self.item_name.get_children():
				row = self.item_name.item(row_id)['values']
				work_account_list.append(row[0])

			work_account_combobox["values"] = work_account_list

	
	def idxReset(self):
		item_list = self.item_name.get_children()
		if self.file_name == "작업 리스트":
			item_list = reversed(item_list)

		for i, row_id in enumerate(item_list, start=1):
			row = self.item_name.item(row_id)['values']
			row[0] = i
			self.item_name.delete(row_id)
			
			if self.file_name == "작업 리스트":
				self.item_name.insert("", 0, values=row)
			else:
				self.item_name.insert("", 'end', values=row)
		self.saveItemList()

	def removeItem(self):
		selected_items = self.item_name.selection()
		for selected_item in selected_items:
			try:
				work_path = self.item_name.item(selected_item)['values'][7]
			except:
				work_path = None


			if os.path.exists(f"./AutoDoc/{work_path}"):
				shutil.rmtree(f"./AutoDoc/{work_path}")

			self.item_name.delete(selected_item)
			
		self.idxReset()

	def removeAllItem(self):
		if self.file_name == "작업 리스트":
			try:
				dir_list = os.listdir("./AutoDoc") 

				for dir in dir_list:
					if os.path.exists(f"./AutoDoc/{dir}"):
						shutil.rmtree(f"./AutoDoc/{dir}")
			except:
				pass

		self.item_name.delete(*self.item_name.get_children())
		self.saveItemList()



def openMenu(event,item_name):
	try:
			item_name.tk_popup(event.x_root, event.y_root)
	finally:
			item_name.grab_release()




def saveLog(site,log):
	log_list.insert('', 0, values=(site, datetime.now(), log))


def exitBot():
	global is_running
	is_running = False
	root.destroy()
	driver.quit()
	sys.exit(0)


class CommunityMacro:
	def __init__(self, driver, id, pw, site, type, reserve_at, subject, content, is_first_loop):
		global is_running
		self.driver = driver
		self.id = id
		self.pw = SimpleEnDecrypt().decrypt(pw)
		self.site = site
		self.type = type
		self.reserve_at = reserve_at
		self.subject = subject
		self.content = content
		self.url = community_site_dict[self.site]
		self.wait = WebDriverWait(self.driver, 15)
		self.is_first_loop = is_first_loop

		try:
			self.driver.switch_to.alert.accept()
		except:
			pass

		if self.reserve_at != 0:
			t = datetime.strptime(self.reserve_at, '%H:%M:%S').time()
			d = datetime.today()

			loop = True
			loop_count = 0
			while loop:
				print(datetime.combine(d, t), datetime.now())
				if datetime.combine(d, t) < datetime.now():
					if self.is_first_loop and loop_count == 0:
						return
					else:
						loop = False

				if not is_running:
					loop = False

				loop_count += 1
				time.sleep(1)
			

		

		if self.site == '펀초이스':
			self.fun_choice()
		elif self.site == '부산살리기':
			self.busan_saliki()
		elif self.site == '부산달리기':
			self.busan_daliki()
		elif self.site == '부산비비기':
			self.busan_bibiki()
		elif self.site == '알밤':
			self.albam()
		elif self.site == '오피가이드':
			self.op_guide()

		time.sleep(3)


	def albam(self):
		try:
			self.bypass_clould_flare(self.url)
		except:
			saveLog(self.site, '로봇탐지 우회에 실패하였습니다.')
			raise

		self.driver.get(f"{self.url}/index.php?mid=index&act=dispMemberLogout")

		id_input = self.wait.until(
			EC.visibility_of_element_located((By.XPATH, "//input[@name='user_id']"))
		)
		id_input.clear()
		id_input.send_keys(self.id)

		pw_input = self.wait.until(
			EC.visibility_of_element_located((By.XPATH, "//input[@name='password']"))
		)
		pw_input.clear()
		pw_input.send_keys(self.pw)
		pw_input.send_keys(Keys.RETURN)

		
		if self.type == '상단업':
			try:
				self.driver.get(f"{self.url}/index.php?mid=index&act=dispMemberOwnDocument")

				links = [link.get_attribute('href') for link in self.driver.find_elements(By.XPATH, "//section[@class='xm']//td[@class='title']//a")]


				for link in links:
					self.driver.get(link)

					elements = self.driver.find_elements(By.XPATH, "//a[contains(text(),'상단점프')]")
					if elements:
						elements[0].click()
						break
				
				time.sleep(0.5)
				self.driver.switch_to.alert.accept()

				saveLog(self.site, '상단업에 성공하였습니다.')
			except Exception as e:
				print(e)
				saveLog(self.site, '상단업에 실패하였습니다.')
			
		elif self.type == '글쓰기':
			#나의 프로필 이미지 가져와서 1페이지에 글 있는지 확인
			self.driver.get(self.url+"/board_tlDj69")
			html = self.driver.page_source

			

			# soup에 넣어주기
			soup = BeautifulSoup(html, 'html.parser')
			my_profile_img = soup.find("div", { "class" : "wrap_userName" }).find_all("img")[1]
			
			for image in soup.find("div", { "class" : "bd_lst_wrp" }).find_all("img"):
				if my_profile_img['src'] == image['src']:
					saveLog(self.site, '1페이지 안에 글이 있습니다.')
					return 


			try:
				self.driver.get(self.url+"/index.php?mid=board_tlDj69&act=dispBoardWrite")
				
				try:
					self.driver.switch_to.alert.dismiss()
				except:
					pass

				#분류
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//select[@name='category_srl']/option[contains(text(),'구인')]"))
				).click()
				
				#제목
				subject_elem = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='postTitle']"))
				)
				subject_elem.clear()
				subject_elem.send_keys(self.subject)
				

				try:
					driver.execute_script("jQuery.fancybox.close(); setCookie('lpopup', 'no',1);")
				except:
					pass

				
				#내용
				driver.find_element(By.XPATH, "//*[@id='xe-fileupload']").send_keys(os.path.abspath(self.content))
				time.sleep(5)


				

				while True:
					time.sleep(1)
					submit_btn = self.wait.until(
						EC.visibility_of_element_located((By.XPATH, "//*[@id='bd']/form/div[5]/input[2]"))
					)
					driver.execute_script("arguments[0].click();", submit_btn)
					self.driver.switch_to.default_content()
					time.sleep(2)

					#캡차
					captcha_img = self.driver.find_element(By.XPATH, "//*[@id='captcha_image']").screenshot_as_png
					url = 'http://captcha.newsoft.kr/'
					files = {'file': captcha_img}
					res = requests.post(url, files=files)
					res.raise_for_status() # 문제시 프로그램 종료
					res = res.json()

					captcha_elem = self.wait.until(
						EC.visibility_of_element_located((By.XPATH, '//*[@id="secret_text"]'))
					)
					captcha_elem.clear()
					captcha_elem.send_keys(res['captcha'])
					captcha_elem.send_keys(Keys.RETURN)
					time.sleep(1)
					
					try:
						driver.switch_to.alert.accept()
					except:
						url = 'http://captcha.newsoft.kr/res/'
						data = {
							'filename':res['filename'],
							"captcha":res['captcha'], 
						}

						res = requests.post(url, json=data)
						res = res.json()
						break


				saveLog(self.site, '글쓰기에 성공하였습니다.')
			except Exception as e:
				print(e)
				saveLog(self.site, '글쓰기에 실패하였습니다.')


	

	def fun_choice(self):
		try:
			self.bypass_clould_flare(self.url)
		except:
			saveLog(self.site, '로봇탐지 우회에 실패하였습니다.')
			raise

		self.driver.get(self.url)

		try:
			logout_btn = self.wait.until(
				EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div/div[3]/div[1]/div[1]/div/form/fieldset/div/div[1]/div[1]/p[2]'))
			)
			logout_btn.click()
		except:
			pass


		id_input = self.wait.until(
			EC.visibility_of_element_located((By.XPATH, "//input[@name='user_id']"))
		)
		id_input.clear()
		id_input.send_keys(self.id)

		pw_input = self.wait.until(
			EC.visibility_of_element_located((By.XPATH, "//input[@name='password']"))
		)
		pw_input.clear()
		pw_input.send_keys(self.pw)
		pw_input.send_keys(Keys.RETURN)

		
		if self.type == '상단업':
			try:
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='btnDocJump']"))
				).click()
				saveLog(self.site, '상단업에 성공하였습니다.')
			except:
				saveLog(self.site, '상단업에 실패하였습니다.')

		elif self.type == '글쓰기':
			try:
				self.driver.get(self.url+"/index.php?mid=joong&act=dispBoardWrite")

				#제목
				subject_elem = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='fo_write']/div[1]/div[1]/input"))
				)
				subject_elem.clear()
				subject_elem.send_keys(self.subject)

				#내용
				driver.find_element(By.XPATH, "//*[@id='xe-fileupload']").send_keys(os.path.abspath(self.content))
				time.sleep(5)

				submit_btn = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='fo_write']/div[2]/span[3]/input"))
				)
				submit_btn.click()

				saveLog(self.site, '글쓰기에 성공하였습니다.')
			except:
				saveLog(self.site, '글쓰기에 실패하였습니다.')


	def busan_saliki(self):
		try:
			self.bypass_clould_flare(self.url)
		except:
			saveLog(self.site, '로봇탐지 우회에 실패하였습니다.')
			raise

		self.driver.get(self.url)

		try:
			driver.execute_script("""
				var elem = document.getElementById("viewModal");
				elem.remove();
			""")
			time.sleep(1)

			driver.execute_script("""
				var elems = document.getElementsByClassName("modal-backdrop fade in");

				Array.from(elems).forEach(elem => {
					elem.remove();
				});
			""")
			time.sleep(1)
		except:
			pass

		try:
			logout_btn = self.wait.until(
				EC.visibility_of_element_located((By.XPATH, '//*[@id="thema_wrapper"]/div[4]/div/div/div[2]/div/div/div[4]/div/div[5]/a[2]'))
			)
			logout_btn.click()
		except:
			pass


		id_input = self.wait.until(
			EC.visibility_of_element_located((By.XPATH, "//input[@name='mb_id']"))
		)
		id_input.clear()
		id_input.send_keys(self.id)

		pw_input = self.wait.until(
			EC.visibility_of_element_located((By.XPATH, "//input[@name='mb_password']"))
		)
		pw_input.clear()
		pw_input.send_keys(self.pw)
		pw_input.send_keys(Keys.RETURN)
		
		
		if self.type == '상단업':
			try:
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='thema_wrapper']/div[4]/div/div/div[2]/div/div/div[6]/div[3]/a[1]"))
				).click()
				saveLog(self.site, '상단업에 성공하였습니다.')
			except:
				saveLog(self.site, '상단업에 실패하였습니다.')
		elif self.type == '글쓰기':
			try:
				self.driver.get(self.url+"/board/bbs/write.php?bo_table=co_06")

				#분류
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//select[@name='ca_name']/option[text()='부산']"))
				).click()

				#제목
				subject_elem = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='wr_subject']"))
				)
				subject_elem.clear()
				subject_elem.send_keys(self.subject)

				#내용
				frame = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='fwrite']/div[4]/div/iframe"))
				)
				self.driver.switch_to.frame(frame)

				frame = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='se2_iframe']"))
				)
				self.driver.switch_to.frame(frame)

				content_elem = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "/html/body"))
				)
				content_elem.clear()
				content_elem.send_keys(".")
				self.driver.switch_to.default_content()

				#이미지
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='variableFiles']/tbody/tr/td/div/div/div/div/input"))
				)
				driver.find_element(By.XPATH, "//*[@id='variableFiles']/tbody/tr/td/div/div/div/div/input").send_keys(os.path.abspath(self.content))
				time.sleep(5)

				submit_btn = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='btn_submit']"))
				)
				driver.execute_script("arguments[0].click();", submit_btn)

				saveLog(self.site, '글쓰기에 성공하였습니다.')
			except:
				saveLog(self.site, '글쓰기에 실패하였습니다.')


	def busan_daliki(self):
		try:
			self.bypass_clould_flare(self.url)
		except:
			saveLog(self.site, '로봇탐지 우회에 실패하였습니다.')
			raise

		self.driver.get(self.url+"/index.php?act=dispMemberLoginForm")

		try:
			logout_btn = self.wait.until(
				EC.visibility_of_element_located((By.XPATH, '//*[@id="content"]/div/div[1]/div[1]/div/div[1]/div/div/form/fieldset/div/a[2]'))
			)
			logout_btn.click()
		except:
			pass


		id_input =self.wait.until(
			EC.visibility_of_element_located((By.XPATH, "//*[@id='fo_login_widget']/fieldset/div/div/input[1]"))
		)
		id_input.clear()
		id_input.send_keys(self.id)

		pw_input = self.wait.until(
			EC.visibility_of_element_located((By.XPATH, "//*[@id='fo_login_widget']/fieldset/div/div/input[2]"))
		)
		pw_input.clear()
		pw_input.send_keys(self.pw)
		pw_input.send_keys(Keys.RETURN)
		
	
		if self.type == '상단업':
			try:
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='content']/div/div[1]/div[1]/div/div[1]/div/div/form/fieldset/li[2]/a"))
				).click()
				
				saveLog(self.site, '제휴 상단업에 성공하였습니다.')
			except:
				saveLog(self.site, '제휴 상단업에 실패하였습니다.')
			time.sleep(0.5)

			try:
				self.driver.switch_to.alert.accept()
			except:
				pass

			try:
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='content']/div/div[1]/div[1]/div/div[1]/div/div/form/fieldset/li[3]/a"))
				).click()

				saveLog(self.site, 'PR 상단업에 성공하였습니다.')
			except:
				saveLog(self.site, 'PR 상단업에 실패하였습니다.')
			time.sleep(0.5)

			try:
				self.driver.switch_to.alert.accept()
			except:
				pass
				
			
		elif self.type == '글쓰기':
			self.driver.get(self.url+"/index.php?mid=comm_cross&act=dispBoardWrite")

			try:
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='access']/div[1]/h1[text()='1일간 글 작성량 2개를 초과하였습니다.']"))
				)
        
				is_written = True
			except:
				is_written = False

			if is_written:
				self.driver.get(self.url+"/index.php?act=dispMemberOwnDocument")

				post_list = []
				for post in self.driver.find_elements(By.XPATH, "//*[@id='content']/div/div[1]/div[2]/div[2]/section/table/tbody/tr/td[2]/a"):
					post_list.append(post.get_attribute('href'))
				
				for post in post_list:
					self.driver.get(post)
					url_split = self.driver.current_url.split("/")

					if url_split[3] == 'comm_cross':
						self.driver.get(self.url+f"/index.php?mid=comm_cross&document_srl={url_split[4]}&act=dispBoardDelete")

						self.wait.until(
							EC.visibility_of_element_located((By.XPATH, "//*[@id='bd']/form/div/input"))
						).click()
						time.sleep(3)
						break

				self.driver.get(self.url+"/index.php?mid=comm_cross&act=dispBoardWrite")

			try:
				#분류
				print()
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//select[@name='category_srl']/option[contains(text(),'구인')]"))
				).click()

				#제목
				subject_elem = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='postTitle']"))
				)
				subject_elem.clear()
				subject_elem.send_keys(self.subject)

				#내용
				driver.find_element(By.XPATH, "//*[@id='xe-fileupload']").send_keys(os.path.abspath(self.content))
				time.sleep(5)

				submit_btn = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='bd']/form/div[5]/input"))
				)
				driver.execute_script("arguments[0].click();", submit_btn)
				time.sleep(5)
				saveLog(self.site, '글쓰기에 성공하였습니다.')
			except:
				saveLog(self.site, '글쓰기에 실패하였습니다.')



	def op_guide(self):
		self.driver.get(self.url+"/bbs/logout.php")
		time.sleep(1)
		self.driver.get(self.url+"/bbs/login.php")


		id_input =self.wait.until(
			EC.visibility_of_element_located((By.XPATH, "//input[@id='login_id']"))
		)
		id_input.clear()
		id_input.send_keys(self.id)

		pw_input = self.wait.until(
			EC.visibility_of_element_located((By.XPATH, "//input[@id='login_pw']"))
		)
		pw_input.clear()
		pw_input.send_keys(self.pw)
		time.sleep(6)
		pw_input.send_keys(Keys.RETURN)
		
	
		if self.type == '상단업':
			try:
				self.driver.execute_script('cmpJump()')
				
				saveLog(self.site, '제휴 상단업에 성공하였습니다.')
			except:
				saveLog(self.site, '제휴 상단업에 실패하였습니다.')
			time.sleep(0.5)

			try:
				self.driver.switch_to.alert.accept()
			except:
				pass

				
			
		elif self.type == '글쓰기':
			self.driver.get(self.url+"/bbs/write.php?bo_table=recruit")

			
			try:
				#분류
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='ca_name']/option[contains(text(),'구인')]"))
				).click()
				
				#제목
				subject_elem = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='wr_subject']"))
				)
				subject_elem.clear()
				subject_elem.send_keys(self.subject)

				#내용
				frame = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//div[@class='cheditor-editarea-wrapper']/iframe"))
				)
				self.driver.switch_to.frame(frame)

				content_elem = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "/html/body"))
				)
				content_elem.clear()
				content_elem.send_keys(".")
				self.driver.switch_to.default_content()

				#파일
				driver.find_element(By.XPATH, "//*[@name='bf_file[]']").send_keys(os.path.abspath(self.content))
				time.sleep(5)

				submit_btn = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='btn_submit']"))
				)
				driver.execute_script("arguments[0].click();", submit_btn)

				saveLog(self.site, '글쓰기에 성공하였습니다.')
			except:
				saveLog(self.site, '글쓰기에 실패하였습니다.')



	def busan_bibiki(self):
		try:
			self.bypass_clould_flare(self.url)
		except:
			saveLog(self.site, '로봇탐지 우회에 실패하였습니다.')
			raise

		self.driver.get(self.url)

		try:
			logout_btn = self.wait.until(
				EC.visibility_of_element_located((By.XPATH, '//*[@id="nt_body"]/div/div/div[2]/div[1]/div/div[2]/a[4]'))
			)
			logout_btn.click()
		except:
			pass


		id_input = self.wait.until(
			EC.visibility_of_element_located((By.XPATH, "//*[@id='outlogin_mb_id']"))
		)
		id_input.clear()
		id_input.send_keys(self.id)

		pw_input = self.wait.until(
			EC.visibility_of_element_located((By.XPATH, "//*[@id='outlogin_mb_password']"))
		)
		pw_input.clear()
		pw_input.send_keys(self.pw)
		pw_input.send_keys(Keys.RETURN)
	

		if self.type == '상단업':
			try:
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='mymenu_outlogin']/div/ul/li[5]/a"))
				).click()
				
				saveLog(self.site, '제휴 상단업에 성공하였습니다.')
			except:
				saveLog(self.site, '제휴 상단업에 실패하였습니다.')
			time.sleep(0.5)

			try:
				self.driver.switch_to.alert.accept()
			except:
				pass
			
			try:
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='mymenu_outlogin']/div/ul/li[7]/a"))
				).click()

				saveLog(self.site, 'PR 상단업에 성공하였습니다.')
			except:
				saveLog(self.site, 'PR 상단업에 실패하였습니다.')
			time.sleep(0.5)

			try:
				self.driver.switch_to.alert.accept()
			except:
				pass

		elif self.type == '글쓰기':
			try:
				self.driver.get(self.url+"/bbs/mypost.php")
				self.driver.find_elements(By.XPATH, "//*[@id='new_list']/ul/li[1]/div[5]/a[text()='구인(매니져/실장)']/parent::*/preceding-sibling::div[3]/child::div/child::div/child::a")[0].click()
				
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='bo_v_btn']/div/button"))
				).click()
				time.sleep(0.5)
				

				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='bo_v_btn']/div/div/div/a[2]"))
				).click()
				time.sleep(0.5)
				self.driver.switch_to.alert.accept()
			except:
				pass

			try:
				self.driver.get(self.url+"/bbs/write.php?bo_table=c_job")

				
				#분류
				self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//select[@name='ca_name']/option[contains(text(),'매니져')]"))
				).click()

				#제목
				subject_elem = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='wr_subject']"))
				)
				subject_elem.clear()
				subject_elem.send_keys(self.subject)


				#내용
				frame = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='fwrite']/ul/li[5]/iframe"))
				)
				self.driver.switch_to.frame(frame)

				frame = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='se2_iframe']"))
				)
				self.driver.switch_to.frame(frame)

				content_elem = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "/html/body"))
				)
				content_elem.clear()
				content_elem.send_keys(".")
				self.driver.switch_to.default_content()

				#파일
				self.driver.find_element(By.XPATH, "//*[@id='fwriteFile0']").send_keys(os.path.abspath(self.content))
				time.sleep(5)

				submit_btn = self.wait.until(
					EC.visibility_of_element_located((By.XPATH, "//*[@id='btn_submit']"))
				)
				self.driver.execute_script("arguments[0].click();", submit_btn)

				saveLog(self.site, '글쓰기에 성공하였습니다.')
			except:
				saveLog(self.site, '글쓰기에 실패하였습니다.')
	

	def bypass_clould_flare(self, url):
		self.driver.get(url)

		is_detected = False
		try:
			self.wait.until(
				EC.visibility_of_element_located((By.XPATH, '//*[@id="challenge-running"]'))
			)

			is_detected = True
		except:
			pass

		time.sleep(1)

		if is_detected:
			
			pyautogui.hotkey('ctrl', 't')
			time.sleep(1)
			pyperclip.copy(url)
			pyautogui.hotkey('ctrl','v')
			time.sleep(1)
			pyautogui.press('enter')
			time.sleep(10) # wait until page has loaded
			
			self.driver.switch_to.window(driver.window_handles[-1])

			try:
				iframe = self.driver.find_element(
					By.XPATH, "//iframe[@title='Widget containing a Cloudflare security challenge']"
				)

				self.driver.switch_to.frame(iframe)
				checkbox = self.driver.find_element(
					By.XPATH, '//*[@id="challenge-stage"]/div/label/span[2]',
				)

				if checkbox:
					checkbox.click()
				time.sleep(5)


			
			finally:
				self.driver.switch_to.default_content()

		current_window = self.driver.current_window_handle

		# Get all window handles
		all_windows = self.driver.window_handles

		# Close all windows except the current one
		for window in all_windows:
			if window != current_window:
				self.driver.switch_to.window(window)
				self.driver.close()

		# Switch back to the current window
		self.driver.switch_to.window(current_window)


		
		
		


def startBot():
	global is_running
	is_running = True
	start_btn['state'] = "disabled"
	thread = Thread(target=startBotThread)
	thread.start()

def stopBot():
	global is_running
	is_running = False
	start_btn['state'] = "normal"

		
def startBotThread():
	is_first_loop = True
	while True:
		for work in reversed(work_list.get_children()):
			global is_running
			if is_running:
				row = work_list.item(work)['values']
				work_id = row[3]
				work_pw = row[4]
				work_site = row[2]
				work_type = row[1]
				work_reserve = row[5]
				
				try:
					work_subject = row[6]
					work_content = row[7]
				except:
					work_subject = None
					work_content = None
				
								
				try:
					CommunityMacro(driver, work_id, work_pw, work_site, work_type, work_reserve, work_subject, work_content, is_first_loop)
				except Exception as e:
					print(e)
					saveLog(work_site, '실패했습니다.')
											
			else:
				break

		if not is_loop.get():
			break

		is_first_loop = False

			
	
	
	is_running = False
	start_btn['state'] = "normal"




if __name__ == "__main__":
	chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]  #크롬드라이버 버전 확인

	subprocess.Popen(r'C:\Program Files\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrometemp"')

	options = webdriver.ChromeOptions()
	options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
	#options.add_argument('--incognito')


	try:
		driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe', options = options)   
	except:
		try:
			chromedriver_autoinstaller.install(True)
			driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe', options = options)
		except:
			service = Service(executable_path=ChromeDriverManager(version="114.0.5735.90").install())
			driver = webdriver.Chrome(service=service, options=options)

	
	#driver = uc.Chrome(options=options,version_main=chrome_ver,use_subprocess=True)

	driver.set_window_size(random.uniform(993,1300), random.uniform(700,1000))

	url = 'https://www.google.com/search?q=%EB%B6%80%EC%82%B0%EB%8B%AC%EB%A6%AC%EA%B8%B0&newwindow=1&biw=1034&bih=868&sxsrf=AB5stBgdM36FWpNokVotpKVLo-1bc_EBZA%3A1690345303228&ei=V5_AZIzBDYf6hwP71IGgAw&ved=0ahUKEwjMyOL6wquAAxUH_WEKHXtqADQQ4dUDCA8&uact=5&oq=%EB%B6%80%EC%82%B0%EB%8B%AC%EB%A6%AC%EA%B8%B0&gs_lp=Egxnd3Mtd2l6LXNlcnAiD-u2gOyCsOuLrOumrOq4sEiSFlAAWIcVcAd4AZABApgBigGgAdYPqgEEMC4xN7gBA8gBAPgBAagCCsICBBAjGCfCAgsQABiABBixAxiDAcICBRAAGIAEwgIHEAAYgAQYCsICBxAAGIoFGEPCAg0QLhiKBRjHARjRAxhDwgIIEAAYgAQYsQPCAggQLhiABBixA8ICERAuGIAEGLEDGIMBGMcBGNEDwgILEC4YgAQYsQMYgwHCAgUQLhiABMICBBAAGAPCAggQLhixAxiABMICBxAjGOoCGCfCAgcQIxiKBRgn4gMEGAAgQYgGAQ&sclient=gws-wiz-serp'
	driver.get(url)
	
	
	root=Tk()
	root.tk.call('encoding', 'system', 'utf-8')
	customFont = tkFont.Font(family="Consolas", size=9)
	root.title("커뮤니티 매크로")
	if os.path.isfile("./icon.ico"):
		root.iconbitmap("./icon.ico")
	root.geometry("1235x545+100+100")
	root.resizable(False, False)
	root.protocol("WM_DELETE_WINDOW", exitBot)
	 
	#남은기간 시작
	expires_at_label = Label(root)
	expires_at_label.place(x=1070,y=515)
	#남은기간 끝


	#공지사항 시작
	url = "http://marco.newsoft.kr/notice.php"
	res = session.get(url)
	res.raise_for_status() # 문제시 프로그램 종료
	notice = res.text

	notice_label = Label(root, text=f"공지사항 : {notice}")
	notice_label.place(x=20,y=515)
	#공지사항 끝


	#작업리스트 시작
	work_list_frame = ttk.LabelFrame(root, text="작업 리스트")
	work_list_frame.place(x=20,y=20,width=825, height=265)

	
	work_type_label = Label(work_list_frame, text="타입")
	work_type_label.place(x=15,y=5)
	work_type = StringVar()
	work_type_combobox = ttk.Combobox(work_list_frame, textvariable=work_type, width=15, values=work_type_list, state="readonly") 
	work_type_combobox.place(x=55,y=5)

	
	work_account_label = Label(work_list_frame, text="계정")
	work_account_label.place(x=210,y=5)
	work_account = StringVar()
	work_account_combobox = ttk.Combobox(work_list_frame, textvariable=work_account, width=15, values=work_account_list, state="readonly") 
	work_account_combobox.place(x=250,y=5)  


	#타이머 기능 시작
	timer_label = Label(work_list_frame, text="예약")
	timer_label.place(x=410,y=5)
	timer_hour = IntVar()
	timer_hour_textbox=Spinbox(work_list_frame,from_=0,to=23,textvariable=timer_hour)
	timer_hour_textbox.place(x=450,y=5, width=30)
	timer_hour_label = Label(work_list_frame, text="시")
	timer_hour_label.place(x=480,y=5)

	timer_minute = IntVar()
	timer_minute_textbox=Spinbox(work_list_frame,from_=0,to=59,textvariable=timer_minute)
	timer_minute_textbox.place(x=500,y=5, width=30)
	timer_minute_label = Label(work_list_frame, text="분")
	timer_minute_label.place(x=530,y=5)

	timer_second = IntVar()
	timer_second_textbox=Spinbox(work_list_frame,from_=0,to=59,textvariable=timer_second)
	timer_second_textbox.place(x=550,y=5, width=30)
	timer_second_label = Label(work_list_frame, text="초")
	timer_second_label.place(x=580,y=5)

	is_timer=IntVar()
	is_timer_checkbox=Checkbutton(work_list_frame, text="예약", variable=is_timer)
	is_timer_checkbox.place(x=605,y=2)
	#타이머 기능 끝

	add_work_list_btn = Button(work_list_frame, text='추가', width=15,height=1, state="disabled", command=AddWork)
	add_work_list_btn.place(x=685,y=2)
	
	work_list_menu = Menu(work_list_frame, tearoff = 0)

	#작업 추가한거 리스트
	work_list = ttk.Treeview(work_list_frame, column=("c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"), show='headings', height=8)
	work_list.column("# 1", anchor=CENTER, width=60)
	work_list.heading("# 1", text="번호")
	work_list.column("# 2", anchor=CENTER, width=80)
	work_list.heading("# 2", text="타입")
	work_list.column("# 3", anchor=CENTER, width=90)
	work_list.heading("# 3", text="사이트")
	work_list.column("# 4", anchor=CENTER, width=90)
	work_list.heading("# 4", text="아이디")
	work_list.column("# 5", anchor=CENTER, width=80)
	work_list.heading("# 5", text="비밀번호")
	work_list.column("# 6", anchor=CENTER, width=110)
	work_list.heading("# 6", text="예약")
	work_list.column("# 7", anchor=CENTER, width=160)
	work_list.heading("# 7", text="제목")
	work_list.column("# 8", anchor=CENTER, width=110)
	work_list.heading("# 8", text="이미지 경로")

	work_list.bind("<Button-3>", partial(openMenu, item_name=work_list_menu))
	work_list.place(x=15,y=40)

	work_list_menu.add_command(label ="선택삭제",command=ItemUtil(work_list,"작업 리스트").removeItem)
	work_list_menu.add_command(label ="전체삭제",command=ItemUtil(work_list,"작업 리스트").removeAllItem)

	#작업리스트 종료


	#로그 프레임 시작
	log_frame = ttk.LabelFrame(root, text="로그")
	log_frame.place(x=20,y=295,width=825, height=215)

	#로그 텍스트 박스
	log_list = ttk.Treeview(log_frame, column=("c1", "c2", "c3"), show='headings', height=7)

	log_list.column("# 1", anchor=CENTER, width=160)
	log_list.heading("# 1", text="사이트")
	log_list.column("# 2", anchor=CENTER, width=156)
	log_list.heading("# 2", text="시간")
	log_list.column("# 3", anchor=CENTER, width=470)
	log_list.heading("# 3", text="로그")

	log_list.place(x=15,y=10)

	#로그 프레임 끝
	
	#프로그램 계정 프레임 시작
	macro_account_frame = ttk.LabelFrame(root, text="프로그램 계정")
	macro_account_frame.place(x=860,y=20,width=355, height=120)

	#프로그램 계정 계정 아이디 텍스트박스
	macro_id_label = Label(macro_account_frame, text="아이디")
	macro_id_label.place(x=10,y=5)
	macro_id = StringVar()
	macro_id_textbox = ttk.Entry(macro_account_frame, width=32, textvariable=macro_id)
	macro_id_textbox.place(x=105,y=5)

	#프로그램 계정 비번 텍스트박스
	macro_pw_label = Label(macro_account_frame, text="비밀번호")
	macro_pw_label.place(x=10,y=30)
	macro_pw = StringVar()
	macro_pw_textbox = ttk.Entry(macro_account_frame, width=32, textvariable=macro_pw)
	macro_pw_textbox.place(x=105,y=30)

	#회원가입 버튼
	join_btn = Button(macro_account_frame, text='회원가입', width=21,height=1, command=macroJoin)
	join_btn.place(x=10,y=60)

	#로그인 버튼
	login_btn = Button(macro_account_frame, text='로그인', width=21,height=1, command=macroLogin)
	login_btn.place(x=180,y=60)
	
	#프로그램 계정 프레임 끝
	

	#커뮤니티 계정 프레임 시작
	community_account_frame = ttk.LabelFrame(root, text="커뮤니티 계정")
	community_account_frame.place(x=860,y=150,width=355, height=290)

	#커뮤니티 사이트 콤보박스
	community_site_label = Label(community_account_frame, text="사이트")
	community_site_label.place(x=15,y=5)
	community_site = StringVar()
	community_site_combobox = ttk.Combobox(community_account_frame, textvariable=community_site, width=17, values=community_site_list, state="readonly") 
	community_site_combobox.place(x=85,y=5)

	#커뮤니티 계정 아이디 텍스트박스
	community_id_label = Label(community_account_frame, text="아이디")
	community_id_label.place(x=15,y=30)
	community_id = StringVar()
	community_id_textbox = ttk.Entry(community_account_frame, width=20, textvariable=community_id)
	community_id_textbox.place(x=85,y=30)

	#커뮤니티 비밀번호 텍스트박스
	community_pw_label = Label(community_account_frame, text="비밀번호")
	community_pw_label.place(x=15,y=55)
	community_pw = StringVar()
	community_pw_textbox = ttk.Entry(community_account_frame, width=20, textvariable=community_pw)
	community_pw_textbox.place(x=85,y=55)
		

	#커뮤니티 계정 추가 버튼
	add_community_account_btn = Button(community_account_frame, text='추가', width=12, height=4, state="disabled",command=addCommunityAccount)
	add_community_account_btn.place(x=243,y=5)

	community_account_list_menu = Menu(community_account_frame, tearoff = 0)

	#커뮤니티 계정 추가한거 리스트
	community_account_list = ttk.Treeview(community_account_frame, column=("c1", "c2", "c3", "c4"), show='headings', height=7)
	community_account_list.column("# 1", anchor=CENTER, width=58)
	community_account_list.heading("# 1", text="번호")
	community_account_list.column("# 2", anchor=CENTER, width=87)
	community_account_list.heading("# 2", text="사이트")
	community_account_list.column("# 3", anchor=CENTER, width=87)
	community_account_list.heading("# 3", text="아이디")
	community_account_list.column("# 4", anchor=CENTER, width=87)
	community_account_list.heading("# 4", text="비밀번호")

	community_account_list.bind("<Button-3>", partial(openMenu, item_name=community_account_list_menu))
	community_account_list.place(x=15,y=90)

	community_account_list_menu.add_command(label ="선택삭제",command=ItemUtil(community_account_list,"커뮤니티 계정").removeItem)
	community_account_list_menu.add_command(label ="전체삭제",command=ItemUtil(community_account_list,"커뮤니티 계정").removeAllItem)


	#커뮤니티 계정 프레임 끝


	#작동 프레임 시작
	setting_frame = ttk.LabelFrame(root, text="작동")
	setting_frame.place(x=860,y=450,width=355, height=60)

	is_loop=IntVar()
	is_loop_checkbox=Checkbutton(setting_frame, text="반복", variable=is_loop)
	is_loop_checkbox.place(x=10,y=5)
		

	#시작 버튼
	start_btn = Button(setting_frame, text='시작', width=10, height=1, state='disabled', command=startBot)
	start_btn.place(x=70,y=5)

	#정지 버튼
	stop_btn = Button(setting_frame, text='정지', width=10, height=1, command=stopBot)
	stop_btn.place(x=160,y=5)

	#종료 버튼
	exit_btn = Button(setting_frame, text='종료', width=10, height=1, command=exitBot)
	exit_btn.place(x=250,y=5)

	#작동 프레임 끝
	root.mainloop()