# coding=utf-8
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
from builtins import object

import pprint
import re
from urllib.parse import urljoin
import requests
import simplejson
import tortilla
import ssl
from . import config
from . import mapping
from . import exception
standard_library.install_aliases()

standard_library.install_aliases()

# Global variable


class Base(object):
    '''Abstract class to manage types (Chassis, Servers etc...).'''
    def __init__(self, url, connection_parameters):
        '''Class constructor'''
        global TORTILLADEBUG
        self.connection_parameters = connection_parameters  # Uggly hack
        self.url = url
        self.api_url = tortilla.wrap(url, debug=config.TORTILLADEBUG)

        config.logger.debug(
            "------------------------------------------------------------")
        config.logger.debug("Url: %s" % url)
        config.logger.debug("Header: %s" % connection_parameters.headers)
        config.logger.debug(
            "------------------------------------------------------------")

        try:
            self.data = self.api_url.get(
                verify=connection_parameters.verify_cert,
                headers=connection_parameters.headers)
        except (requests.ConnectionError, ssl.SSLError) as e:
            # Log and transmit the exception.
            config.logger.info('Raise a RedfishException to upper level')
            msg = 'Connection error : {}\n'.format(e)
            raise exception.ConnectionFailureException(msg)
        except simplejson.scanner.JSONDecodeError as e:
            # Log and transmit the exception.
            config.logger.info('Raise a RedfishException to upper level')
            msg = \
                'Ivalid content : Content does not appear to be a valid ' + \
                'Redfish json\n'
            raise exception.InvalidRedfishContentException(msg)
        config.logger.debug(pprint.PrettyPrinter(indent=4).pformat(self.data))

    def get_link_url(self, link_type):
        '''Need to be explained.

        :param parameter_name: name of the parameter
        :returns:  string -- parameter value
        '''
        self.links = []

        # Manage standard < 1.0
        if float(mapping.redfish_version) < 1.00:
            links = getattr(self.data, mapping.redfish_mapper.map_links())
            if link_type in links:
                return urljoin(
                    self.url,
                    links[link_type][mapping.redfish_mapper.map_links_ref()])
            raise AttributeError
        else:
            links = getattr(self.data, link_type)
            link = getattr(links, mapping.redfish_mapper.map_links_ref())
            return urljoin(self.url, link)

    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, url):
        self.__url = url

    def get_parameter(self, parameter_name):
        '''Generic function to get a specific parameter

        :param parameter_name: name of the parameter
        :returns:  string -- parameter value

        '''
        try:
            return self.data[parameter_name]
        except:
            return 'Parameter does not exist'

    def get_parameters(self):
        '''Generic function to get all parameters

        :returns:  string -- parameter value

        '''
        try:
            return self.data
        except:
            return -1

    def set_parameter(self, parameter_name, value):
        '''Generic function to set a specific parameter

        :param parameter_name: name of the parameter
        :param value: value to set
        :returns:   string -- http response of PATCH request

        '''
        # Craft the request
        action = dict()
        action[parameter_name] = value
        config.logger.debug(action)

        # Perform the POST action
        config.logger.debug(self.api_url)
        response = self.api_url.patch(
            verify=self.connection_parameters.verify_cert,
            headers=self.connection_parameters.headers,
            data=action)
        return response

    def get_name(self):
        '''Get root name

        :returns:  string -- root name or "Not available"

        '''
        try:
            return self.data.Name
        except AttributeError:
            return "Not available"


class BaseCollection(Base):
    '''Abstract class to manage collection (Chassis, Servers etc...).'''
    def __init__(self, url, connection_parameters):
        super(BaseCollection, self).__init__(url, connection_parameters)

        self.links = []

        # linksmembers = self.data.Links.Members
        # linksmembers = self.data.links.Member
        if float(mapping.redfish_version) < 1.00:
            linksmembers = getattr(
                self.data, mapping.redfish_mapper.map_links())
            linksmembers = getattr(
                linksmembers, mapping.redfish_mapper.map_members())
        else:
            linksmembers = getattr(
                self.data, mapping.redfish_mapper.map_members())
        for link in linksmembers:
            # self.links.append(getattr(link,'@odata.id'))
            # self.links.append(getattr(link,'href'))
            self.links.append(urljoin(
                self.url, getattr(
                    link, mapping.redfish_mapper.map_links_ref())))

        config.logger.debug(self.links)


