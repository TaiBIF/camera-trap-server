from django.test import TestCase
from http import HTTPStatus

from taicat.models import Project
# Create your tests here.
class FooTest(TestCase):
    def setUp(self):
        Project.objects.create(id='')

    def test_proj(self):
        p = Project.objects.get(keyword='k')
        self.assertEqual(p.name, 'testcase')

class RobotsTest(TestCase):
    def test_get(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["content-type"], "text/plain")
        lines = response.content.decode().splitlines()
        self.assertEqual(lines[0], "User-Agent: *")

    def test_post(self):
        response = self.client.post("/robots.txt")

        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)
