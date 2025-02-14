import ast
import boto3
import logging
import os
import sys
import traceback

LOG_FILE_NAME = 'output.log'

# Change region to match with the default region that you setup when configuring your AWS CLI
REGION = 'us-east-1'

class S3Handler:
    """S3 handler."""

    def __init__(self):
        self.client = boto3.client('s3')

        logging.basicConfig(filename=LOG_FILE_NAME,
                            level=logging.DEBUG, filemode='w',
                            format='%(asctime)s %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')
        self.logger = logging.getLogger("S3Handler")

    def help(self):
        print("Supported Commands:")
        print("1. createdir <bucket_name>")
        print("2. upload <source_file_name> <bucket_name> [<dest_object_name>]")
        print("3. download <dest_object_name> <bucket_name> [<source_file_name>]")
        print("4. delete <dest_object_name> <bucket_name>")
        print("5. deletedir <bucket_name>")
        print("6. find <pattern> <bucket_name> -- e.g.: find txt bucket1 --")
        print("7. listdir [<bucket_name>]")
    
    def _error_messages(self, issue):
        error_message_dict = {}
        error_message_dict['operation_not_permitted'] = 'Not authorized to access resource.'
        error_message_dict['invalid_directory_name'] = 'Directory name is invalid.'
        error_message_dict['incorrect_parameter_number'] = 'Incorrect number of parameters provided'
        error_message_dict['not_implemented'] = 'Functionality not implemented yet!'
        error_message_dict['bucket_name_exists'] = 'Directory already exists.'
        error_message_dict['bucket_name_empty'] = 'Directory name cannot be empty.'
        error_message_dict['non_empty_bucket'] = 'Directory is not empty.'
        error_message_dict['missing_source_file'] = 'Source file cannot be found.'
        error_message_dict['non_existent_bucket'] = 'Directory does not exist.'
        error_message_dict['non_existent_object'] = 'Destination File does not exist.'
        error_message_dict['unknown_error'] = 'Something was not correct with the request. Try again.'

        if issue:
            return error_message_dict[issue]
        else:
            return error_message_dict['unknown_error']

    def _get_file_extension(self, file_name):
        if os.path.exists(file_name):
            return os.path.splitext(file_name)

    def _get(self, bucket_name):
        response = ''
        try:
            response = self.client.head_bucket(Bucket=bucket_name)
        except Exception as e:
            # print(e)
            # traceback.print_exc(file=sys.stdout)
            
            response_code = e.response['Error']['Code']
            if response_code == '404':
                return False
            elif response_code == '200':
                return True
            else:
                raise e
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            return False

    def createdir(self, bucket_name):

        #directory name cannot be empty
        if not bucket_name:
            return self._error_messages('bucket_name_empty')
        try:
            #directory already exists
            if self._get(bucket_name):
                return self._error_messages('bucket_name_exists')
            self.client.create_bucket(Bucket=bucket_name)
        except Exception as e:
            print(e)
            raise e

        # Success response
        operation_successful = ('Directory %s created.' % bucket_name)
        return operation_successful

    def listdir(self, bucket_name):
        # If bucket_name is provided, check that bucket exits.
        if not bucket_name:
            #if the user gave no bucket name
            response = self.client.list_buckets(
                MaxBuckets=123
            )
            for content in response['Buckets']:
                print(content['Name'])
            return
        else:
            #we were given a bucket name, see if it exists
            try:
                if self._get(bucket_name):
                    response = self.client.list_objects_v2(Bucket=bucket_name)
                    object_names = [obj['Key'] for obj in response['Contents']]
                    return object_names
                else:
                     return self._error_messages('non_existent_bucket')
            except Exception as e:
                #the bucket did not exist, sad :(
                response_code = e.response['Error']['Code']
                if response_code == '404':
                    return self._error_messages('bucket_name_exists')
                print(e)
                raise e

    def upload(self, source_file_name, bucket_name, dest_object_name=''):
        print("Current working directory:", os.path.dirname(os.path.abspath(__file__)))

        # 1. Parameter Validation
        #    - source_file_name exits in current directory
        #    - bucket_name exists

        #source file could not be found
        # if not os.path.isfile(source_file_name):
        #     return self._error_messages('missing_source_file')
    
        destName = source_file_name
        #bucket name can not be empty
        print("bucket name: ", bucket_name)
        if not bucket_name:
            return self._error_messages('bucket_name_empty')
        if dest_object_name:
            destName = dest_object_name

        try:
            #check if the bucket exits
            if self._get(bucket_name):
                fileName = os.path.join(os.path.dirname(os.path.abspath(__file__)), source_file_name)
                self.client.upload_file(fileName, bucket_name,  destName)
                operation_successful = ('File %s uploaded to directory %s.' % (source_file_name, bucket_name))
        except Exception as e:
            # return self._error_messages('bucket_name_empty')
            print(e)
            raise e
            
        # 2. If dest_object_name is not specified then use the source_file_name as dest_object_name

        # 3. SDK call
        #    - When uploading the source_file_name and add it to object's meta-data

    


    def download(self, dest_object_name, bucket_name, source_file_name=''):
        # if source_file_name is not specified then use the dest_object_name as the source_file_name
        # If the current directory already contains a file with source_file_name then move it as a backup
        # with following format: <source_file_name.bak>
        
        # Parameter Validation
        
        # SDK Call
        fileName = dest_object_name
        if source_file_name:
            fileName = source_file_name
        #if we have a duplicate, save it as a backup
        fileName = os.path.join(os.path.dirname(os.path.abspath(__file__)), source_file_name)
        if os.path.isfile(fileName):
            fileName = os.path.splitext(fileName)[0] + ".bak"
            print("bakL: ", fileName)
        print("name: ", fileName)
        try:
            #directory and source file exist
            if self._get(bucket_name):
                self.client.download_file(bucket_name, dest_object_name, fileName)
                operation_successful = ('File %s downloaded from directory %s.' % (dest_object_name, bucket_name))
            else:
                #bucket does not exist
                return self._error_messages('non_existent_bucket')
        except Exception as e:
            #check to see if we have no dest file
            print(e)
            raise e
        

        # Success response
        # operation_successful = ('File %s downloaded from directory %s.' % (dest_object_name, bucket_name))



    def delete(self, dest_object_name, bucket_name):
        
        # Success response
        # operation_successful = ('File %s deleted from directory %s.' % (dest_object_name, bucket_name))

        if self._get(bucket_name):
            try:
                response = self.client.delete_object(
            Bucket=bucket_name,
            Key=dest_object_name
            )
            except Exception as e:
            #check to see if we have no dest file
                print(e)
                raise e

        else:
            #bucket does not exist
            return self._error_messages('non_existent_bucket')

        return self._error_messages('not_implemented')


    def deletedir(self, bucket_name):
        # Delete the bucket only if it is empty
        
        # Success response
        # operation_successful = ("Directory %s deleted." % bucket_name)
        if self._get(bucket_name):
            try:
                response = self.client.delete_bucket(
                        Bucket=bucket_name
                    )
                operation_successful = ("Directory %s deleted." % bucket_name)
                return  operation_successful
            except Exception as e:
                #check to see if we have no dest file
                print(e)
                raise e
        else:
            return self._error_messages('non_existent_bucket')
        


    def find(self, pattern, bucket_name=''):
        # Return object names that match the given pattern

        #no bucket name provided, go through names of the buckets
        if not bucket_name:
            paginator = self.client.get_paginator('list_buckets')
            response_iterator = paginator.paginate(
                    Prefix='',
                    BucketRegion='us-east-1',
                    PaginationConfig={
                        'MaxItems': 123,
                        'PageSize': 123
                    }
                )
                #iterate through all of the buckets
            for page in response_iterator:
                if 'Buckets' in page:
                    for bucket in page['Buckets']:
                        if pattern in bucket['Name']:
                            print("Bucket Name:", bucket['Name'])
        else:
            #we were given a bucket
            if self._get(bucket_name):
                response = self.client.list_objects(Bucket = bucket_name)

                for content in response['Contents']:
                    if pattern in content ['Key']:
                        print("File Name: ", content['Key'])
                    
                
            else:
                return self._error_messages('non_existent_bucket')

        return self._error_messages('not_implemented')


    def dispatch(self, command_string):
        parts = command_string.split(" ")
        response = ''

        if parts[0] == 'createdir':
            # Figure out bucket_name from command_string
            if len(parts) > 1:
                bucket_name = parts[1]
                response = self.createdir(bucket_name)
            else:
                # Parameter Validation
                # - Bucket name is not empty
                response = self._error_messages('bucket_name_empty')
        elif parts[0] == 'upload':
            # Figure out parameters from command_string
            # source_file_name and bucket_name are compulsory; dest_object_name is optional
            # Use self._error_messages['incorrect_parameter_number'] if number of parameters is less
            # than number of compulsory parameters
            source_file_name = parts[1]
            bucket_name = parts[2]
            if len(parts) >  3:
                dest_object_name = parts[3]
            else:
                dest_object_name = ''
            response = self.upload(source_file_name, bucket_name, dest_object_name)
        elif parts[0] == 'download':
            # Figure out parameters from command_string
            # dest_object_name and bucket_name are compulsory; source_file_name is optional
            # Use self._error_messages['incorrect_parameter_number'] if number of parameters is less
            # than number of compulsory parameters
            if len(parts) > 3:
                source_file_name = parts[3]
            else:
                source_file_name = ''
            bucket_name = parts[2]
            dest_object_name = parts[1]
            response = self.download(dest_object_name, bucket_name, source_file_name)
        elif parts[0] == 'delete':
            dest_object_name = parts[1]
            bucket_name = parts[2]
            response = self.delete(dest_object_name, bucket_name)
        elif parts[0] == 'deletedir':
            bucket_name = parts[1]
            response = self.deletedir(bucket_name)
        elif parts[0] == 'find':
            pattern = parts[1]
            if len(parts) > 2 :
                bucket_name = parts[2]
            else:
                bucket_name = ""
            response = self.find(pattern, bucket_name)
        elif parts[0] == 'listdir':
            bucket_name = ""
            if len(parts) > 1:
                bucket_name = parts[1]
            response = self.listdir(bucket_name)
        else:
            response = "Command not recognized."
        return response


def main():

    s3_handler = S3Handler()
    
    while True:
        try:
            command_string = ''
            if sys.version_info[0] < 3:
                command_string = raw_input("Enter command ('help' to see all commands, 'exit' to quit)>")
            else:
                command_string = input("Enter command ('help' to see all commands, 'exit' to quit)>")
    
            # Remove multiple whitespaces, if they exist
            command_string = " ".join(command_string.split())
            
            if command_string == 'exit':
                print("Good bye!")
                exit()
            elif command_string == 'help':
                s3_handler.help()
            else:
                response = s3_handler.dispatch(command_string)
                print(response)
        except Exception as e:
            print(e)

if __name__ == '__main__':
    main()
