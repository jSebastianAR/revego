from threading import Thread
import socket
import time
import re
import errno
import pickle

#REGEX_DATA_GLTERMINAL = r'<02>(.*?)<03>'
#REGEX_DATA_GLTERMINAL = r'\\x02(.*?)\\x03'
REGEX_DATA_GLTERMINAL = r'\x02(.*?)\x03'
LIST_STATIC_DATA = [" 00105Tiket 0000000009478 1000^0100COMPUMAR DEMO^0100 Pemex ES 5189^0000R.F.C. VIEE7001301U3^0000PERMISO CRE: PL/22638/EXP/ES/2019^0   SERVICIO SUGASTI XALAPA^0000 <1b>",\
" 00106Tiket 0000000009478 1000^0000*************************************^0100  CONTADO COPIA^0000*************************************^0000^0000     Cliente:  Publico en General |",\
" 00106Tiket 0000000009478 1000^0000 Fecha Venta: 2020/07/30 19:33:32^0000 Fecha Impre: 2020/08/03 20:36:46^0000       Turno: 2020072201^0000^0101Transaccion^01013015^0000 <13>",\
" 00106Tiket 0000000009478 1000^0000       Venta: 9478^0000      Web Id: t10100000301554^0000        Isla: 1^0000       Bomba: 1^0000    Manguera: 1^0000    Forma Pago: ^0000 <00>",\
" 00106Tiket 0000000009478 1000^0000Producto  Cantidad Precio  Total ^0000-----------------------------------^0000Magna  0.815    81.40    14.80^0000^0000    Subtotal: 12.77 V",\
" 00106Tiket 0000000009478 1000^0000         IVA: 2.03^0000       Total: 14.80^0000^0000CATORCE PESOS CON 80/100 M.N.^0000----------------------------------- }",\
" 00106Tiket 0000000009478 1000^BARQ0518902t1010000030155400014.8202007301933^0   ESTE TICKET ES FACTURABLE SOLO^0   EL DIA DE SU CONSUMO^0   FACTURACION EN LINEA: C",\
" 00107Tiket 0000000009478 1000^0   gl-operacion.com.mx ="]


class listener_thread(Thread):
	"""docstring for listener_thread"""
	def run(self):
		print(f"Server socket escuchando a GLTerminal")
		self.listen()
		#self.functionPruebas()
		
	def listen(self):

		# socket de flujo
		serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# Se establece la configuración donde estará escuchando el socket
		serversocket.bind((socket.gethostbyname(socket.gethostname()), 5023))
		# el server escucha y se establece como máximo dos request
		serversocket.listen(2)

		while True:

			print(f"Esperando conexion, escuchando en {socket.gethostbyname(socket.gethostname())}:{5023}")
			clientsocket, addr = serversocket.accept()
			print(f"================================Conexión recibida================================")
			full_data = ''
			list_of_data = []
			#clientsocket.setblocking(0)
			clientsocket.settimeout(8) #Commit de la revisión 1621
			while True:

				try:
					print(f'Mensaje previo a recv')
					msg = clientsocket.recv(4096)
					#full_data += ' '+ msg.decode()
					#logger.info('LOG_ID'+ str(currentTransaction)+ ' TRAMA RECIBIDA DE PARTE DE GLTERMINAL: '+str(msg))
					print(' TRAMA RECIBIDA DE PARTE DE GLTERMINAL: '+'"'+msg.decode()+'"')
					list_of_data.append(msg.decode())

					if self.analize_trama(msg.decode()): #If finds out that its the last trama to be sended
						break

				except socket.error as e:
					err = e.args[0]
					if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
					    print('Esperando un segundo a que el buffer se llene')
					    time.sleep(1)
					    continue
					else:
						print('Hubo error al recibir los datos!')
						msg=err
						break
				#else:
				#	print('Se termino de recibir todo')

			clientsocket.close()
			#time.sleep(1.5)
			if len(list_of_data)>0:
				print(f'================================list_of_data {list_of_data}================================')
				self.send_Data(self.filterData(list_of_data))
			print(f"================================Conexión cerrada================================")

	def functionPruebas(self):		
		while True:
			print(f"================================Conexión iniciada en functionPruebas================================")
			time.sleep(10)
			self.send_Data(self.filterData(LIST_STATIC_DATA))
			print(f"================================Conexión cerrada en functionPruebas================================")


	def filterData(self,data_list):

		trama_list = []
		for trama in data_list:
			trama_without_str_stx = re.findall(REGEX_DATA_GLTERMINAL,trama,re.DOTALL)[0] #elimina el stx y str 
			trama_without_30first = trama_without_str_stx[30:]
			trama_list.append(trama_without_30first)

		print(f"trama_list {trama_list}")	
		data_and_format = self.get_format_and_sentences(trama_list)

		#delete_str_stx = lambda trama: re.findall(REGEX_DATA_GLTERMINAL,trama,re.DOTALL)[0] #elimina el stx y str 
		#delete_first_30_characters = lambda trama_without_str_stx: trama_without_str_stx[30:] #elimina los primeros 30 caracteres de la trama
		
		#deleted_str_stx = list(map(delete_str_stx,data_list))
		#filtered_data = list(map(delete_first_30_characters,deleted_str_stx))

		#data_with_format = self.get_format_and_sentences(filtered_data)

		print(f"==========================FILTERED DATA {data_and_format}==========================")
		return data_and_format		

	def join_Data(self,data):
		return ' '.join(data)

	def get_format_and_sentences(self,data):
   
		split_data = lambda fullsentence: [fullsentence[0:4],fullsentence[4:]] if len(fullsentence)>4 else ['\n'] #obtiene el formato(primeros 4 caracteres) y el enunciado con el formato.
		data_and_format = []
		for trama in data:
			splited_trama = trama.split('^') #separa la trama por ^
			data_and_format += list(map(split_data,splited_trama))#Obtiene el formato de cada trama y agrega los resultados a una sola lista.

		return data_and_format

	def send_Data(self,data):

		clientsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		port_django = 50000
		port_javascript = 50001
		host_django = socket.gethostbyname(socket.gethostname())
		host_javascript = "127.0.0.1"

		try:#Intentará conectarse al socket de Django
			clientsocket = self.connect_with_server(host_django,port_django)
			data_pickle = pickle.dumps(data)
			clientsocket.send(data_pickle)
		except Exception as e:
			print(f"No se pudo realizar la conexion en Django: {e}")

			try:#Realizando la conexión al websocket directo del FrontEnd
				clientsocket = self.connect_with_server(host_javascript,port_javascript)
				clientsocket.send(data.encode())

			except Exception as e:
				print(f"No se pudo realizar la conexion en el websocket del FrontEnd: {e}")
		else:
			clientsocket.close()
		return

	def connect_with_server(self,host,port):	

		clientsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		clientsocket.connect((host, port))
		return clientsocket

	
	def analize_trama(self,trama):

		if '00107' in trama[:10]: #Looks if is it the code of end of trama
			return True
		else:
			return False



   	