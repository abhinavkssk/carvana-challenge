import torch.utils.data as data
from kaggle_data.downloader import KaggleDataDownloader
from sklearn.model_selection import train_test_split
import PIL
from PIL import Image
import pandas as pd
import numpy as np
import cv2
import os


class DatasetTools:

    def __init__(self):
        self.train_data = None
        self.test_data = None
        self.train_masks_data = None
        self.train_files = None
        self.test_files = None
        self.train_masks_files = None
        self.train_ids = None
        self.masks_ids = None
        self.test_ids = None

    def download_dataset(self):
        """
        Downloads the dataset and return the input paths
        :return: [train_data, test_data, metadata_csv, train_masks_csv, train_masks_data]
        """
        competition_name = "carvana-image-masking-challenge"

        destination_path = "../input/"
        files = ["train.zip", "test.zip", "metadata.csv.zip", "train_masks.csv.zip", "train_masks.zip"]
        datasets_path = ["../input/train", "../input/test", "../input/metadata.csv", "../input/train_masks.csv",
                        "../input/train_masks"]
        is_datasets_present = True

        # If the folders already exists then the files may already be extracted
        # This is a bit hacky but it's sufficient for our needs
        for dir_path in datasets_path:
            if not os.path.exists(dir_path):
                is_datasets_present = False

        if not is_datasets_present:
            # Put your Kaggle user name and password in a $KAGGLE_USER and $KAGGLE_PASSWD env vars respectively
            downloader = KaggleDataDownloader(os.getenv("KAGGLE_USER"), os.getenv("KAGGLE_PASSWD"), competition_name)

            for file in files:
                output_path = downloader.download_dataset(file, destination_path)
                downloader.decompress(output_path, destination_path)
                os.remove(output_path)
        else:
            print("All datasets are present.")

        self.train_data = datasets_path[0]
        self.test_data = datasets_path[1]
        self.train_masks_data = datasets_path[4]
        self.train_files = sorted(os.listdir(self.train_data))
        self.test_files = sorted(os.listdir(self.test_data))
        self.train_masks_files = sorted(os.listdir(self.train_masks_data))
        self.train_ids = list(set(t.split("_")[0] for t in self.train_files))
        self.masks_ids = list(set(t.split("_")[0] for t in self.train_masks_files))
        self.test_ids = list(set(t.split("_")[0] for t in self.test_files))
        return datasets_path

    def get_car_image_files(self, car_image_id, test_file=False, get_mask=False):
        if get_mask:
            if car_image_id in self.masks_ids:
                return [self.train_masks_data + "/" + s for s in self.train_masks_files if car_image_id in s]
            else:
                raise Exception("No mask with this ID found")
        elif test_file:
            if car_image_id in self.test_ids:
                return [self.test_data + "/" + s for s in self.test_files if car_image_id in s]
        else:
            if car_image_id in self.train_ids:
                return [self.train_data + "/" + s for s in self.train_files if car_image_id in s]
        raise Exception("No image with this ID found")

    def get_image_matrix(self, image_path):
        img = Image.open(image_path)
        return np.asarray(img, dtype=np.uint8)

    def get_train_valid_split(self, validation_size=0.2, sample_size=None):
        """

        :param sample_size: int
            Value between 0 and 1 or None.
            Whether you want to have a sample of your dataset.
        :param validation_size: int
            Value between 0 and 1
        :return: list
            Returns the dataset in the form:
            [train_data, train_masks_data, valid_data, valid_masks_data]
        """
        train_ids = self.train_ids
        if sample_size:
            pass
            # TODO finish sample size

        ids_train_split, ids_valid_split = train_test_split(self.train_ids, test_size=validation_size)

        train_ret = []
        train_masks_ret = []
        valid_ret = []
        valid_masks_ret = []

        for id in ids_train_split:
            train_ret.append(self.get_car_image_files(id))
            train_masks_ret.append(self.get_car_image_files(id, get_mask=True))

        for id in ids_valid_split:
            valid_ret.append(self.get_car_image_files(id))
            valid_masks_ret.append(self.get_car_image_files(id, get_mask=True))

        return [np.array(train_ret).ravel(), np.array(train_masks_ret).ravel(),
                np.array(valid_ret).ravel(), np.array(valid_masks_ret).ravel()]


# Reference: https://github.com/pytorch/vision/blob/master/torchvision/datasets/folder.py#L66
class ImageDataset(data.Dataset):
    def __init__(self, X_data, y_data, img_resize, X_transform=None, y_transform=None):
        """
            A dataset loader taking RGB images as
            Args:
                X_data (list): List of paths to the training images
                y_data (list): List of paths to the target images
                X_transform (callable, optional): A function/transform that takes in 2 numpy arrays
                    (train_img, mask_img) and returns a transformed version with the same signature
                y_transform (callable, optional): A function/transform that takes in 2 numpy arrays
                    (train_img, mask_img) and returns a transformed version with the same signature
             Attributes:
                classes (list): List of the class names.
                class_to_idx (dict): Dict with items (class_name, class_index).
                imgs (list): List of (image path, class_index) tuples
        """
        self.X_train = X_data
        self.y_train_masks = y_data
        self.img_resize = img_resize
        self.y_transform = y_transform
        self.X_transform = X_transform

    def __getitem__(self, index):
        """
        Args:
            index (int): Index
        Returns:
            tuple: (image, target) where target is class_index of the target class.
        """
        img = Image.open(self.X_train[index])
        img = img.resize(self.img_resize, Image.ANTIALIAS)
        # Pillow reads gifs
        mask = Image.open(self.y_train_masks[index])
        mask = mask.resize(self.img_resize, Image.ANTIALIAS)

        img = np.asarray(img.convert("RGB"), dtype=np.float32)
        mask = np.asarray(mask.convert("L"), dtype=np.float32)  # GreyScale

        if self.X_transform:
            img, mask = self.X_transform(img, mask)

        if self.y_transform:
            img, mask = self.y_transform(img, mask)

        mask = np.expand_dims(mask, axis=2)
        img /= 255
        mask /= 255
        return img, mask

    def __len__(self):
        assert len(self.X_train) == len(self.y_train_masks)
        return len(self.X_train)