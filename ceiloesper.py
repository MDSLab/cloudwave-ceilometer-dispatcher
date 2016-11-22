# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

#
# Author: Nicola Peditto <npeditto@unime.it> - University of Messina (UniMe) - 2014 2015 2016
#


import os
import json
import httplib2
import logging
import logging.handlers
import time
import calendar

import keystoneclient.v2_0.client as ksclient
import heatclient.client as heatc

#from oslo.utils import timeutils
from oslo_log import log
from oslo_config import cfg
from datetime import *
from ceilometer import dispatcher











#Get configuration parameters from /etc/ceilometer/ceilometer.conf
ceiloesper_dispatcher_opts = [
    cfg.StrOpt('url',
               default=None,
               help='REST URL to send measures'),
    cfg.StrOpt('cw_auth_url',
               default=None,
               help='Authetication URL for Keystone'),
    cfg.StrOpt('cw_username',
               default=None,
               help='Username for Keystone'),
    cfg.StrOpt('cw_tenant_name',
               default=None,
               help='Tenant name for Keystone'),
    cfg.StrOpt('cw_password',
               default=None,
               help='Password for Keystone'),
]

cfg.CONF.register_opts(ceiloesper_dispatcher_opts, group="dispatcher_ceiloesper")



#Init Openstack Log system
LOG = log.getLogger(__name__)


ENV_HEAT_OS_API_VERSION = "1"
ENV_OS_AUTH_URL = cfg.CONF.dispatcher_ceiloesper.cw_auth_url
ENV_OS_USERNAME = cfg.CONF.dispatcher_ceiloesper.cw_username
ENV_OS_TENANT_NAME = cfg.CONF.dispatcher_ceiloesper.cw_tenant_name
ENV_OS_PASSWORD = cfg.CONF.dispatcher_ceiloesper.cw_password



