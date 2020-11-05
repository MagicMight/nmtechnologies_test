#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
from threading import Thread
from time import sleep
import json
from random import random
from math import ceil
import msvcrt
from datetime import datetime as dt
import win10toast
import rsa
import zlib
from tkinter import Tk, Frame, Button, Text, Label, Entry, PhotoImage

from CONFIG import commandDescription
# from FileSync import FileSync

################################################################
SERVER_PORT = '***********'
MY_IP = '***********'
REMOTE_IP_LIST = ['*************', '**************']
# REMOTE_IP_LIST = []
# PUBKEY = 'C:/********'
# PRIVKEY = 'C:/**************'

PUBKEY = 'encode.key'
PRIVKEY = 'decode.key'
################################################################

class RsaChat:

	# Конструктор
	def __init__(self, maxMessages=25):

		# Управление отображением сообщений на экране
		self.messageStackSize = maxMessages
		self.messages = ['']*maxMessages
		self.lastIndex = 0
		self.socketListenerThread = Thread(target = self.socketListener)
		self.needToUpdateMsgBox = True

		self.alias = f'user{ceil(random()*10000)}'

	# Запуск приложения
	def run(self):
		# self.loadRSAKeys()
		self.loadRSAKeys(dec=PRIVKEY, enc=PUBKEY)
		self.createUI()
		self.tagConfigure()
		self.createConnection()
		self.socketListenerThread.start()
		self.sendMessage(action='text', text='Connect to server')

		self.UIRoot.after(200, self.checkNewMessages)
		self.UIRoot.mainloop()

	# Проверка наличия новых сообщений
	def checkNewMessages(self):
		if self.needToUpdateMsgBox:
			self.needToUpdateMsgBox = False
			self.printMessages()
		self.UIRoot.after(200, self.checkNewMessages)

	# Загрузка ключей шифрования RSA
	def loadRSAKeys(self, dec='decode.key', enc='encode.key'):
		f = open(dec, 'r', encoding='ascii')
		c = f.read()
		f.close()
		self.decodeKeyRSA = rsa.PrivateKey.load_pkcs1( c.encode('ascii') )

		f = open(enc, 'r', encoding='ascii')
		d = f.read()
		f.close()
		self.encodeKeyRSA = rsa.PublicKey.load_pkcs1( d.encode('ascii') )

	# Создание подключения и случайного имени пользователя. Если подключиться к серверу не удается, то создать свой сервер
	def createConnection(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(('', 0))
		self.sock.settimeout(2)

		# Попытаться подключиться к серверам по списку
		for ip in REMOTE_IP_LIST:
			try:
				self.serverAddress = (ip, SERVER_PORT)
				self.sock.sendto( '***************'.encode('utf-8') , self.serverAddress)
				data = self.sock.recv(512)
				print(data)
				if data.decode('utf-8') == ''***************'.':
					print(f'Соединение с сервером {ip} установлено')
					self.sock.settimeout(9**5)
					return
			except Exception:
				print(ip, 'can not connect')

		
		# Если соединение не удалось, то создать сервер
		self.sock.settimeout(9**5)
		self.server = Thread(target = self.startServer)
		self.server.start()
		
		self.isServerReady = False
		while not self.isServerReady:
			sleep(0.2)

		self.serverAddress = (MY_IP, SERVER_PORT)
	
	# Запуск сервера
	def startServer(self, ip=MY_IP, port=SERVER_PORT):
		sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
		sock.bind((ip, port))
		clients= []
		print ('Start Server')
		self.isServerReady = True
		while True:
			data, addr = sock.recvfrom(8192)

			try:
				if data.decode('utf-8') == 'рис':
					sock.sendto('еда рабов'.encode('utf-8'), addr)
					clients.append(addr)
					continue
			except Exception:
				pass
			

			if  addr not in clients: 
				clients.append(addr)
				print( addr )

			for client in clients:
				try:
					if client == addr:
						continue
					sock.sendto(data, client)
					print(addr, 'в сети')
				except Exception:
					print(addr, 'не в сети')
					del client
					pass
	
	# Отправка сообщения самому себе
	def sendMessageToMyself(self, newmsg):
		if newmsg['action'] in ['text', 'info', 'description']:
			self.lastIndex = (self.lastIndex+1) % self.messageStackSize
			self.messages[self.lastIndex] = newmsg
		else:
			self.command_contol(cmd=newmsg['action'], cmdata=newmsg)
		self.needToUpdateMsgBox = True

	# Отправка сообщений
	def sendMessage(self, action='text', text='', needSelfSend=True):
		timenow = dt.now()
		print(self.serverAddress)
		newmsg = {	
			'name': self.alias,
			'action': action,
			'text': text,
			'date': timenow.strftime("%H:%M:%S")
		}

		# Сжатие и зашифровка сообщения
		cprs = zlib.compress( json.dumps(newmsg).encode(), level=4 )
		crypto = rsa.encrypt( cprs, self.encodeKeyRSA)
		self.sock.sendto( crypto , self.serverAddress)

		# Продублировать сообщение самому себе
		if needSelfSend:
			self.sendMessageToMyself(newmsg)
			self.inputTextBox.delete(0, 'end')
	
	# Обработка команд
	def command_contol(self, cmd, cmdata=None):
		timenow = dt.now()
		if (cmd == 'help' and cmdata not in commandDescription) or cmd not in commandDescription:
			newmsg = { 'name': self.alias, 'action': 'description', 'text': '', 'date': timenow.strftime("%H:%M:%S") }
			for i in commandDescription:
				newmsg['text'] += f'> {i}\t\t{commandDescription[i]}\n'
			self.sendMessageToMyself(newmsg)
		
		elif cmd == 'help' and cmdata in commandDescription:
			newmsg = { 
				'name': self.alias, 
				'action': 'description', 
				'text': f'{cmd} {cmdata}\n[{cmdata}]: {commandDescription[cmdata]}\n', 
				'date': timenow.strftime("%H:%M:%S") 
			}
			self.sendMessageToMyself(newmsg)

	# Обработка ввода
	def input_control(self, event):

		# Нажатие Enter
		if event.keycode != 13:
			return False
		
		ut = self.inputTextBox.get()
		self.inputTextBox.delete(0, 'end')

		if ut[0] == '/':
			cm = ut.split(' ')
			if len(cm) > 1:
				self.command_contol( cm[0][1:], cm[1] )
			else:
				self.command_contol( cm[0][1:] )
		else:
			self.sendMessage( action="text", text=ut )

	# Создание интерфейса
	def createUI(self):
		FONT_SETTINGS = ('Consolas', 12)

		root = Tk()

		_ICON=PhotoImage(height=32, width=32)
		_ICON.blank()

		root.title('rsachatclient')
		root.resizable(width=True, height=True)
		root.geometry('1000x700')
		root.tk.call('wm', 'iconphoto', root._w, _ICON)

		frame = Frame(root, bg='#000')
		frame.place(relx=0, rely=0, relwidth=1, relheight=1)

		txt = Entry(frame, bg='#000', fg='#fff', font=FONT_SETTINGS)
		txt.place(relx=0.1, rely=0.95, relwidth=1, relheight=0.05)

		aliasLabel = Label(frame, bg='#000', fg='#fff', font=FONT_SETTINGS)
		aliasLabel.place(relx=0, rely=0.95, relwidth=0.1, relheight=0.05)

		outputMsgBox = Text(frame, bg='#000', fg='#fff', font=FONT_SETTINGS)
		outputMsgBox.place(relx=0, rely=0, width=1000, relheight=0.95)

		txt.bind('<Key>', self.input_control)
		txt.focus()

		self.UIRoot = root
		aliasLabel.configure(text=self.alias)
		self.inputTextBox = txt
		self.outputMsgBox = outputMsgBox

	# Настройка тегов для отображения текста
	def tagConfigure(self):
		self.outputMsgBox.tag_configure('DATE_TAG', 	foreground='cyan')
		self.outputMsgBox.tag_configure('USERNAME_TAG', foreground='green')
		self.outputMsgBox.tag_configure('YOURNAME_TAG', foreground='lightgreen')
		self.outputMsgBox.tag_configure('TEXT_TAG', 	foreground='green')
		self.outputMsgBox.tag_configure('DESCR_TAG', 	foreground='teal')

	# Отображение сообщений
	def printMessages(self, clear=True, clearInput=True):
		self.outputMsgBox.configure(state='normal')

		if clear:
			self.outputMsgBox.delete(0.0, str(self.messageStackSize)+".9999")

		for i in range(1, self.messageStackSize+1):
			msg = self.messages[ (self.lastIndex + i) % self.messageStackSize ]
			pos = f'{i}.end'

			if msg == '':
				continue
			
			elif msg['action'] == 'text':
				self.outputMsgBox.insert(pos, f'[{msg["date"]}]', 'DATE_TAG')

				if self.alias == msg['name']:
					self.outputMsgBox.insert(pos, f'[{msg["name"]}]', 'YOURNAME_TAG')
				else:
					self.outputMsgBox.insert(pos, f'[{msg["name"]}]', 'USERNAME_TAG')

				self.outputMsgBox.insert(pos, f': {msg["text"]}', 'TEXT_TAG')
				self.outputMsgBox.insert(pos, '\n')


			elif msg['action'] == 'info':
				t = f'[{msg["date"]}][ *** {msg["text"]} *** ]'
				self.outputMsgBox.insert( "0.0", t+'\n')
			
			elif msg['action'] == 'description':
				t = f'{"-"*90}\n{msg["text"]}{"-"*90}'
				self.outputMsgBox.insert( pos, t+'\n', "DESCR_TAG")

			else:
				print(msg)

		self.outputMsgBox.configure(state='disabled')

	# Цикл прослушивания сети
	def socketListener(self):
		while True:
			data = self.sock.recv(65536)
			decrypt = rsa.decrypt( data, self.decodeKeyRSA )
			decd = zlib.decompress( decrypt )

			gotmsg = json.loads(decd.decode())

			if gotmsg['action'] == 'text' or gotmsg['action'] == 'info':
				self.lastIndex = (self.lastIndex+1) % self.messageStackSize
				self.messages[self.lastIndex] = gotmsg
			else:
				self.command_contol(cmd=gotmsg['action'], cmdata=gotmsg)
			self.needToUpdateMsgBox = True

app = RsaChat()
app.run()