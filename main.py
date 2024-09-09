import argparse
from pointjepa.models import PointJepaEncoder
import torch

def parse_args() -> None:
    parser = argparse.ArgumentParser(
        description="PointJepa Embedding Cluster Visualization"
    )
    parser.add_argument("--finetuned_ckpt_path", "-ch", type=str, required=True)
    return parser.parse_args()

def main():
    li_model = PointJepaEncoder()
    args = parse_args()

    li_model = li_model.load_from_checkpoint(args.finetuned_ckpt_path, strict=False)
    li_model = li_model.cuda()
    print("checkpoint loaded.")
    
    points = torch.randn((1,512, 3)).cuda()
    
    features = li_model(points)
    print(features.shape)
    
if __name__ == "__main__":
    main()