from collections import defaultdict


class FilesAnalizer:
    """
    Анализирует файлы, помечая их либо как к загрузке, либо как к обновлению
    """

    def __init__(self, local_files: list[dict], cloud_files: list[dict]) -> None:
        self.local_files = local_files
        self.cloud_files = cloud_files

    def get_files_for_upload(self):
        files = self._compare_list_of_dicts()
        cloud_files_names = [item['name'] for item in self.cloud_files]
        files_for_upload = []
        for file in files:
            if not (file['name'] in cloud_files_names):
                file['status'] = 'load'
                files_for_upload.append(file)
            elif not (file in self.cloud_files):
                file['status'] = 'reload'
                files_for_upload.append(file)
        return files

    def _make_hash_table(self, list_of_dicts):
        hashes = defaultdict(list)

        for i, item in enumerate(list_of_dicts):
            calculated_hash = hash(frozenset(item.items()))
            hashes[calculated_hash].append(i)

        return hashes


    def _compare_list_of_dicts(self):
        list1_hashes = self._make_hash_table(self.local_files)
        list2_hashes = self._make_hash_table(self.cloud_files)

        not_in_list2 = [
            self.local_files[list1_hashes[hash_value][0]]
            for hash_value in list1_hashes.keys() - list2_hashes.keys()
        ]
        return not_in_list2
