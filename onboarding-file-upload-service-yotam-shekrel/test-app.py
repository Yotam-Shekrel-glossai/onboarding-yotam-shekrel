import requests

# Switching between local and remote execution
# URL = 'https://5d38lyxgh9.execute-api.us-east-2.amazonaws.com/api'
URL = 'http://127.0.0.1:8000'

# Create a test file to upload
with open('test_file.txt', 'w') as f:
    f.write("This is a test file content")

def space_printer():
    # Print two empty lines for better readability in the output
    print(' ')
    print(' ')

def test_all():
    # Run all test functions sequentially
    test_post_function()
    test_get_by_file_id_function()
    test_get_by_client_id_function()
    test_update_function()
    test_delete_function()
    
    space_printer()
    print("All tests are over")

def test_post_function():
    # Test the POST endpoint
    try:
        url = URL + '/post'

        # Prepare the file to be sent in the request
        files = {
            'file': ('test_file.txt', open('test_file.txt', 'rb'), 'text/plain')
        }
        data = {
            'client_id': 'test_client'
        }

        # Send a POST request
        response = requests.post(url, files=files, params=data)
        
        space_printer()
        print('*****Post Test*****')
        # Check the response
        if response.status_code == 200:
            print("Test Passed")
        else:
            print("Test Failed")
            print("Status Code:", response.status_code)
            print("Response:", response.text)
        
    except requests.exceptions.RequestException as e:
        print("Test Failed")
        print("Error:", str(e))

def test_get_by_file_id_function():
    # Test the GET endpoint by file ID
    try:
        url = URL + '/get_by_file_id/test_file.txt'

        response = requests.get(url)

        space_printer()
        print("*****Get By File Id Test*****")
        # Check the response
        if response.status_code == 200:
            print("Test Passed")
        else:
            print("Test Failed")
            print("Status Code:", response.status_code)
            print("Response:", response.text)
    
    except requests.exceptions.RequestException as e:
        print("Test Failed")
        print("Error:", str(e))

def test_get_by_client_id_function():
    # Test the GET endpoint by client ID
    try:   
        url = URL + '/get_by_client_id/test_client'

        response = requests.get(url)

        space_printer()
        print("*****Get By Client Id Test*****")
        # Check the response
        if response.status_code == 200:
            print("Test Passed")
        else:
            print("Test Failed")
            print("Status Code:", response.status_code)
            print("Response:", response.text)

    except requests.exceptions.RequestException as e:
        print("Test Failed")
        print("Error:", str(e))

def test_update_function():
    # Test the UPDATE endpoint
    url = URL + '/update/test_file.txt'

    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'new_file_id': 'new_test_file.txt',
        'client_id': 'new_test_client'
    }

    try:
        # Send a PUT request
        response = requests.put(url, headers=headers, json=data)
        
        space_printer()
        print('*****Update Test*****')
        # Check the response
        if response.status_code == 200:
            print("Test Passed")
        else:
            print("Test Failed")
            print("Status Code:", response.status_code)
            print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        print("Test Failed")
        print("Error:", str(e))

def test_delete_function():
    # Test the DELETE endpoint
    try:
        url = URL + '/delete/new_test_file.txt'
        response = requests.delete(url)

        space_printer()
        print("*****Delete Test*****")
        # Check the response
        if response.status_code == 200:
            print("Test Passed")
        else:
            print("Test Failed")
            print("Status Code:", response.status_code)
            print("Response:", response.text)
    
    except requests.exceptions.RequestException as e:
        print("Test Failed")
        print("Error:", str(e))

# Run the test suite
if __name__ == "__main__":
    test_all()
