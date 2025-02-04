# Copyright The IETF Trust 2022, All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


__author__ = 'Richard Zilincik'
__copyright__ = 'Copyright The IETF Trust 2022, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'richard.zilincik@pantheon.tech'

import json
import os
import subprocess
import unittest

from modules_compilation.file_hasher import FileHasher
from versions import validator_versions


class TestFileHasher(unittest.TestCase):
    resource_path: str

    @classmethod
    def setUpClass(cls):
        cls.resource_path = os.path.join(os.environ['TESTS_RESOURCES_DIR'], 'file_hasher')
        cls.hash_file_paths = (
            cls.resource('sdo_files_modification_hashes.json'),
            cls.resource('sdo_files_modification_hashes.json.lock'),
        )
        with open(cls.resource('versions.json'), 'w') as f:
            json.dump(validator_versions, f)
        cls.correct_hashes = {
            cls.resource('file.txt'): {
                'hash': cls.compute_hash('file.txt'),
                'validator_versions': {},
            },
            cls.resource('other_file.txt'): {
                'hash': cls.compute_hash('other_file.txt'),
                'validator_versions': {},
            },
        }
        cls.incorrect_hashes = cls.correct_hashes.copy()
        cls.incorrect_hashes[cls.resource('file.txt')] = 64 * '0'

    def tearDown(self):
        for path in self.hash_file_paths:
            if not os.path.exists(path):
                continue
            os.remove(path)

    @classmethod
    def compute_hash(cls, file: str) -> str:
        command = f'cat {cls.resource(file)} | sha256sum'
        return subprocess.run(command, shell=True, capture_output=True).stdout.decode().split()[0]

    @classmethod
    def resource(cls, file: str) -> str:
        return os.path.join(cls.resource_path, file)

    def test_hash_values(self):
        fh = FileHasher(dst_dir=self.resource_path, force_compilation=False)
        module_hash_info = fh.should_parse(self.resource('file.txt'))
        fh.updated_hashes[self.resource('file.txt')] = {
            'hash': module_hash_info.hash,
            'validator_versions': {},
        }
        module_hash_info = fh.should_parse(self.resource('other_file.txt'))
        fh.updated_hashes[self.resource('other_file.txt')] = {
            'hash': module_hash_info.hash,
            'validator_versions': {},
        }
        fh.dump_hashed_files_list(self.resource_path)

        with open(self.resource('sdo_files_modification_hashes.json')) as f:
            result = json.load(f)

        self.assertDictEqual(result, self.correct_hashes)

    def test_invalidate_hashes(self):
        with open(self.resource('sdo_files_modification_hashes.json'), 'w') as f:
            json.dump(self.incorrect_hashes, f)

        fh = FileHasher(dst_dir=self.resource_path, force_compilation=False)
        module_hash_info = fh.should_parse(self.resource('file.txt'))
        fh.updated_hashes[self.resource('file.txt')] = {
            'hash': module_hash_info.hash,
            'validator_versions': {},
        }
        module_hash_info = fh.should_parse(self.resource('other_file.txt'))
        fh.updated_hashes[self.resource('other_file.txt')] = {
            'hash': module_hash_info.hash,
            'validator_versions': {},
        }
        fh.dump_hashed_files_list(self.resource_path)

        with open(self.resource('sdo_files_modification_hashes.json')) as f:
            result = json.load(f)

        self.assertDictEqual(result, self.correct_hashes)

    def test_should_parse(self):
        with open(self.resource('sdo_files_modification_hashes.json'), 'w') as f:
            json.dump(self.incorrect_hashes, f)

        fh = FileHasher(dst_dir=self.resource_path, force_compilation=False)
        module_hash_info = fh.should_parse(self.resource('file.txt'))
        self.assertEqual(module_hash_info.hash_changed, True)
        module_hash_info = fh.should_parse(self.resource('other_file.txt'))
        self.assertEqual(module_hash_info.hash_changed, False)

    def test_force_compilation(self):
        with open(self.resource('sdo_files_modification_hashes.json'), 'w') as f:
            json.dump(self.correct_hashes, f)

        fh = FileHasher(dst_dir=self.resource_path, force_compilation=True)
        module_hash_info = fh.should_parse(self.resource('file.txt'))
        self.assertEqual(module_hash_info.hash_changed, True)
        module_hash_info = fh.should_parse(self.resource('other_file.txt'))
        self.assertEqual(module_hash_info.hash_changed, True)
