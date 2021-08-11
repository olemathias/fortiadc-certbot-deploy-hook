import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


class client:
    """Simple FortiADC Client"""
    token = None
    last_access_time = None

    def __init__(self, **kwargs):
        for f in ["host", "password"]:
            if f not in kwargs:
                raise ValueError("Missing required field: {0}".format(f))

        self.host = kwargs.get("host")
        self.base_url = "https://{0}".format(self.host)
        self.username = kwargs.get("username", "admin")
        self.vdom = kwargs.get("vdom", "global")  # TODO Use this

        if self.token is None or self.last_access_time is None:
            self._login(self.username, kwargs.get("password"))

    def _login(self, username, password):
        r = self._request(method="POST", path="user/login",
                          json={"username": username, "password": password})
        if "token" not in r:
            raise Exception("Login failed")

        self.token = r["token"]
        return True

    def _request(self, **kwargs):
        for f in ["path"]:
            if f not in kwargs:
                raise ValueError("Missing required field: {0}".format(f))

        url = "{0}/api/{1}".format(self.base_url, kwargs.get("path"))
        headers = {
            "User-Agent": "fortadc-certbot-deploy-hook",
            "Authorization": "Bearer {0}".format(self.token),
            "Cookie": "last_access_time={0}".format(self.last_access_time)
        }

        s = requests.Session()
        # Retry 5 times, with backoff
        retries = Retry(total=5,
                        backoff_factor=0.5,
                        status_forcelist=[500, 502, 503, 504])
        s.mount('https://', HTTPAdapter(max_retries=retries))

        if kwargs.get("method", "GET").upper() == "GET":
            r = s.get(url, params=kwargs.get("params", None),
                      headers=headers, timeout=5)
            if not r.ok:
                raise Exception("GET request to {0} failed!"
                                " Got status_code {1}".format(
                                    url, r.status_code))
        elif kwargs.get("method").upper() == "POST":
            r = s.post(url, params=kwargs.get("params", None),
                       json=kwargs.get("json", None),
                       data=kwargs.get("data", None),
                       files=kwargs.get("files", None),
                       headers=headers, timeout=5)

            if not r.ok:
                raise Exception("POST request to {0} failed!"
                                " Got status_code {1}".format(
                                    url, r.status_code))
        elif kwargs.get("method").upper() == "DELETE":
            r = s.delete(url, params=kwargs.get("params", None),
                         json=kwargs.get("json", None),
                         data=kwargs.get("data", None),
                         headers=headers, timeout=5)

            if not r.ok:
                raise Exception("DELETE request to {0} failed!"
                                " Got status_code {1}".format(
                                    url, r.status_code))
        else:
            raise ValueError("Unsupported method {}"
                             .format(kwargs.get("method")))

        # Set last_access_time on each request
        self.last_access_time = r.cookies["last_access_time"]
        return r.json()

    def get_certificate_local(self):
        r = self._request(path="system_certificate_local")
        return r["payload"]

    def upload_certificate_local(self, **kwargs):
        for f in ["mkey", "cert_path", "key_path"]:
            if f not in kwargs:
                raise ValueError("Missing required field: {0}".format(f))

        data = {
            "mkey": kwargs.get("mkey"),
            "type": "CertKey",
            "vdom": self.vdom
        }

        files = {
            "cert": open(kwargs.get("cert_path"), 'rb'),
            "key": open(kwargs.get("key_path"), 'rb')
        }

        r = self._request(method="POST", path="upload/certificate_local",
                          data=data, files=files)
        if "payload" not in r or r["payload"] != 0:
            print(r)
            raise Exception("Failed to upload cert")

    def get_certificate_local_group_members(self, **kwargs):
        params = {
            "pkey": kwargs.get("pkey")
        }
        r = self._request(
            path="system_certificate_local_cert_group_child_group_member",
            params=params
        )
        return r["payload"]

    def add_certificate_local_group_member(self, **kwargs):
        data = {
            "local_cert": kwargs.get("mkey"),
            "intermediate_cag": kwargs.get("intermediate", ""),
            "default": kwargs.get("default", "disable"),
            "OCSP_stapling": "",
            "extra_local_cert": ""
        }
        params = {
            "pkey": kwargs.get("pkey")
        }
        r = self._request(
            method="POST",
            path="system_certificate_local_cert_group_child_group_member",
            json=data, params=params
        )

        # IDK why -154, but seems to work :)
        if "payload" not in r or (r["payload"] != 0 and r["payload"] != -154):
            print(r)
            raise Exception("Failed to add cert to group")
        return r

    def delete_certificate_local_group_member(self, **kwargs):
        params = {
            "pkey": kwargs.get("pkey"),
            "mkey": kwargs.get("mkey"),
        }
        r = self._request(
            method="DELETE",
            path="system_certificate_local_cert_group_child_group_member",
            params=params
        )

        if "payload" not in r or r["payload"] != 0:
            print(r)
            raise Exception("Failed to delete cert from group")
        return r["payload"]
