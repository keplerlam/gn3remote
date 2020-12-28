#!/usr/bin/python3
#
# Copyright (C) 2020 Kepler Lam
#
# Program : gns_admin.py
# Creation Date : May 26, 2019
#
# Description : Remote management for GNS projects
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import os
import socket
import requests
import json
import urllib.request
import json
import re
import time

def press1key():
   input("Please press ENTER to continue ....")

def MenuChoice(Menu,QuitOption):
   while (1):
      print("Please choose one of the following options:\n")
      for Item in range(len(Menu)):
         print("\t%i: %s"%(Item+1,Menu[Item][0]))
      print("\tQ: %s\n"%(QuitOption))
      Choice=input()
      if Choice.isdigit():
         C=int(Choice)
         if C<1 or C>len(Menu):
            print("%s is not valid, please try again"%Choice)
         else:
            return Choice,Menu[C-1][1]
      elif Choice.upper()=="Q":
         return Choice,None
      else:
         print("Invalid choice, please try again\n")

def Menu(menu,quitoption,loopover,DefaultCallBack,para):
   while (1):
      os.system("clear")
      choice,call_back=MenuChoice(menu,quitoption)
      if choice.upper()=="Q":
         return
      elif not call_back is None:
         call_back()
      elif not DefaultCallBack is None:
         DefaultCallBack(choice,menu,para)
      if not loopover:
         return
      press1key()

def rcmd(cmd,response):
   s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
   try:
      s.connect((GNS_HOST,23))
      BUFFER_SIZE=4096
      ostr="cd\n"
      s.send(ostr.encode("utf8"))
      while 1:
         l=s.recv(BUFFER_SIZE)
         embed_prompt=l.decode("utf8").replace("\015","")
         obj=re.search(r'.:.*>',embed_prompt)
         if obj:
            prompt=obj.group()
            break
      ostr="%s\n"%cmd
      s.send(ostr.encode("utf8"))
      while 1:
         l=s.recv(BUFFER_SIZE)
         l=l.decode("utf8").replace("\015","")
         response.append(l)
         if prompt in l:
            break
      s.close()
   except socket.timeout:
      print("Connection problem with the remote end, make sure that the rcmd is running")
      return

def get_req(url):
   data=requests.get(url=url)
   binary=data.content
   response=json.loads(binary.decode("utf-8"))
   return response

def post_req(url,body):
   req=urllib.request.Request(url)
   req.add_header('Content-Type', 'application/json; charset=utf-8')
   jsondata=json.dumps(body)
   jsondataasbytes=jsondata.encode('utf-8')
   req.add_header('Content-Length',len(jsondataasbytes))
   response=urllib.request.urlopen(req,jsondataasbytes)
   return response

def telnet_console():
   port=input("Please enter port number: ")
   os.system("telnet %s %s"%(GNS_VM,port))

def start_gns():
   if gns_running():
      print("GNS Server is already running")
      return
   status=[]
   rcmd("start \"\" \"%s\" --local"%GNS_EXE,status)
   return

def closepj(pid):
   url="http://%s:3080/v2/projects/%s/close"%(GNS_HOST,pid)
   body={}
   post_req(url,body)
   return

def openpj(pid):
   url="http://%s:3080/v2/projects/%s/open"%(GNS_HOST,pid)
   body={}
   post_req(url,body)
   return

def load_proj(pjpath):
   url="http://%s:3080/v2/projects/load"%GNS_HOST
   body={"path" : pjpath}
   post_req(url,body)
   return

def start_all(pid):
   url="http://%s:3080/v2/projects/%s/nodes/start"%(GNS_HOST,pid)
   body={}
   post_req(url,body)
   return

def stop_all(pid):
   url="http://%s:3080/v2/projects/%s/nodes/stop"%(GNS_HOST,pid)
   body={}
   post_req(url,body)
   return

def run_proj(cho,mn,pinfo):
   pj=pinfo['Projects'][int(cho)-1]
   if not pinfo['current'] is None:
      if pj[2]==pinfo['current']:
         print("The project selected is currently opened, it will be restart.",end='')
      else:
         print("The current opened project will be automatically closed before starting another one.",end='') 
      proceed=input(" Proceed (Y/N)?")
      if proceed.upper()!="Y":
         return
      print("Please wait to close the current project...")
      closepj(pinfo['current']);
   pjpath=pj[1].replace("\\","/")
   print("Please wait to load the project...")
   load_proj(pjpath)
   print("Please wait to start the devices...")
   start_all(pj[2])
   print("Devices are ready, you can access the console")
   return

def get_proj_path(pid):
   pjinfo=get_req("http://%s:3080/v2/projects/%s"%(GNS_HOST,pid))
   return(pjinfo['path'].replace("\\","/")+"/"+pjinfo['filename'])

def get_proj(pjmenu,pjinfo):
   response=get_req("http://%s:3080/v2/projects"%GNS_HOST)
   pjinfo['current']=None
   pjinfo['Projects']=[]
   pjs=pjinfo['Projects']
   for p in response:
      pjs.append([p['name'],p['path']+"/"+p['filename'],p['project_id'],p['status']])
      if p['status']=="opened":
         pjinfo['current']=p['project_id']
         pjmenu.append([p['name']+' *',None])
      else:
         pjmenu.append([p['name'],None])
   return

def proj_menu():
   if not gns_running():
      print("GNS Server is not running, please start it and try again")
      return
   Project_Menu=[]
   proj_info={}
   get_proj(Project_Menu,proj_info)
   Menu(Project_Menu,"Quit to Main Menu",False,run_proj,proj_info);
   return

