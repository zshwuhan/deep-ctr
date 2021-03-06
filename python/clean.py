import cPickle as pickle
import random
import time

import numpy as np


def collect(fin, size=100000):
    buf = []
    for i in range(size):
        try:
            line = next(fin)
            buf.append(line)
        except StopIteration as e:
            break
    return buf


def rand_collect(fins, size=100000):
    buf = []
    for i in range(size):
        ind = random.randrange(0, len(fins))
        try:
            line = next(fins[ind])
            buf.append(line)
        except StopIteration:
            continue
    return buf


def output(buf, fout_name):
    with open(fout_name, 'ab') as fout:
        buf_str = ''
        buf_size = 0
        for line in buf:
            buf_str += line
            buf_size += 1

            if buf_size % 100000 == 0:
                fout.write(buf_str)
                buf_str = ''
                buf_size = 0
        if buf_size:
            fout.write(buf_str)


def pos_neg_ratio(file_name):
    with open(file_name, 'r') as fin:
        pos = 0
        cnt = 0
        for line in fin:
            if line.split()[0] == '1':
                pos += 1
            cnt += 1
    print pos, cnt, pos * 1.0 / cnt


def sample(fin_path, fout_path, w, op='nds'):
    cnt = 0

    def nds_sample(lines):
        _buf_str = ''
        _buf_size = 0
        for line in lines:
            if int(line.strip().split()[0]) == 0:
                if random.random() < w:
                    _buf_size += 1
                    _buf_str += line
            else:
                _buf_size += 1
                _buf_str += line
        return _buf_str, _buf_size

    def unif_sample(lines):
        np.random.shuffle(lines)
        _buf_size = int(len(lines) * w)
        _buf_str = ''.join(lines[:_buf_size])
        return _buf_str, _buf_size

    with open(fin_path, 'rb') as fin:
        with open(fout_path, 'ab') as fout:
            start_time = time.time()
            buf = []
            buf_str = ''
            buf_size = 0
            for line in fin:
                buf.append(line)
                cnt += 1

                if cnt % 10000 == 0:
                    if op == 'nds':
                        s, n = nds_sample(buf)
                    else:
                        s, n = unif_sample(buf)
                    buf_str += s
                    buf_size += n
                    buf = []
                    if buf_size > 10000:
                        fout.write(buf_str)
                        buf_str = ''
                        buf_size = 0

                    if cnt % 10000000 == 0:
                        end_time = time.time()
                        print cnt, end_time - start_time
                        start_time = end_time

            if len(buf) > 0:
                s, n = nds_sample(buf)
                buf_str += s
                buf_size += n
            if buf_size > 0:
                fout.write(buf_str)


def seg_file(fin_path):
    with open(fin_path, 'rb') as fin:
        cnt = 0
        buf = []
        for line in fin:
            cnt += 1
            buf.append(line)

            if cnt % 4000000 == 0:
                np.random.shuffle(buf)
                output(buf, fin_path + '.%d' % (cnt / 4000000))
                buf = []
        if len(buf):
            output(buf, fin_path + '.%d' % (cnt / 4000000 + 1))


def merge_file(file_list, fout_path):
    fins = [open(f, 'rb') for f in file_list]

    num_lines = 0
    while True:
        start_time = time.time()
        buf = collect(fins)
        num_lines += len(buf)
        if len(buf) < 1:
            return

        np.random.shuffle(buf)
        output(buf, fout_path)
        print num_lines, time.time() - start_time


def build_indices(sets, fltr):
    inds = [{} for i in range(26)]
    for i in range(26):
        for k, v in sets[i].iteritems():
            if v > fltr:
                inds[i][k] = len(inds[i])
    return inds


