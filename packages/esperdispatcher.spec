Name            : cw-dispatcher
Summary         : CloudWave Ceiloesper dispatcher - Y3
Version         : 2.0
Release 	: %{?BUILD_NUMBER}
License         : GPL
BuildArch       : x86_64
BuildRoot       : %{_tmppath}/%{name}-%{version}-root




# Use "Requires" for any dependencies, for example:
Requires        : python-heatclient


# Description gives information about the rpm package. This can be expanded up to multiple lines.
%description
CloudWave Ceiloesper dispatcher: CeiloesperDispatcher - Compliant with Openstack Liberty - Cloudwave Y3



# Prep is used to set up the environment for building the rpm package
%prep

# Used to compile and to build the source
%build



# The installation steps. 
%install
rm -rf $RPM_BUILD_ROOT
install -d -m 755 $RPM_BUILD_ROOT/usr/lib/python2.7/site-packages/ceilometer/dispatcher/
cp ../SOURCES/ceiloesper.py $RPM_BUILD_ROOT/usr/lib/python2.7/site-packages/ceilometer/dispatcher/.
cp ../SOURCES/database_cw.py $RPM_BUILD_ROOT/usr/lib/python2.7/site-packages/ceilometer/dispatcher/.


# Post installation steps
%post
echo -e "  Configuring:"

#1. Insert the new dispatcher in the ceilometer dispatcher list into entry_points.txt
python_home=`python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"`  #e.g: /usr/lib/python2.6/site-packages
%define python_home $python_home
entrypoints=`find %{python_home}"/ceilometer"* -name "entry_points.txt"`
%define entrypoints $entrypoints
newstr="ceiloesper = ceilometer.dispatcher.ceiloesper:CeiloesperDispatcher"
var=`cat %{entrypoints} | awk '{print $1}'| grep ceiloesper`
%define var $var
%define newstr $newstr


if [[ %{var} == %{newstr} ]]; then
        echo -e "\t CW Ceiloesper dispatcher already imported to entry_points.txt!"
else
	openstack-config --set %{entrypoints} ceilometer.dispatcher ceiloesper ceilometer.dispatcher.ceiloesper:CeiloesperDispatcher
	echo -e "\t CW Ceiloesper dispatcher added to entry_points.txt!"
fi



#2. Add cloudwave dispatcher to collector
conf=/etc/ceilometer/ceilometer.conf
%define conf $conf
newstr3="dispatcher=ceiloesper"
var3=`cat /etc/ceilometer/ceilometer.conf | awk '{print $1}'| grep dispatcher=ceiloesper`
%define var3 $var3
%define newstr3 $newstr3
if [[ %{var3} == %{newstr3} ]]; then
        echo -e "\t CW dispatcher already added to /etc/ceilometer/ceilometer.conf!"
else
	openstack-config --set /etc/ceilometer/ceilometer.conf DEFAULT dispatcher ceiloesper
	echo -e "\t CW dispatcher added to /etc/ceilometer/ceilometer.conf"
fi




#3. Insert configuration of dispatcher into /etc/ceilometer/ceilometer.conf
var2=`cat /etc/ceilometer/ceilometer.conf | awk '{print $1}'| grep dispatcher_ceiloesper`
%define var2 $var2
if [[ $var2 == "[dispatcher_ceiloesper]" ]]; then
	echo -e "\t CW Ceiloesper dispatcher already configured!"
else
	
	
	ceiloesper_ip=`cat /etc/hosts | grep ceiloesper | awk '{print $1}'`
	openstack-config --set /etc/ceilometer/ceilometer.conf dispatcher_ceiloesper url http://$ceiloesper_ip:8080/cw-ceiloesper/cw/ceiloesper/monitoringEvent
	openstack-config --set /etc/ceilometer/ceilometer.conf dispatcher_ceiloesper cw_auth_url $OS_AUTH_URL
	openstack-config --set /etc/ceilometer/ceilometer.conf dispatcher_ceiloesper cw_username $OS_USERNAME
	openstack-config --set /etc/ceilometer/ceilometer.conf dispatcher_ceiloesper cw_tenant_name $OS_TENANT_NAME
	openstack-config --set /etc/ceilometer/ceilometer.conf dispatcher_ceiloesper cw_password $OS_PASSWORD

	echo -e "\t CW Ceiloesper dispatcher configured!"
fi


#4. Patch the mongodb dispatcher
cp /usr/lib/python2.7/site-packages/ceilometer/dispatcher/database_cw.py /usr/lib/python2.7/site-packages/ceilometer/dispatcher/database.py
echo -e "\t MongoDB dispatcher patched!"

#5. Restart Ceilometer collector agent
#systemctl restart openstack-ceilometer-collector

echo -e "!!! FILL OUT the [dispatcher_ceiloesper] section in ceilometer.conf and restart openstack-ceilometer-collector !!!"


%postun
python_home=`python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"`
%define python_home $python_home
entrypoints=`find %{python_home}"/ceilometer"* -name "entry_points.txt"`
%define entrypoints $entrypoints
openstack-config --del %{entrypoints} ceilometer.dispatcher ceiloesper
openstack-config --del /etc/ceilometer/ceilometer.conf DEFAULT dispatcher ceiloesper
echo -e "ceilometer.conf and entry_points.txt cleaned!"


# Contains a list of the files that are part of the package
%files

%attr(755, root, -) /usr/lib/python2.7/site-packages/ceilometer/dispatcher/ceiloesper.py
/usr/lib/python2.7/site-packages/ceilometer/dispatcher/ceiloesper.py

%attr(755, root, -) /usr/lib/python2.7/site-packages/ceilometer/dispatcher/database_cw.py
/usr/lib/python2.7/site-packages/ceilometer/dispatcher/database_cw.py


# Used to store any changes between versions
%changelog