class Device(Base):
    '''Abstract class to add common methods between devices
    (Chassis, Servers, System).
    '''
    def get_uuid(self):
        '''Get device uuid

        :returns: device uuid or "Not available"
        :rtype: string

        '''
        try:
            return self.data.UUID
        except AttributeError:
            return "Not available"

    def get_status(self):
        '''Get device status

        :returns: device status or "Not available"
        :rtype: dict

        '''
        try:
            return self.data.Status
        except AttributeError:
            return "Not available"

    def get_model(self):
        '''Get device model

        :returns: device model or "Not available"
        :rtype: string

        '''
        try:
            return self.data.Model
        except AttributeError:
            return "Not available"

    def get_manufacturer(self):
        '''Get device manufacturer

        :returns: device manufacturer or "Not available"
        :rtype: string

        '''
        try:
            return self.data.Manufacturer
        except AttributeError:
            return "Not available"

    def get_serial_number(self):
        '''Get serial number of the device.

        :returns:  serial number or "Not available"
        :rtype: string

        '''
        try:
            return self.data.SerialNumber
        except AttributeError:
            return "Not available"

    def get_asset_tag(self):
        '''Get asset tag of the device.

        :returns: asset tag or "Not available"
        :rtype: string

        '''
        try:
            return self.data.AssetTag
        except AttributeError:
            return "Not available"

    def get_sku(self):
        '''Get sku number of the device.

        :returns: sku number or "Not available"
        :rtype: string

        '''
        try:
            return self.data.SKU
        except AttributeError:
            return "Not available"

    def get_part_number(self):
        '''Get part number of the device.

        :returns: part number or "Not available"
        :rtype: string

        '''
        try:
            return self.data.PartNumber
        except AttributeError:
            return "Not available"


class Root(Base):
    '''Class to manage redfish Root data.'''
    def get_api_version(self):
        '''Return api version.

        :returns: api version
        :rtype: string
        :raises: AttributeError

        '''
        try:
            version = self.data.RedfishVersion
        except AttributeError:
            version = self.data.ServiceVersion

        version = version.replace('.', '')
        version = version[0] + '.' + version[1:]
        return(version)

    def get_api_UUID(self):
        '''Return api UUID.

        :returns: api UUID
        :rtype: string

        '''
        return self.data.UUID


class SessionService(Base):
    '''Class to manage redfish SessionService data.'''
    pass


class Managers(Device):
    '''Class to manage redfish Managers.'''
    def __init__(self, url, connection_parameters):
        super(Managers, self).__init__(url, connection_parameters)
        try:
            # New proliant firmware now respects Redfish v1.00, so seems to
            # correct below statement
            # TODO : better handle exception and if possible support
            # old firmware ?
            self.ethernet_interfaces_collection = \
                EthernetInterfacesCollection(
                    self.get_link_url('EthernetInterfaces'),
                    connection_parameters)

            # Works on proliant, need to treat 095 vs 0.96 differences
            # self.ethernet_interfaces_collection = \
            #        EthernetInterfacesCollection(
            #            self.get_link_url('EthernetNICs'),
            #            connection_parameters)
        except exception.InvalidRedfishContentException:
            # This is to avoid invalid content from the mockup
            self.ethernet_interfaces_collection = None

        except AttributeError:
            # This means we don't have EthernetInterfaces
            self.ethernet_interfaces_collection = None

    def get_type(self):
        '''Get manager type

        :returns: manager type or "Not available"
        :rtype: string

        '''
        try:
            return self.data.ManagerType
        except AttributeError:
            return "Not available"

    def get_firmware_version(self):
        '''Get firmware version of the manager

        :returns:  string -- bios version or "Not available"

        '''
        try:
            return self.data.FirmwareVersion
        except AttributeError:
            # We are here because the attribute could be not defined.
            # This is the case with the mockup for manager 2 and 3
            return "Not available"

    def get_managed_chassis(self):
        '''Get managed chassis ids by the manager

        :returns: chassis ids or "Not available"
        :rtype: list

        '''
        chassis_list = []
        links = getattr(self.data, mapping.redfish_mapper.map_links(self.data))

        try:
            for chassis in links.ManagerForChassis:
                result = re.search(
                    r'Chassis/(\w+)',
                    chassis[mapping.redfish_mapper.map_links_ref(chassis)])
                chassis_list.append(result.group(1))
            return chassis_list
        except AttributeError:
            return "Not available"

    def get_managed_systems(self):
        '''Get managed systems ids by the manager

        :returns: systems ids or "Not available"
        :rtype: list

        '''
        systems_list = []
        links = getattr(self.data, mapping.redfish_mapper.map_links(self.data))

        try:
            for systems in links.ManagerForServers:
                result = re.search(
                    r'Systems/(\w+)',
                    systems[mapping.redfish_mapper.map_links_ref(systems)])
                systems_list.append(result.group(1))
            return systems_list
        except AttributeError:
            return "Not available"

    def reset(self):
        '''Reset the manager.

        :returns:  string -- http response of POST request

        '''
        # Craft the request
        link = getattr(self.data.Actions, "#Manager.Reset")
        link = link.target

        reset_url = urljoin(self.url, link)

        response = requests.post(
            reset_url,
            verify=self.connection_parameters.verify_cert,
            headers=self.connection_parameters.headers)
        # TODO : treat response.
        return response


