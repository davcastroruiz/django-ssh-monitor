import json
import re
import time


######################################
# Getting baseboard information
######################################
def baseboard(client):
    command = "dmidecode -t baseboard | grep -e 'Product Name: ' -e 'Serial Number: '"
    stdin, stdout, stderr = client.exec_command(command)
    model = str(stdout.read()).split("\n")
    try:
        product_name = clean(model[0], "Product Name: ")
        serial_number = clean(model[1], "Serial Number: ")
    except:
        pass
    return json.dumps({"Baseboard": {"Product Name": product_name, "Serial Number": serial_number}})


######################################
# Getting OS Information information
######################################
def operating_system(client):
    command = "cat /etc/os-release | grep -v PRETTY | grep -v CPE | grep NAME"
    stdin, stdout, stderr = client.exec_command(command)
    os_information = clean(stdout.read(), 'NAME=')
    command = "cat /etc/os-release | grep VERSION_ID"
    stdin, stdout, stderr = client.exec_command(command)
    version_id = clean(stdout.read(), 'VERSION_ID=')
    return json.dumps({"OS": {"Name": os_information, "Version": try_to_parse(version_id, float)}})


######################################
# Getting CPU information
######################################
def cpu(client):
    command = 'lscpu | grep -e "Socket(s): " -e "CPU family: " -e "Model name: " -e "Model: "'
    stdin, stdout, stderr = client.exec_command(command)
    model = str(stdout.read()).split("\n")
    try:
        sockets = clean(model[0], "Socket(s): ")
        family = clean(model[1], "CPU family: ")
        model_name = clean(model[3], "Model name: ")
        fam_model = clean(model[2], "Model: ")
    except:
        pass
    return json.dumps({"CPU": {"Sockets": try_to_parse(sockets, int), "Family": try_to_parse(family, int),
                               "Model": try_to_parse(fam_model, int), "Model name": model_name}})


######################################
# Getting RAM information
######################################
def ram(client):
    command = 'dmidecode -t memory | grep -v Clock | grep -v Error | grep -e "Locator: D" -e "Type: "' \
              ' -e "Size: " -e "Speed: " -e "Manufacturer: " -e "Part Number: " -e "Serial Number: "'
    stdin, stdout, stderr = client.exec_command(command)
    dimms = str(stdout.read()).split("\n")
    dimms = filter(None, dimms)
    iterations = len(dimms) / 7
    temp = 0
    temp1 = 7
    mega_ram_json = {}
    for a in range(1, iterations + 1):
        if temp > len(dimms):
            break
        # print("item --> %d:%d" % (temp, temp1))
        ram_json = {}
        for i in (dimms[temp:temp1]):

            temp = i.split(":")
            if temp[0] != "":
                ram_json.update({temp[0].replace("\t", ""): re.sub('\s+', ' ', temp[1]).strip()})

        try:
            locator = ram_json["Locator"]
            ram_json.pop("Locator")
            if "No Module Installed" in ram_json["Size"]:
                mega_ram_json.update({locator: "No Module Installed"})
            else:
                mega_ram_json.update({locator: ram_json})
        except:
            # print ram_json
            pass

        temp1 += 7
        temp = temp1 - 7

    # return json.dumps({"RAM": sorted(mega_ram_json.iteritems(), key=lambda (k, v): (v, k))}, sort_keys=True)
    return json.dumps({"RAM": mega_ram_json})


######################################
# Getting Drives information
######################################
def drive(client):
    command = "rpm -q 'lshw'"
    stdin, stdout, stderr = client.exec_command(command)
    installed = str(stdout.read())
    if "not installed" in installed:
        os = operating_system(client)
        # se necesita un repositorio
        if "Enterprise" in os or "Linux" in os or "CentOS" in os or "Fedora" in os:
            command = "yum install -y lshw"
        else:
            command = "apt-get install lshw"
        client.exec_command(command)
        time.sleep(7)
        command = "rpm -q 'lshw'"
        client.exec_command(command)

    command = "lshw -class disk -disable cpuinfo -disable PCI -disable USB -disable pcilegacy -disable network " \
              "-disable memory"
    stdin, stdout, stderr = client.exec_command(command)
    x = str(stdout.read())
    x = x.split("*")
    mega_array = []
    for i in filter(None, x):
        a = i.split("\n")
        object_item = {}
        for xa in a:
            xa = xa.split(":")
            if len(xa) == 2:
                key = re.sub('\s+', ' ', xa[0]).strip()
                value = re.sub('\s+', ' ', xa[1]).strip()
                object_item.update({key.title(): value})

        if bool(object_item):
            if "sd" in object_item["Logical Name"]:
                try:
                    object_item.pop("Configuration")
                    object_item.pop("-Disk")
                except:
                    pass
                mega_array.append(object_item)
    return json.dumps({"Drives": {"Disks": mega_array, "Number of Devices": len(mega_array)}})


