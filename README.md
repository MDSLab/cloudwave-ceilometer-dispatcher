# CloudWave Ceiloesper Dispatcher
Openstack Ceilometer Dispatcher for the EU project CloudWave.

The CloudWave Ceiloesper Dispatcher is a Ceilometer dispatcher plugin runs on the OpenStack Ceilometer Collector and receives messages from all the CW Ceilometer Agents (cw-agent) running on the OpenStack compute nodes. This dispatcher is able to automatically filter data received by Ceilometer Collector and re-elaborate it in a new message in order to send only information that are really needed by CW Ceiloesper for analysis and event triggering taking into account which measurements and events are of interest for analysis and event triggering (context of interest).


CloudWave Ceiloesper Dispatcher (cw-dispatcher) has been tested to work on:

* Openstack Liberty
* CentOS 7.2 OS

##Installation guide
1. Requirements:
  * Disable Epel repositories and use centos-openstack-liberty
2. Log in (as root) machine where Openstack Ceilometer Collector it is installed 
3. Download the RPM package
  * wget https://github.com/MDSLab/cloudwave-ceilometer-dispatcher/raw/master/packages/cw-dispatcher-2.0-93.x86_64.rpm
4. Install the package:
  * rpm -Uvh cw-dispatcher-2.0-93.x86_64.rpm
  
##Configuration guide

1. Edit the "DEFAULT" and "dispatcher_ceiloesper" sections in /etc/ceilometer/ceilometer.conf on the Ceilometer Collector machine: 
```
[DEFAULT]
# Dispatcher to process data. (multi valued)
# Deprecated group/name - [collector]/dispatcher
dispatcher = database
dispatcher = ceiloesper

[dispatcher_ceiloesper]
url = http://<CEILOESPER-IP>:8080/cw-ceiloesper/cw/ceiloesper/monitoringEvent
cw_auth_url = http://<KEYSTONE-IP>:35357/v2.0
cw_username = admin
cw_tenant_name = admin
cw_password = <ADMIN-PASSWORD>
```

2. Enable the cw-dispatcher plugin in the Ceilometer Collector:
  * openstack-config --set /usr/lib/python2.7/site-packages/ceilometer-5.0.2-py2.7.egg-info/entry_points.txt ceilometer.dispatcher ceiloesper ceilometer.dispatcher.ceiloesper:CeiloesperDispatcher
3. Restart Ceilometer Collector:
  * systemctl restart openstack-ceilometer-collector



  