class ManagersCollection(BaseCollection):
    '''Class to manage redfish ManagersCollection data.'''
    def __init__(self, url, connection_parameters):
        '''Class constructor'''
        super(ManagersCollection, self).__init__(url, connection_parameters)
        self.managers_dict = {}
        for link in self.links:
            index = re.search(r'Managers/(\w+)', link)
            self.managers_dict[index.group(1)] = Managers(
                link, connection_parameters)


class Systems(Device):
    '''Class to manage redfish Systems data.'''
    # TODO : Need to discuss with Bruno the required method.
    #        Also to check with the ironic driver requirement.
    def __init__(self, url, connection_parameters):
        '''Class constructor'''
        super(Systems, self).__init__(url, connection_parameters)
        try:
            self.bios = Bios(url + 'Bios/Settings', connection_parameters)
        except:
            pass

        try:
            self.ethernet_interfaces_collection = \
                EthernetInterfacesCollection(
                    self.get_link_url('EthernetInterfaces'),
                    connection_parameters)
        except AttributeError:
            # This means we don't have EthernetInterfaces
            self.ethernet_interfaces_collection = None

        try:
            self.processors_collection = \
                ProcessorsCollection(
                    self.get_link_url('Processors'),
                    connection_parameters)
        except AttributeError:
            # This means we don't have Processors detailed data
            self.processors_collection = None

        try:
            self.simple_storage_collection = \
                SimpleStorageCollection(
                    self.get_link_url('SimpleStorage'),
                    connection_parameters)
        except AttributeError:
            # This means we don't have Processors detailed data
            self.simple_storage_collection = None

    def reset_system(self):
        '''Force reset of the system.

        :returns:  string -- http response of POST request

        '''
        # Craft the request
        action = dict()
        action['Action'] = 'Reset'
        action['ResetType'] = 'ForceRestart'

        # Debug the url and perform the POST action
        # print self.api_url
        response = self.api_url.post(
            verify=self.connection_parameters.verify_cert,
            headers=self.connection_parameters.headers,
            data=action)
        # TODO : treat response.
        return response

    def get_bios_version(self):
        '''Get bios version of the system.

        :returns: bios version or "Not available"
        :rtype: string

        '''
        try:
            return self.data.BiosVersion
        except AttributeError:
            return "Not available"

    def get_hostname(self):
        '''Get hostname of the system.

        :returns: hostname or "Not available"
        :rtype: string

        '''
        try:
            return self.data.HostName
        except AttributeError:
            return "Not available"

    def get_indicatorled(self):
        '''Get indicatorled of the system.

        :returns: indicatorled status or "Not available"
        :rtype: string

        '''
        try:
            return self.data.IndicatorLED
        except AttributeError:
            return "Not available"

    def get_power(self):
        '''Get power status of the system.

        :returns: system power state or "Not available"
        :rtype: string

        '''
        try:
            return self.data.PowerState
        except AttributeError:
            return "Not available"

    def get_description(self):
        '''Get description of the system.

        :returns: system description or "Not available"
        :rtype: string

        '''
        try:
            return self.data.Description
        except AttributeError:
            return "Not available"

    def get_cpucount(self):
        '''Get the number of cpu in the system.

        :returns: number of cpu or "Not available"
        :rtype: string

        '''
        try:
            return self.data.ProcessorSummary.Count
        except AttributeError:
            return "Not available"

    def get_cpumodel(self):
        '''Get the cpu model available in the system.

        :returns: cpu model or "Not available"
        :rtype: string

        '''
        try:
            return self.data.ProcessorSummary.Model
        except AttributeError:
            return "Not available"

    def get_memory(self):
        '''Get the memory available in the system.

        :returns: memory available or "Not available"
        :rtype: string

        '''
        try:
            return self.data.MemorySummary.TotalSystemMemoryGiB
        except AttributeError:
            return "Not available"

    def get_type(self):
        '''Get system type

        :returns: system type or "Not available"
        :rtype: string

        '''
        try:
            return self.data.SystemType
        except AttributeError:
            return "Not available"

    def get_chassis(self):
        '''Get chassis ids used by the system

        :returns: chassis ids or "Not available"
        :rtype: list

        '''
        chassis_list = []
        links = getattr(self.data, mapping.redfish_mapper.map_links(self.data))

        try:
            for chassis in links.Chassis:
                result = re.search(
                    r'Chassis/(\w+)',
                    chassis[mapping.redfish_mapper.map_links_ref(chassis)])
                chassis_list.append(result.group(1))
            return chassis_list
        except AttributeError:
            return "Not available"

    def get_managers(self):
        '''Get manager ids used by the system

        :returns: managers ids or "Not available"
        :rtype: list

        '''
        managers_list = []
        links = getattr(self.data, mapping.redfish_mapper.map_links(self.data))

        try:
            for manager in links.ManagedBy:
                result = re.search(
                    r'Managers/(\w+)',
                    manager[mapping.redfish_mapper.map_links_ref(manager)])
                managers_list.append(result.group(1))
            return managers_list
        except AttributeError:
            return "Not available"

    def set_parameter_json(self, value):
        '''Generic function to set any system parameter using json structure

        :param value: json structure with value to update
        :returns:   string -- http response of PATCH request

        '''
        # perform the POST action
        # print self.api_url.url()
        response = requests.patch(
            self.api_url.url(),
            verify=self.connection_parameters.verify_cert,
            headers=self.connection_parameters.headers,
            data=value)
        return response.reason

    def set_boot_source_override(self, target, enabled):
        '''Shotcut function to set boot source

        :param target: new boot source. Supported values:
            "None",
            "Pxe",
            "Floppy",
            "Cd",
            "Usb",
            "Hdd",
            "BiosSetup",
            "Utilities",
            "Diags",
            "UefiShell",
            "UefiTarget"
        :param enabled: Supported values:
            "Disabled",
            "Once",
            "Continuous"
        :returns:   string -- http response of PATCH request
        '''
        return self.set_parameter_json(
            '{"Boot": {"BootSourceOverrideTarget": "' +
            target + '"},{"BootSourceOverrideEnabled" : "' + enabled + '"}}')