######################################
# Getting PCI information
######################################
def pci(client):
    general_json = {}
    command = "lspci | grep -v Xeon | grep -v mellanox | grep -i eth"
    stdin, stdout, stderr = client.exec_command(command)
    model = str(stdout.read())
    read2 = model.split("\n")
    network_eth = pci_add(read_str=read2, title_json="Network ETH")
    if network_eth is not None:
        general_json.update(network_eth)

    command = "lspci | grep -v Xeon | grep -i hfi"
    stdin, stdout, stderr = client.exec_command(command)
    model = str(stdout.read())
    read2 = model.split("\n")
    network_hfi = pci_add(read_str=read2, title_json="Network HFI")
    if network_hfi is not None:
        general_json.update(network_hfi)

    command = "lspci | grep -v Xeon | grep -i sata"
    stdin, stdout, stderr = client.exec_command(command)
    model = str(stdout.read())
    read2 = model.split("\n")
    sata = pci_add(read_str=read2, title_json="Sata")
    if sata is not None:
        general_json.update(sata)

    command = "lspci | grep -v Xeon | grep -i mellanox"
    stdin, stdout, stderr = client.exec_command(command)
    model = str(stdout.read())
    read2 = model.split("\n")
    mellanox = pci_add(read_str=read2, title_json="Mellanox")
    if mellanox is not None:
        general_json.update(mellanox)

    command = "lspci | grep -v Xeon | grep -i raid"
    stdin, stdout, stderr = client.exec_command(command)
    model = str(stdout.read())
    read2 = model.split("\n")
    raid = pci_add(read_str=read2, title_json="RAID Bus")
    if raid is not None:
        general_json.update(raid)

    return json.dumps({"PCI": general_json})


######################################
# Getting Power Supplies information
######################################
def psu(client):
    command = "rpm -q 'ipmitool'"
    stdin, stdout, stderr = client.exec_command(command)
    installed = str(stdout.read())
    general_json = {}
    if "not installed" in installed:
        os = operating_system(client)
        # se necesita un repositorio
        if "Enterprise" in os or "Linux" in os or "CentOS" in os or "Fedora" in os:
            command = "yum install -y OpenIPMI ipmitool"
        else:
            command = "apt-get install ipmitool"
        client.exec_command(command)
        time.sleep(7)
        command = "rpm -q 'ipmitool'"
        client.exec_command(command)

    command = "ipmitool fru print 2"
    stdin, stdout, stderr = client.exec_command(command)
    read2 = str(stdout.read()).split("\n")
    read2_json = {}
    for i in read2:
        temp = i.split(":")
        if temp[0] != "":
            read2_json.update({re.sub('\s+', ' ', temp[0]).strip(): re.sub('\s+', ' ', temp[1]).strip()})
    if bool(read2_json):
        general_json.update({"PSU1": read2_json})
    command = "ipmitool fru print 3"
    stdin, stdout, stderr = client.exec_command(command)
    read3 = str(stdout.read()).split("\n")
    read3_json = {}
    for i in read3:
        temp = i.split(":")
        if temp[0] != "":
            read3_json.update({re.sub('\s+', ' ', temp[0]).strip(): re.sub('\s+', ' ', temp[1]).strip()})
    if bool(read3_json):
        general_json.update({"PSU2": read3_json})
    return json.dumps({"PSU": general_json})


def clean(value, key, add=None):
    if add is None:
        add = ''
    value = str(value).replace(key, add).replace("\t", "").replace("\n", "").replace('\"', "")
    return re.sub('\s+', ' ', value).strip()


def custom(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    value = str(stdout.read())
    return {"stdout": value}


"""If we wanted to get the BIOS Info, we would then reference v['dmi_type'] == 0
Type   Information
       ----------------------------------------
          0   BIOS
          1   System
          2   Base Board
          3   Chassis
          4   Processor
          5   Memory Controller
          6   Memory Module
          7   Cache
          8   Port Connector
          9   System Slots
         10   On Board Devices
         11   OEM Strings
         12   System Configuration Options
         13   BIOS Language
         14   Group Associations
         15   System Event Log
         16   Physical Memory Array
         17   Memory Device
         18   32-bit Memory Error
         19   Memory Array Mapped Address
         20   Memory Device Mapped Address
         21   Built-in Pointing Device
         22   Portable Battery
         23   System Reset
         24   Hardware Security
         25   System Power Controls
         26   Voltage Probe
         27   Cooling Device
         28   Temperature Probe
         29   Electrical Current Probe
         30   Out-of-band Remote Access
         31   Boot Integrity Services
         32   System Boot
         33   64-bit Memory Error
         34   Management Device
         35   Management Device Component
         36   Management Device Threshold Data
         37   Memory Channel
         38   IPMI Device
         39   Power Supply


       Keyword     Types
       ------------------------------
       bios        0, 13
       system      1, 12, 15, 23, 32
       baseboard   2, 10
       chassis     3
       processor   4
       memory      5, 6, 16, 17
       cache       7
       connector   8
       slot        9
"""


def try_to_parse(parameter, parse_type):
    try:
        parameter = parse_type(parameter)
    except:
        pass
    return parameter


######################################
# Function to return specific PCI info
# or return None if is empty
######################################
def pci_add(read_str, title_json):
    temp_array = []
    for i in read_str:
        bus = i[:8]
        xa = i[8:].split("controller:")
        if len(xa) == 2:
            temp_array.append(
                {"Bus": bus, "Class": "%scontroller" % xa[0], "Description": re.sub('\s+', ' ', xa[1]).strip()})
    if len(temp_array) > 0:
        return {title_json: temp_array}
    else:
        return  None
