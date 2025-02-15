"""

@Author		:Furqan Khan
@Email		:furqankhan08@gmail.com
@Date 		:1/3/2017

Objective :
The purpose of this file /module /Class is to map to serve teh Rest request
Depending upon the requested url the views module will fetch the data from the backend
python files and would transform the data to json format ,and would finally return the data back to the
requesting application.

"""
from django.shortcuts import render
from Dictator_service.serializers import UserSerializer,ScanAttributes,ProfileAttributes,General,ProjectSerializer,Configuration,test_multi,Exploits,UploadXml,UploadXmlNmap,Poll_me,Polling_,ExploitsConcurrent,Merge_reports,OnFly
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser,MultiPartParser,FormParser,FileUploadParser
from rest_framework import status
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt,csrf_protect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from wsgiref.util import FileWrapper
import Gui_main_driver
import json
import os
import nmap_parser
import FileValidator
import Polling
import uuid
import Nessus_parser
import Qualys_parser
import Report_orchestration
import Exploit_mapping
import zipfile

import IPtable,IPexploits
import ValidateProfile
#from Dictator.Dictator_service.bin_gui_1 import compiler #import *

# Create your views here.\

class SetCsrf(APIView):
	"""
	Objective :
	This class is only for test purpose and it forces the framework to generate a csrf token 
	with custom authentication
	"""
	@method_decorator(ensure_csrf_cookie)
	def get(self,request,format=None):
		return Response(JSONRenderer().render({"helllo":"world"}))

class InitDirectory():
	def __init__(self):
		self.folder_dir=os.path.dirname(os.path.realpath(__file__))
		self.results_path=os.path.join(self.folder_dir,"Results")
		self.profiles_path=os.path.join(self.folder_dir,"Profiles")
		self.folder_name=os.path.join(self.results_path,"Data_")
		
	def init_project_directory(self):
		try:
			if not os.path.exists(self.folder_name+str(self.project_id)):
				os.mkdir(self.folder_name+str(self.project_id))
				s_path=os.path.join(self.results_path,'bk')
				os.system("cp -r "+s_path+ " "+ self.folder_name+str(self.project_id)+"/")
				
			self.data_path=self.folder_name+str(self.project_id)
			return 1;
		except Exception ,ee:
			#self.print_Error("Error while creating directory !!"+str(ee))
			print "EX "+str(ee)
			return -1


class UserList(APIView):
	"""
	Objective :
	The code is only for testing purpose and has no utility with final draft of code
	"""
	
	def get(self,request,format=None):
		Employee_dict={}
		Employee_list=[]
		Employee_dict["id"]=1
		Employee_dict["name"]="Furqan Khan"
		Employee_list.append(Employee_dict)
		Employee_dict={}
		Employee_dict["id"]=2
		Employee_dict["name"]="Burhan Khan"
		Employee_list.append(Employee_dict)
		serialize=UserSerializer(Employee_list,many=True)
		return Response(JSONRenderer().render(serialize.data))
		#return JSONResponse(serialize.data)




class StartScanConcurrent(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the scan attributes 
	and would invoke appropriate backend python files Gui_main_driver.py to start the scan as a process.

	Note :This class would invoke the dicovery and vulnerability scanning in concurrent mode.
	
	IN order to understand about input given to this method and response returned read API documentation.
	"""
	#@csrf_exempt
	def post(self,request,format=None):
		#<<<<<<< HEAD
		#print "Request HIt :"
		#=======
		print "Request HIt :"
		#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
		#data_=JSONParser().parse(request)
		scan_attributes=ScanAttributes(data=request.data)
		#scan_attributes=ScanAttributes(data=data_)
		return_response={}
		
		if scan_attributes.is_valid():
			#return Response(scan_attributes.data)
			obj=Gui_main_driver.Gui_main()
			profile_id=int(scan_attributes.data["profile"])
			dir_obj=InitDirectory()
			profile=ValidateProfile.Profile()
			if scan_attributes.data["edit_profile"]=="1":
				try:
					profile_json=json.loads(scan_attributes.data["profile_json"])
				except Exception ,exc:
						return_response["status"]="failure"
						return_response["errors"]="Exception : "+str(exc)
						return_response["value"]="Exception : "+str(exc)
						return Response(JSONRenderer().render(return_response))
	
				is_valid=profile.validateProfile(profile_id,profile_json)
				if is_valid in [-1, -2] :
						return_response["status"]="failure"
						return_response["errors"]="Invalid Json Data / Value passed for Profile"
						return_response["value"]="Invalid Json Data / Value  passed for Profile"
						return Response(JSONRenderer().render(return_response))
				elif is_valid != 1:
						return_response["status"]="failure"
						return_response["errors"]="Exception : "+str(is_valid)
						return_response["value"]="Exception : "+str(is_valid)
						return Response(JSONRenderer().render(return_response))

			scan_id=obj.main_start(scan_attributes.data["project_name"],scan_attributes.data["IP_range"],scan_attributes.data["Port_range"],scan_attributes.data["switch"],"1","init",int(scan_attributes.data["profile"]),scan_attributes.data["assessment_id"],scan_attributes.data["app_id"],True)

			if scan_id !=-1:
				my_obj=IPtable.IPtable()
				my_obj.Update_status_to_paused_or_processing(scan_id,'processing',True,True)
				my_obj=IPtable.Projects()
				my_obj.Update_mode(scan_id,'concurrent')
				return_response["status"]="success" #+str(scan_attributes.data["project_name"])
				return_response["project_id"]=str(scan_id)
				return_response["value"]=str(scan_id)

				if scan_attributes.data["edit_profile"]=="1":
						dir_obj.project_id=int(scan_id)
						status=dir_obj.init_project_directory()
						if status == -1:
							return_response["status"]="failure"
							return_response["value"]="Scan has started but Not able to create the Directory"
						else:
							stat=profile.CreateCustom(dir_obj.data_path,profile_json,str(scan_id),profile_id,scan_attributes.data["assessment_id"])
							if stat["status"] !="success":
								return_response["status"]="failure"
								return_response["value"]=stat["value"]
							else:
								return_response["profile_id"]=stat["value"]
								IPtable.Projects().UpdateProjectProfile(scan_id,stat["value"])
			else:
				return_response["status"]="failure" #+str(scan_attributes.data["project_name"])
				return_response["project_id"]=str(scan_id)
				return_response["value"]=str(scan_id)
			return Response(JSONRenderer().render(return_response))

		return_response["status"]="failure"
		return_response["errors"]=scan_attributes.errors
		return_response["value"]=scan_attributes.errors
		#return Response(return_response)	
		return Response(JSONRenderer().render(return_response))



class StartScan(APIView):
	#@csrf_exempt
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the scan attributes 
	and would invoke appropriate backend python files Gui_main._driver.py to start the scan as a process
	
	Note :This class will invoke the backend code in sequential mode
	IN order to understand about input given to this method and response returned read API documentation.
	"""
	
	def post(self,request,format=None):
		return_response={}
		try:
			scan_attributes=ScanAttributes(data=request.data)
			if scan_attributes.is_valid():
				obj=Gui_main_driver.Gui_main()
				profile_id=int(scan_attributes.data["profile"])
				dir_obj=InitDirectory()
				profile=ValidateProfile.Profile()
				#if profile_id in [4,5]:
				if scan_attributes.data["edit_profile"]=="1":
						try:
							profile_json=json.loads(scan_attributes.data["profile_json"])
						except Exception ,exc:
							return_response["status"]="failure"
							return_response["errors"]="Exception : "+str(exc)
							return_response["value"]="Exception : "+str(exc)
							return Response(JSONRenderer().render(return_response))

						is_valid=profile.validateProfile(profile_id,profile_json)
						if is_valid in [-1, -2] :
							return_response["status"]="failure"
							return_response["errors"]="Invalid Json Data / Value passed for Profile"
							return_response["value"]="Invalid Json Data / Value  passed for Profile"
							return Response(JSONRenderer().render(return_response))
						elif is_valid != 1:
							return_response["status"]="failure"
							return_response["errors"]="Exception : "+str(is_valid)
							return_response["value"]="Exception : "+str(is_valid)
							return Response(JSONRenderer().render(return_response))
						#if is_valid == 1:
							
				scan_id=obj.main_start(scan_attributes.data["project_name"],scan_attributes.data["IP_range"],scan_attributes.data["Port_range"],scan_attributes.data["switch"],"1","init",int(scan_attributes.data["profile"]),scan_attributes.data["assessment_id"],scan_attributes.data["app_id"])

				if scan_id != -1:
					my_obj=IPtable.IPtable()
					my_obj.Update_status_to_paused_or_processing(scan_id,'processing')
					if scan_attributes.data["mode"]=="sequential_default":
						#print "\n\n\n\nabout to update mode : "+ str(scan_attributes.data["mode"])
						my_objj=IPtable.Projects()
						my_objj.Update_mode(scan_id,'sequential_default')
				
					return_response["status"]="success" #+str(scan_attributes.data["project_name"])
					return_response["project_id"]=str(scan_id)
					#print "About to return the response :"+str(return_response)
					return_response["value"]=str(scan_id)
					if scan_attributes.data["edit_profile"]=="1":
						dir_obj.project_id=int(scan_id)
						status=dir_obj.init_project_directory()
						if status == -1:
							return_response["status"]="failure"
							return_response["value"]="Scan has started but Not able to create the Directory"
						else:
							stat=profile.CreateCustom(dir_obj.data_path,profile_json,str(scan_id),profile_id,scan_attributes.data["assessment_id"])
							if stat["status"] !="success":
								return_response["status"]="failure"
								return_response["value"]=stat["status"]
							else:
								return_response["profile_id"]=stat["value"]
								IPtable.Projects().UpdateProjectProfile(scan_id,stat["value"])
				else:
					return_response["status"]="failure"
					return_response["value"]="-1"

				return Response(JSONRenderer().render(return_response))

			return_response["status"]="failure"
			return_response["errors"]=scan_attributes.errors
			return_response["value"]=scan_attributes.errors
			#return Response(return_response)	
			return Response(JSONRenderer().render(return_response))
		except Exception ,ee:
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]=str(ee)
			#return Response(return_response)	
			return Response(JSONRenderer().render(return_response))

	def get(self,request,format=None):
		Employee_dict={}
		Employee_list=[]
		Employee_dict["id"]=1
		Employee_dict["name"]="Furqan Khan"
		Employee_list.append(Employee_dict)
		Employee_dict={}
		Employee_dict["id"]=2
		Employee_dict["name"]="Burhan Khan"
		Employee_list.append(Employee_dict)
		serialize=UserSerializer(Employee_list,many=True)
		return Response(serialize.data)