class SystemsCollection(BaseCollection):
    '''Class to manage redfish SystemsCollection data.'''
    def __init__(self, url, connection_parameters):
        super(SystemsCollection, self).__init__(url, connection_parameters)

        self.systems_dict = {}

        for link in self.links:
            index = re.search(r'Systems/(\w+)', link)
            self.systems_dict[index.group(1)] = Systems(
                link, connection_parameters)


class Bios(Base):
    '''Class to manage redfish Bios data.'''
    def __init__(self, url, connection_parameters):
        super(Bios, self).__init__(url, connection_parameters)
        self.boot = Boot(re.findall('.+/Bios', url)[0] +
                         '/Boot/Settings', connection_parameters)


class Boot(Base):
    '''Class to manage redfish Boot data.'''
    def __init__(self, url, connection_parameters):
        super(Boot, self).__init__(url, connection_parameters)


class EthernetInterfacesCollection(BaseCollection):
    '''Class to manage redfish EthernetInterfacesColkection data.'''
    def __init__(self, url, connection_parameters):
        super(EthernetInterfacesCollection,
              self).__init__(url, connection_parameters)

        self.ethernet_interfaces_dict = {}

        # Url returned by the mock up is wrong
        # /redfish/v1/Managers/EthernetInterfaces/1 returns a 404.
        # --> this is not true anymore (2016/01/03)
        # The correct one should be /redfish/v1/Managers/1/EthernetInterfaces/1
        # --> correct by mockup return invalid content (not json)
        # Check more than 1 hour for this bug.... grrr....
        for link in self.links:
            index = re.search(r'EthernetInterfaces/(\w+)', link)
            self.ethernet_interfaces_dict[index.group(1)] = \
                EthernetInterfaces(link, connection_parameters)


class EthernetInterfaces(Base):
    '''Class to manage redfish EthernetInterfaces.'''
    def get_mac(self):
        '''Get EthernetInterface MacAddress

        :returns:  string -- interface macaddress or "Not available"

        '''
        try:
            # Proliant firmware seems to not follow redfish systax
            return self.data.MacAddress
        except AttributeError:
            try:
                return self.data.MACAddress
            except AttributeError:
                return "Not available"

    def get_fqdn(self):
        '''Get EthernetInterface fqdn

        :returns:  string -- interface fqdn or "Not available"

        '''
        try:
            return self.data.FQDN
        except AttributeError:
            return "Not available"

    def get_ipv4(self):
        '''Get EthernetInterface ipv4 address

        :returns:  list -- interface ip addresses or "Not available"

        '''

        ipaddresses = []

        try:
            for ip_settings in self.data.IPv4Addresses:
                address = ip_settings['Address']
                ipaddresses.append(address)

            return ipaddresses
        except AttributeError:
            return "Not available"

    def get_ipv6(self):
        '''Get EthernetInterface ipv6 address

        :returns:  list -- interface ip addresses or "Not available"

        '''

        ipaddresses = []

        try:
            for ip_settings in self.data.IPv6Addresses:
                address = ip_settings['Address']
                ipaddresses.append(address)

            return ipaddresses
        except AttributeError:
            return "Not available"


