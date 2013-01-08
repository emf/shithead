#
# This is shithead. It does whois lookups over Tor. (or any socks5 proxy, i guess, but.. why?)
# Why?  because I need to do a lot of lookups, and the registrars don't want me to.
# I figured i'd try shitting this across Tor before I rented time on a botnet for this...
#

def whoRU():
	while True:
		name = q.get()
		try:
			w = pywhois.whois(name)
			#epoch = int(time.mktime(pywhois.parser.cast_date(w.creation_date[0])))
		except:
			faults.put(name)
			continue
		finally:
			q.task_done()

		r.put( (name,w) )


import socks
import socket
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)
socket.socket = socks.socksocket
import pywhois

import time
import sys
from threading import Thread
from Queue import Queue

import sqlite3
import jsonlib

q = Queue()
r = Queue()
faults = Queue()

print "starting threads..."
for i in range(150):
	t = Thread(target=whoRU)
	t.daemon = True
	t.start()

print "enqueueing whois queries..."
f = open("domains.txt","r")
for line in f:
	q.put( line.rstrip() )

print "waiting on queue..."
while True:
	sys.stdout.write("queue: " + str(q.unfinished_tasks) + "/" + str(q.qsize()) + " results: " + str(r.qsize()) + "\x1b[K\r")
	if q.qsize() == 0 and q.unfinished_tasks == 0:
		break
	time.sleep(5)

print "coalescing results..."
results = []
while r.empty() == False:
	results.append(r.get_nowait())
	r.task_done()

print "dumping results to shit.db"

conn = sqlite3.connect("shit.db")
c = conn.cursor()
try:
	c.execute("create table whois(name varchar(255), response text);")
	c.execute("create index whois_dns on whois(name);")
except:
	print "Oh good, it appears to already be created..."
	pass
for o in results:
	(name, whois) = o
	w = jsonlib.write(dict([ (x, getattr(whois,x)) for x in whois.attrs() ]))
	c.execute("insert into whois values(?,?)", (name, w))
conn.commit()
conn.close()

print "coalescing faults..."
results = []
while faults.empty() == False:
	results.append(faults.get_nowait())
	faults.task_done()
	
output = open("faultlist.txt","w+")
print "emitting faultlist.txt"
for o in results:
	output.write( o + "\n" )
output.close()



