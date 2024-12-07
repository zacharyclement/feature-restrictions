from feature_restriction.event_handlers import (
    BaseEventHandler,
    ChargebackOccurredHandler,
    CreditCardAddedHandler,
    PurchaseMadeHandler,
    ScamMessageFlaggedHandler,
)
from feature_restriction.redis_user_manager import RedisUserManager
from feature_restriction.rules import (
    BaseRule,
    ChargebackRatioRule,
    ScamMessageRule,
    UniqueZipCodeRule,
)
from feature_restriction.tripwire_manager import RedisTripwireManager


class RuleRegistry:
    """
    Manages the registration and retrieval of rules.

    Attributes
    ----------
    rules : dict
        A dictionary containing registered rules, where keys are rule names
        and values are rule instances.
    """

    def __init__(self):
        self.rules = {}

    def register_rule(self, rule_instance: BaseRule):
        """
        Registers a rule instance.

        Parameters
        ----------
        rule_instance : object
            The rule instance to register. It must have a `name` attribute.

        Raises
        ------
        ValueError
            If the `rule_instance` does not have a `name` attribute or
            if a rule with the same name is already registered.
        """
        rule_name = getattr(rule_instance, "name", None)
        if not rule_name:
            raise ValueError(
                f"Rule '{rule_instance.__class__.__name__}' must have a 'name' attribute."
            )
        if rule_name in self.rules:
            raise ValueError(
                f"A rule with the name '{rule_name}' is already registered."
            )
        self.rules[rule_name] = rule_instance

    def get_rule(self, rule_name: str):
        """
        Retrieves a rule by its name.

        Parameters
        ----------
        rule_name : str
            The name of the rule to retrieve.

        Returns
        -------
        object or None
            The rule instance if found, otherwise `None`.
        """
        return self.rules.get(rule_name)

    def register_default_rules(
        self, tripwire_manager: RedisTripwireManager, user_manager: RedisUserManager
    ):
        """
        Registers default rules.

        Parameters
        ----------
        tripwire_manager : object
            The manager for handling tripwires.
        user_manager : object
            The manager for handling users.

        Notes
        -----
        Default rules include `UniqueZipCodeRule`, `ScamMessageRule`, and
        `ChargebackRatioRule`.
        """
        self.register_rule(UniqueZipCodeRule(tripwire_manager, user_manager))
        self.register_rule(ScamMessageRule(tripwire_manager, user_manager))
        self.register_rule(ChargebackRatioRule(tripwire_manager, user_manager))


class EventHandlerRegistry:
    """
    Manages the registration and retrieval of event handlers.

    Attributes
    ----------
    event_handler_registry : dict
        A dictionary containing registered event handlers, where keys are event names
        and values are event handler instances.
    event_rules_mapping : dict
        A dictionary mapping event names to a list of associated rule names.
    """

    def __init__(self):
        self.event_handler_registry = {}
        self.event_rules_mapping = {}

    def register_event_handler(
        self, event_handler_instance: BaseEventHandler, rule_names=None
    ):
        """
        Registers an event handler with an optional list of associated rule names.

        Parameters
        ----------
        event_handler_instance : object
            The instance of the event handler to register. It must have an `event_name` attribute.
        rule_names : list of str, optional
            A list of rule names associated with the event. Default is None.

        Raises
        ------
        ValueError
            If the `event_handler_instance` does not have an `event_name` attribute or
            if an event handler with the same event name is already registered.
        """
        event_name = getattr(event_handler_instance, "event_name", None)
        if not event_name:
            raise ValueError(
                f"Handler '{event_handler_instance.__class__.__name__}' must have 'event_name' attribute."
            )

        # Check for duplicate event name
        if event_name in self.event_handler_registry:
            existing_handler = self.event_handler_registry[
                event_name
            ].__class__.__name__
            raise ValueError(
                f"Duplicate event name detected: '{event_name}' is already registered by handler '{existing_handler}'."
            )

        self.event_handler_registry[event_name] = event_handler_instance
        self.event_rules_mapping[event_name] = rule_names or []

    def get_event_handler(self, event_name):
        """
        Retrieves an event handler by its event name.

        Parameters
        ----------
        event_name : str
            The name of the event to retrieve the handler for.

        Returns
        -------
        object or None
            The event handler instance if found, otherwise `None`.
        """
        return self.event_handler_registry.get(event_name)

    def get_rules_for_event(self, event_name):
        """
        Retrieves the rules associated with an event.

        Parameters
        ----------
        event_name : str
            The name of the event to retrieve rules for.

        Returns
        -------
        list of str
            A list of rule names associated with the event. If no rules are
            associated, an empty list is returned.
        """
        return self.event_rules_mapping.get(event_name, [])

    def register_default_event_handlers(self, tripwire_manager, user_manager):
        """
        Registers default event handlers and their associated rules.

        Parameters
        ----------
        tripwire_manager : object
            The manager for handling tripwires.
        user_manager : object
            The manager for handling users.

        Notes
        -----
        Default event handlers include:
        - `CreditCardAddedHandler` with `unique_zip_code_rule`
        - `ScamMessageFlaggedHandler` with `scam_message_rule`
        - `ChargebackOccurredHandler` with `chargeback_ratio_rule`
        - `PurchaseMadeHandler` with no associated rules.
        """
        self.register_event_handler(
            CreditCardAddedHandler(tripwire_manager, user_manager),
            rule_names=["unique_zip_code_rule"],
        )
        self.register_event_handler(
            ScamMessageFlaggedHandler(tripwire_manager, user_manager),
            rule_names=["scam_message_rule"],
        )
        self.register_event_handler(
            ChargebackOccurredHandler(tripwire_manager, user_manager),
            rule_names=["chargeback_ratio_rule"],
        )
        self.register_event_handler(
            PurchaseMadeHandler(tripwire_manager, user_manager), rule_names=[]
        )
