import os
import unittest
import json
from http import HTTPStatus

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))


class FloodUpdateTestsFromAPI(unittest.TestCase):

    def test_flood_update(self):
        test_floods = json.loads(open(root_dir + "/fixtures/test_floods.json").read())
        response = client.post("/latestfloods", json=test_floods)
        assert response.status_code == HTTPStatus.OK


    def test_garbage_flood_update(self):
        test_floods = json.loads(open(root_dir + "/fixtures/bad_test_floods_garbage.json").read())
        response = client.post("/latestfloods", json=test_floods)
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


if __name__ == '__main__':
    unittest.main()