# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
import uuid
import asyncio
from azure.iot.device.aio import IoTHubDeviceClient
import http.client
import pprint
import json
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

api = "2019-03-30"
conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
sas = os.getenv("IOTHUB_SAS")
device_id = os.getenv("IOTHUB_DEVICE_ID")
iothub_name = os.getenv("IOTHUB_NAME")
host_name = "{iotHubName}.azure-devices.net".format(iotHubName=iothub_name)

# Host is in format "<iothub name>.azure-devices.net"


# The type of authorization is through a SAS Token, so we add that to the headers here


async def get_sas(connection):
    # `getBlobSharedAccessSignature` shall create a `POST` HTTP request to a path formatted as the following:`/devices/URI_ENCODED(<deviceId>)/files?api-version=<api-version>]
    getSasPost = "https://{hostName}/devices/{deviceId}/files?api-version={api}".format(
        hostName=host_name, deviceId=device_id, api=api
    )
    uploadjson = {"blobName": "fakeBlobName"}
    get_sas_headers = {
        "Host": host_name,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Content-Length": len(str(uploadjson)),
        "User-Agent": "azure-iot-device/0xFFFFFFF",
    }

    get_sas_headers["Authorization"] = sas
    connection.request("POST", getSasPost, body=json.dumps(uploadjson), headers=get_sas_headers)
    response = connection.getresponse()
    print("Status {} and reason: {}".format(response.status, response.reason))
    headers = response.getheaders()
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(headers)
    response_string = response.read().decode("utf-8")
    json_obj = json.loads(response_string)
    pp.pprint(response_string)
    return json_obj


async def notify_upload_complete(connection, correlationId):
    # `notifyUploadComplete` shall create a `POST` HTTP request to a path formatted as the following:`/devices/URI_ENCODED(<deviceId>)/files/<correlationId>?api-version=<api-version>`]
    # correlationId = "MjAxOTExMDUyMjA4XzcxZDMwOWU0LTdiMjktNGRlMy04MTc3LWE1MjY1NTZlODM1ZV90ZXN0YmxvYi50eHRfdmVyMi4w"
    path = "https://{hostName}/devices/{deviceId}/files/notifications?api-version={api}".format(
        hostName=host_name, deviceId=device_id, correlationId=correlationId, api=api
    )

    body = {
        "correlationId": correlationId,
        "isSuccess": True,
        "statusCode": 201,
        "statusDescription": "We did it, jim.",
    }

    headers = {
        "Host": host_name,
        "User-Agent": "azure-iot-device/0xFFFFFFF",
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": len(str(body)),
        "iothub-name": iothub_name,
    }
    headers["Authorization"] = sas
    connection.request("POST", path, body=json.dumps(body).encode("utf-8"), headers=headers)
    response = connection.getresponse()
    print("Status {} and reason: {}".format(response.status, response.reason))
    response_headers = response.getheaders()
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(response_headers)
    pp.pprint(response.read().decode("utf-8"))


def make_blob_service_url(hostName, containerName, blobName, sasToken):
    # DefaultEndpointsProtocol=https;AccountName=yosephsandboxhubstorage;AccountKey=fakeKey;EndpointSuffix=core.windows.net
    # sandbox2storage.blob.core.windows.net
    service_url = "https://{hostName}/{containerName}/{blobName}{sasToken}".format(
        hostName=hostName, sasToken=sasToken
    )
    return service_url


async def storage_blob(blob_info, container_name):
    try:
        print("Azure Blob storage v12 - Python quickstart sample")
        # blob_service_client = BlobServiceClient(account_url="https://{}".format(hostName),credential=sasToken)
        sas_url = make_blob_service_url(
            blob_info["hostName"],
            blob_info["containerName"],
            blob_info["blobName"],
            blob_info["sasToken"],
        )
        BlobClient.from_blob_url(sas_url)
        # Create a file in local Documents directory to upload and download
        local_path = "./data"
        local_file_name = "quickstart" + str(uuid.uuid4()) + ".txt"
        upload_file_path = os.path.join(local_path, local_file_name)
        # Write text to the file
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        file = open(upload_file_path, "w")
        file.write("Hello, World!")
        file.close()

        # Create a blob client using the local file name as the name for the blob
        # blob_client = blob_service_client.get_blob_client(
        #     container=container_name, blob=local_file_name
        # )

        # print("\nUploading to Azure Storage as blob:\n\t" + local_file_name)

        # # Upload the created file
        # with open(upload_file_path, "rb") as data:
        #     blob_client.upload_blob(data)
    except Exception as ex:
        print("Exception:")
        print(ex)


async def main():

    connection = http.client.HTTPSConnection(host_name)
    connection.connect()
    blob_info = await get_sas(connection)
    # storage_conn_str = make_blob_service_url(blob_info["hostName"], blob_info["sasToken"])
    # foo = await storage_blob(blob_info, blob_info["containerName"])
    # correlationId = 'hi'
    await notify_upload_complete(connection, blob_info["correlationId"])
    connection.close()


if __name__ == "__main__":
    asyncio.run(main())