class ScanProfile(APIView):

	def __init__(self):
		self.folder_dir=os.path.dirname(os.path.realpath(__file__))
		self.Mapper_Json=os.path.join(self.folder_dir,"mapper.json")

	def return_json(self,json_file):
		with open (json_file,"r+") as json_file:
			all_json=json.loads(json_file.read())
		return all_json

	def get(self,request,format=None):
		try:
			response_text={}
			return_response={}
			response_text["status"]="success"
			profile_id=request.data["profile_id"]
			print "profile id is : "+str(profile_id) +str(type(profile_id))
			if type(profile_id)==type([]):
				print "Type list"
				profile_id=profile_id[0]
				print "obtained"
			print "id is : "+str(profile_id)
			if 1:#int(profile_id )!=0:
				ret_val=IPtable.Projects().Profile(profile_id)
				print str(ret_val)
				profile=ret_val[0]
				#print "Output is : "+str(profile) +str(profile_list)
				if profile ==-1:
					return_response["status"]="failure"
					return_response["errors"]="Some error occured.Profile Not found"
					return_response["value"]="Some error occured.Profile Not found"
					return Response(JSONRenderer().render(return_response))
					#return 
				if profile=="Master":
					profile_file=os.path.join(self.folder_dir,"Master.json")
				elif profile=="Custom_Mandatory" or profile=="Mandatory":
					profile_file=os.path.join(self.folder_dir,"Mandatory.json")
				elif profile=="Custom_Analytical" or profile=="Analytical":
					profile_file=os.path.join(self.folder_dir,"Analytical.json")
				else:
					profile_file=ret_val[1]
				c={}		
				with open (profile_file,"r+") as custom_json:
							c["data"]=json.loads(custom_json.read())
				c["id"]=ret_val[2]
				c["name"]=ret_val[0]
				#print "Length is : "+str(len(custom_j))
				response_text["Custom_json"]=c
				response_text["Mapper_json"]=self.return_json(self.Mapper_Json)

			return Response(JSONRenderer().render(response_text))
		except Exception ,ee:
			print "EXception @@: "+str(ee)
			return_response={}
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))

	def post(self,request,format=None):
		try:
			response_text={}
			response_text["status"]="success"
			profile_id=request.data["profile_id"]
			ret_val=IPtable.Projects().ShareProfile(profile_id)
				
			return Response(JSONRenderer().render(ret_val))
		except Exception ,ee:
			return_response={}
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))

class ScanProfiles(APIView):
	
	def __init__(self):
		self.folder_dir=os.path.dirname(os.path.realpath(__file__))
		self.results_path=os.path.join(self.folder_dir,"Results")
		self.folder_name=os.path.join(self.results_path,"Data_")
		self.All_Json=os.path.join(self.folder_dir,"all_commands.json")
		self.Master_Json=os.path.join(self.folder_dir,"Master.json")
		self.Mandatory_Json=os.path.join(self.folder_dir,"Mandatory.json")
		self.Analytical_Json=os.path.join(self.folder_dir,"Analytical.json")
		self.Mapper_Json=os.path.join(self.folder_dir,"mapper.json")

	def return_json(self,json_file):
		with open (json_file,"r+") as json_file:
			all_json=json.loads(json_file.read())
		return all_json
		
	def get(self,request,format=None):
		try:
			print "Hello recieved request !!"
			
			response_text={}
			response_text["status"]="success"
			response_text["All_json"]=self.return_json(self.All_Json)
			response_text["Master_json"]=self.return_json(self.Master_Json)
			response_text["Mandatory_json"]=self.return_json(self.Mandatory_Json)
			response_text["Analytical_json"]=self.return_json(self.Analytical_Json)
			response_text["Mapper_json"]=self.return_json(self.Mapper_Json)
			response_text["Custom_json"]=''
			#print str(request.data["profile_ids"])
			profile_ids=request.data["profile_ids"]
			print "profile id is --->: "+str(profile_ids) +str(type(profile_ids))
			if profile_ids !=0:
				print "Not zero !" +str(profile_ids)
				ret_val=IPtable.Projects().Profile('',True,profile_ids) 
				if ret_val["status"]=="success":
					print "success @@@@"
					custom_json_files=ret_val["value"]
					custom_j=[]
					for custom in custom_json_files:
						print custom["id"]
						c={}
						c["id"]=custom["id"]
						c["name"]=custom["name"]
						#with open (custom["path"],"r+") as custom_json:
						#	c["data"]=json.loads(custom_json.read())
						custom_j.append(c)
					print "Length is : "+str(len(custom_j))
					response_text["Custom_json"]=custom_j
			return Response(JSONRenderer().render(response_text))
		except Exception ,ee:
			return_response={}
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))

	def post(self,request,format=None): #Creating a new Custom Profile
		try:
			return_response={}
			profile_attributes=ProfileAttributes(data=request.data)
			if profile_attributes.is_valid():
			
				obj=Gui_main_driver.Gui_main()
				profile_id=int(profile_attributes.data["profile_id"])
				print "Obtained Profile id : is " +str(profile_id)
				if profile_id not in [1,2,3,4,5]:
						return_response["status"]="failure"
						return_response["errors"]="Custom Profile can be inherited only from Master ,Mandatory and Analytical Profiles"
						return_response["value"]="Custom Profile can be inherited only from Master ,Mandatory and Analytical Profiles"
						return Response(JSONRenderer().render(return_response))
				profile_name=profile_attributes.data["profile_name"]
				dir_obj=InitDirectory()
				profile=ValidateProfile.Profile()

				try:
					profile_json=json.loads(profile_attributes.data["profile_json"])
					ass_id=profile_attributes.data["assessment_id"]
					is_valid=profile.validateProfile(profile_id,profile_json)
					if is_valid in [-1, -2] :
						return_response["status"]="failure"
						return_response["errors"]="Invalid Json Data / Value passed for Profile"
						return_response["value"]="Invalid Json Data / Value  passed for Profile"
						return Response(JSONRenderer().render(return_response))
					elif is_valid != 1:
						return_response["status"]="failure"
						return_response["errors"]="Exception : "+str(is_valid)
						return_response["value"]="Exception : "+str(is_valid)
						return Response(JSONRenderer().render(return_response))
					else:
						custom_file=os.path.join(dir_obj.profiles_path,str(ass_id)+str(".json"))
						save_p=IPtable.Projects().SaveProfile(custom_file,ass_id,profile_name,"Custom")
					
						if save_p["status"]=="success":
							with open (custom_file,"w+") as custom:
								custom.write(json.dumps(profile_json,indent=4))
						else:
							save_p["value"]="Kindly check ,if you are giving UNique name to your profile"

						return Response(JSONRenderer().render(save_p))	
				except Exception ,exc:
					return_response["status"]="failure"
					return_response["errors"]="Exception : "+str(exc)
					return_response["value"]="Exception : "+str(exc)
					return Response(JSONRenderer().render(return_response))	
					
			else:
				return_response["status"]="failure"
				return_response["errors"]=profile_attributes.errors
				return_response["value"]=profile_attributes.errors
				#return Response(return_response)	
				return Response(JSONRenderer().render(return_response))

			
		except Exception ,ex:
			return_response={}
			return_response["status"]="failure"
			return_response["errors"]=str(ex)
			return_response["value"]=str(ex)
			return Response(JSONRenderer().render(return_response))

		

