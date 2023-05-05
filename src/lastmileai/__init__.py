# This would become "import Lastmile from lastmile" & installed via pip, etc.
# See api docs here: https://lastmileai.dev/docs/api
import requests
import json
from datetime import datetime
from random import randint
import os
import mimetypes

class Lastmile(object):
  # Set api_key for other methods, 
  # can also call this 'login' or something in cli/interactive usage
  # Note should probably get from env var or some secret store, this is just
  # for demonstration purposes
  def __init__(self, api_key) -> None:
    self.api_key = api_key

  def api_health(self):
    url = "https://lastmileai.dev/api/health"
    resp = requests.get(url)
    return resp.json()

  def create_trial(self, name):
    # Stable Diffusion's model_id at lastmileai.dev right now
    # Public & promoted model so everyone has access to the same model_id
    model_id = 'cldf8cet50004qss7ieqt3amo'

    url = "https://lastmileai.dev/api/trials/create"
    payload = {'name': name, 'modelId': model_id}
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.api_key}

    resp = requests.post(url, data=json.dumps(payload), headers=headers)
    data = resp.json()
    return data

  def add_input_step(self, trial_id, prompt):
    url = "https://lastmileai.dev/api/trialsteps/create"
    payload = {'trialId': trial_id, 'type': 'INPUT', 'data': [{'code': prompt}]}
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.api_key}

    resp = requests.post(url, data=json.dumps(payload), headers=headers)
    data = resp.json()
    return data

  def add_output_step(self, trial_id):
    url = "https://lastmileai.dev/api/trialsteps/create"
    payload = {'trialId': trial_id, 'type': 'OUTPUT', 'data': []}
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.api_key}

    resp = requests.post(url, data=json.dumps(payload), headers=headers)
    data = resp.json()
    return data

  # Helpers for uploading image & creating upload entity in lastmile DB
  def get_upload_policy(self):
    url = "https://lastmileai.dev/api/upload/policy"
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.api_key}

    resp = requests.get(url, headers=headers)
    data = resp.json()
    return data

  def upload_to_s3(self, policy, image_path):
    url = "https://s3.amazonaws.com/files.uploads.lastmileai.com/"
    date_string = datetime.utcnow().strftime('%Y_%m_%d_%H_%M_%S')
    random_path = randint(0, 10000)
    image_file_name = os.path.basename(image_path)
    upload_key = "uploads/" + policy['userId'] + '/' + date_string + '/' + str(random_path) + '/' + image_file_name
    mime_type = mimetypes.guess_type(image_path)[0]

    form_data = {
        'key': upload_key,
        'acl': 'public-read',
        # TODO: Should support jpg, png, etc.
        'Content-Type': mime_type,
        'AWSAccessKeyId': policy['AWSAccessKeyId'],
        'success_action_status': '201',
        'Policy': policy["s3Policy"],
        'Signature': policy['s3Signature'],
        'file': open(image_path, 'rb')
    }

    resp = requests.post(url, files=form_data)
    if (resp.status_code == 201):
      print("Uploaded successfully to S3")

    return {
        'url': url + upload_key,
        'metadata': {'type': mime_type, 'size': os.path.getsize(image_path)}
    }

  def create_upload_in_lastmile(self, s3_url, metadata):
    url = "https://lastmileai.dev/api/upload/create"
    payload = {'url': s3_url, 'metadata': {'type': metadata['type'], 'size': metadata['size']}}
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.api_key}

    resp = requests.post(url, data=json.dumps(payload), headers=headers)
    data = resp.json()
    return data

  def attach_upload_to_trialstep(self, upload_id, trial_step_id):
    url = "https://lastmileai.dev/api/upload/attach"
    payload = {'id': upload_id, 'entity': 'trialstep', 'entityId': trial_step_id}
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.api_key}

    resp = requests.put(url, data=json.dumps(payload), headers=headers)
    data = resp.json()
    return data

  def create_openai_completion(self, completion_params, embedding_collection_id = None):
    url = "https://lastmileai.dev/api/inference/openai/completion"
    payload = {'completionParams': completion_params, 'embeddingCollectionId': embedding_collection_id}
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.api_key}

    resp = requests.post(url, data=json.dumps(payload), headers=headers)
    data = resp.json()
    return data

  def create_openai_chat_completion(self, completion_params, embedding_collection_id = None):
    url = "https://lastmileai.dev/api/inference/openai/chatgpt/completion"
    payload = {'completionParams': completion_params, 'embeddingCollectionId': embedding_collection_id}
    headers = {'content-type': 'application/json', 'Authorization': 'Bearer ' + self.api_key}

    resp = requests.post(url, data=json.dumps(payload), headers=headers)
    data = resp.json()
    return data


# Example usage to create a trial, add prompt & image(s) - see 
# https://colab.research.google.com/drive/1sFHDD-lR7_7WMEj-GgzmIBEDd81FFI9_?usp=sharing#scrollTo=wczWMpEz61l2
# lastmileAPI = Lastmile()
# lastmileAPI.auth("YOUR_API_TOKEN_IN_STRING_QUOTES_FROM_https://lastmileai.dev/tokens")
# trial = lastmileAPI.create_trial('Stable Diffusion Trial')
# trial_id = trial['id']

# prompt = "a photo of Pikachu fine dining with a view to the Eiffel Tower"
# input_step = lastmileAPI.add_input_prompt(trial_id, prompt)

# policy = lastmileAPI.get_upload_policy()
# s3_upload_obj = lastmileAPI.upload_to_s3(policy, 'output.jpg')
# upload = lastmileAPI.create_upload_in_lastmile(s3_upload_obj['url'], s3_upload_obj['metadata'])
# output_step = lastmileAPI.add_output_step_for_image_attachment(trial_id)
# lastmileAPI.attach_upload_to_trialstep(upload['id'], output_step['id'])
