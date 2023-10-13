import logging
import requests
import json
from datetime import datetime
from random import randint
import os
import mimetypes


class LastMile(object):
    def __init__(self, api_key, API_ENDPOINT="https://lastmileai.dev/api") -> None:
        self.api_key = api_key
        self.API_ENDPOINT = API_ENDPOINT

    def _get_headers(self) -> dict:
        return {
            "content-type": "application/json",
            "Authorization": "Bearer " + self.api_key,
        }

    def api_health(self):
        url = self.API_ENDPOINT + "/health"
        resp = requests.get(url)
        return resp.json()

    def create_trial(self, name):
        url = self.API_ENDPOINT + "/trials/create"
        payload = {
            "name": name,
        }
        headers = self._get_headers()

        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    def create_workflow(self, workbook_id):
        url = self.API_ENDPOINT + "/workflows/create"
        payload = {
            "workbookId": workbook_id,
        }
        headers = self._get_headers()

        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    def create_workflow_run(
        self,
        workflow_id,
        execution_run_id,
        workflow_run_batch_id=None,
        workbook_parameters=None,
    ):
        # Make sure parameter is None if empty string
        if workflow_run_batch_id is not None and len(workflow_run_batch_id) == 0:
            workflow_run_batch_id = None

        url = self.API_ENDPOINT + "/workflows/runs/create"
        payload = {
            "workflowId": workflow_id,
            "executionRunId": execution_run_id,
        }

        if workflow_run_batch_id is not None:
            payload["workflowRunBatchId"] = workflow_run_batch_id

        if workbook_parameters is not None:
            payload["workbookParameters"] = workbook_parameters

        headers = self._get_headers()

        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    def get_workbook(self, id: str):
        url = self.API_ENDPOINT + "/workbooks/read?id=" + id
        headers = self._get_headers()
        resp = requests.get(url, headers=headers)
        data = resp.json()
        return data

    def get_dependency_graph(self, id: str):
        url = self.API_ENDPOINT + "/workbooks/dependencygraph?id=" + id
        headers = self._get_headers()
        resp = requests.get(url, headers=headers)
        data = resp.json()
        return data

    def execute_all_without_parameters(
        self,
        trial_id,
        cell_groups,
        run_data,
    ):
        previous_step_id = None
        for actual_cell_group in cell_groups:
            output = self.execute(
                trial_id, previous_step_id, run_data[actual_cell_group["id"]]
            )

            previous_step_id = output["outputTrialStep"]["id"]

    def execute_all_with_parameters(self, trial_id, cell_groups, workbook_parameters):
        previous_step_id = None
        for i in range(len(cell_groups)):
            actual_cell_group = cell_groups[i]
            new_run_data = self.get_run_data(
                trial_id, i, actual_cell_group, workbook_parameters
            )

            output = self.execute(trial_id, previous_step_id, new_run_data)
            previous_step_id = output["outputTrialStep"]["id"]

    def execute(self, trial_id, previous_step_id, run_data):
        url = self.API_ENDPOINT + "/inference/run"
        payload = run_data

        run_data["trialId"] = trial_id
        run_data["trialStepId"] = None
        run_data["parentTrialStepId"] = previous_step_id
        headers = self._get_headers()

        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    def get_run_data(
        self, trial_id, cell_group_index, actual_cell_group, workbook_parameters
    ):
        url = (
            self.API_ENDPOINT
            + "/workbooks/rundata"
            + "?id="
            + trial_id
            + "&cellGroupIndex="
            + str(cell_group_index)
        )

        headers = self._get_headers()

        resp = requests.post(
            url,
            data=json.dumps(
                {
                    "newCellGroup": actual_cell_group,
                    "workbookParameters": workbook_parameters,
                }
            ),
            headers=headers,
        )
        data = resp.json()

        run_data = data.get("runData", None)
        if run_data is None:
            logging.error("No run data found")
            logging.error(data)
            raise Exception("No run data found")

        return run_data

    def add_input_step(self, trial_id, prompt):
        url = self.API_ENDPOINT + "/trialsteps/create"
        payload = {"trialId": trial_id, "type": "INPUT", "data": [{"code": prompt}]}
        headers = self._get_headers()

        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    def add_output_step(self, trial_id):
        url = self.API_ENDPOINT + "/trialsteps/create"
        payload = {"trialId": trial_id, "type": "OUTPUT", "data": []}
        headers = self._get_headers()

        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    # Helpers for uploading image & creating upload entity in lastmile DB
    def get_upload_policy(self):
        url = self.API_ENDPOINT + "/upload/policy"
        headers = self._get_headers()

        resp = requests.get(url, headers=headers)
        data = resp.json()
        return data

    def upload_to_s3(self, policy, image_path):
        url = "https://s3.amazonaws.com/files.uploads.lastmileai.com/"
        date_string = datetime.utcnow().strftime("%Y_%m_%d_%H_%M_%S")
        random_path = randint(0, 10000)
        image_file_name = os.path.basename(image_path)
        upload_key = (
            "uploads/"
            + policy["userId"]
            + "/"
            + date_string
            + "/"
            + str(random_path)
            + "/"
            + image_file_name
        )
        mime_type = mimetypes.guess_type(image_path)[0]

        form_data = {
            "key": upload_key,
            "acl": "public-read",
            # TODO: Should support jpg, png, etc.
            "Content-Type": mime_type,
            "AWSAccessKeyId": policy["AWSAccessKeyId"],
            "success_action_status": "201",
            "Policy": policy["s3Policy"],
            "Signature": policy["s3Signature"],
            "file": open(image_path, "rb"),
        }

        resp = requests.post(url, files=form_data)
        if resp.status_code == 201:
            print("Uploaded successfully to S3")

        return {
            "url": url + upload_key,
            "metadata": {"type": mime_type, "size": os.path.getsize(image_path)},
        }

    def create_upload_in_lastmile(self, s3_url, metadata):
        url = self.API_ENDPOINT + "/upload/create"
        payload = {
            "url": s3_url,
            "metadata": {"type": metadata["type"], "size": metadata["size"]},
        }
        headers = self._get_headers()

        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    def attach_upload_to_trialstep(self, upload_id, trial_step_id):
        url = self.API_ENDPOINT + "/upload/attach"
        payload = {"id": upload_id, "entity": "trialstep", "entityId": trial_step_id}
        headers = self._get_headers()

        resp = requests.put(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    def create_openai_completion(self, completion_params, embedding_collection_id=None):
        url = self.API_ENDPOINT + "/inference/openai/completion"
        payload = {
            "completionParams": completion_params,
            "embeddingCollectionId": embedding_collection_id,
        }
        headers = self._get_headers()

        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    def create_openai_chat_completion(
        self, completion_params, embedding_collection_id=None
    ):
        url = self.API_ENDPOINT + "/inference/openai/chatgpt/completion"
        payload = {
            "completionParams": completion_params,
            "embeddingCollectionId": embedding_collection_id,
        }
        headers = self._get_headers()

        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    def create_dataset(self, name: str, uploads=[], metadata={}):
        url = self.API_ENDPOINT + "/datasets/create"
        payload = {
            "name": name,
            "type": "FILES",
            "uploads": uploads,
            "metadata": metadata,
        }
        headers = self._get_headers()
        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    def create_embedding_collection(
        self, name: str, dataset_id=None, uploads=[], description=None
    ):
        url = self.API_ENDPOINT + "/embeddings/create"
        payload = {
            "name": name,
            "datasetId": dataset_id,
            "uploads": uploads,
            "description": description,
        }
        headers = self._get_headers()

        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    def update_embedding_collection_status(self, id: str, ready=False, error=None):
        url = self.API_ENDPOINT + "/embeddings/update_status"
        payload = {"id": id, "ready": ready, "error": error}
        headers = self._get_headers()

        resp = requests.put(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    def create_model_fork(
        self, id: str, name: str, embedding_collection_id: str, description=None
    ):
        url = self.API_ENDPOINT + "/models/fork"
        payload = {
            "id": id,
            "name": name,
            "embeddingCollectionId": embedding_collection_id,
            "description": description,
        }
        headers = self._get_headers()

        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        data = resp.json()
        return data

    def get_models(self, owner_type="user"):
        url = self.API_ENDPOINT + "/models/list" + "?ownerType=" + owner_type
        headers = self._get_headers()

        resp = requests.get(url, headers=headers)
        data = resp.json()
        return data