class StopScan(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the scan/project id 
	and would invoke appropriate backend python files Gui_main_driver.py to stop the scan 
	
	In order to understand about input given to this method and response returned read API documentation.
	"""
	
	#@csrf_exempt
	#@method_decorator(csrf_protect)
	def post(self,request,format=None):
		return_response={}
		try:
			scan_attributes=General(data=request.data)
			return_response={}
		
			if scan_attributes.is_valid():
				#return Response(scan_attributes.data)
				obj=Gui_main_driver.Gui_main()
			
				scan_id=obj.main_pause(scan_attributes.data["project_id"],'','')
				if scan_id !=0:
					return_response["status"]="success" #+str(scan_attributes.data["project_name"])
				else:
					return_response["status"]="failure"
				return_response["response_code"]=str(scan_id)
				return_response["value"]=str(scan_id)
				#return Response(JSONRenderer().render(return_response))
				return Response(JSONRenderer().render(return_response))

			return_response["status"]="failure"
			return_response["errors"]=scan_attributes.errors
			return_response["value"]=scan_attributes.errors
			return Response(JSONRenderer().render(return_response))
		except Exception ,ee:
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))



class StopScanConc(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the scan/project id 
	and would invoke appropriate backend python files Gui_main_driver.py to stop the scan 
	
	Note :This class would serve the purpose of stopping concurrent scan.Thus actually it would pause
	both the discovery as well as the vulnerability scanning phase.

	In order to understand about input given to this method and response returned read API documentation.
	"""
	#@csrf_exempt
	def post(self,request,format=None):
		try:
			scan_attributes=General(data=request.data)
			return_response={}
			pause_discovery=True
			pause_exploits=True
			if scan_attributes.is_valid():
				#return Response(scan_attributes.data)
				obj=Gui_main_driver.Gui_main()
				my_obj=IPtable.IPtable()
				stat=IPtable.Projects().fetch_project_status(scan_attributes.data["project_id"])
				if stat["status"]=="success":
					if stat["value"]["project_status"]=="complete":
						pause_discovery=False
					if stat["value"]["project_exploits_status"]=="complete":
						pause_exploits=False
					
				else:
						return_response["status"]="failure" #+str(scan_attributes.data["project_name"])
						return_response["errors"]="Scan can not be started.Some error occured"
						return_response["value"]="Scan status could not be fetched !!!"
						return Response(JSONRenderer().render(return_response))

				if pause_discovery:
					scan_id=obj.main_pause(scan_attributes.data["project_id"],'','')
					#<<<<<<< HEAD
					
					#return Response(JSONRenderer().render(return_response))
					#return Response(JSONRenderer().render(return_response))

				if pause_exploits:
					scan_id=obj.exploits_pause(scan_attributes.data["project_id"],True)

				if pause_discovery or pause_exploits:
					return_response["status"]="success" #+str(scan_attributes.data["project_name"])
					return_response["response_code"]=str(scan_id)
					return_response["value"]=str(scan_id)			
					return Response(JSONRenderer().render(return_response))
				else:
					return_response["status"]="failure"
					return_response["errors"]="CANT pause scan with status as complete"
					return_response["value"]="CANT pause scan with status as complete"
					return Response(JSONRenderer().render(return_response))
				
					#=======
					"""return_response["status"]="success" #+str(scan_attributes.data["project_name"])
					return_response["response_code"]=str(scan_id)
					return_response["value"]=str(scan_id)
					#return Response(JSONRenderer().render(return_response))
					return Response(JSONRenderer().render(return_response))"""

					"""if pause_exploits:
						#exp_id=obj.exploits_pause(scan_attributes.data["project_id"],True)
							
						return_response["status"]="failure" #+str(scan_attributes.data["project_name"])
						return_response["response_code"]="0"
						return_response["value"]="Pause in cuncurrent mode is avalible only with port scanning not with service scanning-Kindly go to current svans tab and select this project in order to restore the state"
						#return Response(JSONRenderer().render(return_response))
						return Response(JSONRenderer().render(return_response))
					#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6"""
			else:
				return_response["status"]="failure"
				return_response["errors"]=scan_attributes.errors
				return_response["value"]=scan_attributes.errors
				return Response(JSONRenderer().render(return_response))
		except Exception ,ee:
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))


class Switches(APIView):
	def get(self,request,format=None):
		try:
			ret_val={}
			switches={}
			obj=IPtable.IPtable()
			resp=obj.getSwitch()
			#<<<<<<< HEAD
			#print "Obtained response is :"+str(resp)
			#=======
			#print "Obtained response is :"+str(resp)
			#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
			return Response(JSONRenderer().render(resp))
		
		except Exception,ex:
			ret_val["status"]="failure"
			ret_val["value"]=str(ex)
			return Response(JSONRenderer().render(ret_val))

class ResumeScanConc(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the scan/project id 
	and would invoke appropriate backend python files Gui_main_driver.py to resume paused the scan 
	
	Note :This class would serve the purpose of resuming concurrent scan.Thus actually it would pause
	both the discovery as well as the vulnerability scanning phase.

	In order to understand about input given to this method and response returned read API documentation.
	"""
	#@csrf_exempt
	def post(self,request,format=None):
		try:
			scan_attributes=General(data=request.data)
			return_response={}
		
			if scan_attributes.is_valid():
				#return Response(scan_attributes.data)
				obj=Gui_main_driver.Gui_main()	
				
				my_obj=IPtable.IPtable()
				stat=IPtable.Projects().fetch_project_status(scan_attributes.data["project_id"])
				if stat["status"]=="success":
					if stat["value"]["project_status"]=="complete":
						my_obj.Update_status_to_paused_or_processing(scan_attributes.data["project_id"],'complete',False,False)
						my_obj.Update_status_to_paused_or_processing(scan_attributes.data["project_id"],'processing',True,False)
						return_response["status"]="success" #+str(scan_attributes.data["project_name"])
						return_response["project_id"]=scan_attributes.data["project_id"]
						return_response["value"]=scan_attributes.data["project_id"]
						return Response(JSONRenderer().render(return_response))
				else:
						return_response["status"]="failure" #+str(scan_attributes.data["project_name"])
						return_response["errors"]="Scan can not be started.Some error occured"
						return_response["value"]="Scan status could not be fetched !!!"
						return Response(JSONRenderer().render(return_response))

				scan_id=obj.main_resume(scan_attributes.data["project_id"],'','',True)
				if scan_id !=-1:
						my_obj.Update_status_to_paused_or_processing(scan_attributes.data["project_id"],'processing',True,True)
						return_response["status"]="success" #+str(scan_attributes.data["project_name"])
						return_response["project_id"]=str(scan_id)
						return_response["value"]=str(scan_id)
						return Response(JSONRenderer().render(return_response))
				else:
					return_response["status"]="failure" #+str(scan_attributes.data["project_name"])
					return_response["errors"]="Scan can not be started.Some error occured"
					return_response["value"]="Some error occured and scan did not start"
					return Response(JSONRenderer().render(return_response))

			else:
				return_response["status"]="failure"
				return_response["errors"]=scan_attributes.errors
				return_response["value"]=scan_attributes.errors
				return Response(JSONRenderer().render(return_response))	
		except Exception ,ee:
			
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))

			

class StopExploits(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the scan/project id 
	and would invoke appropriate backend python files Gui_main_driver.py to stop the vulnerability scan 
	
	In order to understand about input given to this method and response returned read API documentation.
	"""
	#@csrf_exempt
	def post(self,request,format=None):
		try:
			return_response={}
			scan_attributes=General(data=request.data)
			if scan_attributes.is_valid():
				#return Response(scan_attributes.data)
				try:
					concurrent=request.data["concurrent"]
				except Exception ,ex:
					return_response["status"]="failure"
					return_response["errors"]="Required Concurrent Field"
					return_response["value"]="Required Concurrent Field"
					return Response(JSONRenderer().render(return_response))
	
				obj=Gui_main_driver.Gui_main()
				scan_id=obj.exploits_pause(scan_attributes.data["project_id"],concurrent)
				return_response["status"]="success" #+str(scan_attributes.data["project_name"])
				return_response["response_code"]=str(scan_id)
				return_response["value"]=str(scan_id)
				return Response(JSONRenderer().render(return_response))

			return_response["status"]="failure"
			return_response["errors"]=scan_attributes.errors
			return_response["value"]=scan_attributes.errors
			return Response(JSONRenderer().render(return_response))
		except Exception ,ee:
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))