def console_access(cho,mn,ndpara):
   ndinfo=ndpara['nodelist']
   nd=ndinfo[int(cho)-1]
   os.system("telnet %s %s"%(nd[1],nd[2]))

def oper_device(pid,dev_id,oper):
   url="http://%s:3080/v2/projects/%s/nodes/%s/%s"%(GNS_HOST,pid,dev_id,oper)
   body={}
   post_req(url,body)
   return

def restart_device(cho,mn,ndpara):
   proceed=input("The selected device will be rebooted. Proceed (Y/N)?")
   if proceed.upper()!="Y":
      return
   pid=ndpara['pid']
   ndinfo=ndpara['nodelist']
   nd=ndinfo[int(cho)-1]
   oper_device(pid,nd[3],'stop')
   oper_device(pid,nd[3],'start')

def get_node(pid,ndmenu,ndinfo):
   response=get_req("http://%s:3080/v2/projects/%s/nodes"%(GNS_HOST,pid))
   for nd in response:
      ndinfo.append([nd['name'],nd['console_host'],nd['console'],nd['node_id']])
      ndmenu.append([nd['name'],None])

def get_open_proj():
   if not gns_running():
      print("GNS Server is not running, please start it and try again")
      return None
   Project_Menu=[]
   proj_info={}
   get_proj(Project_Menu,proj_info)
   if proj_info['current'] is None:
      print("No opened project, please start a project and try again")
   return proj_info['current']

def restore_snap(cho,mn,sp_para):
   proceed=input("All devices will be rebooted. Proceed (Y/N)?")
   if proceed.upper()!="Y":
      return
   sp=sp_para['snaplist'][int(cho)-1]
   pid=sp_para['pid']
   stop_all(pid)
   time.sleep(5)
   pjpath=get_proj_path(pid)
   url="http://%s:3080/v2/projects/%s/snapshots/%s/restore"%(GNS_HOST,pid,sp[1])
   post_req(url,{})
   start_all(pid)

def exist_snap(pid,snap):
   response=get_req("http://%s:3080/v2/projects/%s/snapshots"%(GNS_HOST,pid))
   for sp in response:
      if sp['name']==snap:
         return True
   return False

def create_snap():
   proceed=input("Make sure you have saved the configuration, as all devices will be rebooted. Proceed (Y/N)?")
   if proceed.upper()!="Y":
      return
   pid=get_open_proj()
   if pid is None:
      print ("Please start a project first.")
      return
   new_snap=input("Please enter the snapshot name:")
   if exist_snap(pid,new_snap):
      proceed=input("Snapshot exist. Overwrite (Y/N)?")
      if proceed.upper()!="Y":
         return
   stop_all(pid)
   url="http://%s:3080/v2/projects/%s/snapshots"%(GNS_HOST,pid)
   body={"name" : new_snap}
   post_req(url,body)
   start_all(pid)

def get_snap(pid,spmenu,spinfo):
   response=get_req("http://%s:3080/v2/projects/%s/snapshots"%(GNS_HOST,pid))
   for sp in response:
      spinfo.append([sp['name'],sp['snapshot_id']])
      spmenu.append([sp['name'],None])

def snap_menu():
   cur_pj=get_open_proj()
   if cur_pj is None:
      return
   Snap_Menu=[]
   snap_para={}
   snap_para['pid']=cur_pj
   snap_info=snap_para['snaplist']=[]
   get_snap(cur_pj,Snap_Menu,snap_info)
   Menu(Snap_Menu,"Quit to Main Menu",False,restore_snap,snap_para);

def node_menu(operation):
   cur_pj=get_open_proj()
   if cur_pj is None:
      return
   Node_Menu=[]
   node_para={}
   node_para['pid']=cur_pj
   node_info=node_para['nodelist']=[]
   get_node(cur_pj,Node_Menu,node_info)
   Menu(Node_Menu,"Quit to Main Menu",False,operation,node_para);
   return

def node_console():
   node_menu(console_access)

def node_restart():
   node_menu(restart_device)

def stop_gns():
   if not gns_running():
      print("GNS Server is not running")
      return
   confirm=input("Confirm (Y/N): ")
   if confirm.upper()=="Y":
      response=post_req("http://%s:3080/v2/shutdown"%GNS_HOST,{})
   return

def status_gns():
   print("GNS3 is %s"%("" if gns_running() else "NOT ")+"running\n")
   return

def gns_running():
   s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
   try:
      s.connect((GNS_HOST,3080))
      s.close()
      return True
   except ConnectionRefusedError:
      return False

def get_ports():
   return

time.sleep(2)
MyMenu=[
   ["start GNS server",start_gns],
   ["Load and start GNS project",proj_menu],
   ["Access Device Console",node_console],
   ["Power Cycle Device",node_restart],
   ["Restore Project Snapshot",snap_menu],
   ["Create Project Snapshot",create_snap],
   ["Stop GNS",stop_gns],
   ["Check GNS3 status",status_gns],
]
GNS_HOST="192.168.1.1"   # Change the IP address to the machine host the GNS client
GNS_EXE="C:\\Program Files\\GNS3\\gns3server.exe"
HOTKEY="C:\\Program Files\\AutoHotkey\\AutoHotkey.exe"
Proj_Dir="C:\\Program Files\\GNS3\\projects"
Script_Dir="C:\\Program Files\\GNS3\\scripts"
Menu(MyMenu,"Quit",True,None,None)

