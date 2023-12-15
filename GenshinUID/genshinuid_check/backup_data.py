from gsuid_core.utils.backup.backup_files import clear_path_all_file

from ..utils.resource.RESOURCE_PATH import TEMP_PATH


async def data_backup():
    clear_path_all_file(TEMP_PATH, '*.jpg')
