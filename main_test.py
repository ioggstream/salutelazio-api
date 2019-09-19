# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import flask
import pytest

import main
import yaml

# Create a fake "app" for generating test request contexts.
from werkzeug.exceptions import BadRequest, NotFound


TEST_CF = "RSSMRO54P05E472I"


@pytest.fixture(scope="module")
def app():
    return flask.Flask(__name__)


def test_search_surname(app):
    with app.test_request_context(
        query_string={"surname": "rossi"},
    ):
        res = main.salutelazio_get(flask.request)
        data = yaml.safe_load(res)

        assert "doctors" in data, data
        assert data["doctors"], data


def test_search_surname_delta(app):
    for delta in [1, 2, 5]:
        with app.test_request_context(
            query_string={"surname": "rossi", "delta": delta},
        ):
            res = main.salutelazio_get(flask.request)
            data = yaml.safe_load(res)

            assert "doctors" in data, data
            assert data["doctors"], data
            assert len(data["doctors"]) == delta + 1


def test_orari_taxCode(app):
    with app.test_request_context(
        path="/" + TEST_CF + "/orari/",
    ):
        res = main.salutelazio_get(flask.request)
        data = yaml.safe_load(res)

        assert "ambulatories" in data, data
        assert data["ambulatories"], data


def test_taxCode_NotImplemented(app):
    with app.test_request_context(
        path="/" + TEST_CF,
    ):
        with pytest.raises(NotFound) as exc:
            res = main.salutelazio_get(flask.request)
        assert "Not Implemented" in exc.value.description


def test_orari_get(app):
    with app.test_request_context(
        query_string={"taxCode": TEST_CF},
        headers={"accept": "application/json"},
    ):
        res = main.orari_get(flask.request)
        assert "address" in res, res


def test_medici_get(app):
    with app.test_request_context(
        query_string={"surname": "rossi"}, headers={"accept": "application/json"}
    ):
        res = main.medici_get(flask.request)
        data = yaml.safe_load(res)
        assert "doctors" in data, data
        assert data["doctors"], data


def test_medici_get_empty_json(app):
    with app.test_request_context(json=""):
        with pytest.raises(BadRequest) as exc:
            res = main.medici_get(flask.request)
        assert "At least one of the following parameter" in exc.value.description


def test_medici_get_xss(app):
    with app.test_request_context(query_string={"surname": "<script>alert(1)</script>"}):
        with pytest.raises(BadRequest) as exc:
            res = main.medici_get(flask.request)
        # Should be ascii error in description.
        assert "ascii" in exc.value.description
