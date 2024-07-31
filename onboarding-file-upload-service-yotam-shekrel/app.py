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

# extract the file name from the request 
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
    s3_client.put_object(Bucket=s3_BUCKET_NAME, Key=key, Body=file_data,Metadata={'client_id': client_id})
    
    # post the file metadata in dynamoDB table
    metadata_table.put_item(Item={
        'fileId' : file_id,
        'client_id': client_id,
        'key': key
    })

    return {'file_id': file_id, 'message': 'File uploaded and metadata stored successfully! Client id: '+client_id+' File id: '+ file_id}

@app.route('/get_by_client_id/{client_id}', methods=['GET'])
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

@app.route('/get_by_file_id/{file_id}', methods=['GET'])
def get_by_file_id(file_id):

    try:
        response = metadata_table.get_item(Key={'fileId': file_id})
        item = response.get('Item')
         
        if not item:
            return Response(body=f"No metadata found for file ID {file_id}",
                            headers={'Content-Type': 'text/plain'},
                            status_code=404)
        
        return Response(body=item,
                        headers={'Content-Type': 'application/json'}, status_code=200)
    
    except Exception as e:
        return Response(body=f"Error retrieving metadata: {str(e)}",
                        headers={'Content-Type': 'text/plain'},
                        status_code=500)
    
@app.route('/delete/{file_id}', methods=['DELETE'])
def delete(file_id):
    try:
        response = metadata_table.get_item(Key={'fileId': file_id})
        
        if 'Item' not in response:
            return Response(body=f"No file with ID {file_id} was found",
                            headers={'Content-Type': 'text/plain'},
                            status_code=404)
        # Delete the file from the S3 bucket
        s3_client.delete_object(Bucket=s3_BUCKET_NAME, Key=file_id)
        
        # Delete the metadata from the DynamoDB table
        metadata_table.delete_item(Key={'fileId': file_id})
        

        return Response(body=f"File with ID {file_id} and its metadata deleted successfully.",
                        headers={'Content-Type': 'text/plain'})
            

    except Exception as e:
        return Response(body=f"Error deleting file and metadata: {str(e)}",
                        headers={'Content-Type': 'text/plain'},
                        status_code=500)

@app.route('/update/{old_file_id}', methods=['PUT'], content_types=['application/json'])
def update_file_id(old_file_id):
    request = app.current_request
    content_type = request.headers.get('Content-Type', '')

    if content_type == 'application/json':
        try:
            body = request.json_body
            new_file_id = body.get('new_file_id')
            new_client_id = body.get('client_id')

            if not new_file_id and not new_client_id:
                return Response(body="At least one of new_file_id or client_id is required", headers={'Content-Type': 'text/plain'}, status_code=400)

            # Retrieve the current metadata from DynamoDB
            response = metadata_table.get_item(Key={'fileId': old_file_id})
            item = response.get('Item')

            if not item:
                return Response(body=f"No metadata found for file ID {old_file_id}",
                                headers={'Content-Type': 'text/plain'},
                                status_code=404)

            # Determine the new file ID
            final_file_id = new_file_id if new_file_id else old_file_id
            final_client_id = new_client_id if new_client_id else item['client_id']

            # Copy the existing file to the new key if the file ID has changed
            if new_file_id:
                copy_source = {'Bucket': s3_BUCKET_NAME, 'Key': old_file_id}
                s3_client.copy_object(
                    Bucket=s3_BUCKET_NAME,
                    CopySource=copy_source,
                    Key=final_file_id,
                    Metadata={'client_id': final_client_id},
                    MetadataDirective='REPLACE'
                )

                # Delete the old file
                s3_client.delete_object(Bucket=s3_BUCKET_NAME, Key=old_file_id)

            else:
                # Update the metadata in S3 if only the client ID has changed
                s3_client.copy_object(
                    Bucket=s3_BUCKET_NAME,
                    CopySource={'Bucket': s3_BUCKET_NAME, 'Key': old_file_id},
                    Key=old_file_id,
                    Metadata={'client_id': final_client_id},
                    MetadataDirective='REPLACE'
                )

            # Update metadata in DynamoDB
            metadata_table.put_item(Item={
                'fileId': final_file_id,
                'client_id': final_client_id,
                'key': final_file_id  # Update the key to new_file_id if it has changed
            })

            # Optionally, delete the old metadata in DynamoDB if the file ID has changed
            if new_file_id:
                metadata_table.delete_item(Key={'fileId': old_file_id})

            return {'old_file_id': old_file_id, 'new_file_id': final_file_id, 'client_id': final_client_id, 'message': 'File ID and/or client ID updated successfully!'}

        except Exception as e:
            return Response(body=f"Error updating file ID or client ID: {str(e)}", headers={'Content-Type': 'text/plain'}, status_code=500)

    return Response(body="Unsupported content type", headers={'Content-Type': 'text/plain'}, status_code=400)
