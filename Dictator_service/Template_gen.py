import json
import sys
import re
class Template():
	def __init__(self):
		self.json_file=sys.argv[1]
	def process(self):
		with open(self.json_file,"r+") as json_data:
			my_dict=json.loads(json_data.read())
		parent_json={}
		for k ,v in my_dict.iteritems():
			json_dict={}
			service=k
			custom=v["Custom"]
			json_dict["Custom"]=custom	
			#json_dict["Service"]=service
			json_dict["Test_cases"]=[]
			if custom==False:
				for test_case in v["Commands"]:						
						id=test_case["id"]
						json_dict["Test_cases"].append(id)
						
			else:
				for custom_cases in v["Commands"]:
					json_dict["Test_cases"].append(custom_cases)
			parent_json[service]=json_dict

		with open(sys.argv[2],"w+") as output:
			output.write(json.dumps(parent_json,ensure_ascii=False,indent=4,sort_keys=True))
		print "Data written successfully"

obj=Template()				
obj.process()
