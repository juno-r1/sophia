import json

with open('kleio.json', 'r') as data:
	metadata = json.load(data)['+']['u_add']
	print(metadata)