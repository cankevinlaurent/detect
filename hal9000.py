# -*- coding: utf-8 -*-

import time
import sqlite3
import ipaddress
import subprocess
import re
import os
from xml.etree import ElementTree as ET

##############################################################################


class Asset:
    '''
    get asset's ip from file.
    
    '''

    def getlist(self, filename):
        try:
            fp = open(filename, 'r')
            list = []
            for line in fp.readlines():
                list.append(line.strip('\n'))
            return list
        except:
            raise MyExcept('Error: Get asset.')

##############################################################################


class MyExcept(Exception):
    '''
    my exception handler, prints message then interrupts program.

    '''

    def __init__(self, msg='Error: Unknown.'):
        print(msg)

    def __del__(self):
        exit(0)

##############################################################################


class CvrtTime:
    '''
    convert timestamp between str and int

    '''

    def convert(self, timestamp):
        '''
        str or int
        
        '''

        try:
            if type(timestamp) is str: #str to int
                return time.mktime(
                    time.strptime(timestamp, '%a %b %d %H:%M:%S %Y'))
            else: #int to str
                return time.ctime(timestamp)
        except:
            raise MyExcept('Error: Convert time.')

##############################################################################


class MyDB:
    '''
    handle my database
    
    '''

    def __init__(self, database='hal9000.db'):
        try:
            self.conn = sqlite3.connect(database)
            self.cursor = self.conn.cursor()
        except:
            raise MyExcept('Error: Initiate database.')

    def __del__(self):
        try:
            self.conn.close()
        except:
            pass

    def _get_host_record(self, ip):
        '''
        get host record by ip
        user ensures the correctness

        '''

        try:
            self.cursor.execute('SELECT * FROM host WHERE ip=(?)', (ip,))
            return self.cursor.fetchone()
        except:
            raise MyExcept('Error: Get host record.')

    def get_host_all_active(self):
        '''
        get all up hosts from db.host
        return: ip

        '''

        try:
            self.cursor.execute('SELECT ip FROM host WHERE stat="up"')
            return self.cursor.fetchall()
        except:
            raise MyExcept('Error: Get hosts all acitve ip.')

    def get_host_oldest_timestamp_active(self):
        '''
        get one host from db.host where it is up and its timestamp is oldest
        return: ip

        '''

        try:
            self.cursor.execute('SELECT ip FROM host WHERE stat="up" ORDER BY timestamp LIMIT 1')
            return self.cursor.fetchone()
        except:
            raise MyExcept('Error: get host oldest timestamp.')

    def get_host_oldest_timestamp(self):
        '''
        get one host from db.host and its timestamp is oldest
        return: ip

        '''

        try:
            self.cursor.execute('SELECT ip FROM host ORDER BY timestamp LIMIT 1')
            return self.cursor.fetchone()
        except:
            raise MyExcept('Error: get host oldest timestamp.')

    def get_host_oldest_portchktime_active(self):
        '''
        get one host from db.host where it is up and its timestamp is oldest
        return: ip

        '''

        try:
            self.cursor.execute('SELECT ip FROM host WHERE stat="up" ORDER BY portchktime LIMIT 1')
            return self.cursor.fetchone()
        except:
            raise MyExcept('Error: get host oldest portchktime.')

    def _replace_host_record(self, record):
        '''
        update all columns of host by ip, create if inexiste
        user ensures the correctness
        
        '''

        try:
            self.cursor.execute(
                'REPLACE INTO host VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                    record.get('ip'),
                    record.get('name'),
                    record.get('stat'),
                    record.get('osname'),
                    record.get('osvendor'),
                    record.get('osfamily'),
                    record.get('osgen'),
                    record.get('osaccuracy'),
                    record.get('dept'),
                    record.get('admin'),
                    record.get('timestamp'),
                    record.get('portchktime'),
                    record.get('desc')))
            self.conn.commit()
        except:
            raise MyExcept('Error: Replace host record.')

    def update_host_record(self, record):
        '''
        only update not-none columns of host by ip, create if inexiste
        
        '''

        if record is None or record.get('ip') is None:
            return

        rec = self._get_host_record(record.get('ip'))
        if rec is None: #ip record inexiste
            self._replace_host_record(record)
        else:
            val = {'ip': record.get('ip'),
                'name': rec[1] if record.get('name') is None else record.get('name'),
                'stat': rec[2] if record.get('stat') is None else record.get('stat'),
                'osname': rec[3] if record.get('osname') is None else record.get('osname'),
                'osvendor': rec[4] if record.get('osvendor') is None else record.get('osvendor'),
                'osfamily': rec[5] if record.get('osfamily') is None else record.get('osfamily'),
                'osgen': rec[6] if record.get('osgen') is None else record.get('osgen'),
                'osaccuracy': rec[7] if record.get('osaccuracy') is None else record.get('osaccuracy'),
                'dept': rec[8] if record.get('dept') is None else record.get('dept'),
                'admin': rec[9] if record.get('admin') is None else record.get('admin'),
                'timestamp': rec[10] if record.get('timestamp') is None else record.get('timestamp'),
                'portchktime': rec[11] if record.get('portchktime') is None else record.get('portchktime'),
                'desc': rec[12] if record.get('desc') is None else record.get('desc')}
            self._replace_host_record(val)

    def _get_service_record(self, ip, portid, protocol):
        '''
        get service record by (ip,portid,protocol)
        user ensures the correctness

        '''

        try:
            self.cursor.execute('SELECT * FROM service WHERE ip=(?) AND \
                portid=(?) AND protocol=(?)', (ip,portid,protocol))
            return self.cursor.fetchone()
        except:
            raise MyExcept('Error: Get service record.')

    def get_service_tcp_oldest_timestamp_active(self):
        '''
        get one port from db.service where it is open and its timestamp is oldest

        '''

        try:
            self.cursor.execute('SELECT ip,portid,timestamp FROM service WHERE state="open" ORDER BY timestamp LIMIT 1')
            return self.cursor.fetchone()
        except:
            raise MyExcept('Error: get service oldest timestamp record.')

    def _replace_service_record(self, record):
        '''
        update all columns of service by (ip,portid,protocol) create if inexiste
        user ensures the correctness

        '''

        try:
            self.cursor.execute(
                'REPLACE INTO service VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(
                    record.get('ip'),
                    record.get('portid'),
                    record.get('protocol'),
                    record.get('state'),
                    record.get('reason'),
                    record.get('servname'),
                    record.get('product'),
                    record.get('version'),
                    record.get('dept'),
                    record.get('admin'),
                    record.get('timestamp'),
                    record.get('desc')))
            self.conn.commit()
        except:
            raise MyExcept('Error: Replace service record.')

    def update_service_record(self, record):
        '''
        only update not-none columns of service by (ip,portid,protocol), create if inexiste

        '''

        if record is None or record.get('ip') is None or \
        record.get('portid') is None or record.get('protocol') is None:
            return

        rec = self._get_service_record(
            record.get('ip'), record.get('portid'), record.get('protocol'))
        if rec is None: #(ip,portid,protocol) record inexiste
            self._replace_service_record(record)
        else:
            val = {'ip': record.get('ip')}
            val['portid'] = record.get('portid')
            val['protocol'] = record.get('protocol')
            val['state'] = rec[3] if record.get('state') is None else record.get('state')
            val['reason'] = rec[4] if record.get('reason') is None else record.get('reason')
            val['servname'] = rec[5] if record.get('servname') is None else record.get('servname')
            val['product'] = rec[6] if record.get('product') is None else record.get('product')
            val['version'] = rec[7] if record.get('version') is None else record.get('version')
            val['dept'] = rec[8] if record.get('dept') is None else record.get('dept')
            val['admin'] = rec[9] if record.get('admin') is None else record.get('admin')
            val['timestamp'] = rec[10] if record.get('timestamp') is None else record.get('timestamp')
            val['desc'] = rec[11] if record.get('desc') is None else record.get('desc')
            self._replace_service_record(val)

