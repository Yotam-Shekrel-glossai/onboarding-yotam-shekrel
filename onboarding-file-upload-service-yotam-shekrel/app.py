from chalice import Chalice, Response
import boto3
import os

app = Chalice(app_name='onboarding-file-upload-service-yotam-shekrel')
s3_BUCKET_NAME = 'onboarding-file-upload-bucket-yotam-shekrel1'
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
metadata_table = dynamodb.Table('onboarding-file-metadata-table-yotam-shekrel')

@app.route('/')
def index():
    return {'hello': 'world', 'my' : 'check'}

def parse_multipart_formdata(data):
    parsed_data = {}
    lines = data.split('\r\n')
    boundary = lines[0]
    
    i = 1
    while i < len(lines):
        if boundary in lines[i]:
            i += 1
            continue
        
        # Process headers
        headers = {}
        while lines[i] != '':
            header_name, header_value = lines[i].split(': ')
            headers[header_name] = header_value
            i += 1
        
        # Process body
        i += 1
        body = []
        while i < len(lines) and boundary not in lines[i]:
            body.append(lines[i])
            i += 1
        
        body = '\r\n'.join(body)
        
        # Determine where to store the body
        if 'Content-Disposition' in headers:
            disposition_parts = headers['Content-Disposition'].split(';')
            name = None
            for part in disposition_parts:
                if 'name=' in part:
                    name = part.split('=')[1].strip().strip('"')
                    break
            
            if name:
                parsed_data[name] = body
        
        i += 1
    
    return parsed_data

@app.route('/post', methods=['POST'], content_types=['multipart/form-data'])
def post():
    request = app.current_request 
    multipart_params = request.raw_body.decode().split('\r\n') #the request as string

    file_data = None
    for i in range(len(multipart_params)):

        if 'filename' in multipart_params[i]:
            file_data = multipart_params[i+3].encode('utf-8')

            #finds the file name
            disposition_parts = multipart_params[i].split(';')
            for part in disposition_parts:
                if 'filename' in part:
                    file_id = part.split('=')[1].strip().strip('"')
            break

    ## handle input error
    if file_data is None or file_id is None:
         return Response(body="ERROR, no file was given by the user", headers={'Content-Type': 'text/plain'})

    client_id = request.query_params.get('client_id')
    if client_id is None:
        return Response(body="ERROR, no client ID was given by the user", headers={'Content-Type': 'text/plain'})
    
    key = f"{file_id}"

    # post the file in s3 bucket
    s3_client.put_object(Bucket=s3_BUCKET_NAME, Key=key, Body=file_data)
    
    # post the file metadata in dynamoDB table
    metadata_table.put_item(Item={
        'fileId' : file_id,
        'client_id': client_id,
        'key': key
    })

    return {'file_id': file_id, 'message': 'File uploaded and metadata stored successfully! Client id: '+client_id+' File id: '+ file_id}


@app.route('/get-item/{client_id}', methods=['GET'])
def get_by_client_id(client_id):

    try:
        response = s3_client.list_objects_v2(Bucket=s3_BUCKET_NAME) 
        files = response.get('Contents', [])

        client_files = []

        for file in files:
            head_response = s3_client.head_object(Bucket=s3_BUCKET_NAME, Key=file['Key'])
            if head_response['Metadata'].get('client_id') == client_id:
                client_files.append(file['Key'])


         # not found
        if len(client_files) == 0:
            return Response(body=str('No files were found for '+ client_id))
        
        # Return the content as a response
        return Response(body=('Success!\n'+str(len(client_files))+' files were found for '+str(client_id)+'\n'+str(client_files)+':\n'),
                        headers={'Content-Type': 'application/json'})

    # error
    except Exception as e:
        return Response(body=f'Error getting item: {str(e)}',
                        headers={'Content-Type': 'text/plain'})
