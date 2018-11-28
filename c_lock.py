import argparse

import cluster_lock


def main(args):
    t = cluster_lock.ClusterLock(args)
    t.trace()


if __name__ == '__main__':
    parser = argparse.ArgumentParser('tracer')

    parser.add_argument('-nc',
                        '--no-ctx',
                        action='store_true',
                        help='don\'t show ctx in the attributes')

    parser.add_argument('-hi',
                        '--holder-ids',
                        nargs='+',
                        help='show only records who relevant to this holder(s)')

    parser.add_argument('lock_names',
                        nargs='*',
                        help='show only specific locks')

    args = parser.parse_args()
    main(args)