##############################################################################


class SplitIpAddr:
    '''
    split network list to ip
    input likes ['ipa/24', 'ipb/26', 'ipc']
    return lieks ['ipa', 'ipb', 'ipc', 'ipd']
    
    '''

    def split(self, netlist):
        try:
            hostlist = []
            for net in netlist:
                if '/' in str(net):
                    hosts = list(ipaddress.ip_network(net).hosts())
                    for host in hosts:
                        hostlist.append(str(host))
                else:
                    hostlist.append(net)
            return hostlist
        except:
            raise MyExcept('Error: IP address.')

##############################################################################


class Ping:
    '''
    ping method
    
    '''
 
    def win_ping(self, ip):
        '''
        windows ping
        result is affected by denying of ping
        return {ip:, stat:, timestamp:}

        -------------------------------
        windows ping output likes this:
        -------------------------------

        Pinging 10.4.100.177 with 32 bytes of data:
        Reply from 10.4.100.177: bytes=32 time=2ms TTL=64
        Reply from 10.4.100.177: bytes=32 time=1ms TTL=64
        Reply from 10.4.100.177: bytes=32 time=3ms TTL=64

        Ping statistics for 10.4.100.177:
            Packets: Sent = 3, Received = 3, Lost = 0 (0% loss),
        Approximate round trip times in milli-seconds:
            Minimum = 1ms, Maximum = 3ms, Average = 2ms

        '''

        try:
            cmd = 'ping -n 3 -w 50 ' + ip
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        except:
            raise MyExcept('Error: ping or ip is not found.')

        print('Done with %s' %(ip))
        return {'ip': ip,
            'stat': 'up' if b'TTL' in proc.communicate()[0] else 'down',
            'timestamp': int(time.time())}

