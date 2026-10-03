"""Free-player configuration and playback decisions; no capture or UI ownership."""
import copy

QUEUE_LIMIT = 50
BONK_MODES = ('normal', 'instant')


def defaults(roster):
    return dict(queue=list(roster), shuffle=True, loop=True, recent_history=True,
                tips=False, source=None, recent=[])


def validate_config(value, roster):
    if not isinstance(value, dict):
        raise ValueError('Player settings must be an object.')
    result = defaults(roster)
    queue = value.get('queue', result['queue'])
    if not isinstance(queue, list) or not 1 <= len(queue) <= QUEUE_LIMIT:
        raise ValueError('Choose 1–50 queue entries. Duplicates are allowed.')
    if any(type(state) is not int or state not in roster for state in queue):
        raise ValueError('Queue contains an unavailable world. Choose approved Main worlds.')
    result['queue'] = list(queue)
    for key in ('shuffle', 'loop', 'recent_history', 'tips'):
        if key in value and type(value[key]) is not bool:
            raise ValueError(f'{key} must be on or off.')
        result[key] = value.get(key, result[key])
    source = value.get('source')
    # Migrate the old explicit loopback ID. A dynamic system-default selection
    # is deliberately not migrated into a different endpoint.
    if source is None and isinstance(value.get('device'), str) and value['device']:
        source = dict(kind='loopback', id=value['device'], name='Saved output')
    if source is not None:
        if not isinstance(source, dict) or source.get('kind') not in ('loopback', 'microphone') or not isinstance(source.get('id'), str) or not source['id']:
            raise ValueError('Saved audio source is invalid. Select a replacement.')
        source = dict(kind=source['kind'], id=source['id'], name=str(source.get('name', source['id'])))
    result['source'] = source
    result['recent'] = [x for x in value.get('recent', []) if type(x) is int and x in roster][-8:]
    return result


class Playback:
    def __init__(self, config, roster):
        self.roster = tuple(roster)
        self.config = validate_config(config, roster)
        self.pending_config = None
        self.running = False
        self.available = True  # LiveSession gates availability independently of listening intent.
        self.paused = False
        self.holds = set()
        self.bonk_pending = False
        self.bonk_mode = 'normal'  # Session-only; never part of saved config.
        self.bonk_pending_mode = 'normal'
        self.bonk_expedite = False
        self.index = -1
        self.resume_fresh = False
        self.end_reason = ''

    @property
    def held(self):
        return bool(self.holds)

    def start(self):
        self.running = True
        self.paused = False
        self.resume_fresh = True
        self.end_reason = ''

    def stop(self, reason='Stopped · current world is settling'):
        self.running = self.paused = self.bonk_pending = False
        self.bonk_pending_mode = 'normal'
        self.bonk_expedite = False
        self.end_reason = reason

    def pause(self):
        if self.running:
            self.paused = not self.paused
            self.bonk_pending = False
            self.bonk_pending_mode = 'normal'
            self.bonk_expedite = False
            if not self.paused:
                self.resume_fresh = True

    def hold(self, owner, active):
        if active:
            self.holds.add(owner)
        else:
            self.holds.discard(owner)

    def release_focus(self, owner):
        self.holds = {x for x in self.holds if not x.startswith(owner)}

    def set_bonk_mode(self, mode):
        if mode not in BONK_MODES:
            raise ValueError('Choose Normal or Instant Bonk.')
        self.bonk_mode = mode

    def bonk(self, transitioning=False, mode=None):
        if mode is not None:
            self.set_bonk_mode(mode)
        if not self.running or self.paused:
            return
        if transitioning:
            # One bounded speed-up request for the current arrival, never a
            # second queued world. Normal retains its active-handoff behavior.
            if self.bonk_mode == 'instant' and self.available:
                self.bonk_expedite = True
        elif not self.bonk_pending:
            if self.bonk_mode == 'instant' and not self.available:
                return
            self.bonk_pending = True
            self.bonk_pending_mode = self.bonk_mode

    def configure(self, value, current=None):
        config = validate_config(value, self.roster)
        if current is None:
            self.config = config
            self.index = -1
        else:
            # Explicit apply at the next boundary. Editing the panel is a draft.
            self.pending_config = config

    def initial(self, choose):
        self.index = 0
        return choose(self.config['queue']) if self.config['shuffle'] else self.config['queue'][0]

    def next(self, current, choose):
        self.bonk_pending = False
        self.bonk_pending_mode = 'normal'
        self.bonk_expedite = False
        if self.pending_config is not None:
            self.config = self.pending_config
            self.pending_config = None
            self.index = -1
        queue = self.config['queue']
        if self.config['shuffle']:
            self.index = -1
            return choose(queue)
        self.index += 1
        if self.index >= len(queue):
            if self.config['loop']:
                self.index = 0
            else:
                self.stop('Queue complete · final world is settling')
                return None
        return queue[self.index]

    def snapshot(self):
        return dict(running=self.running, available=self.available, paused=self.paused, held=self.held,
                    bonk_mode=self.bonk_mode,
                    queue_index=self.index, config=copy.deepcopy(self.config),
                    pending_config=self.pending_config is not None, reason=self.end_reason)
