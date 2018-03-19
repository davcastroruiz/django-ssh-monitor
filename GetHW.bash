#!/bin/bash
######################################
#Getting ready all stuff
######################################
/bin/echo "Starting process"
#Cheking IPMITOOL
aux=$(rpm -qa ipmitool)
if ` echo $(rpm -qa ipmitool) | grep "ipmitool" > /dev/null` # if ipmitool is installed
	then /bin/echo "IPMItool is installed"
else
	/bin/echo "IPMItool isn't installed"
fi

######################################
#Getting basebord information
######################################
/bin/echo "Getting basebord information"
/bin/echo "----------------------" > File.txt
/bin/echo "@@ BASEBOARD INFO" >> File.txt
/bin/echo "----------------------" >> File.txt
dmidecode -t baseboard | grep -e "Product Name: " >> File.txt

######################################
#Getting OS Information information
######################################
/bin/echo "Getting OS information"
/bin/echo "" >> File.txt
/bin/echo "----------------------" >> File.txt
/bin/echo "@@ OS INFO" >> File.txt
/bin/echo "----------------------" >> File.txt
cat /etc/os-release | grep -v PRETTY | grep -v CPE | grep NAME >> File.txt
cat /etc/os-release | grep VERSIO_ID >> File.txt

######################################
#Getting CPU information
######################################
/bin/echo "Getting CPU information"
/bin/echo "" >> File.txt
/bin/echo "----------------------" >> File.txt
/bin/echo "@@ CPU INFO" >> File.txt
/bin/echo "----------------------" >> File.txt
lscpu | grep -e "Socket(s): " -e "CPU family: " -e "Model: " -e "Model name: " >> File.txt

######################################
#Getting RAM information
######################################
/bin/echo "Getting RAM information"
/bin/echo "" >> File.txt
/bin/echo "----------------------" >> File.txt
/bin/echo "@@ RAM INFO" >> File.txt
/bin/echo "----------------------" >> File.txt
dmidecode -t memory | grep -m 1 "Number Of Devices: " >> File.txt
/bin/echo ""
dmidecode -t memory | grep -v Clock | grep -v Error | grep -e "Locator: D" -e "Size: " -e "Type: " -e "Speed: " -e "Manufacturer: " -e "Part Number: " >> File.txt

######################################
#Getting Power Supplies information
######################################
/bin/echo "Getting PSU information"
/bin/echo "" >> File.txt
/bin/echo "----------------------" >> File.txt
/bin/echo "@@ PSU INFO" >> File.txt
/bin/echo "----------------------" >> File.txt
ipmitool fru read 2 >> File.txt
/bin/echo ""
ipmitool fru read 3 >> File.txt

######################################
#Getting Drives information
######################################
/bin/echo "Getting Drives information"
/bin/echo "" >> File.txt
/bin/echo "----------------------" >> File.txt
/bin/echo "@@ DRIVES INFO" >> File.txt
/bin/echo "----------------------" >> File.txt
lsscsi >> File.txt


######################################
#Getting PCI information
######################################
/bin/echo "Getting PCI information"
/bin/echo "" >> File.txt
/bin/echo "----------------------" >> File.txt
/bin/echo "@@ PCI INFO" >> File.txt
/bin/echo "----------------------" >> File.txt
lspci >> File.txt

/bin/echo "Finished"
