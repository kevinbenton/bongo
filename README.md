# bongo
Bongo: A BGP Route Processor Built for Defending Against Bad Routes

## What is it?
Bongo is a program with a plugin architecture used to receive BGP
routes, decide whether or not each route is acceptable, and then
take action based on each route's acceptability.

There are two types of plugins: acceptors and reactors.

Acceptor plugins receive a BGP update in the form of 'prefix, next hop, AS path'
and decide whether or not the route should be accepted. The sample plugin
included references a country code mapping of ASNs and a policy of which
prefixes should be allowed to cross specific countries.

Reactor plugins are informed when a route is accepted or rejected by the
acceptor plugins (or are withdrawn from BGP). They can then take action
by distributing routes to downstream peers, setting up firewall rules, etc.

All plugins are available in bongo_bgp/plugins/ and plugins are loaded via
the command-line. Run 'bongo-route-processor --help' for syntax.

The plugins included can react to bad routes in two broad categories:
* Generating block rules to prevent traffic from using the route
* Stopping the propagation of the bad route

It can also use BGP information to perform other tasks like
IP spoofing preventions.


More information can be found on the motivation for these approaches in
the following papers:
[Bongo: A BGP Speaker Built for Defending Against Bad Routes](ftp://cs.indiana.edu/pub/techreports/TR723.pdf)
[Firewalling Scenic Routes: Preventing Data Exfiltration via Political and Geographic Routing Policies](http://dl.acm.org/citation.cfm?id=2994477)
[Filtering Source-Spoofed IP Traffic Using Feasible Path Reverse Path Forwarding with SDN](http://www.ijcce.org/vol5/471-N0002.pdf)


### Generating block rules to prevent traffic from using the route
See the 'Running firewalling demo' below


### Stopping the propagation of the bad route

This prevents routes from being propagated on to downstream peers with
selective BGP announcements.

See the 'Mitigating bad route propagation section' below.


### Dropping Source-Spoofed Traffic from a Peer
See the 'feasible path reverse path filtering' section below.


Running firewalling demo
========================
This demo will setup a topology of router1<->router2<->router3<->router4 using
local loopback addresses on a Linux environment (this was tested using Ubuntu 16.10).

router1 is the organization that wants to avoid using bad routes so it is using
Bongo.

router2, router3, and router4 are all just emulating normal BGP speakers by
periodically adding a withdrawing routes.

router4 will occasionally hijack a sub-prefix of one of router2's routes.
router1 (running bongo), will react to this by generating block rules while
router4 is advertising the route because it will violate the AS restrictions
in the policy file.

```
# install python prereqs
sudo apt-get install python-minimal python-pip

# clone exabgp to run
cd ~
git clone https://github.com/Exa-Networks/exabgp.git
cd exabgp
git checkout 3.4
sudo pip install -r requirements.txt

# add extra loopback addresses to act as different routers
sudo ip addr add 127.100.0.1/8 dev lo  # bongo router
sudo ip addr add 127.100.0.2/8 dev lo  # bongo peer
sudo ip addr add 127.100.0.3/8 dev lo  # intermediary
sudo ip addr add 127.100.0.4/8 dev lo  # evil router

# startup routing sessions
cd ~/bongo/
sudo python setup.py develop
for pid in $(ps -ef | grep 'sbin/exabgp' | grep -v grep | awk '{ print $2 }'); do
    kill $pid;
done
for i in {1..4}; do
screen -d -m -S router${i} env exabgp_tcp_port=1179 ~/exabgp/sbin/exabgp -e $(pwd)/configs_for_demos/firewalling_scenic_routes/127.100.0.${i}.env $(pwd)/configs_for_demos/firewalling_scenic_routes/127.100.0.${i}.conf
done
```

Once the processes are running, you can see the logged events:
```
tail -F logs/logged_events.log
```

For this demo bongo is being invoked in the following manner:
```
bongo-route-processor --acceptor bongo_bgp.plugins.route_acceptors.asn_country_check.ASNCountryCheck --reactor bongo_bgp.plugins.route_reactors.logger.LOGToFile
```

This loads up the asn_country_check plugin that determines if routes are acceptable.
The reactor plugin is just a logging plugin, but you can also load the iptables
and/or openflow reactor plugins to see how this can be used to block traffic in
a real system.


Mitigating bad route propagation demo
=====================================
This demo will setup a topology of router0<->router1<->router2<->router3<->router4
using local loopback addresses on a Linux environment (this was tested using
Ubuntu 16.10).

router1 is the organization that wants to avoid propagating bad routes so it is
using Bongo with the 'bongo_bgp.plugins.route_reactors.route_filter.FilteredAnnouncer'
plugin.

router2, router3, and router4 are all just emulating normal BGP speakers by
periodically adding a withdrawing routes.

router0 only receives routes to make it simple to see what it is receiving.

router4 will occasionally hijack a sub-prefix of one of router2's routes.
This will violate the loaded ASNCountryCheck acceptor plugin and
router1 (running bongo) will react to this by stopping the propagation
down to router0.

```
# install python prereqs
sudo apt-get install python-minimal python-pip

# clone exabgp to run
cd ~
git clone https://github.com/Exa-Networks/exabgp.git
cd exabgp
git checkout 3.4
sudo pip install -r requirements.txt

# add extra loopback addresses to act as different routers
sudo ip addr add 127.100.0.0/8 dev lo  # downstream router
sudo ip addr add 127.100.0.1/8 dev lo  # bongo router
sudo ip addr add 127.100.0.2/8 dev lo  # bongo peer
sudo ip addr add 127.100.0.3/8 dev lo  # intermediary
sudo ip addr add 127.100.0.4/8 dev lo  # evil router

# startup routing sessions
cd ~/bongo/
sudo python setup.py develop
for pid in $(ps -ef | grep 'sbin/exabgp' | grep -v grep | awk '{ print $2 }'); do
    kill $pid;
done
for i in {0..4}; do
screen -d -m -S router${i} env exabgp_tcp_port=1179 ~/exabgp/sbin/exabgp -e $(pwd)/configs_for_demos/stopping_route_propagation/127.100.0.${i}.env $(pwd)/configs_for_demos/stopping_route_propagation/127.100.0.${i}.conf
done
```

Once the processes are running, you can see the logged events from bongo on router1:
```
tail -F logs/logged_events.log
```

Join the router0 screen with to see the withdrawls of the /24 prefix on from router1:
```
screen -r router0
```
Disconnect from the session with 'ctrl-A d'


Feasible Path Reverse Path Filtering
====================================
In this topology we have router0<->router1 where router1 is providing many
BGP prefixes that will be converted into anti-spoofing rules and installed
into a local openvswitch bridge by router0 running bongo with the FPRPF reactor
plugin loaded.

Note in this scenario that Bongo is not being used to determine if a route is
bad so no 'acceptor' plugins are loaded. This just merely uses a 'reactor'
plugin to install filtering rules based on the incoming BGP stream.

So router0 is running bongo with the following command: 'bongo-route-processor --reactor bongo_bgp.plugins.route_reactors.fprpf.FPRPFReactor'

This demo requires OVS on the host and a filtering bridge of 'filter-br' setup.
The bridge specifics can be modified in the
'bongo_bgp.plugins.route_reactors.fprpf.FPRPFReactor' plugin.

```
# Ensure the bridge exists before starting:
sudo ovs-vsctl br-exists filter-br || add-br filter-br

# install python prereqs
sudo apt-get install python-minimal python-pip

# clone exabgp to run
cd ~
git clone https://github.com/Exa-Networks/exabgp.git
cd exabgp
git checkout 3.4
sudo pip install -r requirements.txt

# add extra loopback addresses to act as different routers
sudo ip addr add 127.100.0.0/8 dev lo  # bongo FPRPF instance
sudo ip addr add 127.100.0.1/8 dev lo  # upstream router issuing hundreds of routes

# startup routing sessions
cd ~/bongo/
sudo python setup.py develop
for pid in $(ps -ef | grep 'sbin/exabgp' | grep -v grep | awk '{ print $2 }'); do
    kill $pid;
done
for i in {0..1}; do
screen -d -m -S router${i} env exabgp_tcp_port=1179 ~/exabgp/sbin/exabgp -e $(pwd)/configs_for_demos/FPRPF/127.100.0.${i}.env $(pwd)/configs_for_demos/FPRPF/127.100.0.${i}.conf
done
```

You should now be able to see the new filtering flows being inserted on the bridge.


Sample output:
```
$ sudo ovs-ofctl dump-flows filter-br
NXST_FLOW reply (xid=0x4):
 cookie=0x0, duration=13.360s, table=0, n_packets=0, n_bytes=0, idle_age=13, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.26.0/24 actions=NORMAL
 cookie=0x0, duration=13.308s, table=0, n_packets=0, n_bytes=0, idle_age=13, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.28.0/24 actions=NORMAL
 cookie=0x0, duration=13.296s, table=0, n_packets=0, n_bytes=0, idle_age=13, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.32.0/24 actions=NORMAL
 cookie=0x0, duration=13.229s, table=0, n_packets=0, n_bytes=0, idle_age=13, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.22.0/24 actions=NORMAL
 cookie=0x0, duration=13.182s, table=0, n_packets=0, n_bytes=0, idle_age=13, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.38.0/24 actions=NORMAL
 cookie=0x0, duration=13.170s, table=0, n_packets=0, n_bytes=0, idle_age=13, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.48.0/24 actions=NORMAL
 cookie=0x0, duration=13.137s, table=0, n_packets=0, n_bytes=0, idle_age=13, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.36.0/24 actions=NORMAL
 cookie=0x0, duration=13.125s, table=0, n_packets=0, n_bytes=0, idle_age=13, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.30.0/24 actions=NORMAL
 cookie=0x0, duration=13.103s, table=0, n_packets=0, n_bytes=0, idle_age=13, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.34.0/24 actions=NORMAL
 cookie=0x0, duration=13.092s, table=0, n_packets=0, n_bytes=0, idle_age=13, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.24.0/24 actions=NORMAL
 cookie=0x0, duration=13.082s, table=0, n_packets=0, n_bytes=0, idle_age=13, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.18.0/24 actions=NORMAL
 cookie=0x0, duration=13.028s, table=0, n_packets=0, n_bytes=0, idle_age=13, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.40.0/24 actions=NORMAL
 cookie=0x0, duration=13.005s, table=0, n_packets=0, n_bytes=0, idle_age=13, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.30.0/24 actions=NORMAL
 cookie=0x0, duration=12.973s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.34.0/24 actions=NORMAL
 cookie=0x0, duration=12.961s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.44.0/24 actions=NORMAL
 cookie=0x0, duration=12.929s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.20.0/24 actions=NORMAL
 cookie=0x0, duration=12.918s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.16.0/24 actions=NORMAL
 cookie=0x0, duration=12.882s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.42.0/24 actions=NORMAL
 cookie=0x0, duration=12.854s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.46.0/24 actions=NORMAL
 cookie=0x0, duration=12.831s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.28.0/24 actions=NORMAL
 cookie=0x0, duration=12.640s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.36.0/24 actions=NORMAL
 cookie=0x0, duration=12.625s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.26.0/24 actions=NORMAL
 cookie=0x0, duration=12.611s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.32.0/24 actions=NORMAL
 cookie=0x0, duration=12.595s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.38.0/24 actions=NORMAL
 cookie=0x0, duration=12.577s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.24.0/24 actions=NORMAL
 cookie=0x0, duration=12.235s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.12.0/24 actions=NORMAL
 cookie=0x0, duration=12.223s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.6.0/24 actions=NORMAL
 cookie=0x0, duration=12.214s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.16.0/24 actions=NORMAL
 cookie=0x0, duration=12.199s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.22.0/24 actions=NORMAL
 cookie=0x0, duration=12.187s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.28.0/24 actions=NORMAL
 cookie=0x0, duration=12.177s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.36.0/24 actions=NORMAL
 cookie=0x0, duration=12.167s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.42.0/24 actions=NORMAL
 cookie=0x0, duration=12.157s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.48.0/24 actions=NORMAL
 cookie=0x0, duration=12.138s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.38.0/24 actions=NORMAL
 cookie=0x0, duration=12.126s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.8.0/24 actions=NORMAL
 cookie=0x0, duration=12.114s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.48.0/24 actions=NORMAL
 cookie=0x0, duration=12.102s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.10.0/24 actions=NORMAL
 cookie=0x0, duration=12.090s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.14.0/24 actions=NORMAL
 cookie=0x0, duration=12.079s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.20.0/24 actions=NORMAL
 cookie=0x0, duration=12.066s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.10.0/24 actions=NORMAL
 cookie=0x0, duration=12.054s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.8.0/24 actions=NORMAL
 cookie=0x0, duration=12.043s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.40.0/24 actions=NORMAL
 cookie=0x0, duration=12.031s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.40.0/24 actions=NORMAL
 cookie=0x0, duration=12.019s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.18.0/24 actions=NORMAL
 cookie=0x0, duration=12.007s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.0.0/24 actions=NORMAL
 cookie=0x0, duration=11.997s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.2.0/24 actions=NORMAL
 cookie=0x0, duration=11.985s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.14.0/24 actions=NORMAL
 cookie=0x0, duration=11.972s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.26.0/24 actions=NORMAL
 cookie=0x0, duration=11.959s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.16.0/24 actions=NORMAL
 cookie=0x0, duration=11.948s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.22.0/24 actions=NORMAL
 cookie=0x0, duration=11.935s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.32.0/24 actions=NORMAL
 cookie=0x0, duration=11.923s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.4.0/24 actions=NORMAL
 cookie=0x0, duration=11.911s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.42.0/24 actions=NORMAL
 cookie=0x0, duration=11.899s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.46.0/24 actions=NORMAL
 cookie=0x0, duration=11.888s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.2.0/24 actions=NORMAL
 cookie=0x0, duration=11.876s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.24.0/24 actions=NORMAL
 cookie=0x0, duration=11.862s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.6.0/24 actions=NORMAL
 cookie=0x0, duration=11.850s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.20.0/24 actions=NORMAL
 cookie=0x0, duration=11.838s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.18.0/24 actions=NORMAL
 cookie=0x0, duration=11.829s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.12.0.0/24 actions=NORMAL
 cookie=0x0, duration=11.806s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.12.0/24 actions=NORMAL
 cookie=0x0, duration=11.795s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.30.0/24 actions=NORMAL
 cookie=0x0, duration=11.785s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.34.0/24 actions=NORMAL
 cookie=0x0, duration=11.762s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.44.0/24 actions=NORMAL
 cookie=0x0, duration=11.752s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.4.4.0/24 actions=NORMAL
 cookie=0x0, duration=11.013s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.34.0/24 actions=NORMAL
 cookie=0x0, duration=11.002s, table=0, n_packets=0, n_bytes=0, idle_age=11, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.38.0/24 actions=NORMAL
 cookie=0x0, duration=10.992s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.40.0/24 actions=NORMAL
 cookie=0x0, duration=10.969s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.4.0/24 actions=NORMAL
 cookie=0x0, duration=10.948s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.44.0/24 actions=NORMAL
 cookie=0x0, duration=10.936s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.3.48.0/24 actions=NORMAL
 cookie=0x0, duration=10.925s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.20.0/24 actions=NORMAL
 cookie=0x0, duration=10.911s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.16.0/24 actions=NORMAL
 cookie=0x0, duration=10.900s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.42.0/24 actions=NORMAL
 cookie=0x0, duration=10.890s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.8.0/24 actions=NORMAL
 cookie=0x0, duration=10.879s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.48.0/24 actions=NORMAL
 cookie=0x0, duration=10.868s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.22.0/24 actions=NORMAL
 cookie=0x0, duration=10.858s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.26.0/24 actions=NORMAL
 cookie=0x0, duration=10.845s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.28.0/24 actions=NORMAL
 cookie=0x0, duration=10.835s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.44.0/24 actions=NORMAL
 cookie=0x0, duration=10.823s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.32.0/24 actions=NORMAL
 cookie=0x0, duration=10.799s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.36.0/24 actions=NORMAL
 cookie=0x0, duration=10.787s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.46.0/24 actions=NORMAL
 cookie=0x0, duration=10.775s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.14.0/24 actions=NORMAL
 cookie=0x0, duration=10.763s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.18.0/24 actions=NORMAL
 cookie=0x0, duration=10.752s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.24.0/24 actions=NORMAL
 cookie=0x0, duration=10.742s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.12.0/24 actions=NORMAL
 cookie=0x0, duration=10.730s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.10.0/24 actions=NORMAL
 cookie=0x0, duration=10.705s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.30.0/24 actions=NORMAL
 cookie=0x0, duration=10.695s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.6.0/24 actions=NORMAL
 cookie=0x0, duration=10.681s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.46.0/24 actions=NORMAL
 cookie=0x0, duration=10.980s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.2.0.0/22 actions=NORMAL
 cookie=0x0, duration=10.958s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.7.0.0/20 actions=NORMAL
 cookie=0x0, duration=10.810s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.9.0.0/18 actions=NORMAL
 cookie=0x0, duration=10.718s, table=0, n_packets=0, n_bytes=0, idle_age=10, priority=10,ip,dl_dst=00:11:22:33:44:55,nw_dst=10.3.0.0/19 actions=NORMAL
 cookie=0x0, duration=12.865s, table=0, n_packets=0, n_bytes=0, idle_age=12, priority=5,dl_dst=00:11:22:33:44:55 actions=drop
```

In the last line above you can see where leaky compression was used by allowing the entire
10.3.0.0/19 block to fit into the configured 100 flow limit for the table. More details
can be found in the filtering paper on the reasoning behind this feature.
