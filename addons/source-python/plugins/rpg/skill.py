import collections

from listeners.tick import TickRepeat

import rpg.utils


def event_callback(*event_names):
    """Register a callback for events based on their names.

    :param tuple \*event_names:
        Names of the events to register the callback for
    """
    def decorator(callback):
        callback._events = event_names
        return callback
    return decorator


class _SkillMeta(type):
    """Metaclass for taking care of skills' event callbacks.

    Creates :attr:`_event_callbacks` dictionary with the events' names
    as keys and lists of the corresponding callbacks as values.
    """

    def __init__(cls, name, bases, attrs):
        """Register event callbacks upon class's initialization."""
        super().__init__(name, bases, attrs)
        cls._event_callbacks = collections.defaultdict(list)
        for f in attrs.values():
            if not hasattr(f, '_events'):
                continue
            for event_name in f._events:
                cls._event_callbacks[event_name].append(f)


class Skill(metaclass=_SkillMeta):
    """Skills are used by players to gain special powers.

    Each skill has four main attributes:

    * :attr:`name` of the skill.
    * Short :attr:`description` of the skill.
    * :attr:`level` which can be increased to strengthen the skill.
    * :attr:`max_level` to limit the skill from being leveled further.
      If ``None``, the skill can be leveled infinitely.

    Skills also have event callbacks, which are registered using the
    :func:`event_callback` function. These callbacks use the skill's
    current level to indicate how strong the effect should be.

    Skills are created by subclassing this base class and defining the
    basic class attributes: :attr:`name`, :attr:`description`,
    and :attr:`max_level`. Unless explicitly defined as class variables,
    name and description are recieved from the class's name and
    docstring. See :meth:`name` and :meth:`description` for more info.

    See :mod:`skills` module for more complete examples of skills,
    but here's a simple ``BonusHealth`` skill to begin with:

    .. code-block:: python

        class Bonus_Health(Skill):
            "Grant +25 bonus health for each level upon spawning."
            max_level = 16

            @callback('player_spawn')
            def _give_health(self, player, **event_args):
                player.health += self.level * 25
    """

    @rpg.utils.ClassProperty
    def class_id(cls):
        """Unique class ID for the skill class.

        Automatically retrieved from the skill class's
        :attr:`__qualname__` unless explicitly overridden in a subclass.
        """
        return cls.__qualname__

    @rpg.utils.ClassProperty
    def name(cls):
        """Name of the skill.

        Automatically retrieved from the skill class's
        :attr:`__name__` unless explicitly overridden in a subclass.
        Any underscores in the :attr:`__name__` are replaced with
        spaces. Override this if actual underscores are needed.
        """
        return cls.__name__.replace('_', ' ')

    @rpg.utils.ClassProperty
    def description(cls):
        """A short description of the skill.

        Automatically retrieved from the skill class's
        :attr:`__doc__` unless explicitly overridden in a subclass.
        """
        return cls.__doc__

    max_level = None

    def __init__(self, level=0):
        """Initialize the skill.

        :param int level:
            Initial level for the skill
        """
        self.level = level

    @property
    def upgrade_cost(self):
        """Cost of upgrading the skill."""
        return (self.level + 1) * 5

    @property
    def downgrade_refund(self):
        """Refund for downgrading the skill."""
        return self.level * 4

    def execute_callbacks(self, event_name, **event_args):
        """Execute a callback for event based on its name.

        :param str event_name:
            Name of the event which's callback to execute
        :param dict \*\*event_args:
            Keyword arguments of the event forwarded to the callback
        """
        if event_name not in self._event_callbacks:
            return
        for callback in self._event_callbacks[event_name]:
            callback(self, **event_args)


class TickRepeatSkill(Skill):
    """Base class for skills that need to use tick repeat.

    Adds a :attr:`tick_repeat` attribute linked to the abstract
    :meth:`_tick` method.
    """

    def __init__(self, level=0):
        """Initialize the skill.

        :param int level:
            Initial level for the skill
        """
        super().__init__(level)
        self.tick_repeat = TickRepeat(self._tick)

    def _tick(self, *args, **kwargs):
        """Callback for the :attr:`tick_repeat` attribute."""
        raise NotImplementedError(
            "_tick method not implemented by a TickRepeatSkill class.")
