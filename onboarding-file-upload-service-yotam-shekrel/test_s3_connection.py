import boto3

# prints the list of objects in my bucket
def list_s3_buckets():
    bucket_name = "onboarding-file-upload-bucket-yotam-shekrel1"
    s3 = boto3.client('s3')
    try:
        response = s3.list_objects_v2(Bucket = bucket_name)
        if 'Contents' in response:
            print(f"Objects in bucket '{bucket_name}':")
            for obj in response['Contents']:
                print(f"  - {obj['Key']}")
        else:
            print(f"No objects found in bucket '{bucket_name}'.")
    except Exception as e:
        print("Error:", e)
if __name__ == "__main__":
    list_s3_buckets()
