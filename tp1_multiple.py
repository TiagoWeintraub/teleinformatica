#!/usr/bin/python

from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.node import OVSKernelSwitch
from mininet.node import Node
import argparse

def myNetwork(n_sucursales):

    net = Mininet( topo=None, build=False, ipBase='192.168.100.0/24')

    info('\n*** Add switches')

    switches_s = []
    switches_ss = []

    for i in range(n_sucursales):
        switch_name = 's{}'.format(str(i+1))
        switch = net.addSwitch(switch_name, cls=OVSKernelSwitch, failMode='standalone')
        switches_s.append(switch)
        
        switch_name = 'ss{}'.format(str(i+1))
        switch = net.addSwitch(switch_name, cls=OVSKernelSwitch, failMode='standalone')
        switches_ss.append(switch)

    info('\n*** Add routers')
    
    rc = net.addHost('rc', ip="192.168.100.6") # Va de 0-7 y uso la última dirección utilizable
    rc.cmd('sysctl net.ipv4.ip_forward=1')
    
    routers = []
    for i in range(n_sucursales):
        router_name = f'r{i+1}'
        router = net.addHost(router_name, ip=f"192.168.100.{str(i*8+1)}")
        routers.append(router)
        routers[i].cmd('sysctl net.ipv4.ip_forward=1')

    info('\n*** Add hosts')
    hosts = []
    for i in range(n_sucursales):
        host_name = f'h{i+1}'
        host = net.addHost(host_name, ip=f"10.0.{str(i+1)}.254")
        hosts.append(host)

    info('\n*** Add links')
    for i in range(n_sucursales):
        net.addLink(rc,switches_s[i], intfName1=f'rcs{str(i+1)}-eth0', params1={'ip': f'192.168.100.{str(i*8+6)}/29'})
        net.addLink(routers[i], switches_s[i], intfName1=f'r{str(i+1)}s{str(i+1)}-eth0', params1={'ip': f'192.168.100.{str(i*8+1)}/29'})
        net.addLink(routers[i], switches_ss[i], intfName1=f'r{str(i+1)}ss{str(i+1)}-eth0', params1={'ip': f'10.0.{str(i+1)}.1/24'})
        net.addLink(hosts[i], switches_ss[i], intfName1=f'h{str(i+1)}ss{str(i+1)}-eth0', params1={'ip': f'10.0.{str(i+1)}.254/24'})

    info('\n*** Starting network ')
    net.build()

    info('\n*** Creating routes:')
    
    for i in range(n_sucursales):
        for x in range(n_sucursales):
            info(f'\n- from h{str(i+1)} to r{str(x+1)}', hosts[i].cmd(f'ip r add 192.168.100.{str(x*8)}/29 via 10.0.{str(i+1)}.1 dev h{str(i+1)}ss{str(i+1)}-eth0'))
            if x != i:
                info(f'\n- from h{str(i+1)} to h{str(i+1)}',hosts[i].cmd(f'ip r add 10.0.{str(x+1)}.0/24 via 10.0.{str(i+1)}.1 dev h{str(i+1)}ss{str(i+1)}-eth0'))
                info(f'\n- from r{str(i+1)} to r{str(x+1)}',routers[i].cmd(f'ip r add 192.168.100.{str(x*8)}/29 via 192.168.100.{str(i*8+6)} dev r{str(i+1)}s{str(i+1)}-eth0'))
                info(f'\n- from r{str(i+1)} to r{str(x+1)}',routers[i].cmd(f'ip r add 192.168.100.{str(x*8)}/29 via 192.168.100.{str(i*8+6)} dev r{str(i+1)}s{str(i+1)}-eth0'))
                info(f'\n- from r{i+1} to h{x+1}', routers[i].cmd(f'ip r add 10.0.{x+1}.0/24 via 192.168.100.{i*8+6} dev r{i+1}s{i+1}-eth0'))
        info(f'\n- from rc to h{str(i+1)}',rc.cmd(f'ip r add 10.0.{str(i+1)}.0/24 via 192.168.100.{str(i*8+1)} dev rcs{str(i+1)}-eth0'))
    
    # info('\n\n*** Starting controllers')
    for controller in net.controllers:
        controller.start()

    # info('\n*** Starting switches ')
    for s in switches_s:
        s.start([])
        
    for s in switches_ss:
        s.start([])
            
    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    parser = argparse.ArgumentParser(description="Ingrese la cantidad de sucursales: -n 'Cantidad de sucursales' ")
    parser.add_argument('-n', type=int, default=6, help='Cantidad de sucursales')
    args = parser.parse_args()
    setLogLevel('info')
    if args.n <= 32:
        myNetwork(args.n)
    else:
        print('No puede haber más de 32 sucursales')

'''
mininet> pingall
*** Ping: testing ping reachability
rc -> r1 r2 r3 r4 r5 r6 h1 h2 h3 h4 h5 h6 
r1 -> rc r2 r3 r4 r5 r6 h1 h2 h3 h4 h5 h6 
r2 -> rc r1 r3 r4 r5 r6 h1 h2 h3 h4 h5 h6 
r3 -> rc r1 r2 r4 r5 r6 h1 h2 h3 h4 h5 h6 
r4 -> rc r1 r2 r3 r5 r6 h1 h2 h3 h4 h5 h6 
r5 -> rc r1 r2 r3 r4 r6 h1 h2 h3 h4 h5 h6 
r6 -> rc r1 r2 r3 r4 r5 h1 h2 h3 h4 h5 h6 
h1 -> rc r1 r2 r3 r4 r5 r6 h2 h3 h4 h5 h6 
h2 -> rc r1 r2 r3 r4 r5 r6 h1 h3 h4 h5 h6 
h3 -> rc r1 r2 r3 r4 r5 r6 h1 h2 h4 h5 h6 
h4 -> rc r1 r2 r3 r4 r5 r6 h1 h2 h3 h5 h6 
h5 -> rc r1 r2 r3 r4 r5 r6 h1 h2 h3 h4 h6 
h6 -> rc r1 r2 r3 r4 r5 r6 h1 h2 h3 h4 h5 
*** Results: 0% dropped (156/156 received)
'''