class ResumeScan(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the scan/project id 
	and would invoke appropriate backend python files Gui_main_driver.py to resume the scan. 
	
	In order to understand about input given to this method and response returned read API documentation.
	"""
	#@csrf_exempt
	def post(self,request,format=None):
		scan_attributes=General(data=request.data)
		return_response={}
		
		if scan_attributes.is_valid():
			#return Response(scan_attributes.data)
			obj=Gui_main_driver.Gui_main()
			
			scan_id=obj.main_resume(scan_attributes.data["project_id"],'','')
			if scan_id != -1:
				my_obj=IPtable.IPtable()
				my_obj.Update_status_to_paused_or_processing(scan_id,'processing')
				return_response["status"]="success" #+str(scan_attributes.data["project_name"])
				return_response["project_id"]=str(scan_id)
				return_response["value"]=str(scan_id)
				return Response(JSONRenderer().render(return_response))
			else:
				return_response["status"]="failure" #+str(scan_attributes.data["project_name"])
				return_response["errors"]="Some exception occured ,Cant resume project"
				return_response["value"]="Some exception occured,Cant resume project"
				return Response(JSONRenderer().render(return_response))

		return_response["status"]="failure"
		return_response["errors"]=scan_attributes.errors
		return_response["value"]=scan_attributes.errors
		return Response(JSONRenderer().render(return_response))	



class ResumeExploits(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the scan/project id 
	and would invoke appropriate backend python files Gui_main_driver.py to resume  the vul scan 
	
	In order to understand about input given to this method and response returned read API documentation.
	"""
	#@csrf_exempt
	def post(self,request,format=None):
		try:
			scan_attributes=General(data=request.data)
			return_response={}
		
			if scan_attributes.is_valid():
				#return Response(scan_attributes.data)
				obj=Gui_main_driver.Gui_main()			
				exploit_status=obj.exploits_resume(scan_attributes.data["project_id"])
				if exploit_status["status"]=="success":
						my_obj=IPtable.IPtable()
						my_obj.Update_status_to_paused_or_processing(scan_attributes.data["project_id"],'processing',True)

				return_response["status"]="success" #+str(scan_attributes.data["project_name"])
				return_response["project_id"]=str(scan_attributes.data["project_id"])
				return_response["value"]=str(scan_attributes.data["project_id"])
				return Response(JSONRenderer().render(return_response))
			return_response["status"]="failure"
			return_response["errors"]=scan_attributes.errors
			return_response["value"]=scan_attributes.errors
			return Response(JSONRenderer().render(return_response))	
		except Exception ,ee:
			
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))


class ProjectStatus(APIView):
	

	def get(self,request,format=None):
		try:
			obj=IPtable.Projects()
			
			to_validate=General(data=request.data)
			if to_validate.is_valid():
				data=obj.fetch_project_status(to_validate.data["project_id"])
				return Response(JSONRenderer().render(data))
		except Exception ,ee:
			resp_text={}
			resp_text["status"]="failure"
			resp_text["value"]=str(ee)
			return Response(JSONRenderer().render(resp_text))
			

class ExploitableProjects(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would return the project id's of the
	projects for which the discovery would be over and would be eligible for vulnerability scan

	In order to understand about input given to this method and response returned read API documentation.
	"""

	def get(self,request,format=None):
		try:
			paused=request.data["paused"]
			obj=IPtable.Projects()
			if paused==True:
				projects=obj.completed_projects(None,True)	
			else:
				projects=obj.completed_projects()
			project_list=[]
			for project in projects:
				#print str(project[0])+ "   " +str(project[1])
				project_dict={}
				project_dict["id"]=project[0]
				project_dict["name"]=project[1]
				project_dict["project_status"]=project[2]
				project_dict["project_status_exploits"]=project[3]
				project_dict["mode"]=project[4]
				#,mode,Date,IPrange,Port_range,switch
				project_dict["Date"]=str(project[5]).split()[0]
				project_dict["Time"]=str(project[5]).split()[1]
				project_dict["IPrange"]=project[6]
				project_dict["port_range"]=project[7]
				project_dict["switch"]=project[8]
				project_list.append(project_dict)
		
			#print "\n\n\n My val is --->"+str(project_list)
			return_response={}
		
			if 1:#serialize.is_valid():
				return_response["status"]="success"
				#return_response["data"]=serialize.data
				return_response["data"]=project_list
			
			return Response(JSONRenderer().render(return_response))	

		except Exception ,ee:
			return_response={}
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))	
		



class ExploitConfig_overwrite(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the updated configuration 
	for a project and would delete the old configuration and results and would update to default
 	configuration .Thus invoking the file Gui_main_driver.py for the method updateDefaultconfiguration()
	In order to understand about input given to this method and response returned read API documentation.
	"""

	def configure_response(self,default_config):
			#<<<<<<< HEAD
			#print "IN configure response !"
			#=======
			#print "IN configure response !"
			#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
			config_list=[]
			config_dict={}
			return_val=[]
			for config in default_config["value"]:
				#<<<<<<< HEAD
				#print str(config)
				#=======
				#print str(config)
				#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
				config_dict={}
				#print str(project[0])+ "   " +str(project[1])
				config_dict["id"]=config[0]
				config_dict["project_id"]=config[1]
				config_dict["host"]=config[2]
				config_dict["port"]=config[3]
				config_dict["service"]=config[4]
				config_dict["project_status"]=config[5]
				config_dict["Commands"]=config[6]
				config_dict["reconfig_service"]=False
				config_dict["reconfig_exploit"]=False
				if len(config)> 7:
					config_dict["service_type"]=config[7]
				if len(config)>8:
					config_dict["state"]=config[8]
					config_dict["version"]=config[9]
				if len(config) >9:
					config_dict["test_case"]=config[10]
				
				

				config_list.append(config_dict)
			return_val.append(config_dict)
			return_val.append(config_list)
			return return_val
		

	def post(self,request,format=None):
		#<<<<<<< HEAD
		#print "\n\n IN post method of config overwrite !!!"
		#=======
		#print "\n\n IN post method of config overwrite !!!"
		#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
		obj=Gui_main_driver.Gui_main()
		project_id=request.data["project_id"]
		continue_=False
		delete=True	
		default_config=obj.Overwrite_and_GetDefaultConfiguration(project_id,'','',continue_,delete,False)
		if default_config["status"]=="reconfig":
			resp=self.configure_response(default_config)
			config_dict=resp[0]
			config_list=resp[1]
			#print "\n\n\n"+str(project_list)
			return_response={}
			
			if 1:#serialize.is_valid():
		
				return_response["status"]="success"
				#return_response["data"]=serialize.data  #Note Both work the same !!!
				return_response["data"]=config_list#serialize.data #Thus while reteriving data we can simply send back query list to json data !!.No need to build wrapper
			else:
				return_response["status"]="failure"
				return_response["errors"]=serialize.errors
				return_response["value"]=serialize.errors
		
			return Response(JSONRenderer().render(return_response))	
		else:
			#<<<<<<< HEAD
			#print "\n\nReturning default config \n\n"
			#=======
			#print "\n\nReturning default config \n\n"
			#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
			return Response(JSONRenderer().render(default_config))


class AddTestCase(APIView):

	
	def post(self,request,format=None):
		#<<<<<<< HEAD
		#print "hello world !!"
		#=======
		#print "hello world !!"
		#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
		return_response={}
		all_values=[]
		obj=Gui_main_driver.Gui_main()
		try: 
			
			project_id=request.data["project_id"]
			data_=Configuration(data=request.data["data"],many=True)
			concurrent=request.data["concurrent"] 

		except Exception ,ee:
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]="Error message is -->"+str(ee)
			return Response(JSONRenderer().render(return_response))	

		try:
			
			if data_.is_valid(): #list of dictionaries with each dictionary contains list of dict
				#<<<<<<< HEAD
				#print "Project id is : "+str(project_id)
				continue_=False
				delete=False
				#print str(all_values)
				#print "Concurrent value is :"+str(concurrent)
				#=======
				#print "Project id is : "+str(project_id)
				continue_=False
				delete=False
				#print str(all_values)
				#print "Concurrent value is :"+str(concurrent)
				#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
				if concurrent =="0":	
					update_result=obj.InsertDefaultconfiguration(data_.data,project_id)
				elif concurrent=="1":
					update_result=obj.InsertDefaultconfiguration(data_.data,project_id,'','',True)
				
				
				#print "The length of elements returned :"+str(len(update_result))
				#print "\n\nObtained result is :" +str(update_result)
				return_response["status"]="success"
				return_response["value"]=update_result[0] #tedupdate status of services
				return_response["data"]=update_result[1] #the list of updated services
			else:
				return_response["status"]="failure"
				return_response["value"]="Error message is :"+str(data_.errors)
				return_response["errors"]=data_.errors

		except Exception ,ee:
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]="Error message is :"+str(ee)
			return Response(JSONRenderer().render(return_response))	

		return Response(JSONRenderer().render(return_response))	