def make_index(fin_path, fout_path, inds):
    print 'processing', fin_path
    fin = open(fin_path, 'rb')

    def get_index(i, key):
        if key in inds[i]:
            return inds[i][key]
        else:
            return len(inds[i])

    num_lines = 0
    with open(fout_path, 'wb') as fout:
        start_time = time.time()
        while True:
            buf = collect(fin)
            num_lines += len(buf)

            if len(buf) < 1:
                return

            out_buf = ''
            for line in buf:
                fields = line.strip().split('\t')
                vals = [max(x, '0') for x in fields[1:14]]
                cats = [int(max(x, '0'), 16) for x in fields[14:]]
                out_buf += fields[0] + '\t' + '\t'.join(vals) + '\t' + '\t'.join(
                    [str(get_index(i, cats[i])) for i in range(26)]) + '\n'
            fout.write(out_buf)
            if num_lines % 1000000 == 0:
                print num_lines, time.time() - start_time
                start_time = time.time()


def cnt_pos_neg_with_inds(log_path, inds):
    print log_path
    fin = open(log_path, 'rb')

    num_lines = 0
    body_cnts = np.array([[0.0, 0.0] for _i in range(26)])
    tail_cnts = np.array([[0.0, 0.0] for _i in range(26)])
    while True:
        start_time = time.time()
        buf = collect(fin)
        num_lines += len(buf)
        if len(buf) < 1:
            print body_cnts[:, 1] / body_cnts.sum(axis=1)
            print tail_cnts[:, 1] / tail_cnts.sum(axis=1)
            print time.time() - start_time
            return

        for line in buf:
            fields = line.strip().split('\t')
            label = int(fields[0])
            cats = [int(max(x, '0'), 16) for x in fields[14:]]
            for _i in range(26):
                if cats[_i] in inds[_i]:
                    body_cnts[_i][label] += 1
                else:
                    tail_cnts[_i][label] += 1


if __name__ == '__main__':
    # save = pickle.load(open('../data/stat.pickle', 'rb'))
    # indices = [{} for i in range(26)]
    # trivial = [set() for i in range(26)]

    # for i in range(26):
    #     set = save['sets'][i]
    #     for k, v in set.iteritems():
    #         if v > 10:
    #             indices[i][k] = len(indices[i])
    #         else:
    #             trivial[i].add(k)

    # print [len(x) + 1 for x in indices]
    #
    # pickle.dump({'ind': indices, 'tri': trivial}, open('../data/stat.index.pickle', 'wb'))
    save = pickle.load(open('../data/2.5.stat.pickle'))
    cats = save['sets']
    for fltr in [100]:
        print fltr
        inds = build_indices(cats, fltr)
        print [len(x) for x in inds]
        make_index('../data/test.nds.2.5.shuf', '../data/test.nds.2.5.shuf.ind.%d' % fltr, inds, fltr)
        make_index('../data/test.unif.2.5.shuf', '../data/test.unif.2.5.shuf.ind.%d' % fltr, inds, fltr)
        make_index('../data/nds.2.5.shuf', '../data/nds.2.5.shuf.ind.%d' % fltr, inds, fltr)
        # cnt_pos_neg_with_inds('../data/test.nds.2.5', inds)
        # cnt_pos_neg_with_inds('../data/test.unif.2.5', inds)
        # cnt_pos_neg_with_inds('../data/nds.2.5', inds)

        # shuffle and merge files
        # file_list = ['../data/nds.2.5.' + str(i) for i in range(1, 20)]
        # merge_file(file_list, '../data/nds.2.5.shuf')
        # print 'shuffle %s finish' % '../data/nds.2.5.shuf'
        # file_list = ['../data/test.nds.2.5.' + str(i) for i in range(1, 4)]
        # merge_file(file_list, '../data/test.nds.2.5.shuf')
        # print 'shuffle %s finish' % '../data/test.nds.2.5.shuf'
        # file_list = ['../data/test.unif.2.5.' + str(i) for i in range(1, 3)]
        # merge_file(file_list, '../data/test.unif.2.5.shuf')
        # print 'shuffle %s finish' % '../data/test.unif.2.5.shuf'
