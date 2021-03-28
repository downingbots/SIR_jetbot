import torchvision.datasets as datasets
from dataset_utils import *

# based on:
# https://pytorch.org/docs/stable/_modules/torchvision/datasets/folder.html#ImageFolder
#
# The goal of this class is to remap data collected for a particular function to a more generalized
# set of metadata. For example, a particular function may not use all robot actions (e.g., the arm
# or reverse) but the NN is consistently trained across all possible robot actions.
# Another example is "automatic mode", where the primitive actions can be mapped to to NOOPs
# if determined programatically.
# 
# only_new_images: root directory 
class ImageFolder2(datasets.ImageFolder):
    def __init__(
            self,
            root: str,
            app_name,
            app_type,
            transform = None,
            target_transform = None,
            # loader: Callable[[str], Any] = torchvision.default_loader,
            is_valid_file = None,
            full_action_set = None,
            remap_to_noop = None,
            only_new_images = None,
    ):
        # super(datasets.ImageFolder, self).__init__(root, loader, IMG_EXTENSIONS if is_valid_file is None else None,
        self.app_type = app_type
        if self.app_type == "FUNC":
            self.app_name = None
            self.nn_name = app_name
        else:
            self.app_name = app_name
            self.nn_name = None
        self.ds_util = DatasetUtils(self.app_name, self.app_type)
        # From original code:
        # self.classes = [d.name for d in os.scandir(dir) if d.is_dir()]
        # self.classes.sort()
        # self.class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}
        # self.imgs= [image_path, class_index]
        if full_action_set is not None:
          # full_action_set.sort()  # full_action_set is a sorted tuple
          self.classes = full_action_set
          self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}
          print("new:", self.class_to_idx)

        if full_action_set is not None or remap_to_noop is not None:
          old_classes = self.classes
          old_class_to_idx = self.class_to_idx
          print("old:", old_class_to_idx)

        try:
          super(ImageFolder2, self).__init__(root, 
                                          # loader
                                          # IMG_EXTENSIONS if is_valid_file is None else None,
                                          transform=transform,
                                          target_transform=target_transform,
                                          is_valid_file=is_valid_file)
        except:
          self.imgs = []
          return 
        self.imgs = self.samples

        if remap_to_noop is not None:
          # NOOP must be in class list
          noop_idx = self.classes.index("NOOP")

          old_class_idx = []
          for old_class in remap_to_noop: 
              old_class_idx.append( old_classes.index(old_class))

        if only_new_images is not None and only_new_images:
          # new_images = ds_util.new_images(root)
          new_images,idx_list = self.ds_util.get_dataset_images(mode="FUNC", nn_name=self.nn_name, position="NEXT")

          img_lst = []
          for i, [image_path, old_class_index] in enumerate(self.imgs): 
               if image_path in new_images:
                  img_lst.append(self.imgs[i])
          print("original number of images in dataset:", len(self.imgs))
          print("number of new images in dataset     :", len(img_lst))
          print("number of new images in dataset idx :", len(new_images))
          print("idx_list:", idx_list)
          self.imgs = img_lst

        if full_action_set is not None or remap_to_noop is not None or only_new_images is not None:
          for i, [image_path, old_class_index] in enumerate(self.imgs): 
              if (remap_to_noop is not None and old_class_index in old_class_idx):
                  item = image_path, noop_idx
                  self.imgs[i] = item
                  print(self.imgs[i], old_class_index)
              elif (full_action_set is not None and
                    old_classes[old_class_index] != self.classes[old_class_index]):
                  # self.classes should be a superset of the old_classes,
                  # but the sorting can reorder the idx.
                  print("old_class_index", old_class_index)
                  print("old_classes", old_classes)
                  print("class_to_idx", self.class_to_idx)
                  new_item  = image_path, self.class_to_idx[old_classes[old_class_index]]
                  self.imgs[i] = new_item
                  print(self.imgs[i], old_class_index)

    def all_images_processed(self, mode, nn_name):
          return self.ds_util.all_indices_processed(mode, nn_name)

    def save_images_processed(self, mode, nn_name):
          # new_images = ds_util.new_images(root)
          self.ds_util.dataset_images_processed(mode, nn_name)
