import pytest

from shared.storage.exceptions import BucketAlreadyExistsError, FileNotInStorageError
from shared.storage.memory import MemoryStorageService
from tests.base import BaseTestCase

minio_config = {
    "access_key_id": "codecov-default-key",
    "secret_access_key": "codecov-default-secret",
    "verify_ssl": False,
    "host": "minio",
    "port": "9000",
}


class TestMemoryStorageService(BaseTestCase):
    def test_create_bucket(self, codecov_vcr):
        storage = MemoryStorageService(minio_config)
        bucket_name = "thiagoarchivetest"
        res = storage.create_root_storage(bucket_name, region="")
        assert res == {"name": "thiagoarchivetest"}

    def test_create_bucket_already_exists(self, codecov_vcr):
        storage = MemoryStorageService(minio_config)
        bucket_name = "alreadyexists"
        storage.root_storage_created = True
        with pytest.raises(BucketAlreadyExistsError):
            storage.create_root_storage(bucket_name)

    def test_write_then_read_file(self, codecov_vcr):
        storage = MemoryStorageService(minio_config)
        path = "test_write_then_read_file/result"
        data = "lorem ipsum dolor test_write_then_read_file á"
        bucket_name = "thiagoarchivetest"
        writing_result = storage.write_file(bucket_name, path, data)
        assert writing_result
        reading_result = storage.read_file(bucket_name, path)
        assert reading_result.decode() == data

    def test_write_then_append_then_read_file(self, codecov_vcr):
        storage = MemoryStorageService(minio_config)
        path = "test_write_then_append_then_read_file/result"
        data = "lorem ipsum dolor test_write_then_read_file á"
        second_data = "mom, look at me, appending data"
        bucket_name = "thiagoarchivetest"
        writing_result = storage.write_file(bucket_name, path, data)
        second_writing_result = storage.append_to_file(bucket_name, path, second_data)
        assert writing_result
        assert second_writing_result
        reading_result = storage.read_file(bucket_name, path)
        assert reading_result.decode() == "\n".join([data, second_data])

    def test_append_to_non_existing_file(self, request, codecov_vcr):
        storage = MemoryStorageService(minio_config)
        path = f"{request.node.name}/result.txt"
        second_data = "mom, look at me, appending data"
        bucket_name = "thiagoarchivetest"
        second_writing_result = storage.append_to_file(bucket_name, path, second_data)
        assert second_writing_result
        reading_result = storage.read_file(bucket_name, path)
        assert reading_result.decode() == second_data

    def test_read_file_does_not_exist(self, request, codecov_vcr):
        storage = MemoryStorageService(minio_config)
        path = f"{request.node.name}/does_not_exist.txt"
        bucket_name = "thiagoarchivetest"
        with pytest.raises(FileNotInStorageError):
            storage.read_file(bucket_name, path)

    def test_write_then_delete_file(self, request, codecov_vcr):
        storage = MemoryStorageService(minio_config)
        path = f"{request.node.name}/result.txt"
        data = "lorem ipsum dolor test_write_then_read_file á"
        bucket_name = "thiagoarchivetest"
        writing_result = storage.write_file(bucket_name, path, data)
        assert writing_result
        deletion_result = storage.delete_file(bucket_name, path)
        assert deletion_result is True
        with pytest.raises(FileNotInStorageError):
            storage.read_file(bucket_name, path)

    def test_delete_file_doesnt_exist(self, request, codecov_vcr):
        storage = MemoryStorageService(minio_config)
        path = f"{request.node.name}/result.txt"
        bucket_name = "thiagoarchivetest"
        with pytest.raises(FileNotInStorageError):
            storage.delete_file(bucket_name, path)

    def test_batch_delete_files(self, request, codecov_vcr):
        storage = MemoryStorageService(minio_config)
        path_1 = f"{request.node.name}/result_1.txt"
        path_2 = f"{request.node.name}/result_2.txt"
        path_3 = f"{request.node.name}/result_3.txt"
        paths = [path_1, path_2, path_3]
        data = "lorem ipsum dolor test_write_then_read_file á"
        bucket_name = "thiagoarchivetest"
        storage.write_file(bucket_name, path_1, data)
        storage.write_file(bucket_name, path_3, data)
        deletion_result = storage.delete_files(bucket_name, paths)
        assert deletion_result == [True, False, True]
        for p in paths:
            with pytest.raises(FileNotInStorageError):
                storage.read_file(bucket_name, p)

    def test_list_folder_contents(self, request, codecov_vcr):
        storage = MemoryStorageService(minio_config)
        path_1 = f"thiago/{request.node.name}/result_1.txt"
        path_2 = f"thiago/{request.node.name}/result_2.txt"
        path_3 = f"thiago/{request.node.name}/result_3.txt"
        path_4 = f"thiago/{request.node.name}/f1/result_1.txt"
        path_5 = f"thiago/{request.node.name}/f1/result_2.txt"
        path_6 = f"thiago/{request.node.name}/f1/result_3.txt"
        all_paths = [path_1, path_2, path_3, path_4, path_5, path_6]
        bucket_name = "thiagoarchivetest"
        for i, p in enumerate(all_paths):
            data = f"Lorem ipsum on file {p} for {i * 'po'}"
            storage.write_file(bucket_name, p, data)
        results_1 = list(
            storage.list_folder_contents(bucket_name, f"thiago/{request.node.name}")
        )
        expected_result_1 = [
            {"name": path_1, "size": 70},
            {"name": path_2, "size": 72},
            {"name": path_3, "size": 74},
            {"name": path_4, "size": 79},
            {"name": path_5, "size": 81},
            {"name": path_6, "size": 83},
        ]
        assert sorted(
            expected_result_1, key=lambda x: (x["name"], x["size"])
        ) == sorted(results_1, key=lambda x: (x["name"], x["size"]))
        results_2 = list(
            storage.list_folder_contents(bucket_name, f"thiago/{request.node.name}/f1")
        )
        expected_result_2 = [
            {"name": path_4, "size": 79},
            {"name": path_5, "size": 81},
            {"name": path_6, "size": 83},
        ]
        assert sorted(
            expected_result_2, key=lambda x: (x["name"], x["size"])
        ) == sorted(results_2, key=lambda x: (x["name"], x["size"]))
