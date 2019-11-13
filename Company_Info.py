import requests
import csv
import time
KEY = 'a06e623cd04b0c8bc4348819794bbd53'
COMPANY_ROW_NUM = [29, 34, 39, 44, 49, 54, 59, 64, 69, 74, 79, 83, 87, 91, 95, 99, 103, 107, 111, 115]
TITLE = ['Company Name', 'Number of Employees', 'Funding','Categories']

company_names = set()
with open('data 5-10-10.tsv', mode='r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter='\t')
    for row in csv_reader:
        if row[0] == 'Name':
            continue
        company_names.update([row[x] for x in COMPANY_ROW_NUM if row[x] != ''])
company_names = list(company_names)

cannotfind = []
with open('company_data.tsv', mode='w') as data_file:
    writer = csv.writer(data_file, delimiter='\t', quotechar='"')
    writer.writerow(TITLE)
    
    index = 0
    page = 1
    while index < len(company_names):
        name = company_names[index]
        response = requests.get(
        'https://api.crunchbase.com/v3.1/organizations',
        params={'name': name, 'page':page, 'user_key': KEY})
        
        if (response.status_code != 200):
            time.sleep(60)
            continue
            
        response = response.json()['data']['items']

        if len(response) == 0:
            print('Cannot Find ' + name)
            cannotfind.append(name)
            page = 1
            index += 1
            continue
            
        found_match = False
        for company in response:
            if company['properties']['name'] != name:
                continue
            
            found_match = True
            id = company['uuid']
            
            response = requests.get(
            'https://api.crunchbase.com/v3.1/organizations/' + id,
            params={'user_key': KEY})
            
            if (response.status_code != 200):
                time.sleep(60)
                continue
            
            response = response.json()['data']
            
            company_name = response['properties']['name']
            employee_min = response['properties']['num_employees_min']
            employee_max = response['properties']['num_employees_max']
            funding = response['properties']['total_funding_usd']
            categories = response['relationships']['categories']['items']
            category_data = []
            for category in categories:
                category_data.append(category['properties']['name'])
            
            data_row = [company_name, '-'.join([str(x) for x in [employee_min, employee_max]]), funding, ','.join(category_data)]
            writer.writerow(data_row)
            
        if not found_match:
            page += 1
            continue
        page = 1
        index += 1
        if (index % 100 == 0):
            print('=============Current Progress===============  ' + str(index))
            
print("Cannot find:")
print(cannotfind)
