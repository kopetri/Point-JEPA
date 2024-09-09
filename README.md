# Point-JEPA

Joint-Embedding Predictive Architecture on Point Clouds

## Model Zoo


| Type                         | Dataset      | Evaluation                          | Config                                                                                       | Checkpoint                                                                                                                                    |
| ---------------------------- | ------------ | ----------------------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Point-JEPA pre-trained        | ShapeNet     | -                                   | [config](configs/Point-JEPA/pretraining/shapenet.yaml)                                                  | [checkpoint](https://drive.google.com/file/d/1MR3OYA6N0TINyPCKgwOU3zswQoM8DXbY/view?usp=drive_link)                          |
| Point-JEPA SVM Linear | ShapeNet     | **93.7&pm;0.2**                                   | -                                                  | [checkpoint](https://drive.google.com/file/d/1MR3OYA6N0TINyPCKgwOU3zswQoM8DXbY/view?usp=drive_link)                          |
| Classification fine-tuned    | ModelNet40   | **93.8&pm;0.2** / **94.1&pm;0.1** (OA / Voting) | [config](configs/Point-JEPA/classification/modelnet40.yaml)   | [checkpoint](https://drive.google.com/file/d/1EOiHBu06pRah2MRlEapPQmks3BmjXgbB/view?usp=sharing)         |
| Classification fine-tuned    | ScanObjectNN | **86.6&pm;0.3** (OA)                      | [config](configs/Point-JEPA/classification/scanobjectnn.yaml) | [checkpoint](https://drive.google.com/file/d/1vnhQdVBliGxQ09vazZCuOlFsgBAThlqg/view?usp=sharing)       |
| Part segmentation fine-tuned | ShapeNetPart | **85.8&pm;0.1** (Cat. mIoU)               | [config](configs/Point-JEPA/part_segmentation/shapenetpart.yaml)                                        | [checkpoint](https://drive.google.com/file/d/1lS1_lKTsaTgQ4MCucfSCkmNyhLAgaxG7/view?usp=sharing) |


Please note that weights that are attached above are the ones that yields the best results out of 10 independent runs (details mentioned in the paper).
