import json

# 注意编码格式需要更换为utf-8
with open('Hexagon_GMRF_parsed_text.json', 'r',encoding='utf_8') as temp_file:
    GMRF_data = json.load(temp_file)
    # print(GMRF_data)

print(json.dumps(GMRF_data, indent=4))

for i in data['emp_details']: 
    print(i) 