##############################################################################


class Scanner:
    '''
    various scan methods by nmap
    
    '''

    def __init__(self):
        '''
        check if nmap existe
        
        '''

        try:
            cmd = 'nmap -V'
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        except:
            raise MyExcept('Error: nmap was not found in path.')

        nmap_output = proc.communicate()[0] #sav stdout
        if b'Nmap version' not in nmap_output:
            raise MyExcept('Error: nmap was not found in path.')

    def scan_os(self, ip):
        '''
        guess host's os info by nmap scan
        return: dict record
        
        ---------------------------
        nmap xml output likes this:
        ---------------------------

        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE nmaprun>
        <?xml-stylesheet href="file:///C:/Program Files (x86)/Nmap/nmap.xsl" type="text/xsl"?>
        <!-- Nmap 7.40 scan initiated Sun Feb 05 12:04:03 2017 as: nmap -oX - -O --osscan-limit 192.168.5.1 -->
        <nmaprun scanner="nmap" args="nmap -oX - -O --osscan-limit 192.168.5.1" start="1486267443" startstr="Sun Feb 05 12:04:03 2017" version="7.40" xmloutputversion="1.04">
            <scaninfo type="syn" protocol="tcp" numservices="1000" services="1,3-4,6-7,9,13,17,19-26,30,32-33,37,42-43,49,53,70,79-85,88-90,99-100,106,109-111,113,119,125,135,139,143-144,146,161,163,179,199,211-212,222,254-256,259,264,280,301,306,311,340,366,389,406-407,416-417,425,427,443-445,458,464-465,481,497,500,512-515,524,541,543-545,548,554-555,563,587,593,616-617,625,631,636,646,648,666-668,683,687,691,700,705,711,714,720,722,726,749,765,777,783,787,800-801,808,843,873,880,888,898,900-903,911-912,981,987,990,992-993,995,999-1002,1007,1009-1011,1021-1100,1102,1104-1108,1110-1114,1117,1119,1121-1124,1126,1130-1132,1137-1138,1141,1145,1147-1149,1151-1152,1154,1163-1166,1169,1174-1175,1183,1185-1187,1192,1198-1199,1201,1213,1216-1218,1233-1234,1236,1244,1247-1248,1259,1271-1272,1277,1287,1296,1300-1301,1309-1311,1322,1328,1334,1352,1417,1433-1434,1443,1455,1461,1494,1500-1501,1503,1521,1524,1533,1556,1580,1583,1594,1600,1641,1658,1666,1687-1688,1700,1717-1721,1723,1755,1761,1782-1783,1801,1805,1812,1839-1840,1862-1864,1875,1900,1914,1935,1947,1971-1972,1974,1984,1998-2010,2013,2020-2022,2030,2033-2035,2038,2040-2043,2045-2049,2065,2068,2099-2100,2103,2105-2107,2111,2119,2121,2126,2135,2144,2160-2161,2170,2179,2190-2191,2196,2200,2222,2251,2260,2288,2301,2323,2366,2381-2383,2393-2394,2399,2401,2492,2500,2522,2525,2557,2601-2602,2604-2605,2607-2608,2638,2701-2702,2710,2717-2718,2725,2800,2809,2811,2869,2875,2909-2910,2920,2967-2968,2998,3000-3001,3003,3005-3007,3011,3013,3017,3030-3031,3052,3071,3077,31278,63331,64623,64680,65000,65129,65389"/>
            <verbose level="0"/>
            <debugging level="0"/>
            <host starttime="1486267444" endtime="1486267451">
                <status state="up" reason="arp-response" reason_ttl="0"/>
                <address addr="192.168.5.1" addrtype="ipv4"/>
                <address addr="78:C1:A7:0B:43:32" addrtype="mac" vendor="zte"/>
                <hostnames></hostnames>
                <ports>
                    <extraports state="closed" count="996"><extrareasons reason="resets" count="996"/></extraports>
                    <port protocol="tcp" portid="53"><state state="open" reason="syn-ack" reason_ttl="64"/><service name="domain" method="table" conf="3"/></port>
                    <port protocol="tcp" portid="80"><state state="open" reason="syn-ack" reason_ttl="64"/><service name="http" method="table" conf="3"/></port>
                    <port protocol="tcp" portid="7777"><state state="open" reason="syn-ack" reason_ttl="64"/><service name="cbt" method="table" conf="3"/></port>
                    <port protocol="tcp" portid="52869"><state state="open" reason="syn-ack" reason_ttl="64"/><service name="unknown" method="table" conf="3"/></port>
                </ports>
                <os>
                    <portused state="open" proto="tcp" portid="53"/>
                    <portused state="closed" proto="tcp" portid="1"/>
                    <portused state="closed" proto="udp" portid="35682"/>
                    <osmatch name="Linux 2.6.32 - 3.10" accuracy="100" line="53646">
                        <osclass type="general purpose" vendor="Linux" osfamily="Linux" osgen="2.6.X" accuracy="100"><cpe>cpe:/o:linux:linux_kernel:2.6</cpe></osclass>
                        <osclass type="general purpose" vendor="Linux" osfamily="Linux" osgen="3.X" accuracy="100"><cpe>cpe:/o:linux:linux_kernel:3</cpe></osclass>
                    </osmatch>
                </os>
                <uptime seconds="1179974" lastboot="Sun Jan 22 20:17:57 2017"/>
                <distance value="1"/>
                <tcpsequence index="258" difficulty="Good luck!" values="A0D96948,F32FE618,9944DBDB,C0BE68C8,15CA9851,3FCCDE8"/>
                <ipidsequence class="All zeros" values="0,0,0,0,0,0"/>
                <tcptssequence class="100HZ" values="7087F02,7087F0D,7087F18,7087F23,7087F2E,7087F39"/>
                <times srtt="15960" rttvar="28032" to="128088"/>
            </host>
            <runstats>
                <finished time="1486267451" timestr="Sun Feb 05 12:04:11 2017" elapsed="8.36" summary="Nmap done at Sun Feb 05 12:04:11 2017; 1 IP address (1 host up) scanned in 8.36 seconds" exit="success"/>
                <hosts up="1" down="0" total="1"/>
            </runstats>
        </nmaprun>
        
        '''

        try:
            cmd = 'nmap -oX - -Pn -O --osscan-limit --host-timeout 360 ' + ip
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            raise MyExcept('Error: nmap os scan.')
        
        nmap_output = bytes.decode(proc.communicate()[0]) #sav stdout
        try:
            dom = ET.fromstring(nmap_output) #None will also raise MyExcept
        except:
            raise MyExcept('Error: nmap output.')

        if dom.find('host') is None:
            return None
        if dom.find('host/os/osmatch') is None:
            return None
        record = {'ip': ip,
            'osname': dom.find('host/os/osmatch').get('name')}
        osclass = dom.find('host/os/osmatch/osclass')
        if osclass is not None:
            record['osvendor'] = osclass.get('vendor')
            record['osfamily'] = osclass.get('osfamily')
            record['osgen'] = osclass.get('osgen')
            record['osaccuracy'] = int(osclass.get('accuracy'))
        print('Done with %s' %(ip))
        return record

    def scan_ports_tcp(self, ip):
        '''
        only detects port's state, not service's version.
        return only open or open|filtered ports
        
        '''
        
        try:
            cmd = 'nmap -oX - -Pn -p 1-65535 -sS -T4 --host-timeout 360 ' + ip
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            raise MyExcept('Error: tcp ports fast scan error.')

        nmap_output = bytes.decode(proc.communicate()[0]) #sav stdout
        try:
            dom = ET.fromstring(nmap_output) #None will also raise MyExcept
        except:
            raise MyExcept('Error: nmap output.')

        if dom.find('host') is None: #host is down
            return None

        result = [] #all ports' information
        for port in dom.findall('host/ports/port'):
            dport = {'ip': ip,
                'portid': int(port.get('portid')),
                'protocol': 'tcp',
                'state': port.find('state').get('state'),
                #'reason': port.find('state').get('reason'),
                #'timestamp': int(dom.find('runstats/finished').get('time'))
            }
            if 'open' not in dport['state']:
                continue
            #if port.find('service') is not None:
                #dport['servname'] = port.find('service').get('name')
            result.append(dport)

        if len(result) == 0:
            return None
        else:
            return result

    def scan_service_tcp(self, ip, port):
        '''
        guess one service info by one given ip & one given TCP port

        '''

        try:
            cmd = 'nmap -oX - -Pn -p ' + str(port) + ' -T4 -sV --version-light --host-timeout 20 ' + ip
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            raise MyExcept('Error: nmap port scan.')

        nmap_output = bytes.decode(proc.communicate()[0]) #sav stdout
        try:
            dom = ET.fromstring(nmap_output) #None will also raise MyExcept
        except:
            raise MyExcept('Error: nmap output.')

        if dom.find('host') is None: #host is down
            return None

        result = {'ip': ip,
            'portid': port,
            'protocol': 'tcp',
            'timestamp': int(dom.find('runstats/finished').get('time'))}

        portid = dom.find('host/ports/port')
        if portid is None:
            return result

        result['state'] = portid.find('state').get('state')
        result['reason'] = portid.find('state').get('reason')

        if portid.find('service') is not None:
            result['servname'] = portid.find('service').get('name')
            result['product'] = portid.find('service').get('product')
            result['version'] = portid.find('service').get('version')

        return result

##############################################################################