class ProcessorsCollection(BaseCollection):
    '''Class to manage redfish ProcessorsCollection data.'''
    def __init__(self, url, connection_parameters):
        super(ProcessorsCollection,
              self).__init__(url, connection_parameters)

        self.processors_dict = {}

        for link in self.links:
            index = re.search(r'Processors/(\w+)', link)
            self.processors_dict[index.group(1)] = \
                Processors(link, connection_parameters)


class Processors(Base):
    '''Class to manage redfish Processors.'''
    def get_speed(self):
        '''Get processor speed

        :returns: processor speed or "Not available"
        :rtype: string

        '''
        try:
            return self.data.MaxSpeedMHz
        except AttributeError:
            return "Not available"

    def get_cores(self):
        '''Get processor cores number

        :returns: cores number or "Not available"
        :rtype: string

        '''
        try:
            return self.data.TotalCores
        except AttributeError:
            return "Not available"

    def get_threads(self):
        '''Get processor threads number

        :returns: threads number or "Not available"
        :rtype: string

        '''
        try:
            return self.data.TotalThreads
        except AttributeError:
            return "Not available"


class SimpleStorageCollection(BaseCollection):
    '''Class to manage redfish SimpleStorageCollection data.'''
    def __init__(self, url, connection_parameters):
        super(SimpleStorageCollection,
              self).__init__(url, connection_parameters)

        self.simple_storage_dict = {}

        for link in self.links:
            index = re.search(r'SimpleStorage/(\w+)', link)
            self.simple_storage_dict[index.group(1)] = \
                SimpleStorage(link, connection_parameters)


class SimpleStorage(Base):
    '''Class to manage redfish SimpleStorage'''
    def get_status(self):
        '''Get storage status

        :returns: storage status or "Not available"
        :rtype: dict

        '''
        try:
            return self.data.Status
        except AttributeError:
            return "Not available"

    def get_devices(self):
        '''Get storage devices

        :returns: storage devices or "Not available"
        :rtype: list of dict

        '''
        try:
            return self.data.Devices
        except AttributeError:
            return "Not available"


class ChassisCollection(BaseCollection):
    '''Class to manage redfish ChassisCollection data.'''
    def __init__(self, url, connection_parameters):
        super(ChassisCollection, self).__init__(url, connection_parameters)

        self.chassis_dict = {}

        for link in self.links:
            index = re.search(r'Chassis/(\w+)', link)
            self.chassis_dict[index.group(1)] = Chassis(
                link, connection_parameters)


class Chassis(Device):
    '''Class to manage redfish Chassis data.'''
    def __init__(self, url, connection_parameters):
        '''Class constructor'''
        super(Chassis, self).__init__(url, connection_parameters)

        try:
            self.thermal = Thermal(self.get_link_url('Thermal'),
                                   connection_parameters)
        except AttributeError:
            self.thermal = None

        try:
            self.power = Power(self.get_link_url('Power'),
                               connection_parameters)
        except AttributeError:
            self.Power = None

    def get_type(self):
        '''Get chassis type

        :returns: chassis type or "Not available"
        :rtype: string

        '''
        try:
            return self.data.ChassisType
        except AttributeError:
            return "Not available"


class Thermal(Base):
    '''Class to manage redfish Thermal data.'''
    def get_temperatures(self):
        '''Get chassis sensors name and temparature

        :returns: chassis sensor and temperature
        :rtype: dict

        '''
        temperatures = {}

        try:
            for sensor in self.data.Temperatures:
                temperatures[sensor.Name] = sensor.ReadingCelsius
            return temperatures
        except AttributeError:
            return "Not available"

    def get_fans(self):
        '''Get chassis fan name and rpm

        :returns: chassis fan and rpm
        :rtype: dict

        '''
        fans = {}

        try:
            for fan in self.data.Fans:
                fans[fan.FanName] = fan.ReadingRPM
            return fans
        except AttributeError:
            return "Not available"


class Power(Base):
    '''Class to manage redfish Power data.'''
    pass