class ExploitConfig(APIView):

	"""
	Objective :
	The objective of this class is to serve the Post method which would take the updated configuration 
	for a project and would update the configuration .Thus invoking the file Gui_main_driver.py for the 
	method updateDefaultconfiguration().Finally it will return the updated configuration
	In order to understand about input given to this method and response returned read API documentation.
	"""


	def post(self,request,format=None):
		#<<<<<<< HEAD
		#print "hello world !!"
		#=======
		#print "hello world !!"
		#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
		return_response={}
		all_values=[]
		obj=Gui_main_driver.Gui_main()
		try: 
			concurrent=request.data["concurrent"]
			project_id=request.data["project_id"]
			data_=Configuration(data=request.data["data"],many=True) #it transforms the underlying dictionary to ordered dictionary which is nothing but cololection of tuples.It does that recursively
			 #data_=test_multi(data=request.data["data"],many=True)
		except Exception ,ee:
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]="Error message is -->"+str(ee)
			return Response(JSONRenderer().render(return_response))	

		try:
			
			if data_.is_valid(): #list of dictionaries with each dictionary contains list of dict
				#<<<<<<< HEAD
				#print "Project id is : "+str(project_id)
				continue_=False
				delete=False
				#print str(all_values)
				#=======
				#print "Project id is : "+str(project_id)
				continue_=False
				delete=False
				#print str(all_values)
				#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
				if concurrent =="0":	
					update_result=obj.updateDefaultconfiguration(data_.data,project_id)
				elif concurrent=="1":
					update_result=obj.updateDefaultconfiguration(data_.data,project_id,'','',True)
				#<<<<<<< HEAD
				#print "The length of elements returned :"+str(len(update_result))
				#=======
				#print "The length of elements returned :"+str(len(update_result))
				#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
				#print "\n\nObtained result is :" +str(update_result)
				return_response["status"]="success"
				return_response["value"]=update_result[0] #tedupdate status of services
				return_response["data"]=update_result[1] #the list of updated services
			else:
				return_response["status"]="failure"
				return_response["value"]="Error message is :"+str(data_.errors)
				return_response["errors"]=data_.errors
		except Exception ,ee:
			return_response["status"]="failure"
			return_response["errors"]=str(ee)
			return_response["value"]="Error message is :"+str(ee)
			return Response(JSONRenderer().render(return_response))	

		return Response(JSONRenderer().render(return_response))	
		
	def configure_response(self,default_config):
			#<<<<<<< HEAD
			#print "IN configure response !"
			#=======
			#print "IN configure response !"
			#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
			config_list=[]
			config_dict={}
			return_val=[]
			for config in default_config["value"]:
				#print str(config)
				config_dict={}
				#print str(project[0])+ "   " +str(project[1])
				config_dict["id"]=config[0]
				config_dict["project_id"]=config[1]
				config_dict["host"]=config[2]
				config_dict["port"]=config[3]
				config_dict["service"]=config[4]
				config_dict["project_status"]=config[5]
				config_dict["Commands"]=config[6]
				config_dict["reconfig_service"]=False
				config_dict["reconfig_exploit"]=False
				if len(config)> 7:
					config_dict["service_type"]=config[7]
				if len(config)>8:
					config_dict["state"]=config[8]
					config_dict["version"]=config[9]
				if len(config) >9:
					config_dict["test_case"]=config[10]
				
				
				config_list.append(config_dict)
			return_val.append(config_dict)
			return_val.append(config_list)
			return return_val
		

	def get(self,request,format=None):
		obj=Gui_main_driver.Gui_main()
		project_id=request.data["project_id"]
		continue_=False
		delete=False	
		default_config=obj.getDefaultConfiguration(project_id,continue_,delete,False)
		if default_config["status"]=="reconfig":
			resp=self.configure_response(default_config)
			config_dict=resp[0]
			config_list=resp[1]
			#print "\n\n\n"+str(project_list)
			return_response={}
			try:
				#<<<<<<< HEAD
				print "Reached here in TRy"
				#=======
				#print "Reached here"
				#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
				#serialize=Configuration(data=config_dict)
				#print "\n\n\nseturnrializers are :"+str(serialize)+"\n\n"

			except Exception ,ee :
				print "EXception " +str(ee)
				return_response["status"]="failure"
				return_response["errors"]=str(ee)
				return_response["value"]=str(ee)
				return Response(JSONRenderer().render(return_response))	
		

			
			if 1:#serialize.is_valid():
		
				return_response["status"]="success"
				#return_response["data"]=serialize.data  #Note Both work the same !!!
				return_response["data"]=config_list#serialize.data #Thus while reteriving data we can simply send back query list to json data !!.No need to build wrapper
				
			else:
				return_response["status"]="failure"
				return_response["errors"]=serialize.errors
				return_response["value"]=serialize.errors
		
			return Response(JSONRenderer().render(return_response))	
		else:
			#<<<<<<< HEAD
			#print "\n\nReturning default config \n\n"
			#=======
			#print "\n\nReturning default config \n\n"
			#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
			return Response(JSONRenderer().render(default_config))
		
		

class LaunchExploits(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the project id as input and
	would start vulneraibility scanning for the obtained project id.
	It invokes Gui_main_driver.py file to start vulneribility scanning.
	In order to understand about input given to this method and response returned read API documentation.
	"""

	def post(self,request,format=None):
		try:	
			self.project_obj=IPtable.Projects()		
			obj=Gui_main_driver.Gui_main()
			exploit_data=Exploits(data=request.data)
			return_response={}
			if(exploit_data.is_valid()):
				project_id=exploit_data.data["project_id"]
				continue_=True
				delete=False
				get_default_config=False
				threading=exploit_data.data["threading"]
				result=self.project_obj.completed_projects(int(project_id))
				if result[0] > 0:
					exploit_status=obj.LaunchExploits(project_id,continue_,delete,get_default_config,threading)
					if exploit_status["status"]=="success":
						my_obj=IPtable.IPtable()
						my_obj.Update_status_to_paused_or_processing(project_id,'processing',True)

					
					return_response["status"]=exploit_status["status"]
					return_response["value"]=exploit_status["value"]
				else:
					return_response["status"]="failure"
					return_response["value"]="In valid project id ."

			else:
				return_response["status"]="failure"
				return_response["errors"]=exploit_data.errors
				return_response["value"]=exploit_data.errors
			return Response(JSONRenderer().render(return_response))
	
		except Exception,ee:
			return_response={}
			return_response["status"]="failure"
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))


class LaunchExploitsConcurrent(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the project id as input and
	would start vulneraibility scanning for the obtained project id.
	It invokes Gui_main_driver.py file to start vulneribility scanning in concurrent mode.
	In order to understand about input given to this method and response returned read API documentation.
	"""

	def post(self,request,format=None):
		try:			
			obj=Gui_main_driver.Gui_main()
			exploit_data=ExploitsConcurrent(data=request.data)
			return_response={}
			if(exploit_data.is_valid()):
				project_id=exploit_data.data["project_id"]
				continue_=True
				delete=False
				get_default_config=False
				threading=exploit_data.data["threading"]
				if threading==True:
					threading=False
				rec_list=exploit_data.data["record_list"]
				exploit_status=obj.LaunchExploits(project_id,continue_,delete,get_default_config,False,True,rec_list)
				return_response["status"]=exploit_status["status"]
				return_response["value"]=exploit_status["value"]
			else:
				return_response["status"]="failure"
				return_response["errors"]=exploit_data.errors
				return_response["value"]=exploit_data.errors
			return Response(JSONRenderer().render(return_response))
	
		except Exception,ee:
			return_response={}
			return_response["status"]="failure"
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))

