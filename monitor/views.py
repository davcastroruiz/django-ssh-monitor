import json

from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render_to_response, redirect
import sys, paramiko

from django.template.context_processors import csrf
import commands as cmd
from ast import literal_eval as val_dict
from models import Connection
from django.core import serializers


def main_base_view(request):
    dictionary = dict(request=request)
    dictionary.update(csrf(request))
    if request.method == 'POST':
        connection_instance = Connection()
        connection_instance.alias = request.POST['alias']
        connection_instance.username = request.POST['user']
        connection_instance.password = request.POST['pwd']
        connection_instance.ip = request.POST['ip']
        connection_instance.port = request.POST['port']
        connection_instance.save()
        return redirect('monitor:main_base')
    dictionary.update({"Connections": Connection.objects.all()})

    return render_to_response('monitor/home_page.html', dictionary)


def get_json_information(request):
    if request.method == "POST":
        alias = request.POST['alias_json']
        pseudo_buffer = request.POST['pseudo_buffer_json']
        download_type = request.POST['download']
        if download_type == "xml":
            response = HttpResponse(content_type='application/xml')
            xml = json2xml(json_obj={"Information": val_dict(pseudo_buffer)}, line_padding="")
            response['Content-Disposition'] = 'attachment; filename="%s.xml"' % alias
            response.write(xml)
        else:
            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="%s.json"' % alias
            response.write(pseudo_buffer)
        return response
    else:
        return redirect('monitor:main_base')


def ssh_information_view(request, pk):
    connection = Connection.objects.get(pk=pk)
    dictionary = dict(request=request, ssh_information=ssh_information(connection), alias=connection.alias, pk=pk)
    dictionary.update(csrf(request))
    return render_to_response('monitor/ssh_information_page.html', dictionary)


def ssh_information(connection):
    # hostname = "172.22.202.204"
    hostname = connection.ip
    password = connection.password
    username = connection.username
    port = int(connection.port)

    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port=port, username=username, password=password)
        value = val_dict(cmd.baseboard(client))
        value.update(val_dict(cmd.operating_system(client)))
        value.update(val_dict(cmd.cpu(client)))
        ram = cmd.ram(client)
        temp = json.loads(ram)
        if bool(temp["RAM"]):
            value.update(val_dict(ram))

        psu = cmd.psu(client)
        temp = json.loads(psu)
        if bool(temp["PSU"]):
            value.update(val_dict(cmd.psu(client)))

        value.update(val_dict(cmd.drive(client)))
        pci = cmd.pci(client)
        temp = json.loads(pci)
        if bool(temp["PCI"]):
            value.update(val_dict(pci))

    except Exception as e:
        value = "Error:\n%s" % e
    finally:
        client.close()
    return value


def ssh_client_command(request):
    pk = request.GET.get("pk", None)
    connection = Connection.objects.get(pk=pk)
    hostname = connection.ip
    password = connection.password
    username = connection.username
    port = int(connection.port)

    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port=port, username=username, password=password)
        command = request.GET.get("command", None)
        value = cmd.custom(client, command)
    except Exception as e:
        value = "Error:\n%s" % e
    finally:
        client.close()
    return JsonResponse(value, safe=False)


def get_info_client(request):
    pk = request.GET.get("pk", None)
    try:
        connection = Connection.objects.get(pk=pk)
        hostname = connection.ip
        alias = connection.alias
        password = connection.password
        username = connection.username
        port = int(connection.port)
        value = {"hostname": hostname, "password": password, "username": username, "port": port, "alias": alias,
                 "error": "", "id": pk}
    except Exception as e:
        value = {"error": e}
    return JsonResponse(value, safe=False)


def test_connection_client(request):
    pk = request.GET.get("pk", None)
    try:
        connection = Connection.objects.get(pk=pk)
        hostname = connection.ip
        alias = connection.alias
        password = connection.password
        username = connection.username
        port = int(connection.port)
        value = {"hostname": hostname, "password": password, "username": username, "port": port, "alias": alias,
                 "id": pk}
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname, port=port, username=username, password=password)
            value.update({"result": "successful"})
        except Exception as e:
            value.update({"result": "unsuccessful", "description": str(e)})
        finally:
            client.close()
    except Exception as e:
        value = {"result": "error", "description": str(e)}
    return JsonResponse(value, safe=False)


def remove_update(request):
    if request.method == 'POST':
        try:
            action = request.POST['action']
            pk = request.POST['pk_edit']
            if action == "update":
                connection_instance = Connection.objects.get(pk=pk)
                connection_instance.alias = request.POST['alias_edit']
                connection_instance.username = request.POST['user_edit']
                connection_instance.password = request.POST['pwd_edit']
                connection_instance.ip = request.POST['ip_edit']
                connection_instance.port = request.POST['port_edit']
                connection_instance.save()
            elif action == "remove":
                connection_instance = Connection.objects.get(pk=pk)
                connection_instance.delete()
            else:
                pass
        except Exception as e:
            print(e)

    return redirect('monitor:main_base')


def json2xml(json_obj, line_padding=""):
    result_list = list()

    json_obj_type = type(json_obj)

    if json_obj_type is list:
        for sub_elem in json_obj:
            result_list.append(json2xml(sub_elem, line_padding))
        return "\n".join(result_list)

    if json_obj_type is dict:
        for tag_name in json_obj:
            sub_obj = json_obj[tag_name]
            result_list.append("%s<%s>" % (line_padding, tag_name.replace(" ", "_")))
            result_list.append(json2xml(sub_obj, "\t" + line_padding))
            result_list.append("%s</%s>" % (line_padding, tag_name.replace(" ", "_")))
        return "\n".join(result_list)

    return "%s%s" % (line_padding, json_obj)