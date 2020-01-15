#!/usr/bin/env python
import os
import argparse
import json
import shutil

import numpy as np
import torch
import skvideo.io

from processor.io import IO
import tools
import tools.utils as utils

class Demo(IO):
    """
        Demo for Skeleton-based Action Recgnition
    """
    def start(self):
        video = utils.video.get_video_frames('/media/simslab-cs/A/videoset/cgutest.mp4')
        height, width, _ = video[0].shape
        
        file_json = 'cgutest.json'
        with open(file_json, encoding='utf-8') as data_file:
            data = json.loads(data_file.read())
        sequence_info = []
        weight = data.get('## description').get('image_width')
        height = data.get('## description').get('image_height')
        for frame_number in data.keys():
            try:
                frame_number = int(frame_number)
            except Exception as e:
                continue
            #Get highest possibilites human confiden score --> usualy at detection no 0
            id_name = list(data.get(str(frame_number)).keys())[2]

            frame_id = frame_number
            frame_data = {'frame_index': frame_id}
            skeletons = []

            score, coordinates = [], []
            skeleton = {}


            for part in data.get(str(frame_number)).get(id_name):
                coordinates += [int(part.get('position')[0]*weight+0.5),int(
                    part.get('position')[1]*height+0.5)]
                score += [part.get('score')]
            skeleton['pose'] = coordinates
            skeleton['score'] = score
            skeletons +=[skeleton]
            frame_data['skeleton'] = skeletons
            sequence_info += [frame_data]

        video_info = dict()
        video_info['data'] = sequence_info
        video_info['label'] = 'unknowns'
        video_info['label_index'] = -1
        print('BREAKKKKKKK')
        

        # parse skeleton data
        pose, _ = utils.video.video_info_parsing(video_info)
        data = torch.from_numpy(pose)
        data = data.unsqueeze(0)
        data = data.float().to(self.dev).detach()

        # extract feature
        print('\nNetwork forwad...')
        self.model.eval()
        output, feature = self.model.extract_feature(data)
        output = output[0]
        feature = feature[0]
        intensity = (feature*feature).sum(dim=0)**0.5
        intensity = intensity.cpu().detach().numpy()
        label = output.sum(dim=3).sum(dim=2).sum(dim=1).argmax(dim=0)
        print('Prediction result: {}'.format(label_name[label]))
        print('Done.')

        # visualization
        print('\nVisualization...')
        label_sequence = output.sum(dim=2).argmax(dim=0)
        label_name_sequence = [[label_name[p] for p in l ]for l in label_sequence]
        edge = self.model.graph.edge
        images = utils.visualization.stgcn_visualize(
            pose, edge, intensity, video,label_name[label] , label_name_sequence, self.arg.height)
        print('Done.')

        # save video
        print('\nSaving...')
        if not os.path.exists(output_result_dir):
            os.makedirs(output_result_dir)
        writer = skvideo.io.FFmpegWriter(output_result_path,
                                        outputdict={'-b': '300000000'})
        for img in images:
            writer.writeFrame(img)
        writer.close()
        print('The Demo result has been saved in {}.'.format(output_result_path))

    @staticmethod
    def get_parser(add_help=False):

        # parameter priority: command line > config > default
        parent_parser = IO.get_parser(add_help=False)
        parser = argparse.ArgumentParser(
            add_help=add_help,
            parents=[parent_parser],
            description='Demo for Spatial Temporal Graph Convolution Network')

        # region arguments yapf: disable
        parser.add_argument('--video',
            default='./resource/media/skateboarding.mp4',
            help='Path to video')
        parser.add_argument('--openpose',
            default='3dparty/openpose/build',
            help='Path to openpose')
        parser.add_argument('--output_dir',
            default='./data/demo_result',
            help='Path to save results')
        parser.add_argument('--height',
            default=1080,
            type=int,
            help='Path to save results')
        parser.set_defaults(config='./config/st_gcn/kinetics-skeleton/demo.yaml')
        parser.set_defaults(print_log=False)
        # endregion yapf: enable

        return parser
