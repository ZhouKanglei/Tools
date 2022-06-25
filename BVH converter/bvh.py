# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 2022/6/25 10:02

import numpy as np
import re

import os
from transforms3d.euler import euler2mat, mat2euler

import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'serif'
plt.rcParams['text.usetex'] = True
plt.rcParams['savefig.bbox'] = 'tight'


class bvhJoint(object):
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.offset = np.zeros(3)
        self.channels = []
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def __repr__(self):
        return self.name

    def position_animated(self):
        return any([x.endswith('position') for x in self.channels])

    def rotation_animated(self):
        return any([x.endswith('rotation') for x in self.channels])


class bvh(object):
    def __init__(self):
        self.joints = {}
        self.root = None
        self.keyframes = None
        self.frames = 0
        self.fps = 0
        self.adj = None

    def _parse_hierarchy(self, text):
        lines = re.split('\\s*\\n+\\s*', text)

        joint_stack = []

        for line in lines:
            words = re.split('\\s+', line)
            instruction = words[0]

            if instruction == "JOINT" or instruction == "ROOT":
                parent = joint_stack[-1] if instruction == "JOINT" else None
                joint = bvhJoint(words[1], parent)
                self.joints[joint.name] = joint
                if parent:
                    parent.add_child(joint)
                joint_stack.append(joint)
                if instruction == "ROOT":
                    self.root = joint
            elif instruction == "CHANNELS":
                for i in range(2, len(words)):
                    joint_stack[-1].channels.append(words[i])
            elif instruction == "OFFSET":
                for i in range(1, len(words)):
                    joint_stack[-1].offset[i - 1] = float(words[i])
            elif instruction == "End":
                joint = bvhJoint(joint_stack[-1].name + "_end", joint_stack[-1])
                joint_stack[-1].add_child(joint)
                joint_stack.append(joint)
                self.joints[joint.name] = joint
            elif instruction == '}':
                joint_stack.pop()

    def _gen_adj(self):
        self.adj = np.eye(len(anim.joints), len(anim.joints))
        joint_names = list(anim.joint_names())

        for i in range(len(anim.joints)):
            parent = anim.joints[joint_names[i]].parent
            if parent != None:
                j = joint_names.index(parent.name)
                self.adj[i, j] = 1
                self.adj[j, i] = 1
                print(i, '----', j)

    def _add_pose_recursive(self, joint, offset, poses):
        pose = joint.offset + offset
        poses.append(pose)

        for c in joint.children:
            self._add_pose_recursive(c, pose, poses)

    def plot_hierarchy(self):
        import matplotlib.pyplot as plt
        poses = []
        self._add_pose_recursive(self.root, np.zeros(3), poses)
        pos = np.array(poses)

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        self._plot(ax, pos)

        plt.show()

    def parse_motion(self, text):
        lines = re.split('\\s*\\n+\\s*', text)

        frame = 0
        for line in lines:
            if line == '':
                continue
            words = re.split('\\s+', line)

            if line.startswith("Frame Time:"):
                self.fps = round(1 / float(words[2]))
                continue

            if line.startswith("Frames:"):
                self.frames = int(words[1])
                continue

            if self.keyframes is None:
                self.keyframes = np.empty((self.frames, len(words)), dtype=np.float32)

            for angle_index in range(len(words)):
                self.keyframes[frame, angle_index] = float(words[angle_index])

            frame += 1

    def parse_string(self, text):
        hierarchy, motion = text.split("MOTION")
        self._parse_hierarchy(hierarchy)
        self._gen_adj()
        self.parse_motion(motion)

    def _extract_rotation(self, frame_pose, index_offset, joint):
        local_rotation = np.zeros(3)
        for channel in joint.channels:
            if channel.endswith("position"):
                continue
            if channel == "Xrotation":
                local_rotation[0] = frame_pose[index_offset]
            elif channel == "Yrotation":
                local_rotation[1] = frame_pose[index_offset]
            elif channel == "Zrotation":
                local_rotation[2] = frame_pose[index_offset]
            else:
                raise Exception(f"Unknown channel {channel}")
            index_offset += 1

        local_rotation = np.deg2rad(local_rotation)
        M_rotation = np.eye(3)
        for channel in joint.channels:
            if channel.endswith("position"):
                continue

            if channel == "Xrotation":
                euler_rot = np.array([local_rotation[0], 0., 0.])
            elif channel == "Yrotation":
                euler_rot = np.array([0., local_rotation[1], 0.])
            elif channel == "Zrotation":
                euler_rot = np.array([0., 0., local_rotation[2]])
            else:
                raise Exception(f"Unknown channel {channel}")

            M_channel = euler2mat(*euler_rot)
            M_rotation = M_rotation.dot(M_channel)

        return M_rotation, index_offset

    def _extract_position(self, joint, frame_pose, index_offset):
        offset_position = np.zeros(3)
        for channel in joint.channels:
            if channel.endswith("rotation"):
                continue
            if channel == "Xposition":
                offset_position[0] = frame_pose[index_offset]
            elif channel == "Yposition":
                offset_position[1] = frame_pose[index_offset]
            elif channel == "Zposition":
                offset_position[2] = frame_pose[index_offset]
            else:
                raise Exception(f"Unknown channel {channel}")
            index_offset += 1

        return offset_position, index_offset

    def _recursive_apply_frame(self, joint, frame_pose, index_offset, p, r, M_parent, p_parent):
        if joint.position_animated():
            offset_position, index_offset = self._extract_position(joint, frame_pose, index_offset)
        else:
            offset_position = np.zeros(3)

        if len(joint.channels) == 0:
            joint_index = list(self.joints.values()).index(joint)
            p[joint_index] = p_parent + M_parent.dot(joint.offset)
            r[joint_index] = mat2euler(M_parent)
            return index_offset

        if joint.rotation_animated():
            M_rotation, index_offset = self._extract_rotation(frame_pose, index_offset, joint)
        else:
            M_rotation = np.eye(3)

        M = M_parent.dot(M_rotation)
        position = p_parent + M_parent.dot(joint.offset) + offset_position

        rotation = np.rad2deg(mat2euler(M))
        joint_index = list(self.joints.values()).index(joint)
        p[joint_index] = position
        r[joint_index] = rotation

        print(joint_index, joint.position_animated(), joint.rotation_animated())

        for c in joint.children:
            index_offset = self._recursive_apply_frame(c, frame_pose, index_offset, p, r, M, position)



        return index_offset

    def frame_pose(self, frame):
        p = np.empty((len(self.joints), 3))
        r = np.empty((len(self.joints), 3))
        frame_pose = self.keyframes[frame]
        M_parent = np.eye(3, 3)
        self._recursive_apply_frame(self.root, frame_pose, 0, p, r, M_parent, np.zeros(3))

        return p, r

    def all_frame_poses(self):
        p = np.empty((self.frames, len(self.joints), 3))
        r = np.empty((self.frames, len(self.joints), 3))

        for frame in range(len(self.keyframes)):
            p[frame], r[frame] = self.frame_pose(frame)

        return p, r

    def _plot(self, ax, p):

        ax.cla()
        ax.scatter(p[:, 0], p[:, 2], p[:, 1], color='C0', s=8)

        for i in range(self.adj.shape[0]):
            for j in range(self.adj.shape[0]):
                if i > j and self.adj[i, j] == 1:
                    ax.plot([p[i, 0], p[j, 0]], [p[i, 2], p[j, 2]], [p[i, 1], p[j, 1]], linewidth=3, color='C1',
                            alpha=0.5)

        length = max([max(p[:, 0]) - min(p[:, 0]), max(p[:, 2]) - min(p[:, 2]), max(p[:, 1]) - min(p[:, 1])])
        ax.set_xlim((max(p[:, 0]) + min(p[:, 0]) - length) / 2, (max(p[:, 0]) + min(p[:, 0]) + length) / 2)
        ax.set_ylim((max(p[:, 2]) + min(p[:, 2]) - length) / 2, (max(p[:, 2]) + min(p[:, 2]) + length) / 2)
        ax.set_zlim((max(p[:, 1]) + min(p[:, 1]) - length) / 2, (max(p[:, 1]) + min(p[:, 1]) + length) / 2)

        ax.set_xlabel('$x$')
        ax.set_ylabel('$y$')
        ax.set_zlabel('$z$')

    def _plot_pose(self, p, r, fig=None, ax=None):
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import axes3d, Axes3D
        if fig is None:
            fig = plt.figure()
        if ax is None:
            ax = fig.add_subplot(111, projection='3d')

        self._plot(ax, p)

    def plot_frame(self, frame, fig=None, ax=None):
        p, r = self.frame_pose(frame)
        self._plot_pose(p, r, fig, ax)

        plt.title(f'{frame}-th frame')
        plt.show()

    def joint_names(self):
        return self.joints.keys()

    def parse_file(self, path):
        with open(path, 'r') as f:
            self.parse_string(f.read())

    def plot_all_frames(self):
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import axes3d, Axes3D
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        all_p, all_r = self.all_frame_poses()
        for i in range(self.frames):
            p, r = all_p[i], all_r[i]

            self._plot_pose(p, r, fig, ax)

            length = np.max(
                [np.max(all_p[:, :, 0]) - np.min(all_p[:, :, 0]), np.max(all_p[:, :, 2]) - np.min(all_p[:, :, 2]),
                 np.max(all_p[:, :, 1]) - np.min(all_p[:, :, 1])])
            ax.set_xlim((np.max(all_p[:, :, 0]) + np.min(all_p[:, :, 0]) - length) / 2,
                        (np.max(all_p[:, :, 0]) + np.min(all_p[:, :, 0]) + length) / 2)
            ax.set_ylim((np.max(all_p[:, :, 2]) + np.min(all_p[:, :, 2]) - length) / 2,
                        (np.max(all_p[:, :, 2]) + np.min(all_p[:, :, 2]) + length) / 2)
            ax.set_zlim((np.max(all_p[:, :, 1]) + np.min(all_p[:, :, 1]) - length) / 2,
                        (np.max(all_p[:, :, 1]) + np.min(all_p[:, :, 1]) + length) / 2)


            plt.title(f'{i}-th frame')
            plt.draw()
            plt.pause(0.001)

    def make_video(self, video_name='.bvh.mp4'):
        import matplotlib.pyplot as plt
        from matplotlib import animation
        plt.close()

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        all_p, all_r = self.all_frame_poses()

        def update(i):
            p, r = all_p[i], all_r[i]

            self._plot_pose(p, r, fig, ax)

            length = np.max(
                [np.max(all_p[:, :, 0]) - np.min(all_p[:, :, 0]), np.max(all_p[:, :, 2]) - np.min(all_p[:, :, 2]),
                 np.max(all_p[:, :, 1]) - np.min(all_p[:, :, 1])])
            ax.set_xlim((np.max(all_p[:, :, 0]) + np.min(all_p[:, :, 0]) - length) / 2,
                        (np.max(all_p[:, :, 0]) + np.min(all_p[:, :, 0]) + length) / 2)
            ax.set_ylim((np.max(all_p[:, :, 2]) + np.min(all_p[:, :, 2]) - length) / 2,
                        (np.max(all_p[:, :, 2]) + np.min(all_p[:, :, 2]) + length) / 2)
            ax.set_zlim((np.max(all_p[:, :, 1]) + np.min(all_p[:, :, 1]) - length) / 2,
                        (np.max(all_p[:, :, 1]) + np.min(all_p[:, :, 1]) + length) / 2)

            plt.title(f'{i}-th frame')

        ani = animation.FuncAnimation(fig=fig, func=update, frames=self.frames)

        os.makedirs(os.path.dirname(video_name), exist_ok=True)
        ani.save(filename=video_name, writer='ffmpeg', fps=20)
        print(f'Save video to {video_name}.')

        def __repr__(self):
            return f"BVH {len(self.joints.keys())} joints, {self.frames} frames"


if __name__ == '__main__':
    # create bvh parser
    anim = bvh()
    # parser file
    anim.parse_file("example.bvh")
    print(anim.__repr__)

    # draw the skeleton in T-pose
    anim.plot_hierarchy()

    # extract single frame pose: axis0=joint, axis1=positionXYZ/rotationXYZ
    p, r = anim.frame_pose(0)

    # extract all poses: axis0=frame, axis1=joint, axis2=positionXYZ/rotationXYZ
    all_p, all_r = anim.all_frame_poses()

    print(all_p.shape)

    # print all joints, their positions and orientations
    for _p, _r, _j in zip(p, r, anim.joint_names()):
        print(f"{_j}: p={_p}, r={_r}")

    # draw the skeleton for the given frame
    # anim.plot_frame(22)

    # show full animation
    # anim.plot_all_frames()
    
    # generate video
    anim.make_video('./output.gif')

