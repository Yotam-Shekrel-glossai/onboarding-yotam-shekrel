from chalice import Chalice, Response
import uuid
import boto3

app = Chalice(app_name='onboarding-file-upload-service-yotam-shekrel')
s3_BUCKET_NAME = 'onboarding-file-upload-bucket-yotam-shekrel1'
s3_client = boto3.client('s3')

@app.route('/')
def index():
    return {'hello': 'world', 'my' : 'check'}

@app.route('/post', methods=['POST'], content_types=['multipart/form-data'])
def post():
    request = app.current_request
    multipart_params = request.raw_body.decode().split('\r\n')

    file_data = None
    for i in range(len(multipart_params)):
        if 'filename' in multipart_params[i]:
            file_data = multipart_params[i+3].encode;
            break

    if file_data == None:
        print("ERROR, no file was given by the user")

    file_id = str(uuid.uuid4())

    s3_client.put_object(Bucket= s3_BUCKET_NAME, Key = file_id, Body = file_data)

    return {'file_id': file_id, 'message': 'File uploaded successfully!'}


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
