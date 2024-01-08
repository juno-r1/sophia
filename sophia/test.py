import re

unmatched = r'(?P<unmatched>(\'[^\']*$)|(\"[^\"]*$))' # Detects unmatched quotes
single = r'\'[^\']*$'
notquote = r'\'[^\']*(?!\')$'
string = '\'\''
for item in re.finditer(single, string):
	print(item)