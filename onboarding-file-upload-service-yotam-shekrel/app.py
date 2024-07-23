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


@app.route('/get-item/{key}', methods=['GET'])
def get(key):
    try:
        response = s3_client.get_object(Bucket=s3_BUCKET_NAME, Key=key) # trying to get the item
        content = response['Body'].read().decode('utf-8')
        
        # Return the content as a response
        return Response(body=content,
                        headers={'Content-Type': 'text/plain'})
    # not found
    except s3_client.exceptions.NoSuchKey:
        return Response(body='Item not found',
                        headers={'Content-Type': 'text/plain'})
    
    # error
    except Exception as e:
        return Response(body=f'Error getting item: {str(e)}',
                        headers={'Content-Type': 'text/plain'})
