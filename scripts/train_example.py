import os
import configargparse

import torch
from torch.utils.data import DataLoader

from lib_main import datasets
from lib_main import losses, trainer, summaries, models


def parse_args():
    p = configargparse.ArgumentParser()
    p.add('-c', '--config_filepath', required=False, is_config_file=True, help='Path to config file.')

    dirname = os.path.abspath(os.path.dirname(__file__+'/../../../../'))
    p.add_argument('--saving_root', type=str, default=os.path.join(dirname, 'logs')
                   , help='root for saving logging')

    p.add_argument('--experiment_name', type=str, required=False, default='pre_train_sdf_exp',
                   help='Name of subdirectory in logging_root where summaries and checkpoints will be saved.')

    p.add_argument('--sidelength', type=int, default=128)

    # model parameters
    p.add_argument('--z_dim', type=int, default=128)

    # General training options
    p.add_argument('--batch_size', type=int, default=2)
    p.add_argument('--lr', type=float, default=1e-4, help='learning rate. default=5e-5')
    p.add_argument('--num_epochs', type=int, default=40001,
                   help='Number of epochs to train for.')

    p.add_argument('--epochs_til_ckpt', type=int, default=100,
                   help='Time interval in seconds until checkpoint is saved.')
    p.add_argument('--steps_til_summary', type=int, default=3000,
                   help='Time interval in seconds until tensorboard summary is saved.')
    p.add_argument('--iters_til_ckpt', type=int, default=10000,
                   help='Training steps until save checkpoint')

    p.add_argument('--device',  type=str, default='cuda',)

    p.add_argument('--depth_aug', action='store_true', help='depth_augmentation')
    p.add_argument('--multiview_aug', action='store_true', help='multiview_augmentation')

    p.add_argument('--checkpoint_path', default=None, help='Checkpoint to trained model.')
    p.add_argument('--dgcnn', action='store_true',
                   help='If you want to use a DGCNN encoder instead of pointnet (requires more GPU memory)')
    opt = p.parse_args()
    return opt


def get_model(opt, device):
    ################# SDF MODEL #####################
    ## Decoder ##
    dec_sdf = DecoderInner(z_dim=3)
    ## Build model ##
    occupancy_net = base.SDFNeuralField(decoder=dec_sdf).to(device)
    return occupancy_net


def main(opt):

    if opt.device =='cuda':
        device = torch.device('cuda:' + str(0) if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device('cpu')

    ## Dataset
    train_dataset = datasets.AcronymSDFDataset(one_object=True)
    train_dataloader = DataLoader(train_dataset, batch_size=opt.batch_size, shuffle=True,
                                  drop_last=True)

    ## Model
    model = get_model(opt, device)

    if opt.checkpoint_path is not None:
        model.load_state_dict(torch.load(opt.checkpoint_path))

    # Losses
    loss = losses.SDFLoss()
    loss_fn = val_loss_fn = loss.loss_fn

    # saving directories
    root_dir = opt.saving_root
    exp_dir  = os.path.join(root_dir, opt.experiment_name)

    ## Summaries
    summary = summaries.sdf_summary

    # Train
    trainer.train(model=model, train_dataloader=train_dataloader, epochs=opt.num_epochs, model_dir= exp_dir,
                summary_fn=summary, device=device,
                lr=opt.lr, steps_til_summary=opt.steps_til_summary, epochs_til_checkpoint=opt.epochs_til_ckpt,
                loss_fn=loss_fn, iters_til_checkpoint=opt.iters_til_ckpt,
                clip_grad=False, val_loss_fn=val_loss_fn, overwrite=True)


if __name__ == '__main__':
    args = parse_args()
    main(args)