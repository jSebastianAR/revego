#Script for test the casting from string to hex#
import binascii
import datetime
import calendar

s = 0x02
stx = ""
etx = ""
str_request = "01321-723-681                                 4.0.1                 01              101"

full_string = stx+str_request+etx
print((binascii.hexlify(stx.encode("utf-8")).decode("utf-8")))

#Funcion para CRC
def xor_strings(data):
	
	print(f"Data: {data}\n\n\n")
	for i in range(0,len(data)):

		if i==0:
			result = chr(ord(data[i]) ^ ord(data[i+1]))
			#print(f"{data[i]} xor {data[i+1]}={result}")
		elif i>0 and i+1<len(data): 
			aux = result
			result = chr(ord(result) ^ ord(data[i+1]))
			#print(f"{aux} xor {data[i+1]}={result}")

	print(f"Resultado CRC: {result}")
	return result		

#Convierte la info en hexadecimal
def string2hex(string_sentence):

	hex_string 	= binascii.hexlify(string_sentence.encode())
	hex_stx = binascii.hexlify(stx.encode())
	hex_etx = binascii.hexlify(etx.encode())

	print(f"El resultado hexadecimal es: {hex_stx}, {hex_string.decode()} {hex_etx}")
	#print(data)

def main():

	while True:
		string_sentence = input("ingresa la trama a transformar: ")
		string2hex(str_request)

#xor_strings(full_string)
string2hex(str_request)
my_date = datetime.date.today()
start = ""
print(calendar.day_name[my_date.weekday()])
