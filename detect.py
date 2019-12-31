# -*- coding: utf-8 -*-

import hal9000
from multiprocessing import Pool, Process

##############################################################################


def con_ping():
    '''
    concurrent ping
    runtime estimate: 15m

    '''

    addrlist = hal9000.Asset().getlist('asset.lst')
    ipaddr = hal9000.SplitIpAddr().split(addrlist)

    mydb = hal9000.MyDB()
    ping = hal9000.Ping()

    pool = Pool(240) #240 is prefered

    results = []
    for ip in ipaddr:
        results.append(pool.apply_async(ping.win_ping, args=(ip,)))
    pool.close()
    pool.join()

    for result in results:
        mydb.update_host_record(result.get())
        print('Wrote %s' %(result.get()))

    print('All done.')

def non_ping():
    '''
    non-current ping
    
    '''

    mydb = hal9000.MyDB()
    ping = hal9000.Ping()

    while True:
        ip = mydb.get_host_oldest_timestamp()
        result = ping.win_ping(ip[0])
        mydb.update_host_record(result)
        print('Delibrately wait 20s ...')
        hal9000.time.sleep(20)

def con_scan_os():
    '''
    should run after ping() since it scans only active ip.
    runtime estimate: 4h
    
    '''

    mydb = hal9000.MyDB()
    ipaddr = mydb.get_host_all_active()

    scanner = hal9000.Scanner()

    pool = Pool(10) #10 is preferd
    
    results = []
    for ip in ipaddr:
        results.append(pool.apply_async(scanner.scan_os, args=(ip[0],)))
    pool.close()
    pool.join()
    
    for result in results:
        mydb.update_host_record(result.get())
        print('Wrote %s' %(result.get()))

    print('All done.')
    
def non_scan_ports_tcp():
    '''
    should run after ping() because it scans only active ip.
    
    '''

    mydb = hal9000.MyDB()
    scanner = hal9000.Scanner()

    while True:
        ip = mydb.get_host_oldest_portchktime_active()
        result = scanner.scan_ports_tcp(ip[0])
        if result is not None:
            for record in result:
                mydb.update_service_record(record)
                print('Done with %s' %(record))
        rec = {'ip': ip[0], 'portchktime': int(hal9000.time.time())}
        mydb.update_host_record(rec)
        print('Done with %s' %(rec))

def non_scan_service_tcp():
    '''
    should run after scan_ports_tcp() because it scans only active ports.

    '''

    mydb = hal9000.MyDB()
    scanner = hal9000.Scanner()
    while True:
        record = mydb.get_service_tcp_oldest_timestamp_active()
        mydb.cursor.execute('UPDATE service SET timestamp=8888888888 WHERE ip="'+str(record[0])+'" and portid='+str(record[1]))
        mydb.conn.commit()
        result = scanner.scan_service_tcp(record[0],record[1])
        mydb.update_service_record(result)
        print(result)

##############################################################################

if __name__ == '__main__':
    non_scan_service_tcp()