#CloudWave dispatcher for Ceiloesper communication
class CeiloesperDispatcher(dispatcher.Base):
    '''Dispatcher class for recording metering data to Ceiloesper CEP engine.

    The dispatcher class which logs each meter into a file configured in
    ceilometer configuration file. An example configuration may look like the
    following:

    [dispatcher_ceiloesper]
    url=http://192.168.1.255:9999/ceiloesper/post

    To enable this dispatcher, the following section needs to be present in
    ceilometer.conf file

    [collector]
    dispatchers = ceiloesper
    '''


    def __init__(self, conf):
        
        LOG.info('CW -> CEILOESPER DISPATCHER')
        """
        ENV_HEAT_OS_API_VERSION = "1"
	ENV_OS_AUTH_URL = cfg.CONF.dispatcher_ceiloesper.cw_auth_url
        ENV_OS_USERNAME = cfg.CONF.dispatcher_ceiloesper.cw_username
        ENV_OS_TENANT_NAME = cfg.CONF.dispatcher_ceiloesper.cw_tenant_name
        ENV_OS_PASSWORD = cfg.CONF.dispatcher_ceiloesper.cw_password
      	"""
	LOG.info('CW -> CEILOESPER DISPATCHER\nKeystone credentials:\n\tAUTH_URL: %s\n\tUSERNAME: %s\n\tTENANT_NAME: %s\n\tPASSWORD: %s',ENV_OS_AUTH_URL, ENV_OS_USERNAME, ENV_OS_TENANT_NAME, ENV_OS_PASSWORD)
      
        super(CeiloesperDispatcher, self).__init__(conf)
        
        # HEAT CLIENT #######################################################################
        LOG.info('CW -> HEAT CLIENT INITIALIZATION STARTED!')

        keystone = ksclient.Client(
                auth_url=ENV_OS_AUTH_URL,
                username=ENV_OS_USERNAME,
                password=ENV_OS_PASSWORD,
                tenant_name= ENV_OS_TENANT_NAME
        )

        
        for y in keystone.services.list():
                if y.name == 'heat':
                    	heat_service_id = y.id
			LOG.info('HEAT heat_service_id: %s', heat_service_id)
    
        for z in keystone.endpoints.list():
                if z.service_id == heat_service_id:
                    	heat_endpoint = z.internalurl
    			LOG.info('HEAT heat_endpoint PRE: %s', heat_endpoint)
        # % changes to $ in different openstack versions
        
	self.init_endpoint = heat_endpoint 
	heat_endpoint = heat_endpoint.replace('%(tenant_id)s', keystone.project_id)
        #heat_endpoint = heat_endpoint.replace('$(tenant_id)s', keystone.project_id)

	LOG.info('HEAT heat_endpoint POST: %s', heat_endpoint)

        self.heat = heatc.Client(
                ENV_HEAT_OS_API_VERSION,
                endpoint = heat_endpoint,
                token = keystone.auth_token
        )
        self.instances = {}
    
        #INIT instances' cache
        self.makeCache()


        m_inst=json.dumps(self.instances, sort_keys=True, indent=4, separators=(',', ': '))
        LOG.info('\nCW -> Resource IDs Heat list [ResourceID : StackID] UPDATED: \n%s', str(m_inst))
    
        LOG.info('CW -> HEAT CLIENT INITIALIZATION COMPLETED!')    
        # HEAT CLIENT #######################################################################


    def makeCache(self):
        ''' Make instances' cache '''
	"""
        for stack in self.heat.stacks.list(global_tenant=True):
                for res in self.heat.resources.list(stack.id):
			LOG.info('RESOURCES in HEAT: %s', res)
			if res.resource_type == "OS::Nova::Server":
                        	self.instances[res.physical_resource_id] = stack.id
	"""

        for stack in self.heat.stacks.list(global_tenant=True):
                #fstack=json.dumps(stack, sort_keys=True, indent=4, separators=(',', ': '))
                LOG.info('\n\n\nStack: %s - Project: %s\n\n', stack.stack_name, stack.project)
                temp_endpoint = self.init_endpoint.replace('%(tenant_id)s', stack.project )
                #heat_endpoint = heat_endpoint.replace('$(tenant_id)s', stack.project )
                LOG.info('HEAT heat_endpoint TEMP: %s', temp_endpoint)

                keystone_temp = ksclient.Client(
                        auth_url=ENV_OS_AUTH_URL,
                        username=ENV_OS_USERNAME,
                        password=ENV_OS_PASSWORD,
                        tenant_id=stack.project
                )


                heat_temp = heatc.Client(
                        ENV_HEAT_OS_API_VERSION,
                        endpoint = temp_endpoint,
                        token = keystone_temp.auth_token
                )
                for res in heat_temp.resources.list(stack.id):
                        LOG.info('RESOURCES in HEAT: %s', res)
                        if res.resource_type == "OS::Nova::Server":
                                self.instances[res.physical_resource_id] = stack.id





    def checkCache(self, inst_uuid):    
        ''' 
        Check if the instance is cached 
        @param    inst_uuid:    instance uuid to check
        '''
        if inst_uuid not in self.instances :

          try:
 
	    if self.instances[str(inst_uuid)] != None:
	     
            	LOG.info('CW -> INSTANCE not in cache!')
            	self.makeCache()
            
            	if inst_uuid not in self.instances:
               		LOG.info('CW -> INSTANCE without StackID! NO cached!!!')
			self.instances[str(inst_uuid)] = None
                	return False
            	else:
                	m_inst=json.dumps(self.instances, sort_keys=True, indent=4, separators=(',', ': '))
                	LOG.info('\nCW -> Resource IDs Heat list [ResourceID : StackID] UPDATED: \n%s', str(m_inst))
                	LOG.info('CW -> NEW INSTANCE: CACHED!')
                	return True
          except:
		LOG.debug('CW -> INSTANCE SKIPPED!') 

        else:
            LOG.debug('CW -> INSTANCE in cache!')
            return True



    def sendMeasure(self, data=None):
        ''' 
        REST Client to send measures to Ceiloesper 
        @param    data:    Json message with the measure
        '''
        LOG.info("CW -> MEASURE SENT TO CEILOESPER: \n%s\n", data)
        url=self.conf.dispatcher_ceiloesper.url
        http = httplib2.Http()
        response, send=http.request(url,"POST",body=data)
        result=json.dumps(response, sort_keys=True, indent=4, separators=(',', ': '))
        #LOG.debug("CW -> CEIOESPER RESPONSE: %s", send)
        #LOG.info("\nCW -> CEIOESPER RESULT: \n%s", result)
        #meterdata=json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))



    def record_metering_data(self, data):
    
        # We may have receive only one counter on the wire
        if not isinstance(data, list):
            data = [data]

        #If there are more samples in a messagge
        for meter in data:    
        
	    #TO SEE ALL METRICS ARE COMING TO COLLECTOR
	    result=json.dumps(meter, sort_keys=True, indent=4, separators=(',', ': '))
	    #LOG.info("CW -> GLOBAL METRIC: %s", result)

	    if meter['user_id'] == None:

		#COMPUTE MONITOR AND HARDWARE METERS

		#LOG.info('CW -> COMPUTE MONITOR METRIC %s from %s: not forwarded!!!', meter['counter_name'], meter['resource_id'])
                LOG.info("CW -> CENTRAL-COMPUTE METER: %s", result)

		# FOR SNMP HARDWARE METRICS OF EACH COMPUTE NODE
		if meter['source'] == "hardware":

                	#LOG.info("CW -> HARDWARE METRIC: %s", result)
			LOG.info("CW -> HARDWARE METRIC: HOST %s - %s - %s %s", meter['resource_id'], meter['counter_name'], str(meter['counter_volume']), meter['counter_unit'])
            		#result=json.dumps(meter, sort_keys=True, indent=4, separators=(',', ': '))
            		#LOG.info("CW -> FULL HARDWARE METRIC: %s", result)

			meter_name = meter['counter_name']
			meter_compute = meter['resource_id']
			meter_volume = str(meter['counter_volume'])
                        meter_unit=meter['counter_unit']
			meter_hw_metadata = "hardware"
			meter_timestamp = calendar.timegm(datetime.strptime(meter['timestamp'], '%Y-%m-%dT%H:%M:%S.%f').timetuple()) # Y3
                        esper_data='{"applicationId":"None","probe_inst":"None","name":"'+meter_name+'","volume":"'+meter_volume+'","metadata":"'+meter_hw_metadata+'","unit":"'+meter_unit+'","timestamp":"'+str(meter_timestamp)+'","source":"'+meter_compute+'", "vlan_ip":"None", "host_id":"None"}'

                        self.sendMeasure(esper_data)
		
		# FOR THE METRICS COLLECTED BY MONITOR PLUGINS AND CENTRAL POLLSTERS (BOTH CREATED BY CEILOMETER CENTRAL AGENT)
		elif meter['source'] == "openstack":

			LOG.info("CW -> COMPUTE METRIC: %s - %s - %s %s", meter['resource_id'], meter['counter_name'], str(meter['counter_volume']), meter['counter_unit'])
			
			# TO FORWARD TO CEILOESPER ONLY "vlan.bandwidth" METRICS
			if meter['counter_name'] == "vlan.bandwidth":
				result=json.dumps(meter, sort_keys=True, indent=4, separators=(',', ': '))
                                LOG.debug("CW -> VLAN bandwidth: %s", result)

			if meter['counter_name'] == "host.avg_packetloss":

				result=json.dumps(meter, sort_keys=True, indent=4, separators=(',', ': '))
                        	LOG.info("CW -> VLAN METRIC: %s", result)				

				meter_name=meter['counter_name']
				meter_volume=str(meter['counter_volume'])
				meter_unit=meter['counter_unit']
				user_data="ceilometer"
                		#meter_timestamp=calendar.timegm(datetime.strptime(meter['timestamp'], '%Y-%m-%d %H:%M:%S.%f').timetuple()) # Y2
				meter_timestamp=calendar.timegm(datetime.strptime(meter['timestamp'], '%Y-%m-%dT%H:%M:%S.%f').timetuple()) # Y3
				#LOG.debug("CW -> MONITOR MSG TIMESTAMP: %s", meter_timestamp)
				meter_resource_id=meter['resource_id']
				meter_payload=meter['resource_metadata'].get('payload')
				meter_stackid=meter_payload.get('stack_id')   #stackID inserted by cloudwave

                		esper_data='{"applicationId":"'+meter_stackid+'","probe_inst":"None","name":"'+meter_name+'","volume":"'+meter_volume+'","metadata":"'+str(user_data)+'","unit":"'+meter_unit+'","timestamp":"'+str(meter_timestamp)+'","source":"APPLICATION", "vlan_ip":"'+meter_resource_id+'", "host_id":"None"}'

                		self.sendMeasure(esper_data)

			if meter['counter_name'] == "hardware.network.outgoing.bytes.rate":
                                result=json.dumps(meter, sort_keys=True, indent=4, separators=(',', ': '))
                                LOG.info("CW -> OUTGOING B/s METRIC: %s", result)

	                        meter_name = "cw-bandwidth"
        	                meter_compute = meter['resource_id']
                	        meter_volume = str(meter['counter_volume'])
				meter_bandwidth = meter['counter_volume']*8/1000000;
                	        meter_unit=meter['counter_unit']
                       		meter_hw_metadata = "hardware"
	                        meter_timestamp = calendar.timegm(datetime.strptime(meter['timestamp'], '%Y-%m-%dT%H:%M:%S.%f').timetuple()) # Y3
				
				#meter_CM_stackid="5ce549cd-5fe2-49ec-9e06-71f18e89e6d9" #Y3 demo hardcoding
        	                #esper_data='{"applicationId":"'+meter_CM_stackid+'","probe_inst":"None","name":"'+meter_name+'","volume":"'+meter_volume+'","metadata":"'+meter_hw_metadata+'","unit":"'+meter_unit+'","timestamp":"'+str(meter_timestamp)+'","source":"'+meter_compute+'", "vlan_ip":"None", "host_id":"None"}'

				esper_data='{"applicationId":"None","probe_inst":"None","name":"'+meter_name+'","volume":"'+meter_volume+'","metadata":"'+meter_hw_metadata+'","unit":"'+meter_unit+'","timestamp":"'+str(meter_timestamp)+'","source":"'+meter_compute+'", "vlan_ip":"None", "host_id":"None"}'

				LOG.info("CW -> CW-BANDWIDTH for %s: %s Mbps", meter_compute, str(meter_bandwidth) )
                                self.sendMeasure(esper_data)

		else:
			LOG.info("CW -> COMPUTE METRIC USELESS")			


	    else:
	      
	      	#INSTANCES METRICS (Openstack and CloudWave)

		#LOG.info("CW -> INSTANCE METRIC: %s", meter)

		meter_inst_uuid=meter['resource_id']
		meter_stackid=meter['resource_metadata'].get('stack_id')   #stackID inserted by cloudwave
		meter_hostid=meter['resource_metadata'].get('host')
		meter_inst_name=meter['resource_metadata'].get('display_name')
		meter_name=meter['counter_name']

		LOG.info("CW ---> INSTANCE METRIC %s FROM %s", meter_name, meter_inst_uuid)# meter_inst_name)

		meter_volume=str(meter['counter_volume'])
		meter_unit=meter['counter_unit']

		#TIMESTAMP CONVERSION TO MILLISECONDS
		meter_timestamp=meter['timestamp']
		try:
			#meter_timestamp=calendar.timegm(datetime.strptime(meter_timestamp, '%Y-%m-%dT%H:%M:%SZ').timetuple()) # Y2
			meter_timestamp=calendar.timegm(datetime.strptime(meter_timestamp, '%Y-%m-%dT%H:%M:%S.%f').timetuple()) # Y3
          		#LOG.info("CW -> VM MSG TIMESTAMP conversion: %s -> %s", meter['timestamp'], meter_timestamp) 
		except:
			meter_timestamp=calendar.timegm(datetime.strptime(meter_timestamp, '%Y-%m-%d %H:%M:%S.%f').timetuple()) # Y3

		# FOR TUNNELLED CLOUDWAVE METRICS
                if meter['resource_metadata'].get('nested_uuid'):
                	nested_uuid=meter['resource_metadata'].get("nested_uuid")
			if self.checkCache(nested_uuid):
				meter_stackid = self.instances[nested_uuid]            #stackID from HEAT

				if meter_stackid != meter['resource_metadata'].get('stack_id'):
					LOG.info("CW -> CLOUDWAVE TUNNELLED METRIC generated by %s of a DIFFERENT stack: %s. (Sent by %s).", nested_uuid, meter_stackid, meter_inst_name)
				else:
					LOG.info("CW -> CLOUDWAVE TUNNELLED METRIC generated by %s of the SAME stack: %s. (Sent by %s).", nested_uuid, meter_stackid, meter_inst_name)

                        meter_inst_uuid = str(nested_uuid)

		# FOR CLOUDWAVE APPLICATION METRICS
		if meter_stackid:

		    if meter['resource_metadata'].get('nested_uuid'):
			# ALREADY FILTERED in the previous section "FOR TUNNELLED CLOUDWAVE METRIC"
			#LOG.info('CW -> CLOUDWAVE METRIC %s from VM %s with stack_id: %s', meter_name, meter_inst_uuid, meter_stackid)
			pass
		    else:
		    	LOG.info('CW -> CLOUDWAVE METRIC %s from VM %s (%s) with stack_id: %s', meter_name, meter_inst_name, meter_inst_uuid, meter_stackid)

		    if meter['resource_metadata'].get('user_supplied'):
		    	user_data=json.dumps(meter['resource_metadata'].get('user_supplied'))
		    	user_data=user_data.replace('"',"'")
		    else:
		    	user_data="ceilometer"

		    #LOG.info('CW -> CloudWave user metadata: %s', user_data)
			
		    esper_data='{"applicationId":"'+meter_stackid+'","probe_inst":"'+meter_inst_uuid+'","name":"'+meter_name+'","volume":"'+meter_volume+'","metadata":"'+str(user_data)+'","unit":"'+meter_unit+'","timestamp":"'+str(meter_timestamp)+'","source":"VM", "vlan_ip":"None", "host_id":"'+meter_hostid+'"}'

		    self.sendMeasure(esper_data)

		else:

		    # OPENSTACK METRICS THAT COME FROM CEILOMETER POLLSTERS

		    # TO collect Openstack network metrics
		    net_inst_id=meter_inst_uuid.split('-', 1 )[0]
		    if net_inst_id == "instance":
			net_inst_id=meter_inst_uuid.split('-', 2 )
			meter_inst_uuid = net_inst_id[2].rsplit('-', 2 )[0]
			LOG.info('CW -> CEILOMETER NETWORK METRIC: %s - %s', meter_inst_uuid, meter_name)
			

		    # CHECK IF THE VM IS DEPLOYED WITH HEAT
		    if self.checkCache(meter_inst_uuid):

			#LOG.info('CW -> CEILOMETER POLLSTER METRIC (%s) from VM %s deployed with HEAT! %s', meter_name, meter_inst_name, meter_inst_uuid)
			LOG.info('CW -> CEILOMETER POLLSTER METRIC (%s) from VM %s deployed with HEAT!', meter_name, meter_inst_uuid)
			
			inst_stackid=self.instances[meter_inst_uuid]            #stackID from HEAT
			
			#FOR DEFUALT CEILOMETER METRICS
			if meter_hostid == None:
                        	meter_hostid = "None"

			esper_data='{"applicationId":"'+inst_stackid+'","probe_inst":"'+meter_inst_uuid+'","name":"'+meter_name+'","volume":"'+meter_volume+'","metadata":"ceilometer","unit":"'+meter_unit+'","timestamp":"'+str(meter_timestamp)+'","source":"VM", "vlan_ip":"None", "host_id":"'+meter_hostid+'"}'

			self.sendMeasure(esper_data)
		    
		    else:
			LOG.info('CW -> %s VM %s is a standard VM! No sent to Ceiloesper!!!', meter_inst_uuid, meter_inst_name)


    def record_events(self, events):
        #LOG.debug('CW -> CEILOESPER record events')
        return []