class DownloadAllMannual(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the project id as input and
	would return a zipped folder containing all the reports, pcap files and etc.

	In order to understand about input given to this method and response returned read API documentation.
	"""

	def __init__(self):
		self.folder_dir=os.path.dirname(os.path.realpath(__file__))
		self.results_path=os.path.join(self.folder_dir,"Results")
		self.folder_name=os.path.join(self.results_path,"Data_")
		self.All_Json=os.path.join(self.folder_dir,"all_commands.json")
		self.Master_Json=os.path.join(self.folder_dir,"Master.json")
		self.Mandatory_Json=os.path.join(self.folder_dir,"Mandatory.json")
		self.Analytical_Json=os.path.join(self.folder_dir,"Analytical.json")



	def zipdir(self,path,ziph):
		for dirname,subdirs,files in os.walk(path):
			abs_path_dir=dirname
			rel_path_dir=abs_path_dir[len(path)+len(os.sep):]
			#<<<<<<< HEAD
			#print "ADd dir is :"+str(rel_path_dir)
			#=======
			#print "ADd dir is :"+str(rel_path_dir)
			#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
			for file_ in files:
					abs_path=os.path.join(dirname,file_)
					rel_path=abs_path[len(path)+len(os.sep):]
					ziph.write(abs_path,rel_path)
	
	def init_project_directory(self,project_id):
		#print "Initialising parent directory "
		try:
			if not os.path.exists(self.folder_name+str(project_id)):
				return -1
			return 1;
		except Exception ,ee:
			#self.print_Error("Error while creating directory !!"+str(ee))
			print "EX "+str(ee)
			return -1
	
	def post(self,request,format=None):
			self.project_obj=IPtable.Projects()
			try:
				return_response={}
				to_validate=General(data=request.data)
				if to_validate.is_valid():
					#<<<<<<< HEAD
					#print str(to_validate.data)
					#=======
					#print str(to_validate.data)
					#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
					project_id=to_validate.data["project_id"]
					result=self.project_obj.completed_projects(int(project_id))
					print "Result is : " +str(result)
					if result[0] > 0:
						status=self.init_project_directory(project_id)
						print "status is : "+str(status)
						if status != -1:
							my_obj=IPexploits.IPexploits()
							my_obj.data_path=self.folder_name+str(project_id)
							my_obj.generate_report(project_id)
							self.data_path=self.folder_name+str(project_id)
							zip_folder_name="Data_"+str(project_id)+".zip"
							zip_folder_creation_path=os.path.join(self.results_path,zip_folder_name)
							zip_folder_path=self.data_path #file to be zipped
							zipf=zipfile.ZipFile(zip_folder_creation_path,'w',zipfile.ZIP_DEFLATED)
							self.zipdir(zip_folder_path,zipf)
							zipf.close()
							zip_file=open(zip_folder_creation_path,'rb')
							resp=HttpResponse(FileWrapper(zip_file),content_type="application/zip")
							resp['content-Disposition']='attachment;filename="%s"'%'text.zip'
							return resp
							
						else:
							return_response["status"]="failure"
							return_response["value"]="No data is present for the given project id :"
					else:
						return_response["status"]="failure"
						return_response["value"]="In valid project id ."


						
				else:
					return_response["status"]="failure"
					return_response["value"]=to_validate.errors
			
				return Response(JSONRenderer().render(return_response))
			except Exception ,ee:
				print "Exception ! " +str(ee)
				return_response={}
				return_response["status"]="failure"
				return_response["value"]=str(ee)
				return Response(JSONRenderer().render(return_response))


class MergeReports(APIView):

	"""
	Objective :
	The objective of this class is to serve the Post method which would take the project id as input and
	would return a zipped folder containing the merged qualys ,nessus and mannual vul scanning report.

	In order to understand about input given to this method and response returned read API documentation.
	"""


	def post(self,request,format=None):
			obj=Report_orchestration.Report_merger(True,True)
			self.project_obj=IPtable.Projects()
			try:
				return_response={}
				to_validate=Merge_reports(data=request.data)
				if to_validate.is_valid():
					#<<<<<<< HEAD
					#print str(to_validate.data)
					#=======
					#print str(to_validate.data)
					#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
					project_id=to_validate.data["project_id"]
					format_=to_validate.data["report_format"]
					#obj=Report_merger(True,True)
					result=self.project_obj.completed_projects(int(project_id))
					if result[0] > 0:
						resp=obj.generate_report(int(project_id),format_)
						if resp["status"]=="success":
							return_response["status"]="success"
							return_response["value"]=resp["value"]
							zip_file=open(resp["value"],'rb')
							resp=HttpResponse(FileWrapper(zip_file),content_type="application/zip")
							resp['content-Disposition']='attachment;filename="%s"'%'result.zip'
							return resp
						else:
							return_response["status"]="failure"
							return_response["value"]=resp["value"]
					else:
						return_response["status"]="failure"
						return_response["value"]="In valid project id ."


						
				else:
					return_response["status"]="failure"
					return_response["value"]=to_validate.errors
			
				return Response(JSONRenderer().render(return_response))
			except Exception ,ee:
				return_response={}
				return_response["status"]="failure"
				return_response["value"]=str(ee)
				return Response(JSONRenderer().render(return_response))

			
			
class UploadQualysXml(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the qualys xml report and 
	would parse it and store it in database table.

	In order to understand about input given to this method and response returned read API documentation.
	"""

	parser_classes=(MultiPartParser,)

	def post(self,request,format=None):
		try:
			#<<<<<<< HEAD
			#print "Inside Qualys XML :"
			#=======
			#print "Inside Qualys XML :"
			#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
			to_validate=UploadXml(data=request.data)
			return_response={}
			if to_validate.is_valid():
				file_obj=request.FILES['filename']
				F_validator=FileValidator.FileValidator()
				is_xml=F_validator.validateXML(file_obj)
				if is_xml:
					#print "Validation results are :-->" +str(is_xml)				
					#<<<<<<< HEAD
					#print str(file_obj.name)
					#=======
					#print str(file_obj.name)
					#>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
					folder_dir=os.path.dirname(os.path.realpath(__file__))
					results_path=os.path.join(folder_dir,"XML_reports")
					un_id=uuid.uuid1()
					pid=to_validate.data["project_name"]
					
					xml_file_name=str(file_obj.name)+"_pid:"+str(pid)+"_uid:"+str(un_id)+".xml"
					xml_file_path=os.path.join(results_path,xml_file_name)
					with open (xml_file_path,'wb') as out_file:
						for chunks in file_obj.chunks():
							out_file.write(chunks)
					#<<<<<<< HEAD
					#print "uploaded File :--> "+str(xml_file_path) 
					#=======
					#print "uploaded File :--> "+str(xml_file_path) 
					#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
					qualys=Qualys_parser.QualysParser()
					qualys_results=None
					val=qualys.parse(xml_file_path,int(pid))
					if val["status"]=="success":
						return_response["status"]="success"
						return_response["value"]=str(pid)
					else:
						return_response["status"]="failure"
						return_response["value"]=str(val["value"])
					os.remove(xml_file_path)
					#<<<<<<< HEAD
					#print "File removed"
					#=======
					#print "File removed"
					#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
				else:
					return_response["status"]="failure"
					return_response["value"]="Supplied file was not XML ,only XML type accepted"
			else:
				return_response["status"]="failure"
				return_response["value"]=to_validate.errors
				
			return Response(JSONRenderer().render(return_response))

		except Exception ,ee:
			return_response={}
			return_response["status"]="failure"
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))

