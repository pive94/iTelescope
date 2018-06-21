#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import logging
from PyQt4 import QtCore
import asyncore
from time import sleep, time
from string import replace
from bitstring import BitArray, BitStream, ConstBitStream
import coords
import socket
from datetime import datetime
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, Angle

TCP_IP = '192.168.137.93'
TCP_PORT = 5005
BUFFER_SIZE = 1024
logging.basicConfig(level=logging.DEBUG, format="%(filename)s: %(funcName)s - %(levelname)s: %(message)s")

## \brief Implementation of the server side connection for 'Stellarium Telescope Protocol'
#
#  Manages the execution thread to the server side connection with Stellarium
class Telescope_Channel(QtCore.QThread, asyncore.dispatcher):

	## Class constructor
	#
	# \param conn_sock Connection socket
	def __init__(self, conn_sock):
		self.is_writable = False
		self.buffer = ''
		asyncore.dispatcher.__init__(self, conn_sock)
		QtCore.QThread.__init__(self, None)
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.connect((TCP_IP, TCP_PORT))
	## Indicates the socket is readable
	#
	# \return Boolean True/False
	def readable(self):
		return True

	## Indicates the socket is writable
	#
	# \return Boolean True/False
	def writable(self):
		return self.is_writable

	## Close connection handler
	#
	def handle_close(self):
		logging.debug("Disconnected")
		self.close()

	## Reading socket handler
	#
	# Reads and processes client data, and throws the proper signal with coordinates as parameters
	def handle_read(self):
		#format: 20 bytes in total. Size: intle:16
		#Incomming messages comes with 160 bytes..
		data0 = self.recv(160);
		if data0:
			data = ConstBitStream(bytes=data0, length=160)
			#print "All: %s" % data.bin

			msize = data.read('intle:16')
			mtype = data.read('intle:16')
			mtime = data.read('intle:64')

			# RA:
			ant_pos = data.bitpos
			ra = data.read('hex:32')
			data.bitpos = ant_pos
			ra_uint = data.read('uintle:32')

			# DEC:
			ant_pos = data.bitpos
			dec = data.read('hex:32')
			data.bitpos = ant_pos
			dec_int = data.read('intle:32')

			logging.debug("Size: %d, Type: %d, Time: %d, RA: %d (%s), DEC: %d (%s)" % (msize, mtype, mtime, ra_uint, ra, dec_int, dec))
			(sra, sdec, stime) = coords.eCoords2str(float("%f" % ra_uint), float("%f" % dec_int), float("%f" %  mtime))
			#Sends back the coordinates to Stellarium
			self.act_pos(coords.hourStr_2_rad(sra), coords.degStr_2_rad(sdec))
			convdec = sdec.replace('º', 'd').replace("''", 's').replace("'", 'm')
			convra = sra.replace('h', '.').replace("m", '.').replace("s", '.')
			sra_aux = convra.split('.')
			sra_h = float(sra_aux[0])
			sra_m = float(sra_aux[1])
			sra_s = float(sra_aux[2])
			sra_d=sra_h*15
			sra_m=sra_m*0.25
			sra_s=sra_s*0.00416667
			sra_sum=sra_d+sra_m+sra_s
			sra_aux1=str(sra_sum)
			sra_aux2 = sra_aux1.split('.')
			sra_df = int(sra_aux2[0])
			sra_dec = sra_sum-sra_df
			sra_dec = sra_dec*60
			sra_aux3=str(sra_dec)
			sra_aux4 = sra_aux3.split('.')
			sra_mf = int(sra_aux4[0])
			sra_dec1 = sra_dec - sra_mf
			sra_dec1 = sra_dec1 * 60
			sra_aux5 = str(sra_dec1)
			sra_aux6 = sra_aux5.split('.')
			sra_sf = str(sra_aux6[0])
			sra_df=str(sra_df)
			sra_mf = str(sra_mf)
			convraf=sra_df+'d'+sra_mf+'m'+sra_sf+'s'
			#print(convraf)
			#print(convdec)
			Qro = EarthLocation(lat=Angle('20d35m17.02s'),
								lon=Angle('-100d23m17.02s'),
								height=2152 * u.m)
			# Fecha y hora
			utc_time = Time(datetime.utcnow(), scale='utc')
			time = utc_time

			# Ecuatoriales
			Objeto = SkyCoord(Angle(convraf),
							  Angle(convdec),
							  frame='icrs')
			# Horizontales
			Objeto = Objeto.transform_to(AltAz(obstime=time, location=Qro))

			print("Azimut: ", int(Objeto.az.degree))
			print("Altura: ", int(Objeto.alt.degree))
			#MESSAGE1 = str(int(Objeto.az.degree))
			#MESSAGE2 = str(int(Objeto.alt.degree))
			#self.s.send((MESSAGE1))
			#self.s.send((MESSAGE2))
			#data = self.s.recv(BUFFER_SIZE)
			#print ("received data:", data)


	## Updates the field of view indicator in Stellarium
	#
	# \param ra Right ascension in signed string format
	# \param dec Declination in signed string format
	def act_pos(self, ra, dec):
		(ra_p, dec_p) = coords.rad_2_stellarium_protocol(ra, dec)

		times = 10 #Number of times that Stellarium expects to receive new coords //Absolutly empiric..
		for i in range(times):
			self.move(ra_p, dec_p)


	## Sends to Stellarium equatorial coordinates
	#
	#  Receives the coordinates in float format. Obtains the timestamp from local time
	#
	# \param ra Ascensión recta.
	# \param dec Declinación.
	def move(self, ra, dec):
		msize = '0x1800'
		mtype = '0x0000'
		localtime = ConstBitStream(replace('int:64=%r' % time(), '.', ''))
		#print "move: (%d, %d)" % (ra, dec)

		sdata = ConstBitStream(msize) + ConstBitStream(mtype)
		sdata += ConstBitStream(intle=localtime.intle, length=64) + ConstBitStream(uintle=ra, length=32)
		sdata += ConstBitStream(intle=dec, length=32) + ConstBitStream(intle=0, length=32)
		self.buffer = sdata
		self.is_writable = True
		self.handle_write()

	## Transmission handler
	#
	def handle_write(self):
		self.send(self.buffer.bytes)
		self.is_writable = False


## \brief Implementation of the server side communications for 'Stellarium Telescope Protocol'.
#
#  Each connection request generate an independent execution thread as instance of Telescope_Channel
class Telescope_Server(QtCore.QThread, asyncore.dispatcher):

	## Class constructor
	#
	# \param port Port to listen on
	def __init__(self, port=10001):
		asyncore.dispatcher.__init__(self, None)
		QtCore.QThread.__init__(self, None)
		self.tel = None
		self.port = port

	## Starts thread
	#
	# Sets the socket to listen on
	def run(self):
		logging.info(self.__class__.__name__+" running.")
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind(('localhost', self.port))
		self.listen(1)
		self.connected = False
		asyncore.loop()

	## Handles incomming connection
	#
	# Stats a new thread as Telescope_Channel instance, passing it the opened socket as parameter
	def handle_accept(self):
		self.conn, self.addr = self.accept()
		logging.debug('%s Connected', self.addr)
		self.connected = True
		self.tel = Telescope_Channel(self.conn)

	## Closes the connection
	#
	def close_socket(self):
		if self.connected:
			self.conn.close()
			#self.s.close()


#Run a Telescope Server
if __name__ == '__main__':
	try:
		Server = Telescope_Server()
		Server.run()
	except KeyboardInterrupt:
		logging.debug("\nBye!")
