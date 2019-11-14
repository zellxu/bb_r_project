import requests
import csv
import time
KEY = 'a06e623cd04b0c8bc4348819794bbd53'
COMPANY_ROW_NUM = [31, 37, 43, 49, 55, 61, 67, 73, 79, 85, 91, 96, 101, 106, 111, 116, 121, 126, 131, 136]
TITLE = ['Company Name', 'Number of Employees', 'Funding','Categories']

company_ids = set()
with open('Updated Data.tsv', mode='r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter='\t')
    for row in csv_reader:
        if row[0] == 'Company ID':
            continue
        company_ids.update([row[x] for x in COMPANY_ROW_NUM if row[x] != ''])

cannotfind = []
with open('company_data_updated.tsv', mode='w') as data_file:
    writer = csv.writer(data_file, delimiter='\t', quotechar='"')
    writer.writerow(TITLE)
    
    index = 0
    for id in company_ids:
        counter = 0
        while True:
            response = requests.get(
            'https://api.crunchbase.com/v3.1/organizations/' + id,
            params={'user_key': KEY})

            if (response.status_code == 200 or counter > 5):
                break
            time.sleep(60)
            counter += 1
            
        if response.status_code != 200: 
            print(id)
            cannotfind.append(id)
            index += 1
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
        if (index % 100 == 0):
            print('=============Current Progress===============  ' + str(index))
        index += 1
        if index > 10:
            break
            
print("Cannot find:")
print(cannotfind)