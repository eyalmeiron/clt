import subprocess
import simplejson
import colorama
import sys
from datetime import datetime

from descriptions import Descriptions
from colors import Colors


# attribute to not display. when dict then ignore only with this value
ignored_more_attributes = [
    'lockName',
    'holders',
    'newHolders',
    'remainingHolders',
    'holderId',
    'maxHolders',
    {'timeout': ['0s', '0']},
    'key',
    'stringNewHolders',
    'stringPrevHolders',
    'openWatch',
    {'allowMultipleAcquire': ['true']},
]


class ClusterLock(object):

    def __init__(self, args):
        self._ctx = args.ctx
        self._lock_names = args.lock_names
        self._holder_ids = args.holder_ids
        self._no_peek = args.no_peek

        self._locks = {}

    def trace(self):
        self._load_records()
        self._print_locks()

    def _load_records(self):
        info = Descriptions.info
        fails = Descriptions.fails
        successes = Descriptions.successes

        if self._no_peek:
            info = filter(lambda description: 'peek' not in description, info)
            fails = filter(lambda description: 'peek' not in description, fails)
            successes = filter(lambda description: 'peek' not in description, successes)

        all_descriptions = info + fails + successes
        cmd = 'grep --no-filename \'lockName\' *debug*.log | ' \
              'grep \'"lang":"go"\' | ' \
              'grep \'{0}\''.format('\\|'.join(all_descriptions))

        out, err, code = self._run_command(cmd)
        if code == 1:
            self._report('No cluster lock found in the logs', fatal=True)
        elif code == 2:
            self._report('Not found log files', fatal=True)
        elif code != 0:
            self._report(err, fatal=True)
        else:
            for line in out.split('\n'):
                if line != '':
                    json = simplejson.loads(line)
                    if json.get('more') != {}:
                        lock_name, record = self._save_record(json)
                        self._locks[lock_name]['records'].append(record)

    @staticmethod
    def _run_command(command):
        process = subprocess.Popen(['/bin/bash', '-c', command],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)

        out, err = process.communicate()
        return out, err, process.returncode

    def _save_record(self, json):
        record = {}
        lock_name = json.get('more').get('lockName')

        if lock_name not in self._locks:
            self._locks[lock_name] = {
                'max_holders': None,
                'records': [],
                'holders': set(),
            }

        # holder id
        holder_id = json.get('more').get('holderId', '')
        record['holder_id'] = holder_id
        self._locks[lock_name]['holders'].add(holder_id)

        # description
        description = json.get('what')
        if description == 'Succeeded to set holders. Start function':
            description = 'Lock acquired'
        elif description == 'Lock is busy, starting watcher':
            description = 'Lock is busy, waiting for update'
        elif description == 'Got an acquire request' and json.get('more', {}).get('openWatch') == 'false':
            description = 'Got an try_acquire request'
        record['description'] = description

        # timestamp
        record['when'] = json.get('when')

        # max_holders
        attributes = json.get('more')
        if self._locks[lock_name]['max_holders'] is None:
            self._locks[lock_name]['max_holders'] = attributes.get('actual value', attributes.get('maxHolders'))

        # holders
        holders = ''
        if 'holders' in attributes and 'newHolders' in attributes:
            holders = attributes['newHolders']
        elif 'holders' in attributes:
            holders = attributes['holders']
        record['holders'] = holders

        # more attributes
        for ignored_attribute in ignored_more_attributes:
            if type(ignored_attribute) == dict:
                key = ignored_attribute.keys()[0]
                for ignore_value in ignored_attribute[key]:
                    if key in attributes and ignore_value == attributes[key]:
                        del attributes[key]
                        break

            elif ignored_attribute in attributes:
                del attributes[ignored_attribute]
        if self._ctx:
            attributes['ctx'] = json.get('ctx')
        record['more'] = attributes

        return lock_name, record

    def _print_locks(self):
        for lock_name in self._locks:
            if self._lock_names == [] or lock_name in self._lock_names:
                self._print_lock(lock_name)

    def _print_lock(self, lock_name):

        # if holder ids to display wae provided and not in this lock, don't print this lock
        if self._holder_ids is not None:
            if not self.array_include_array(self._holder_ids, self._locks[lock_name]['holders']):
                return

        holders_colors = Colors.get_colors(self._locks[lock_name]['holders'])

        max_holders = self._locks[lock_name]['max_holders']
        max_holders_string = ''
        if max_holders != -1:
            max_holders_string = ' (max holders {0})'.format(self._locks[lock_name]['max_holders'])
        print '\n{0}{1}{2}'.format(self._colorize('Lock name: ', 'reset'),
                                   self._colorize(lock_name, 'white'),
                                   max_holders_string)

        # if not found holders at all to this lock
        if self._locks[lock_name]['holders'] == {None}:
            max_len_holder_id = 10
        else:
            max_len_holder_id = max(map(lambda holder_id: len(holder_id), self._locks[lock_name]['holders']))
        max_len_description = max(map(lambda record: len(record['description']), self._locks[lock_name]['records']))
        max_len_holders = max(map(lambda record: len(str(record['holders'])), self._locks[lock_name]['records']))

        prev_record_time = None
        for record in sorted(self._locks[lock_name]['records'], key=lambda record_in_array: record_in_array['when']):

            if self._holder_ids is not None and record['holder_id'] not in self._holder_ids:
                continue

            when = record['when']
            holder_id = self._colorize(record['holder_id'], holders_colors[record['holder_id']])
            description = record['description']
            # ctx = colorize('ctx={0}'.format(record['ctx']), 'reset')

            attributes = record['more']
            holders = self._colorize_holders(record['holders'])

            string_attributes = ''
            for attribute in attributes:
                string_attributes += '{0}{1}{2}{3}'.format(attribute,
                                                           self._colorize('=', 'reset'),
                                                           attributes[attribute],
                                                           self._colorize(' | ', 'reset'))
            attributes = self._colorize_holders('[{0}]'.format(string_attributes[:-10]))

            # add spaces
            holder_id = '{0}{1}'.format(holder_id, ' ' * (
                        max_len_holder_id - (len(record['holder_id']) if record['holder_id'] is not None else 0)))
            description = '{0}{1}'.format(description, ' ' * (max_len_description - len(description)))
            holders = '{0}{1}'.format(holders, ' ' * (
                        max_len_holders - (len(str(record['holders'])) if record['holders'] is not '' else 0)))

            # colorize description
            if record['description'] in Descriptions.fails:
                description = self._colorize(description, 'red')
            elif record['description'] in Descriptions.successes:
                description = self._colorize(description, 'green')

            prev_record_time = self._print_time_diff(prev_record_time, record['when'])

            print '{when}  {holder_id}  {description}  {holders}  {attributes}'.format(
                when=when,
                holder_id=holder_id,
                description=description,
                holders=holders,
                attributes=attributes
            )

    @staticmethod
    def array_include_array(arr1, arr2):
        for item in arr1:
            if item in arr2:
                return True
        return False

    @staticmethod
    def _colorize(text, color):
        color = getattr(colorama.Fore, color.upper())
        reset_color = colorama.Fore.BLUE
        return u'{0}{1}{2}'.format(color, text, reset_color)

    def _colorize_holders(self, holders):
        if holders == '':
            return ''
        return ''.join([self._colorize('[', 'RESET'), holders[1:-1], self._colorize(']', 'RESET')])

    def _print_time_diff(self, prev_record_time, record_when):
        current_record_time = datetime.strptime(record_when, '%Y-%m-%dT%H:%M:%S.%f')
        if prev_record_time is not None:
            diff_time = current_record_time - prev_record_time
            if diff_time.total_seconds() > 0.4:
                print self._colorize('|----- {0:.2f} Seconds -----|'.format(diff_time.total_seconds()), 'reset')
        return current_record_time

    def _report(self, message, fatal=False):
        print self._colorize(message, Colors.fatal if fatal else Colors.info)
        if fatal:
            sys.exit(1)
