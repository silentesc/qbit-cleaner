import os
import subprocess
from loguru import logger


class FileUtils:
    def __init__(self, data_path: str, torrents_path: str, media_path: str) -> None:
        self.data_path = data_path if data_path.endswith("/") else f"{data_path}/"
        self.torrents_path = torrents_path if torrents_path.endswith("/") else f"{torrents_path}/"
        self.media_path = media_path if media_path.endswith("/") else f"{media_path}/"


    def find_hard_links(self, file_path: str) -> list[str]:
        """
        Finds all hard links to a given file on a Linux system.

        Args:
            file_path (str): The path to the file.

        Returns:
            list: A list of paths to all hard links, including the original.
                Returns an empty list if the file is not found or an error occurs.
        """
        if not os.path.exists(file_path):
            logger.error(f"Error: File not found at '{file_path}'")
            return []

        try:
            stats = os.stat(file_path)
            inode_num = stats.st_ino

            command = ['find', self.data_path, '-xdev', '-inum', str(inode_num)]
            result = subprocess.check_output(command, stderr=subprocess.DEVNULL, text=True)
            result_list: list[str] = result.strip().split('\n')
            logger.trace(f"Hard links for {file_path}")
            [logger.trace(f"--> {r}") for r in result_list]
            return result_list
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"An error occurred: {e}")
            return []


    def get_link_count(self, file_path: str) -> int:
        """
        Gets the link count to a given file

        Args:
            file_path (str): The path to the file.

        Returns:
            int: An int of the count of links, including the original (always minimum of 1).
                Returns -1 if an error happened.
        """
        try:
            file_stat = os.stat(file_path)
            link_count = file_stat.st_nlink
            logger.trace(f"link count for {file_path} is {link_count}")
            return link_count
        except FileNotFoundError: # This can happen if a file is deleted while the script is running
            logger.warning(f"Warning: Could not find file {file_path}")
        except Exception as e:
            logger.error(f"An error occurred with {file_path}: {e}")
        return -1


    def is_content_in_media_library(self, content_path: str) -> bool:
        """
        Checks if the content_path has any connection to the media_path via a link.
        Recursively goes through all files in the folder and checks for links to the media path.
        content_path supports file path and dir path.

        Args:
            content_path (str): The path to the file/dir

        Returns:
            bool: Whether any of the content (or links of it) is in the media path
        """
        if os.path.isdir(content_path):
            logger.trace(f"{content_path} is a dir")
            for root, _, files in os.walk(content_path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    link_count: int = self.get_link_count(file_path=file_path)
                    if link_count > 1:
                        if any([self.media_path in f for f in self.find_hard_links(file_path=file_path)]):
                            logger.trace(f"{file_path} does have hard links in media library")
                            return True
                        else:
                            logger.trace(f"{file_path} does not have hard links in media library")
        elif os.path.isfile(content_path):
            logger.trace(f"{content_path} is a file")
            link_count: int = self.get_link_count(file_path=content_path)
            if link_count > 1:
                if any([self.media_path in f for f in self.find_hard_links(file_path=content_path)]):
                    logger.trace(f"{content_path} does have hard links")
                    return True
                else:
                    logger.trace(f"{content_path} does not have hard links")
        else:
            logger.warning(f"Not a dir or file, probably be deleted: {content_path}")
        return False