class ReportOnFly(APIView):
	
	"""
	Objective :
	The objective of this class is to serve the Post method which would take either qualys or nessus 
	report as input at one time and would parse the report and map cve's with exploits and would
	return final copy of integrated report in the format chosen by user.

	In order to understand about input given to this method and response returned read API documentation.
	"""

	parser_classes=(MultiPartParser,)

	def post(self,request,format=None):
		try:
			to_validate=OnFly(data=request.data)
			return_response={}
			if to_validate.is_valid():
				file_obj=request.FILES['filename']
				F_validator=FileValidator.FileValidator()
				is_xml=F_validator.validateXML(file_obj)
				if is_xml:
					valid=["nessus","qualys"]
					if (to_validate.data["source"] not in valid):
						return_response["status"]="failure"
						return_response["value"]="The source of report must be either qualys or nessus"
						return Response(JSONRenderer().render(return_response))
										
					#<<<<<<< HEAD
					#print str(file_obj.name)
					#=======
					#print str(file_obj.name)
					#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
					folder_dir=os.path.dirname(os.path.realpath(__file__))
					results_path=os.path.join(folder_dir,"XML_reports")
					un_id=uuid.uuid1()
					xml_file_name=str(file_obj.name)+"_uid:"+str(un_id)+".xml"
					xml_file_path=os.path.join(results_path,xml_file_name)
					with open (xml_file_path,'wb') as out_file:
						for chunks in file_obj.chunks():
							out_file.write(chunks)
					#<<<<<<< HEAD
					#print "uploaded File -"+str(xml_file_path)
					#=======
					#print "uploaded File -"+str(xml_file_path)
					#>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
					if to_validate.data["source"]=="nessus":
						obj=Exploit_mapping.Exploit_mapping(xml_file_path)
					else:
						obj=Exploit_mapping.Exploit_mapping('',xml_file_path)

					val=obj.generate_report(to_validate.data["report_format"])
					os.remove(xml_file_path)
					if val["status"]=="success":
						#<<<<<<< HEAD
						#print "Success reutrned"
						#=======
						#print "Success reutrned"
						#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
						return_response["status"]="success"
						return_response["value"]=val["value"]
						zip_file=open(val["value"],'rb')
						resp=HttpResponse(FileWrapper(zip_file),content_type="application/zip")
						resp['content-Disposition']='attachment;filename="%s"'%'Report.zip'
						return resp

					else:
						return_response["status"]="failure"
						return_response["value"]=str(val["value"])
					
					
				else:
					return_response["status"]="failure"
					return_response["value"]="Supplied file was not XML ,only XML type accepted"
			else:
				return_response["status"]="failure"
				return_response["value"]=to_validate.errors
				
			return Response(JSONRenderer().render(return_response))

		except Exception ,ee:
			print "Inside exception :"+str(ee)
			return_response={}
			return_response["status"]="failure"
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))
			#return Response(status=204)


