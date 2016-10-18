# cloudwave-ceilometer-dispatcher
Openstack Ceilometer Dispatcher for the EU project CloudWave.

The CW Ceiloesper Dispatcher is a Ceilometer dispatcher plugin runs on the OpenStack Ceilometer Collector and receives messages from all the CW Ceilometer Agents (cw-agent) running on the OpenStack compute nodes. This dispatcher is able to automatically filter data received by Ceilometer Collector and re-elaborate it in a new message in order to send only information that are really needed by CW Ceiloesper for analysis and event triggering taking into account which measurements and events are of interest for analysis and event triggering (context of interest).
