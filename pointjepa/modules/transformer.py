from dataclasses import dataclass
from typing import List, Optional

import torch
import torch.nn as nn
from timm.models.layers import DropPath
from torch import nn


class Mlp(nn.Module):
    def __init__(
        self,
        in_features,
        hidden_features=None,
        out_features=None,
        act_layer=nn.GELU,
        drop=0.0,
    ):
        super().__init__()
        out_features = out_features or in_features
        hidden_features = hidden_features or in_features

        self.fc1 = nn.Linear(in_features, hidden_features)
        self.act = act_layer()
        self.fc2 = nn.Linear(hidden_features, out_features)
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        x = self.fc1(x)
        x = self.act(x)
        x = self.drop(x)
        x = self.fc2(x)
        x = self.drop(x)
        return x


class Attention(nn.Module):
    def __init__(
        self,
        dim,
        num_heads=8,
        qkv_bias=False,
        qk_scale=None,
        attn_drop=0.0,
        proj_drop=0.0,
    ):
        super().__init__()
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = qk_scale or head_dim**-0.5
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)

    def forward(self, x):
        B, N, C = x.shape
        qkv = (
            self.qkv(x)
            .reshape(B, N, 3, self.num_heads, C // self.num_heads)
            .permute(2, 0, 3, 1, 4)
        )
        q, k, v = qkv[0], qkv[1], qkv[2]

        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = attn.softmax(dim=-1)
        _attn = attn
        attn = self.attn_drop(attn)

        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x, _attn


class OffsetAttention(nn.Module):
    def __init__(
        self,
        dim,
        num_heads=8,
        qkv_bias=False,
        qk_scale=None,
        attn_drop=0.0,
        proj_drop=0.0,
    ):
        super().__init__()
        self.num_heads = num_heads
        head_dim = dim // num_heads
        # self.scale = qk_scale or head_dim**-0.5
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)

    def forward(self, x):
        B, N, C = x.shape
        qkv = (
            self.qkv(x)
            .reshape(B, N, 3, self.num_heads, C // self.num_heads)
            .permute(2, 0, 3, 1, 4)
        )
        q, k, v = qkv[0], qkv[1], qkv[2]  # [B, H, N, C]

        attn = q @ k.transpose(-2, -1)  # [B, H, N, N]
        attn = attn.softmax(dim=-1)
        attn = attn / (1e-9 + attn.sum(dim=-2, keepdim=True))
        _attn = attn
        attn = self.attn_drop(attn)

        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x, _attn


class Block(nn.Module):
    def __init__(
        self,
        dim,
        num_heads,
        mlp_ratio=4.0,
        qkv_bias=False,
        qk_scale=None,
        drop=0.0,
        attn_drop=0.0,
        drop_path=0.0,
        act_layer=nn.GELU,
        norm_layer=nn.LayerNorm,
        attn_module: nn.Module = Attention,
    ):

        super().__init__()

        mlp_hidden_dim = int(dim * mlp_ratio)

        self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()

        # ATTENTION BLOCK
        self.norm1 = norm_layer(dim)
        self.attn = attn_module(
            dim,
            num_heads=num_heads,
            qkv_bias=qkv_bias,
            qk_scale=qk_scale,
            attn_drop=attn_drop,
            proj_drop=drop,
        )

        # MLP BLOCK
        self.norm2 = norm_layer(dim)
        self.mlp = Mlp(
            in_features=dim,
            hidden_features=mlp_hidden_dim,
            act_layer=act_layer,
            drop=drop,
        )

    def forward(self, x) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        _x, attn = self.attn(self.norm1(x))
        x = x + self.drop_path(_x)
        ffn = self.mlp(self.norm2(x))
        x = x + self.drop_path(ffn)
        return x, attn, ffn


@dataclass()
class TransformerEncoderOutput:
    last_hidden_state: torch.Tensor  # (B, T, C)
    hidden_states: Optional[List[torch.Tensor]] = None  # [(B, T, C)]
    attentions: Optional[List[torch.Tensor]] = None  # [(B, H, T)]
    ffns: Optional[List[torch.Tensor]] = None  # [(B, T, C)]


class TransformerEncoder(nn.Module):
    def __init__(
        self,
        embed_dim=768,
        depth=4,
        num_heads=12,
        mlp_ratio=4.0,
        qkv_bias=False,
        qk_scale=None,
        drop_rate=0.0,
        attn_drop_rate=0.0,
        drop_path_rate: float | List[float] = 0.0,
        add_pos_at_every_layer=False,
    ):
        super().__init__()

        self.blocks = nn.ModuleList(
            [
                Block(
                    dim=embed_dim,
                    num_heads=num_heads,
                    mlp_ratio=mlp_ratio,
                    qkv_bias=qkv_bias,
                    qk_scale=qk_scale,
                    drop=drop_rate,
                    attn_drop=attn_drop_rate,
                    drop_path=(
                        drop_path_rate[i]
                        if isinstance(drop_path_rate, list)
                        else drop_path_rate
                    ),
                )
                for i in range(depth)
            ]
        )

        # output norm
        self.norm = nn.LayerNorm(embed_dim)

        self.add_pos_at_every_layer = add_pos_at_every_layer

    def forward(
        self,
        x: torch.Tensor,
        pos: torch.Tensor,
        return_hidden_states: bool = False,
        return_attentions: bool = False,
        return_ffns: bool = False,
    ) -> TransformerEncoderOutput:
        hidden_states = [] if return_hidden_states else None
        attentions = [] if return_attentions else None
        ffns = [] if return_ffns else None
        if not self.add_pos_at_every_layer:
            x = x + pos
        for block in self.blocks:
            if self.add_pos_at_every_layer:
                x = x + pos
            x, attn, ffn = block(x)
            if return_hidden_states:
                assert hidden_states is not None
                hidden_states.append(x)
            if return_attentions:
                assert attentions is not None
                attentions.append(attn)
            if return_ffns:
                assert ffns is not None
                ffns.append(ffn)
        x = self.norm(x)
        return TransformerEncoderOutput(x, hidden_states, attentions, ffns)


class TransformerPredictor(nn.Module):
    def __init__(
        self,
        embed_dim=384,
        predictor_embed_dim=192,
        depth=6,
        num_heads=4,
        mlp_ratio=4.0,
        qkv_bias=True,
        qk_scale=None,
        drop_rate=0.0,
        attn_drop_rate=0.05,
        drop_path_rate=0.25,
        add_pos_at_every_layer=False,
        add_target_pos=False,
    ):
        super().__init__()
        self.predictor_embed = nn.Linear(embed_dim, predictor_embed_dim, bias=True)
        self.mask_token = nn.Parameter(torch.zeros(1, 1, predictor_embed_dim))
        # Might need trunc normal init here

        # Here we use the same positional encoding as the student
        self.positional_encoding = nn.Sequential(
            nn.Linear(3, 128),
            nn.GELU(),
            nn.Linear(128, predictor_embed_dim),
        )

        self.predictor_norm = nn.LayerNorm(predictor_embed_dim)
        self.predictor_proj = nn.Linear(predictor_embed_dim, embed_dim, bias=True)

        self.predictor = TransformerEncoder(
            embed_dim=predictor_embed_dim,
            depth=depth,
            num_heads=num_heads,
            mlp_ratio=mlp_ratio,
            qkv_bias=qkv_bias,
            qk_scale=qk_scale,
            drop_rate=drop_rate,
            attn_drop_rate=attn_drop_rate,
            drop_path_rate=drop_path_rate,
            add_pos_at_every_layer=add_pos_at_every_layer,
        )
        self.add_target_pos = add_target_pos

    def forward(self, x, center_x, center_pred):
        # x: (B, N, C)
        # center_x: (B, N, 3)
        # center_pred: (B, T, 3)

        # Bring it down to narrower dimension
        x = self.predictor_embed(x)  # (B, N, predictor_embed_dim)

        # Add positional encoding
        if self.add_target_pos:
            pos = self.positional_encoding(center_x)
        else:
            pos = torch.zeros_like(center_x)

        B, N_ctxt, D = x.shape
        _, N_tgt, _ = center_pred.shape

        # concate mask tokens to x
        pos_embed = self.positional_encoding(center_pred)  # (B, T, predictor_embed_dim)
        mask_tokens = self.mask_token.repeat(B, N_tgt, 1)  # (B, T, predictor_embed_dim)
        pos_embed += mask_tokens

        pos = torch.cat((pos, pos_embed), dim=1)  # (B, N + T, predictor_embed_dim
        empty_feat = torch.zeros((B, N_tgt, D), device=x.device, dtype=x.dtype)
        x = torch.cat((x, empty_feat), dim=1)

        # Run through transformer
        x = self.predictor(x, pos=pos).last_hidden_state

        x = x[:, N_ctxt:, :]
        # Same with the target shape
        x = self.predictor_proj(x)  # (B, T, C)

        return x