class UploadNessusXml(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the nessus xml report and 
	would parse it and store it in database table.

	In order to understand about input given to this method and response returned read API documentation.
	"""

	parser_classes=(MultiPartParser,)

	def post(self,request,format=None):
		try:
			to_validate=UploadXml(data=request.data)
			return_response={}
			if to_validate.is_valid():
				file_obj=request.FILES['filename']
				F_validator=FileValidator.FileValidator()
				is_xml=F_validator.validateXML(file_obj)
				if is_xml:
					#print "Validation results are :-->" +str(is_xml)				
					#<<<<<<< HEAD
					#print str(file_obj.name)
					#=======
					#print str(file_obj.name)
					#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
					folder_dir=os.path.dirname(os.path.realpath(__file__))
					results_path=os.path.join(folder_dir,"XML_reports")
					un_id=uuid.uuid1()
					pid=to_validate.data["project_name"]
					
					xml_file_name=str(file_obj.name)+"_pid:"+str(pid)+"_uid:"+str(un_id)+".nessus"
					xml_file_path=os.path.join(results_path,xml_file_name)
					with open (xml_file_path,'wb') as out_file:
						for chunks in file_obj.chunks():
							out_file.write(chunks)
					#<<<<<<< HEAD
					#print "uploaded File -"+str(xml_file_path)
					#=======
					#print "uploaded File -"+str(xml_file_path)
					#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
					nessus=Nessus_parser.Nessus_Parser()				
					nessus_results=None		#	('m.nessus','0','',"return"))	
					val=nessus.parse(xml_file_path,int(pid))
					if val["status"]=="success":
						return_response["status"]="success"
						return_response["value"]=str(pid)
					else:
						return_response["status"]="failure"
						return_response["value"]=str(val["value"])
					os.remove(xml_file_path)
					#<<<<<<< HEAD
					#print "File removed"
					#=======
					#print "File removed"
					#>>>>>>> b6b8e9ee72399e3d683c7808a85d7f1c8ce3cbf6
				else:
					return_response["status"]="failure"
					return_response["value"]="Supplied file was not XML ,only XML type accepted"
			else:
				return_response["status"]="failure"
				return_response["value"]=to_validate.errors
				
			return Response(JSONRenderer().render(return_response))

		except Exception ,ee:
			return_response={}
			return_response["status"]="failure"
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))
			#return Response(status=204)

class UploadNmapXml(APIView):
	"""
	Objective :
	The objective of this class is to serve the Post method which would take the nmap xml report and 
	would parse it and store it in database table.

	In order to understand about input given to this method and response returned read API documentation.
	"""

	parser_classes=(MultiPartParser,)

	def post(self,request,format=None):
		try:
			IPtable_obj=IPtable.IPtable()
			to_validate=UploadXmlNmap(data=request.data)
			return_response={}
			if to_validate.is_valid():
				file_obj=request.FILES['filename']
				F_validator=FileValidator.FileValidator()
				is_xml=F_validator.validateXML(file_obj)
				if is_xml:
					folder_dir=os.path.dirname(os.path.realpath(__file__))
					results_path=os.path.join(folder_dir,"XML_reports")
					pid=IPtable_obj.Insert(to_validate.data["project_name"],'import',str(file_obj.name))
					IPtable_obj.update_mapping(to_validate.data["app_id"],int(pid),to_validate.data["assessment_id"])
					if (pid==-1):
						return_response["status"]="failure"
						return_response["value"]="Some error occured while inserting details"
						return Response(JSONRenderer().render(return_response))
					
					xml_file_name=str(file_obj.name)+"_"+str(pid)
					xml_file_path=os.path.join(results_path,xml_file_name)
					with open (xml_file_path,'wb') as out_file:
						for chunks in file_obj.chunks():
							out_file.write(chunks)

					val=nmap_parser.Import('gui',xml_file_path,to_validate.data["project_name"],pid)
					if val["status"]=="success":
						return_response["status"]="success"
						return_response["value"]=str(pid)
						my_obj=IPtable.IPtable()
						my_obj.Update_status_to_paused_or_processing(pid,'complete')
					else:
						return_response["status"]="failure"
						return_response["value"]=str(val["value"])
				else:
					return_response["status"]="failure"
					return_response["value"]="Supplied file was not XML ,only XML type accepted"
			else:
				return_response["status"]="failure"
				return_response["value"]=to_validate.errors
				
			return Response(JSONRenderer().render(return_response))

		except Exception ,ee:
			return_response={}
			return_response["status"]="failure"
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))

class Reconfigure():
		"""
		Objective :
		The objective of this class is to help in reconfiguration of the input given by user for 
		updating configuration.It does not interact with the web service directly.

		In order to understand about input given to this method and response returned read API
 		documentation.
		"""

		def configure_response(self,default_config):
			config_list=[]
			config_dict={}
			record_list=[]
			return_val=[]
			
			for config in default_config["value"]:
				#print str(config)
				config_dict={}
				#print str(project[0])+ "   " +str(project[1])
				config_dict["id"]=config[0]
				record_list.append(config[0])
				config_dict["project_id"]=config[1]
				config_dict["host"]=config[2]
				config_dict["port"]=config[3]
				config_dict["service"]=config[4]
				config_dict["project_status"]=config[5]
				config_dict["Commands"]=config[6]
				config_dict["reconfig_service"]=False
				config_dict["reconfig_exploit"]=False
				if len(config)> 7:
					config_dict["service_type"]=config[7]
				if len(config)>8:
					config_dict["state"]=config[8]
					config_dict["version"]=config[9]
				if len(config) >9:
					config_dict["test_case"]=config[10]
				
				

				config_list.append(config_dict)
			return_val.append(config_dict)
			return_val.append(config_list)
			return_val.append(record_list)
			return return_val

class PollingConfig(APIView):

	"""
	Objective :
	The objective of this class is to serve the Post-Get methods which would take the project id and would
	return the configuration for the vul scanning for the records for which the discovery would be over.
	This is essentially used in concurrent mode

	In order to understand about input given to this method and response returned read API documentation.
	"""


	def get(self,request,format=None):
		try:
			return_response={}
			project_id=request.data["project_id"]
			obj=Polling.PollingExploits(int(project_id))
			continue_=False
			delete=False	
			
			default_config=obj.getConfiguration() #Get config of all records with pid
			if default_config["status"]=="reconfig":
				exp_obj=Reconfigure() 
				resp=exp_obj.configure_response(default_config)
				config_dict=resp[0]
				config_list=resp[1]
				record_list=resp[2]
				return_response["status"]="success"
				#return_response["data"]=serialize.data  #Note Both work the same !!!
				return_response["data"]=config_list
				return_response["record_list"]=record_list
				return Response(JSONRenderer().render(return_response))
	
			else:
				return Response(JSONRenderer().render(default_config))
		except Exception ,ee:
			return_response["status"]="failure"
			return_response["data"]=str(ee)
			return Response(JSONRenderer().render(return_response))
	
	def post(self,request,format=None):
		try:
			return_response={}
			update_data=Polling_(data=request.data)
			return_response={}
			if(update_data.is_valid()):
				project_id=update_data.data["project_id"]
				record_list=update_data.data["record_list"]
				obj=Polling.PollingExploits(int(project_id))
				return_response=obj.UpdateStatus(record_list)
				
			else:
				return_response["status"]="failure"
				return_response["errors"]=update_data.errors
				return_response["value"]=update_data.errors
			return Response(JSONRenderer().render(return_response))
		
		except Exception ,ee:
			return_response["status"]="failure"
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))

	
class PercentPolling(APIView):

	"""
	Objective :
	The objective of this class is to serve the Get-Post method which would return teh percantage of the
	completion in case of discovery and vulnerability scanning

	In order to understand about input given to this method and response returned read API documentation.
	"""


	def get(self,request,format=None):
		try:
			self.project_obj=IPtable.Projects()
			return_response={}
			poll_data=Poll_me(data=request.data)
			if poll_data.is_valid():
					project_id=request.data["project_id"]
					#result=self.project_obj.completed_projects(int(project_id))
					if 1:#result[0] > 0:
						obj=IPtable.Projects()
						continue_=False
						delete=False
						valid_source=["discovery","scan"]	
						if request.data["source"] not in valid_source:
							return_response["status"]="failure"
							return_response["data"]="The source can either be scan or discovery"
							return_response["value"]="The source can either be scan or discovery"
							return Response(JSONRenderer().render(return_response))
	
						
						poll_results=obj.Poll(int(project_id),request.data["source"])
						if poll_results != -1:
							return_response["status"]="success"
							#return_response["data"]=serialize.data  #Note Both work the same !!!
							return_response["data"]=poll_results[0]
							
							return_response["value"]=poll_results[0]
							return Response(JSONRenderer().render(return_response))
	
						else:
							return_response["status"]="failure"
							return_response["value"]="Cant fetch Polling status.Kindly check supplied params"
							return_response["data"]="Cant fetch Polling status.Kindly check supplied params"
							return Response(JSONRenderer().render(return_response))
					else:
						return_response["status"]="failure"
						return_response["value"]="In valid project id"
						return_response["data"]="In valid project id"
						return Response(JSONRenderer().render(return_response))

			else:
				return_response["status"]="failure"
				return_response["data"]=poll_data.errors
				return_response["errors"]=poll_data.errors
				return_response["value"]=poll_data.errors
				return Response(JSONRenderer().render(return_response))

	
		except Exception ,ee:
			return_response["status"]="failure"
			return_response["data"]=str(ee)
			return Response(JSONRenderer().render(return_response))
			

class ScannningStUp(APIView):
	def post(self,request,format=None):
		try:
			return_response={}
			update_data=General(data=request.data)
			try:
				concurrent=request.data["concurrent"] if request.data["concurrent"] != None else -1

			except:
				concurrent=-1
				print "In except and conc is :"+str(concurrent)
			return_response={}
			if(update_data.is_valid()):
				project_id=update_data.data["project_id"]
				#record_list=update_data.data["record_list"]
				
				obj=Polling.PollingExploits(int(project_id))

				if concurrent ==-1:
					return_response=obj.UpdateStatusExploit('',True)
				else:
					return_response=obj.UpdateStatusExploit('',True)
					return_response=obj.UpdateStatusInit()
				
			else:
				return_response["status"]="failure"
				return_response["errors"]=update_data.errors
				return_response["value"]=update_data.errors

			return Response(JSONRenderer().render(return_response))
		
		except Exception ,ee:
			return_response["status"]="failure"
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))

	
class PollingExploit(APIView):
	"""
	Objective :
	The objective of this class is to poll the vulnerability scanning and return results.

	In order to understand about input given to this method and response returned read API documentation.
	"""


	def get(self,request,format=None):
		try:
			self.project_obj=IPtable.Projects()
			return_response={}
			project_id=request.data["project_id"]
			#Note the project need not be having status as complete
			#as we might need this for concurrent mode also where the status 
			#of the master project might not be complete
			#result=self.project_obj.completed_projects(int(project_id))
			#if result[0] > 0:
			if 1:
					obj=Polling.PollingExploits(int(project_id))
					continue_=False
					delete=False	
			
					default_config=obj.ExploitPoll()
					if default_config["status"]=="success":
						exp_obj=Reconfigure() 
						resp=exp_obj.configure_response(default_config)
						config_dict=resp[0]
						config_list=resp[1]
						record_list=resp[2]
						return_response["status"]="success"
						#return_response["data"]=serialize.data  #Note Both work the same !!!
						return_response["data"]=config_list
						return_response["record_list"]=record_list
						return Response(JSONRenderer().render(return_response))
	
					else:

						return Response(JSONRenderer().render(default_config))
			else:
					return_response["status"]="failure"
					return_response["data"]="In valid project id"
					return_response["value"]="In valid project id"
					return Response(JSONRenderer().render(return_response))
	
		except Exception ,ee:
			return_response["status"]="failure"
			return_response["data"]=str(ee)
			return Response(JSONRenderer().render(return_response))
	
	def post(self,request,format=None):
		try:
			return_response={}
			update_data=Polling_(data=request.data)
			return_response={}
			if(update_data.is_valid()):
				project_id=update_data.data["project_id"]
				record_list=update_data.data["record_list"]
				obj=Polling.PollingExploits(int(project_id))
				return_response=obj.UpdateStatusExploit(record_list)
				
			else:
				return_response["status"]="failure"
				return_response["errors"]=update_data.errors
				return_response["value"]=update_data.errors
			return Response(JSONRenderer().render(return_response))
		
		except Exception ,ee:
			return_response["status"]="failure"
			return_response["value"]=str(ee)
			return Response(JSONRenderer().render(return_response))


	
		
class ExploitConfigConc(APIView):
	"""
	Objective :
	The objective of this class is to serve Get method which would be used 
	to fetch results of vulnerability scanning when mode is concurrent.
	It is different fro polling as polling will give us config for records which have been immidiately
	finished by discovery ,but this will give use the chosen/updated config for all the records

	In order to understand about input given to this method and response returned read API documentation.
	"""

	def get(self,request,format=None):
		try:
			return_response={}
			obj=Gui_main_driver.Gui_main()
			project_id=request.data["project_id"]
			continue_=False
			delete=False	
			default_config=obj.getDefaultConfiguration(project_id,'','',True,True,'')
			if default_config["status"]=="reconfig":
					exp_obj=Reconfigure() 
					resp=exp_obj.configure_response(default_config)
					config_dict=resp[0]
					config_list=resp[1]
					record_list=resp[2]
					return_response["status"]="success"
					#return_response["data"]=serialize.data  #Note Both work the same !!!
					return_response["data"]=config_list
					return_response["record_list"]=record_list
					return Response(JSONRenderer().render(return_response))
	
			else:

					return Response(JSONRenderer().render(default_config))

		except Exception ,ee:
			#except Exception ,ee:
			return_response["status"]="failure"
			return_response["data"]=str(ee)
			return Response(JSONRenderer().render(return_response))
	
		



