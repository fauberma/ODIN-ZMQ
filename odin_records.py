import numpy as np
import re
import pandas as pd
import os
from PIL import Image
import cv2
import matplotlib.pyplot as plt
from matplotlib.widgets import PolygonSelector, RectangleSelector
from matplotlib.path import Path
from matplotlib.patches import Polygon

class Odin:
    def __init__(self, file_loc):
        self.file_loc = os.path.normpath(file_loc)

        #get settings
        with open(os.path.join(self.file_loc, 'settings.exp')) as f:
            lines = [line.strip() for line in f.readlines()]
        general, roi = lines[:lines.index('[[ROI]]')], lines[lines.index('[[ROI]]'):]
        self.sets = dict([line.split('=') for line in general if '=' in line])

        #self.ROI_sets = dict()
        #for line in roi:
        #    if line == '[[ROI]]':
        #        continue

        self.n_chan = int(self.sets['alt_count'])
        self.f_dim = (int(self.sets['yend0'])-int(self.sets['ybegin0']), int(self.sets['xend0'])-int(self.sets['xbegin0']))
        self.chan = dict([[self.sets['alt_name'+str(i)], slice(i*self.f_dim[1], (i+1) * self.f_dim[1])] for i in range(self.n_chan)])

        #get log file
        self.log = pd.read_csv(os.path.join(self.file_loc, 'ROI0', 'ROI0.log'))
        self.log['ID'] = self.log.index
        self.n_frames = len(self.log)
        self.features = set([col[:-1] for col in self.log.columns])

        # AVI file
        if self.sets['video_format'] == 'avi':
            self.frames = np.empty((self.n_frames, self.f_dim[0], self.f_dim[1]*self.n_chan))
            vidcap = cv2.VideoCapture(os.path.join(self.file_loc, 'ROI0', 'ROI0.avi'))
            for i in range(self.n_frames):
                success, frame = vidcap.read()
                if not success:
                    break
                self.frames[i] = frame[:, :, 0]
            self.dtype = self.frames.dtype

        #REC file
        elif self.sets['video_format'] == 'rec':
            self.header = {}
            with open(os.path.join(self.file_loc, 'ROI0', 'ROI0.rec'), 'rb') as f:
                while True:  # read header until End of header
                    line = f.readline().decode('ASCII').strip()
                    if '=' in line:
                        key, val = line.split('=')
                        try:
                            val = int(val)
                        except ValueError:
                            pass
                        self.header[key] = val
                    if 'End of header' in line:
                        break

            self.dtype = 'uint' + str(self.header['BitsPerPixel'])
            self.n_frames = self.header['NumberofFrames_00']
            self.frame_dim = (self.header['FrameHeightInPixel'], self.header['FrameWidthInPixel'])
            with open(os.path.join(self.file_loc, 'ROI0', 'ROI0.rec'), 'rb') as f:
                f.seek(self.header['OffsetToFirstFrame'])  # jump to location of first frame
                self.frames = np.frombuffer(f.read(), dtype=self.dtype).reshape(self.n_frames, *self.frame_dim)

        with open(os.path.join(self.file_loc, 'realtime.c')) as f:
            script_content = f.read()

        pattern = r'const int region_0_0_size = (\d+);\s*const float region_0_0\[\]={(.*?)};'

        # Find the region_0_0 array content using the regular expression
        match = re.search(pattern, script_content, re.DOTALL)

        if match:
            region_0_0_size = int(match.group(1))

            # Extract the content of the region_0_0 array
            region_0_0_content = match.group(2)

            # Split the content by commas to get individual vertices
            vertices = region_0_0_content.split(',')

            # Process each vertex (assuming each vertex has an x and y coordinate)
            self.vertices = np.array([float(coord.strip()) for coord in vertices if coord.strip() != '']).reshape((region_0_0_size,2))
            #self.vertices = self.vertices[:, ::-1]

        else:
            print("No polygon for sorting in this script.")

        pattern = r'in_regions0\(.*?in_polygon\(region_0_0, region_0_0_size, (.*?), (.*?)\)'

        # Find the in_regions0 function and extract the arguments passed to in_polygon using the regular expression
        matches = re.findall(pattern, script_content, re.DOTALL)

        if matches:
            # Print the extracted arguments for each match
            for match in matches:
                chan_x, x = match[0].split('.')
                chan_y, y = match[1].split('.')
                self.sorting_x = x+chan_x[2]
                self.sorting_y = y+chan_y[2]

    def export_frames(self, export_loc, list_of_frames=None):
        for n in range(self.n_frames) if list_of_frames is None else list_of_frames:
            Image.fromarray(self.frames[n]).save(os.path.join(export_loc, str(n) + '.png'))

    def add_polygon(self, xkey, ykey, query='ID==ID', markersize=5, hue=None):
        fig, ax = plt.subplots(figsize=(7, 7))
        ax.set_xlabel(xkey)
        ax.set_ylabel(ykey)
        data = self.log.query(query).reset_index()
        if hue is not None:
            color = (data[hue]).astype(int)
            pts = ax.scatter(data[xkey], data[ykey], c=color, s=markersize, cmap='seismic')
        else:
            pts = ax.scatter(data[xkey], data[ykey], s=markersize)
        return (SelectFromCollection(ax, pts), data)

    def apply_polygon_gate(self, polygon, gate_name):
        selector, data = polygon
        selector.disconnect()
        self.log[gate_name] = False
        self.log.loc[selector.ind, gate_name] = True

    def inspect(self, xkey, ykey, query='ID==ID', markersize=5, hue=None):
        def onclick(event):
            f_index = data.loc[event.ind[0], 'ID']
            im = self.frames[f_index]
            ax2.imshow(im, cmap='gray', interpolation='None')
            ax2.set_title('Frameindex: {}'.format(f_index))
            ax2.grid(False)
            ax2.axis(False)

        fig, (ax1, ax2) = plt.subplots(figsize=(10, 5), ncols=2)
        ax1.set_xlabel(xkey)
        ax1.set_ylabel(ykey)
        data = self.log.query(query).reset_index()
        if hue is not None:
            color = (data[hue]).astype(int)
            ax1.scatter(data[xkey], data[ykey], c=color, cmap='seismic', picker=True, s=markersize)
        else:
            ax1.scatter(data[xkey], data[ykey], picker=True, s=markersize, edgecolor='None')

        fig.canvas.mpl_connect('pick_event', onclick)

    def simulate_gates(self, bf_key='nBF', fl_key='nFL', query='ID==ID', scale=5000):
        data = self.log.query(query)
        matrix, bf_bins, fl_bins = np.histogram2d(data[bf_key], data[fl_key], range=[(0, 10), (0, 10)], normed=True)

        bf_coord = np.repeat(bf_bins[:-1], len(fl_bins) - 1)
        fl_coord = np.tile(fl_bins[:-1], len(bf_bins) - 1)
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.scatter(bf_coord, fl_coord, s=matrix.flatten() * scale)
        ax.set_xlabel(bf_key)
        ax.set_ylabel(fl_key)
        ax.set_title('Gate coverage: {} %'.format(int(100*len(data)/len(self.log))))
        for bf, fl, s in zip(bf_coord, fl_coord, matrix.flatten()):
            if s > 0.001:
                ax.text(bf, fl, np.round(100 * s, 1), c='r', horizontalalignment='center', verticalalignment='center')


class SelectFromCollection:
    def __init__(self, ax, collection, alpha_other=0.3):
        self.canvas = ax.figure.canvas
        self.collection = collection
        self.alpha_other = alpha_other

        self.xys = collection.get_offsets()
        self.Npts = len(self.xys)

        # Ensure that we have separate colors for each object
        self.fc = collection.get_facecolors()
        if len(self.fc) == 0:
            raise ValueError('Collection must have a facecolor')
        elif len(self.fc) == 1:
            self.fc = np.tile(self.fc, (self.Npts, 1))

        self.poly = PolygonSelector(ax, self.onselect)
        self.ind = []

    def onselect(self, verts):
        path = Path(verts)
        self.ind = np.nonzero(path.contains_points(self.xys))[0]
        self.fc[:, -1] = self.alpha_other
        self.fc[self.ind, -1] = 1
        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()

    def disconnect(self):
        self.poly.disconnect_events()
        self.fc[:, -1] = 1
        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()