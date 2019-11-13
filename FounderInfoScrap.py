#!/usr/bin/env python
# coding: utf-8


import requests
import csv
import re
import time
KEY = 'a06e623cd04b0c8bc4348819794bbd53'
education_title = ['Education Type', 'Education School', 'Major', 'Start', 'End']
funding_title = ['Company Name','Company ID', 'Title', 'Funding', 'Founded on', 'Stock']
work_title = ['Work Company Name','Work Company ID', 'Title', 'Start', 'End']

NUM_EDUCATION = 5
NUM_FUNDING = 10
NUM_WORK = 10
title = ['Name', 'ID', 'Gender', 'Organization', 'Location']
for i in range(NUM_EDUCATION):
    title.extend(education_title)
for i in range(NUM_FUNDING):
    title.extend(funding_title)
for i in range(NUM_WORK):
    title.extend(work_title)


names = []
with open('2.1 Crunchbase.csv', mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        if(row["Organization/Person Name URL"].strip() != ""):
            names.append(row['Organization/Person Name URL'].split('/')[-1])
            
cannotfind = [] # for the organizations that don't exist anymore
work_with_no_relationships = [] # for the messed up CrunchBase data when job has no relationship...

with open('Updated Data.tsv', mode='w') as data_file:
    writer = csv.writer(data_file, delimiter='\t', quotechar='"')
    writer.writerow(title)
    
    index = 0
    while index < len(names):
        name = names[index]
        counter = 0
        while True:
            response = requests.get(
            'https://api.crunchbase.com/v3.1/organizations/' + name,
            params={'user_key': KEY})

            if (response.status_code == 200 or counter > 5):
                break
            time.sleep(60)
            counter += 1
            
        if response.status_code != 200: 
            print(name)
            cannotfind.append(name)
            index += 1
            continue

        org = response.json()['data']
        founders = org['relationships']['founders']['items']
        for founder in founders:
            id = founder['uuid']
            
            counter = 0
            while True:
                response = requests.get(
                'https://api.crunchbase.com/v3.1/people/' + id,
                params={'user_key': KEY})

                if (response.status_code == 200 or counter > 5):
                    break
                time.sleep(60)
                counter += 1
            
            if response.status_code != 200: 
                print(id)
                cannotfind.append(id)
                continue
            response = response.json()['data']

            person = response['properties']
            location = ''
            if 'item' in response['relationships']['primary_location']:
                location = response['relationships']['primary_location']['item']['properties']['country']
            education = response['relationships']['degrees']['items']
            funding = response['relationships']['founded_companies']['items']
            work = response['relationships']['jobs']['items']

            data_row = [' '.join([person['first_name'],person['last_name']]), id, person['gender'], org['properties']['name'], location]

            for i in range(NUM_EDUCATION):
                edu_row = ['','','','',''] #added a column for major
                # edu type, edu name, edu major, edu from, edu end
                if (i < len(education)):
                    edu = education[i]
                    edu_row = [edu['properties']['degree_type_name'], 
                               edu['relationships']['school']['properties']['name'],
                               edu['properties']['degree_subject'],
                               edu['properties']['started_on'],
                               edu['properties']['completed_on']]
                data_row.extend(edu_row)

            real_work = []
            for w in work:
                if 'relationships' not in w:
                    entry = (name, w['uuid'])
                    work_with_no_relationships.append(entry)
                    print(entry)
                    continue
                is_match = False
                for fund in funding:
                    if (w['relationships']['organization']['uuid'] == fund['uuid']):
                        is_match = True
                        break
                if (is_match == False):
                    real_work.append(w)

            for i in range(NUM_FUNDING):
                funding_row = ['','','','','','']
                #com name, ID, title, funding in USD, founded on, stock symbol(proxy for IPO, None if negative)
                if (i < len(funding)):
                    fund = funding[i]
                    work_title = ''
                    for w in work:
                        if 'relationships' not in w:
                            continue
                        if w['relationships']['organization']['uuid'] == fund['uuid']:
                            work_title = w['properties']['title']
                    
                    funding_row = [fund['properties']['name'], 
                               fund['uuid'],
                               work_title,
                               fund['properties']['total_funding_usd'],
                               fund['properties']['founded_on'],
                               fund['properties']['stock_symbol']]
                data_row.extend(funding_row)

            for i in range(NUM_WORK):
                work_row = ['','','','','']
                #name, ID, title, start, end
                if (i < len(real_work)):
                    w = real_work[i]
                    work_row = [w['relationships']['organization']['properties']['name'],
                                w['relationships']['organization']['uuid'],
                                w['properties']['title'],
                                w['properties']['started_on'],
                                w['properties']['ended_on']]
                data_row.extend(work_row)
            writer.writerow(data_row)
        if (index % 100 == 0):
            print('Current Progress: ' + str(index))
        index += 1

print("Cannot find:")
print(cannotfind)
print("Work with no relationships:")
print(work_with_no_relationships)
