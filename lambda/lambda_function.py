import json
import re
import os
import boto3
import uuid

from xml.etree import ElementTree

array_fields = [x.lower().strip() for x in os.environ.get('ARRAY_FIELDS').split(',')]
ignore_fields = [x.lower().strip() for x in os.environ.get('IGNORE_FIELDS').split(',')]

class XmlDictConfig(dict):
    '''
    Example usage:

    >>> tree = ElementTree.parse('your_file.xml')
    >>> root = tree.getroot()
    >>> xmldict = XmlDictConfig(root)

    Or, if you want to use an XML string:

    >>> root = ElementTree.XML(xml_string)
    >>> xmldict = XmlDictConfig(root)

    And then use xmldict for what it is... a dict.
    '''
    def __init__(self, parent_element):
        if parent_element.items():
            self.update(dict(parent_element.items()))
        
        childrenNames = [element.tag for element in parent_element]
        print(childrenNames)
        for element in parent_element:
            if element.tag.lower() in ignore_fields: 
                continue
            
            if element:
                value = XmlDictConfig(element)

            # this assumes that if you've got an attribute in a tag,
            # you won't be having any text. This may or may not be a 
            # good idea -- time will tell. It works for the way we are
            # currently doing XML configuration files...
            elif element.items():
                value = dict(element.items())
            # finally, if there are no child tags and no attributes, extract
            # the text
            else:
                value = element.text
            
            if childrenNames.count(element.tag) > 1 or element.tag.lower() in array_fields:
                lst = self.get(element.tag, [])
                lst.append(value)
                self.update({element.tag: lst})
            else:
                self.update({element.tag: value})

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    input_folder = os.environ.get('INPUT_FOLDER')
    output_folder = os.environ.get('OUTPUT_FOLDER')
    output_bucket = os.environ.get('OUTPUT_BUCKET')
    
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        tmpkey = key.replace('/', '')
        download_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
        upload_path = '/tmp/converted-{}'.format(tmpkey)
        s3_client.download_file(bucket, key, download_path)
        convert(download_path, upload_path)
        upload_key = key.replace(input_folder, output_folder).replace('.xml', '.json')
        s3_client.upload_file(upload_path, output_bucket, upload_key)

        with open(upload_path, mode='r') as file:
            contents = file.read()
            print(contents)
            return contents

    
def convert(download_path, upload_path):
    root = ElementTree.parse(download_path).getroot()
    xmldict = XmlDictConfig(root)
    print(xmldict)
    has_header = False
    has_body = False
    flattened_dict = {}
    for key, value in xmldict.items():
        if re.match(r'^MIM\d+[A-Z]?_.*$', key):
            flattened_dict.update(flatten(value, 'body'))
            has_body = True
        elif key == 'MessageHeader':
            flattened_dict.update(flatten(value, 'header'))
            has_header = True

    with open(upload_path, 'w') as file:        
        json.dump(flattened_dict, file)

def flatten(aDict, preffix = ""):
    result = {}
    for key, value in aDict.items():
        k = key if not len(preffix) else preffix + "_" + key
        if isinstance(value, dict):
            result.update(flatten(value, k))
        else:
            result[k] = value
    return result

    