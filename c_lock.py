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

    args = parser.parse_args()
    main(args)
